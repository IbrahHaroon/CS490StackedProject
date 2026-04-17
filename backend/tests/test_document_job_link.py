"""Tests for document_job_link.py — link/unlink documents to jobs, query links."""

from datetime import date as _date

import pytest
from sqlalchemy.exc import IntegrityError

from database.models.applied_jobs import create_applied_jobs
from database.models.company import create_company
from database.models.document_job_link import (
    get_documents_for_job,
    get_jobs_for_document,
    link_document_to_job,
    unlink_document_from_job,
)
from database.models.documents import create_document
from database.models.position import create_position
from database.models.user import create_user


@pytest.fixture
def user(session):
    return create_user(session, "link_user@example.com")


@pytest.fixture
def doc(session, user):
    return create_document(session, user.user_id, "Resume", "/docs/resume.pdf")


def _create_job(session, user_id: int):
    company = create_company(session, "LinkCorp", "1 Main St", "NY", 10001)
    position = create_position(
        session, company.company_id, "Engineer", None, None, None, None, _date.today()
    )
    return create_applied_jobs(
        session,
        user_id=user_id,
        position_id=position.position_id,
        years_of_experience=2,
    )


# ─────────────────────────────────────────────────────────────────────────────
# link_document_to_job
# ─────────────────────────────────────────────────────────────────────────────


class TestLinkDocumentToJob:
    def test_creates_link(self, session, user, doc):
        job = _create_job(session, user.user_id)
        link = link_document_to_job(session, doc.doc_id, job.job_id)
        assert link is not None
        assert link.doc_id == doc.doc_id
        assert link.job_id == job.job_id

    def test_link_id_assigned(self, session, user, doc):
        job = _create_job(session, user.user_id)
        link = link_document_to_job(session, doc.doc_id, job.job_id)
        assert link.link_id is not None
        assert link.link_id >= 1

    def test_linked_at_set(self, session, user, doc):
        job = _create_job(session, user.user_id)
        link = link_document_to_job(session, doc.doc_id, job.job_id)
        assert link.linked_at is not None

    def test_duplicate_link_returns_existing(self, session, user, doc):
        job = _create_job(session, user.user_id)
        link1 = link_document_to_job(session, doc.doc_id, job.job_id)
        link2 = link_document_to_job(session, doc.doc_id, job.job_id)
        assert link1.link_id == link2.link_id

    def test_invalid_doc_id_raises(self, session, user):
        job = _create_job(session, user.user_id)
        with pytest.raises((IntegrityError, Exception)):
            link_document_to_job(session, 99999, job.job_id)
            session.flush()

    def test_invalid_job_id_raises(self, session, doc):
        with pytest.raises((IntegrityError, Exception)):
            link_document_to_job(session, doc.doc_id, 99999)
            session.flush()


# ─────────────────────────────────────────────────────────────────────────────
# unlink_document_from_job
# ─────────────────────────────────────────────────────────────────────────────


class TestUnlinkDocumentFromJob:
    def test_removes_existing_link(self, session, user, doc):
        job = _create_job(session, user.user_id)
        link_document_to_job(session, doc.doc_id, job.job_id)
        result = unlink_document_from_job(session, doc.doc_id, job.job_id)
        assert result is True

    def test_returns_false_when_no_link(self, session, user, doc):
        job = _create_job(session, user.user_id)
        result = unlink_document_from_job(session, doc.doc_id, job.job_id)
        assert result is False

    def test_link_gone_after_unlink(self, session, user, doc):
        job = _create_job(session, user.user_id)
        link_document_to_job(session, doc.doc_id, job.job_id)
        unlink_document_from_job(session, doc.doc_id, job.job_id)
        assert get_documents_for_job(session, job.job_id) == []


# ─────────────────────────────────────────────────────────────────────────────
# get_documents_for_job
# ─────────────────────────────────────────────────────────────────────────────


class TestGetDocumentsForJob:
    def test_returns_empty_when_no_links(self, session, user):
        job = _create_job(session, user.user_id)
        assert get_documents_for_job(session, job.job_id) == []

    def test_returns_linked_documents(self, session, user):
        doc1 = create_document(session, user.user_id, "Resume", "/r.pdf")
        doc2 = create_document(session, user.user_id, "Cover Letter", "/c.pdf")
        job = _create_job(session, user.user_id)
        link_document_to_job(session, doc1.doc_id, job.job_id)
        link_document_to_job(session, doc2.doc_id, job.job_id)
        links = get_documents_for_job(session, job.job_id)
        assert len(links) == 2

    def test_returns_empty_for_nonexistent_job(self, session):
        assert get_documents_for_job(session, 99999) == []


# ─────────────────────────────────────────────────────────────────────────────
# get_jobs_for_document
# ─────────────────────────────────────────────────────────────────────────────


class TestGetJobsForDocument:
    def test_returns_empty_when_no_links(self, session, doc):
        assert get_jobs_for_document(session, doc.doc_id) == []

    def test_returns_linked_jobs(self, session, user, doc):
        job1 = _create_job(session, user.user_id)
        job2 = _create_job(session, user.user_id)
        link_document_to_job(session, doc.doc_id, job1.job_id)
        link_document_to_job(session, doc.doc_id, job2.job_id)
        links = get_jobs_for_document(session, doc.doc_id)
        assert len(links) == 2

    def test_returns_empty_for_nonexistent_doc(self, session):
        assert get_jobs_for_document(session, 99999) == []
