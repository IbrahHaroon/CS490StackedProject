"""
Unit tests for profile completeness logic.

Tests the compute_profile_completeness() helper which mirrors the
completionFields logic in Profile.jsx so it can be verified independently.
"""

from datetime import date
from unittest.mock import MagicMock

from database.services.sprint2_profile_completeness import (
    CompletenessReport,
    compute_profile_completeness,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _mock_profile(**kwargs) -> MagicMock:
    """Return a mock Profile with the given attributes set."""
    defaults = {
        "first_name": "Jane",
        "last_name": "Doe",
        "phone_number": "555-1234",
        "dob": date(1995, 3, 10),
        "summary": "Experienced engineer.",
    }
    defaults.update(kwargs)
    p = MagicMock()
    for k, v in defaults.items():
        setattr(p, k, v)
    return p


def _mock_document(doc_type: str) -> MagicMock:
    d = MagicMock()
    d.document_type = doc_type
    return d


# ---------------------------------------------------------------------------
# TestCompletenessReportDataclass
# ---------------------------------------------------------------------------


class TestCompletenessReportDataclass:
    def test_completed_count_all_done(self):
        fields = [{"label": "A", "done": True}, {"label": "B", "done": True}]
        r = CompletenessReport(fields=fields)
        assert r.completed_count == 2

    def test_completed_count_none_done(self):
        fields = [{"label": "A", "done": False}, {"label": "B", "done": False}]
        r = CompletenessReport(fields=fields)
        assert r.completed_count == 0

    def test_total_count(self):
        fields = [{"label": str(i), "done": True} for i in range(5)]
        r = CompletenessReport(fields=fields)
        assert r.total_count == 5

    def test_percentage_all_complete(self):
        fields = [{"label": str(i), "done": True} for i in range(7)]
        r = CompletenessReport(fields=fields)
        assert r.percentage == 100

    def test_percentage_none_complete(self):
        fields = [{"label": str(i), "done": False} for i in range(7)]
        r = CompletenessReport(fields=fields)
        assert r.percentage == 0

    def test_percentage_partial(self):
        # 3 out of 7 → 43%
        fields = [{"label": str(i), "done": i < 3} for i in range(7)]
        r = CompletenessReport(fields=fields)
        assert r.percentage == round(3 / 7 * 100)

    def test_is_complete_true(self):
        fields = [{"label": "A", "done": True}]
        r = CompletenessReport(fields=fields)
        assert r.is_complete is True

    def test_is_complete_false(self):
        fields = [{"label": "A", "done": False}]
        r = CompletenessReport(fields=fields)
        assert r.is_complete is False

    def test_missing_returns_only_incomplete_labels(self):
        fields = [
            {"label": "First Name", "done": True},
            {"label": "Phone Number", "done": False},
            {"label": "Resume", "done": False},
        ]
        r = CompletenessReport(fields=fields)
        assert r.missing == ["Phone Number", "Resume"]

    def test_missing_empty_when_all_complete(self):
        fields = [{"label": "A", "done": True}, {"label": "B", "done": True}]
        r = CompletenessReport(fields=fields)
        assert r.missing == []

    def test_percentage_with_empty_fields(self):
        r = CompletenessReport(fields=[])
        assert r.percentage == 0


# ---------------------------------------------------------------------------
# TestComputeProfileCompleteness — full profile
# ---------------------------------------------------------------------------


class TestComputeProfileCompleteness:
    def test_full_profile_with_resume_is_100(self):
        profile = _mock_profile()
        docs = [_mock_document("Resume")]
        report = compute_profile_completeness(profile, "jane@example.com", docs)
        assert report.percentage == 100
        assert report.is_complete is True

    def test_fields_count_matches_expected_seven(self):
        profile = _mock_profile()
        report = compute_profile_completeness(profile, "jane@example.com", [])
        assert report.total_count == 7

    def test_missing_email_detected(self):
        profile = _mock_profile()
        docs = [_mock_document("Resume")]
        report = compute_profile_completeness(profile, None, docs)
        assert "Email" in report.missing

    def test_missing_phone_detected(self):
        profile = _mock_profile(phone_number=None)
        docs = [_mock_document("Resume")]
        report = compute_profile_completeness(profile, "jane@example.com", docs)
        assert "Phone Number" in report.missing

    def test_missing_summary_detected(self):
        profile = _mock_profile(summary=None)
        docs = [_mock_document("Resume")]
        report = compute_profile_completeness(profile, "jane@example.com", docs)
        assert "Summary" in report.missing

    def test_missing_dob_detected(self):
        profile = _mock_profile(dob=None)
        docs = [_mock_document("Resume")]
        report = compute_profile_completeness(profile, "jane@example.com", docs)
        assert "Date of Birth" in report.missing

    def test_missing_resume_detected(self):
        profile = _mock_profile()
        report = compute_profile_completeness(profile, "jane@example.com", [])
        assert "Resume" in report.missing

    def test_cover_letter_does_not_count_as_resume(self):
        profile = _mock_profile()
        docs = [_mock_document("Cover Letter")]
        report = compute_profile_completeness(profile, "jane@example.com", docs)
        assert "Resume" in report.missing

    def test_resume_case_insensitive(self):
        profile = _mock_profile()
        docs = [_mock_document("RESUME")]
        report = compute_profile_completeness(profile, "jane@example.com", docs)
        assert "Resume" not in report.missing

    def test_none_profile_marks_profile_fields_missing(self):
        report = compute_profile_completeness(None, "jane@example.com", [])
        assert "First Name" in report.missing
        assert "Last Name" in report.missing
        assert "Phone Number" in report.missing
        assert "Date of Birth" in report.missing
        assert "Summary" in report.missing

    def test_none_profile_email_still_counted(self):
        report = compute_profile_completeness(None, "jane@example.com", [])
        assert "Email" not in report.missing

    def test_none_documents_treated_as_no_docs(self):
        profile = _mock_profile()
        report = compute_profile_completeness(profile, "jane@example.com", None)
        assert "Resume" in report.missing

    def test_multiple_docs_resume_found(self):
        profile = _mock_profile()
        docs = [_mock_document("Cover Letter"), _mock_document("Resume")]
        report = compute_profile_completeness(profile, "jane@example.com", docs)
        assert "Resume" not in report.missing

    def test_completely_empty_is_0_percent(self):
        report = compute_profile_completeness(None, None, None)
        assert report.percentage == 0

    def test_percentage_increases_as_fields_filled(self):
        # Start with no profile and no docs — add fields one by one
        r0 = compute_profile_completeness(None, None, None)
        r1 = compute_profile_completeness(None, "jane@example.com", None)
        assert r1.percentage > r0.percentage

    def test_missing_first_name_detected(self):
        profile = _mock_profile(first_name=None)
        docs = [_mock_document("Resume")]
        report = compute_profile_completeness(profile, "jane@example.com", docs)
        assert "First Name" in report.missing

    def test_missing_last_name_detected(self):
        profile = _mock_profile(last_name=None)
        docs = [_mock_document("Resume")]
        report = compute_profile_completeness(profile, "jane@example.com", docs)
        assert "Last Name" in report.missing
