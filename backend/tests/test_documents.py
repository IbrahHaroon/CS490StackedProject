"""Tests for documents.py — create_document, get_document, lookup_documents, get_all_documents."""

import pytest
from database.models.user import create_user
from database.models.documents import create_document, get_document, lookup_documents, get_all_documents


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
        doc = create_document(session, user.user_id, "Resume", "/storage/user1/resume.pdf")
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
