"""Tests for document_version.py — create_version, get_versions, get_version, get_latest_version."""

import pytest
from sqlalchemy.exc import IntegrityError

from database.models.document_version import (
    create_version,
    get_latest_version,
    get_version,
    get_versions,
)
from database.models.documents import create_document
from database.models.user import create_user


@pytest.fixture
def user(session):
    return create_user(session, "ver_user@example.com")


@pytest.fixture
def doc(session, user):
    return create_document(session, user.user_id, "Resume", "/docs/resume.pdf")


# ─────────────────────────────────────────────────────────────────────────────
# create_version
# ─────────────────────────────────────────────────────────────────────────────


class TestCreateVersion:
    def test_returns_version_object(self, session, doc):
        ver = create_version(session, doc.doc_id, content="v1 content")
        assert ver is not None

    def test_version_id_assigned(self, session, doc):
        ver = create_version(session, doc.doc_id, content="v1 content")
        assert ver.version_id is not None
        assert ver.version_id >= 1

    def test_first_version_number_is_one(self, session, doc):
        ver = create_version(session, doc.doc_id, content="v1 content")
        assert ver.version_number == 1

    def test_auto_increments_version_number(self, session, doc):
        v1 = create_version(session, doc.doc_id, content="v1")
        v2 = create_version(session, doc.doc_id, content="v2")
        v3 = create_version(session, doc.doc_id, content="v3")
        assert v1.version_number == 1
        assert v2.version_number == 2
        assert v3.version_number == 3

    def test_stores_content(self, session, doc):
        ver = create_version(session, doc.doc_id, content="my resume text")
        assert ver.content == "my resume text"

    def test_stores_document_location(self, session, doc):
        ver = create_version(
            session, doc.doc_id, document_location="/uploads/resume_v1.pdf"
        )
        assert ver.document_location == "/uploads/resume_v1.pdf"

    def test_created_at_set(self, session, doc):
        ver = create_version(session, doc.doc_id, content="v1")
        assert ver.created_at is not None

    def test_doc_id_linked_correctly(self, session, doc):
        ver = create_version(session, doc.doc_id, content="v1")
        assert ver.doc_id == doc.doc_id

    def test_invalid_doc_id_raises(self, session):
        with pytest.raises((IntegrityError, Exception)):
            create_version(session, 99999, content="orphan")
            session.flush()

    def test_versions_scoped_to_document(self, session, user):
        doc1 = create_document(session, user.user_id, "Resume", "/r1.pdf")
        doc2 = create_document(session, user.user_id, "Cover Letter", "/c1.pdf")
        create_version(session, doc1.doc_id, content="d1v1")
        create_version(session, doc1.doc_id, content="d1v2")
        create_version(session, doc2.doc_id, content="d2v1")
        assert get_versions(session, doc1.doc_id).__len__() == 2
        assert get_versions(session, doc2.doc_id).__len__() == 1
        # version numbering is independent per document
        d2_ver = get_versions(session, doc2.doc_id)[0]
        assert d2_ver.version_number == 1


# ─────────────────────────────────────────────────────────────────────────────
# get_versions
# ─────────────────────────────────────────────────────────────────────────────


class TestGetVersions:
    def test_returns_empty_list_for_no_versions(self, session, doc):
        result = get_versions(session, doc.doc_id)
        assert result == []

    def test_returns_ordered_by_version_number(self, session, doc):
        create_version(session, doc.doc_id, content="v1")
        create_version(session, doc.doc_id, content="v2")
        create_version(session, doc.doc_id, content="v3")
        versions = get_versions(session, doc.doc_id)
        assert [v.version_number for v in versions] == [1, 2, 3]

    def test_returns_correct_count(self, session, doc):
        create_version(session, doc.doc_id, content="v1")
        create_version(session, doc.doc_id, content="v2")
        assert len(get_versions(session, doc.doc_id)) == 2

    def test_returns_empty_for_nonexistent_doc(self, session):
        result = get_versions(session, 99999)
        assert result == []


# ─────────────────────────────────────────────────────────────────────────────
# get_version
# ─────────────────────────────────────────────────────────────────────────────


class TestGetVersion:
    def test_returns_correct_version(self, session, doc):
        ver = create_version(session, doc.doc_id, content="target")
        fetched = get_version(session, ver.version_id)
        assert fetched is not None
        assert fetched.version_id == ver.version_id
        assert fetched.content == "target"

    def test_returns_none_for_missing_id(self, session):
        assert get_version(session, 99999) is None

    def test_returns_none_for_zero_id(self, session):
        assert get_version(session, 0) is None


# ─────────────────────────────────────────────────────────────────────────────
# get_latest_version
# ─────────────────────────────────────────────────────────────────────────────


class TestGetLatestVersion:
    def test_returns_none_when_no_versions(self, session, doc):
        assert get_latest_version(session, doc.doc_id) is None

    def test_returns_highest_version_number(self, session, doc):
        create_version(session, doc.doc_id, content="v1")
        create_version(session, doc.doc_id, content="v2")
        create_version(session, doc.doc_id, content="v3 latest")
        latest = get_latest_version(session, doc.doc_id)
        assert latest is not None
        assert latest.version_number == 3
        assert latest.content == "v3 latest"

    def test_returns_single_version_when_only_one(self, session, doc):
        create_version(session, doc.doc_id, content="only one")
        latest = get_latest_version(session, doc.doc_id)
        assert latest.version_number == 1

    def test_returns_none_for_nonexistent_doc(self, session):
        assert get_latest_version(session, 99999) is None
