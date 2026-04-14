"""
Profile completeness helper.

Computes a structured completeness report for a user's profile so that
both the API and tests can reason about it without duplicating logic.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from database.models.documents import Documents
    from database.models.profile import Profile


@dataclass
class CompletenessReport:
    fields: list[dict]  # [{"label": str, "done": bool}, ...]

    @property
    def completed_count(self) -> int:
        return sum(1 for f in self.fields if f["done"])

    @property
    def total_count(self) -> int:
        return len(self.fields)

    @property
    def percentage(self) -> int:
        if self.total_count == 0:
            return 0
        return round((self.completed_count / self.total_count) * 100)

    @property
    def missing(self) -> list[str]:
        return [f["label"] for f in self.fields if not f["done"]]

    @property
    def is_complete(self) -> bool:
        return self.completed_count == self.total_count


def compute_profile_completeness(
    profile: "Profile | None",
    email: str | None,
    documents: "list[Documents] | None" = None,
) -> CompletenessReport:
    """
    Return a CompletenessReport for the given profile data.

    Parameters
    ----------
    profile:
        The Profile ORM object (or None if not yet created).
    email:
        The user's email address.
    documents:
        List of Documents objects owned by the user (used to check resume presence).
    """
    docs = documents or []
    has_resume = any(d.document_type.lower() == "resume" for d in docs)

    fields = [
        {"label": "First Name", "done": bool(profile and profile.first_name)},
        {"label": "Last Name", "done": bool(profile and profile.last_name)},
        {"label": "Email", "done": bool(email)},
        {"label": "Phone Number", "done": bool(profile and profile.phone_number)},
        {"label": "Date of Birth", "done": bool(profile and profile.dob)},
        {"label": "Summary", "done": bool(profile and profile.summary)},
        {"label": "Resume", "done": has_resume},
    ]

    return CompletenessReport(fields=fields)
