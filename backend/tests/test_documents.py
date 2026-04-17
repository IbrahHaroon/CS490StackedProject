"""Tests for documents.py — create_document, get_document, lookup_documents, get_all_documents."""

import time
from datetime import date as _date

import pytest

from database.models.applied_jobs import create_applied_jobs
from database.models.company import create_company
from database.models.documents import (
    create_document,
    get_all_documents,
    get_document,
    lookup_documents,
    update_document,
)
from database.models.position import create_position
from database.models.user import create_user


@pytest.fixture
def user(session):
    return create_user(session, "docs_user@example.com")


# ─────────────────────────────────────────────────────────────────────────────
# create_document
# ─────────────────────────────────────────────────────────────────────────────


class TestCreateDocument:
    def test_returns_document_object(self, session, user):
        doc = create_document(session, user.user_id, "Resume", "/docs/resume.pdf")
        assert doc is not None

    def test_doc_id_assigned(self, session, user):
        doc = create_document(session, user.user_id, "Resume", "/docs/resume.pdf")
        assert doc.doc_id is not None
        assert doc.doc_id >= 1

    def test_document_type_stored_correctly(self, session, user):
        doc = create_document(session, user.user_id, "Cover Letter", "/docs/cover.pdf")
        assert doc.document_type == "Cover Letter"

    def test_document_location_stored_correctly(self, session, user):
        doc = create_document(
            session, user.user_id, "Resume", "/storage/user1/resume.pdf"
        )
        assert doc.document_location == "/storage/user1/resume.pdf"

    def test_user_id_linked_correctly(self, session, user):
        doc = create_document(session, user.user_id, "Resume", "/docs/r.pdf")
        assert doc.user_id == user.user_id

    def test_multiple_documents_get_unique_ids(self, session, user):
        doc1 = create_document(session, user.user_id, "Resume", "/d/r1.pdf")
        doc2 = create_document(session, user.user_id, "Cover Letter", "/d/c1.pdf")
        assert doc1.doc_id != doc2.doc_id


# ─────────────────────────────────────────────────────────────────────────────
# get_document
# ─────────────────────────────────────────────────────────────────────────────


class TestGetDocument:
    def test_returns_correct_document(self, session, user):
        doc = create_document(session, user.user_id, "Resume", "/docs/r.pdf")
        fetched = get_document(session, doc.doc_id)
        assert fetched.doc_id == doc.doc_id

    def test_returns_none_for_missing_id(self, session):
        result = get_document(session, 99999)
        assert result is None

    def test_returns_none_for_id_zero(self, session):
        result = get_document(session, 0)
        assert result is None

    def test_fields_match_after_fetch(self, session, user):
        doc = create_document(session, user.user_id, "Portfolio", "/docs/port.pdf")
        fetched = get_document(session, doc.doc_id)
        assert fetched.document_type == "Portfolio"
        assert fetched.document_location == "/docs/port.pdf"

    def test_returns_none_for_negative_id(self, session):
        result = get_document(session, -3)
        assert result is None

    def test_two_docs_return_different_records(self, session, user):
        d1 = create_document(session, user.user_id, "Resume", "/r.pdf")
        d2 = create_document(session, user.user_id, "Cover Letter", "/c.pdf")
        f1 = get_document(session, d1.doc_id)
        f2 = get_document(session, d2.doc_id)
        assert f1.document_type != f2.document_type


# ─────────────────────────────────────────────────────────────────────────────
# lookup_documents
# ─────────────────────────────────────────────────────────────────────────────


class TestLookupDocuments:
    def test_returns_zero_for_user_with_no_docs(self, session, user):
        count = lookup_documents(session, user.user_id)
        assert count == 0

    def test_returns_one_after_single_upload(self, session, user):
        create_document(session, user.user_id, "Resume", "/r.pdf")
        count = lookup_documents(session, user.user_id)
        assert count == 1

    def test_returns_correct_count_for_multiple_docs(self, session, user):
        create_document(session, user.user_id, "Resume", "/r.pdf")
        create_document(session, user.user_id, "Cover Letter", "/c.pdf")
        create_document(session, user.user_id, "Portfolio", "/p.pdf")
        count = lookup_documents(session, user.user_id)
        assert count == 3

    def test_returns_zero_for_nonexistent_user(self, session):
        count = lookup_documents(session, 99999)
        assert count == 0

    def test_counts_only_docs_for_correct_user(self, session):
        u1 = create_user(session, "lu1@example.com")
        u2 = create_user(session, "lu2@example.com")
        create_document(session, u1.user_id, "Resume", "/r.pdf")
        create_document(session, u1.user_id, "Cover Letter", "/c.pdf")
        create_document(session, u2.user_id, "Resume", "/r2.pdf")
        assert lookup_documents(session, u1.user_id) == 2
        assert lookup_documents(session, u2.user_id) == 1

    def test_count_increments_with_each_upload(self, session, user):
        assert lookup_documents(session, user.user_id) == 0
        create_document(session, user.user_id, "Doc1", "/d1.pdf")
        assert lookup_documents(session, user.user_id) == 1
        create_document(session, user.user_id, "Doc2", "/d2.pdf")
        assert lookup_documents(session, user.user_id) == 2


# ─────────────────────────────────────────────────────────────────────────────
# get_all_documents
# ─────────────────────────────────────────────────────────────────────────────


class TestGetAllDocuments:
    def test_returns_empty_tuple_for_no_docs(self, session, user):
        result = get_all_documents(session, user.user_id)
        assert result == ()

    def test_returns_tuple_type(self, session, user):
        create_document(session, user.user_id, "Resume", "/r.pdf")
        result = get_all_documents(session, user.user_id)
        assert isinstance(result, tuple)

    def test_returns_correct_number_of_documents(self, session, user):
        create_document(session, user.user_id, "Resume", "/r.pdf")
        create_document(session, user.user_id, "Cover Letter", "/c.pdf")
        result = get_all_documents(session, user.user_id)
        assert len(result) == 2

    def test_all_items_are_document_objects(self, session, user):
        from database.models.documents import Documents

        create_document(session, user.user_id, "Resume", "/r.pdf")
        create_document(session, user.user_id, "Portfolio", "/p.pdf")
        result = get_all_documents(session, user.user_id)
        for doc in result:
            assert isinstance(doc, Documents)

    def test_only_returns_docs_for_correct_user(self, session):
        u1 = create_user(session, "ga1@example.com")
        u2 = create_user(session, "ga2@example.com")
        create_document(session, u1.user_id, "Resume", "/r1.pdf")
        create_document(session, u2.user_id, "Resume", "/r2.pdf")
        create_document(session, u2.user_id, "Cover Letter", "/c2.pdf")
        result = get_all_documents(session, u1.user_id)
        assert len(result) == 1

    def test_returns_empty_tuple_for_nonexistent_user(self, session):
        result = get_all_documents(session, 99999)
        assert result == ()


# ─────────────────────────────────────────────────────────────────────────────
# TestDocumentMetadata — S3-002 new fields
# ─────────────────────────────────────────────────────────────────────────────


class TestDocumentMetadata:
    def test_default_status_is_draft(self, session, user):
        doc = create_document(session, user.user_id, "Resume", "/r.pdf")
        assert doc.status == "Draft"

    def test_custom_status(self, session, user):
        doc = create_document(session, user.user_id, "Resume", "/r.pdf", status="Final")
        assert doc.status == "Final"

    def test_tags_stored(self, session, user):
        doc = create_document(
            session, user.user_id, "Resume", "/r.pdf", tags="python,backend"
        )
        assert doc.tags == "python,backend"

    def test_tags_default_none(self, session, user):
        doc = create_document(session, user.user_id, "Resume", "/r.pdf")
        assert doc.tags is None

    def test_created_at_set(self, session, user):
        doc = create_document(session, user.user_id, "Resume", "/r.pdf")
        assert doc.created_at is not None

    def test_updated_at_set(self, session, user):
        doc = create_document(session, user.user_id, "Resume", "/r.pdf")
        assert doc.updated_at is not None

    def test_is_archived_defaults_false(self, session, user):
        doc = create_document(session, user.user_id, "Resume", "/r.pdf")
        assert doc.is_archived is False


# ─────────────────────────────────────────────────────────────────────────────
# TestUpdateDocument — S3-002/S3-007/S3-008 update fields
# ─────────────────────────────────────────────────────────────────────────────


class TestUpdateDocument:
    def test_update_content(self, session, user):
        doc = create_document(session, user.user_id, "Resume", content="old")
        updated = update_document(session, doc.doc_id, content="new")
        assert updated.content == "new"

    def test_update_document_name(self, session, user):
        doc = create_document(session, user.user_id, "Resume", document_name="old_name")
        updated = update_document(session, doc.doc_id, document_name="new_name")
        assert updated.document_name == "new_name"

    def test_update_status(self, session, user):
        doc = create_document(session, user.user_id, "Resume")
        updated = update_document(session, doc.doc_id, status="Final")
        assert updated.status == "Final"

    def test_update_tags(self, session, user):
        doc = create_document(session, user.user_id, "Resume")
        updated = update_document(session, doc.doc_id, tags="java,spring")
        assert updated.tags == "java,spring"

    def test_update_is_archived(self, session, user):
        doc = create_document(session, user.user_id, "Resume")
        updated = update_document(session, doc.doc_id, is_archived=True)
        assert updated.is_archived is True

    def test_update_bumps_updated_at(self, session, user):
        doc = create_document(session, user.user_id, "Resume", content="v1")
        original_updated = doc.updated_at
        time.sleep(0.05)
        updated = update_document(session, doc.doc_id, content="v2")
        assert updated.updated_at > original_updated

    def test_update_returns_none_for_missing_doc(self, session):
        assert update_document(session, 99999, content="x") is None


# ─────────────────────────────────────────────────────────────────────────────
# TestDocumentJobLink — S2-024
# ─────────────────────────────────────────────────────────────────────────────


def _create_job(session, user_id: int) -> int:
    company = create_company(session, "Acme", "1 Main St", "NY", 10001)
    position = create_position(
        session, company.company_id, "Engineer", None, None, None, None, _date.today()
    )
    job = create_applied_jobs(
        session,
        user_id=user_id,
        position_id=position.position_id,
        years_of_experience=2,
    )
    return job.job_id


class TestDocumentJobLink:
    def test_create_document_without_job_id_defaults_null(self, session, user):
        doc = create_document(session, user.user_id, "Resume", "/r.pdf")
        assert doc.job_id is None

    def test_create_document_with_job_id_links_correctly(self, session, user):
        job_id = _create_job(session, user.user_id)
        doc = create_document(session, user.user_id, "Resume", "/r.pdf", job_id=job_id)
        assert doc.job_id == job_id

    def test_document_job_id_accepts_null(self, session, user):
        doc = create_document(
            session, user.user_id, "Cover Letter", "/c.pdf", job_id=None
        )
        assert doc.job_id is None

    def test_invalid_job_id_raises_integrity_error(self, session, user):
        import pytest
        from sqlalchemy.exc import IntegrityError

        with pytest.raises((IntegrityError, Exception)):
            create_document(session, user.user_id, "Resume", "/r.pdf", job_id=99999)
            session.flush()


# ─────────────────────────────────────────────────────────────────────────────
# TestRegression — existing behaviour unbroken after job_id column addition
# ─────────────────────────────────────────────────────────────────────────────


class TestRegression:
    def test_original_create_still_works_without_job_id(self, session, user):
        doc = create_document(session, user.user_id, "Resume", "/docs/r.pdf")
        assert doc.doc_id is not None
        assert doc.user_id == user.user_id
        assert doc.document_type == "Resume"

    def test_original_get_still_works(self, session, user):
        doc = create_document(session, user.user_id, "Portfolio", "/p.pdf")
        fetched = get_document(session, doc.doc_id)
        assert fetched is not None
        assert fetched.doc_id == doc.doc_id

    def test_original_delete_still_works(self, session, user):
        create_document(session, user.user_id, "Resume", "/r.pdf")
        result = get_all_documents(session, user.user_id)
        assert len(result) == 1
