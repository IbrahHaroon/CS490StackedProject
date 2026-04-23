"""Model-level tests for DocumentVersion (S3-003).

Covers version_number auto-increment, the UNIQUE(document_id, version_number)
constraint, ordering of `get_versions_for_document`, cascade delete, and the
`restore_version` helper used by POST /documents/{id}/versions/{vid}/restore.
"""

import pytest
from sqlalchemy.exc import IntegrityError

from database.models.document import (
    create_document,
    get_document,
    hard_delete_document,
)
from database.models.document_version import (
    DocumentVersion,
    create_document_version,
    get_document_version,
    get_versions_for_document,
    restore_version,
)
from database.models.user import create_user


@pytest.fixture
def user(session):
    return create_user(session, "ver_user@test.com")


@pytest.fixture
def doc(session, user):
    return create_document(session, user.user_id, "Resume.txt", "Resume")


# ─────────────────────────────────────────────────────────────────────────────
# version_number auto-increment
# ─────────────────────────────────────────────────────────────────────────────


class TestVersionNumberAutoIncrement:
    def test_first_version_is_one(self, session, doc):
        v = create_document_version(session, doc.document_id, content="v1 body")
        assert v.version_number == 1

    def test_second_version_is_two(self, session, doc):
        create_document_version(session, doc.document_id, content="v1")
        v = create_document_version(session, doc.document_id, content="v2")
        assert v.version_number == 2

    def test_independent_per_document(self, session, user):
        d1 = create_document(session, user.user_id, "A.txt", "Resume")
        d2 = create_document(session, user.user_id, "B.txt", "Resume")
        v1_d1 = create_document_version(session, d1.document_id, content="x")
        v1_d2 = create_document_version(session, d2.document_id, content="y")
        # Both should be version_number=1 — counters are scoped per document.
        assert v1_d1.version_number == 1
        assert v1_d2.version_number == 1

    def test_source_field_persisted(self, session, doc):
        v = create_document_version(session, doc.document_id, content="x", source="ai")
        assert v.source == "ai"

    def test_default_source_is_none_when_not_provided(self, session, doc):
        v = create_document_version(session, doc.document_id, content="x")
        assert v.source is None


# ─────────────────────────────────────────────────────────────────────────────
# UNIQUE(document_id, version_number) constraint
# ─────────────────────────────────────────────────────────────────────────────


class TestUniqueVersionNumber:
    def test_duplicate_version_number_rejected(self, session, doc):
        """Manually inserting two rows with the same (document_id, version_number)
        must violate the UNIQUE constraint. The helper auto-increments so this
        only triggers when bypassed."""
        session.add(
            DocumentVersion(
                document_id=doc.document_id, version_number=1, content="first"
            )
        )
        session.commit()
        session.add(
            DocumentVersion(
                document_id=doc.document_id, version_number=1, content="dupe"
            )
        )
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()


# ─────────────────────────────────────────────────────────────────────────────
# get_versions_for_document — ordering + scoping
# ─────────────────────────────────────────────────────────────────────────────


class TestGetVersionsForDocument:
    def test_returns_empty_for_doc_with_no_versions(self, session, doc):
        assert get_versions_for_document(session, doc.document_id) == []

    def test_returns_desc_by_version_number(self, session, doc):
        create_document_version(session, doc.document_id, content="v1")
        create_document_version(session, doc.document_id, content="v2")
        create_document_version(session, doc.document_id, content="v3")
        rows = get_versions_for_document(session, doc.document_id)
        assert [v.version_number for v in rows] == [3, 2, 1]

    def test_does_not_leak_other_documents_versions(self, session, user):
        d1 = create_document(session, user.user_id, "A.txt", "Resume")
        d2 = create_document(session, user.user_id, "B.txt", "Resume")
        create_document_version(session, d1.document_id, content="x")
        create_document_version(session, d2.document_id, content="y1")
        create_document_version(session, d2.document_id, content="y2")
        assert len(get_versions_for_document(session, d1.document_id)) == 1
        assert len(get_versions_for_document(session, d2.document_id)) == 2


# ─────────────────────────────────────────────────────────────────────────────
# Cascade delete: dropping a Document removes its versions
# ─────────────────────────────────────────────────────────────────────────────


class TestCascadeDelete:
    def test_hard_delete_document_removes_its_versions(self, session, doc):
        v1 = create_document_version(session, doc.document_id, content="v1")
        v2 = create_document_version(session, doc.document_id, content="v2")
        assert hard_delete_document(session, doc.document_id) is True
        assert get_document_version(session, v1.version_id) is None
        assert get_document_version(session, v2.version_id) is None


# ─────────────────────────────────────────────────────────────────────────────
# restore_version helper
# ─────────────────────────────────────────────────────────────────────────────


class TestRestoreVersion:
    def test_restore_flips_current_version_id(self, session, doc):
        v1 = create_document_version(session, doc.document_id, content="v1")
        v2 = create_document_version(session, doc.document_id, content="v2")
        # Simulate the create_new_version endpoint that sets current → v2
        from database.models.document import update_document

        update_document(session, doc.document_id, current_version_id=v2.version_id)
        # Now restore back to v1
        updated = restore_version(session, doc.document_id, v1.version_id)
        assert updated is not None
        assert updated.current_version_id == v1.version_id

    def test_restore_returns_updated_document(self, session, doc):
        v1 = create_document_version(session, doc.document_id, content="v1")
        result = restore_version(session, doc.document_id, v1.version_id)
        # Returned object should be the live Document row
        assert result is not None
        assert result.document_id == doc.document_id

    def test_restore_rejects_cross_document_version(self, session, user):
        d1 = create_document(session, user.user_id, "A.txt", "Resume")
        d2 = create_document(session, user.user_id, "B.txt", "Resume")
        v_d2 = create_document_version(session, d2.document_id, content="x")
        # Try to restore d2's version_id against d1 — should fail
        result = restore_version(session, d1.document_id, v_d2.version_id)
        assert result is None
        # And d1's current_version_id stays untouched
        d1_after = get_document(session, d1.document_id)
        assert d1_after.current_version_id is None

    def test_restore_returns_none_for_nonexistent_version(self, session, doc):
        result = restore_version(session, doc.document_id, 99999)
        assert result is None
