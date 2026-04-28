"""Model-level tests for JobDocumentLink.

Covers the persistence helpers (`link_version_to_job`, `unlink`,
`get_links_for_job`), the UNIQUE(job_id, version_id, role) constraint, and
ON DELETE CASCADE behavior from both Job and DocumentVersion.

Router-level ownership rules are exercised separately in
`test_router_documents_security.py::TestJobLinkOwnership`. This file fills
the persistence-layer gap.
"""

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from database.models.document import create_document, hard_delete_document
from database.models.document_version import create_document_version
from database.models.job import create_job, delete_job
from database.models.job_document_link import (
    JobDocumentLink,
    get_links_for_job,
    link_version_to_job,
    unlink,
)
from database.models.user import create_user

# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────


@pytest.fixture
def user(session):
    return create_user(session, "link_user@test.com")


@pytest.fixture
def other_user(session):
    return create_user(session, "link_other@test.com")


@pytest.fixture
def job(session, user):
    return create_job(session, user.user_id, "Backend Engineer", "Stripe")


@pytest.fixture
def doc(session, user):
    return create_document(session, user.user_id, "Resume.txt", "Resume")


@pytest.fixture
def version(session, doc):
    return create_document_version(session, doc.document_id, content="v1 body")


# ─────────────────────────────────────────────────────────────────────────────
# link_version_to_job — happy path
# ─────────────────────────────────────────────────────────────────────────────


class TestLinkVersionToJob:
    def test_creates_link(self, session, job, version):
        link = link_version_to_job(
            session, job_id=job.job_id, version_id=version.version_id, role="resume"
        )
        assert link is not None
        assert link.link_id is not None
        assert link.job_id == job.job_id
        assert link.version_id == version.version_id
        assert link.role == "resume"
        assert link.linked_at is not None

    def test_link_is_persisted(self, session, job, version):
        link = link_version_to_job(
            session, job_id=job.job_id, version_id=version.version_id, role="resume"
        )
        # Round-trip through the DB to confirm persistence
        fetched = session.get(JobDocumentLink, link.link_id)
        assert fetched is not None
        assert fetched.job_id == job.job_id
        assert fetched.version_id == version.version_id

    def test_role_optional_defaults_to_none(self, session, job, version):
        link = link_version_to_job(
            session, job_id=job.job_id, version_id=version.version_id
        )
        assert link.role is None


# ─────────────────────────────────────────────────────────────────────────────
# link_version_to_job — idempotency
# ─────────────────────────────────────────────────────────────────────────────


class TestLinkIdempotency:
    def test_same_triple_returns_existing(self, session, job, version):
        first = link_version_to_job(
            session, job_id=job.job_id, version_id=version.version_id, role="resume"
        )
        second = link_version_to_job(
            session, job_id=job.job_id, version_id=version.version_id, role="resume"
        )
        # Same row, no duplicate
        assert first.link_id == second.link_id

    def test_idempotent_with_null_role(self, session, job, version):
        first = link_version_to_job(
            session, job_id=job.job_id, version_id=version.version_id
        )
        second = link_version_to_job(
            session, job_id=job.job_id, version_id=version.version_id
        )
        assert first.link_id == second.link_id

    def test_no_duplicate_rows_after_repeated_call(self, session, job, version):
        for _ in range(5):
            link_version_to_job(
                session,
                job_id=job.job_id,
                version_id=version.version_id,
                role="resume",
            )
        rows = (
            session.execute(
                select(JobDocumentLink).where(
                    JobDocumentLink.job_id == job.job_id,
                    JobDocumentLink.version_id == version.version_id,
                    JobDocumentLink.role == "resume",
                )
            )
            .scalars()
            .all()
        )
        assert len(rows) == 1


# ─────────────────────────────────────────────────────────────────────────────
# Multiple roles per (job, version)
# ─────────────────────────────────────────────────────────────────────────────


class TestMultipleRoles:
    def test_different_roles_create_separate_links(self, session, job, version):
        l1 = link_version_to_job(
            session, job_id=job.job_id, version_id=version.version_id, role="resume"
        )
        l2 = link_version_to_job(
            session,
            job_id=job.job_id,
            version_id=version.version_id,
            role="cover_letter",
        )
        assert l1.link_id != l2.link_id

    def test_get_links_returns_both_roles(self, session, job, version):
        link_version_to_job(
            session, job_id=job.job_id, version_id=version.version_id, role="resume"
        )
        link_version_to_job(
            session,
            job_id=job.job_id,
            version_id=version.version_id,
            role="cover_letter",
        )
        roles = {link.role for link in get_links_for_job(session, job.job_id)}
        assert roles == {"resume", "cover_letter"}


# ─────────────────────────────────────────────────────────────────────────────
# Unique constraint enforcement at the DB level
# ─────────────────────────────────────────────────────────────────────────────


class TestUniqueConstraint:
    def test_direct_duplicate_insert_raises(self, session, job, version):
        """Bypass the helper and confirm the UNIQUE(job_id, version_id, role)
        constraint is enforced by the DB itself."""
        link_version_to_job(
            session, job_id=job.job_id, version_id=version.version_id, role="resume"
        )
        dupe = JobDocumentLink(
            job_id=job.job_id, version_id=version.version_id, role="resume"
        )
        session.add(dupe)
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()


# ─────────────────────────────────────────────────────────────────────────────
# unlink
# ─────────────────────────────────────────────────────────────────────────────


class TestUnlink:
    def test_removes_link(self, session, job, version):
        link = link_version_to_job(
            session, job_id=job.job_id, version_id=version.version_id, role="resume"
        )
        assert unlink(session, link.link_id) is True
        assert session.get(JobDocumentLink, link.link_id) is None

    def test_returns_false_for_nonexistent_link(self, session):
        assert unlink(session, 999_999) is False

    def test_unlink_does_not_delete_underlying_version(self, session, job, version):
        link = link_version_to_job(
            session, job_id=job.job_id, version_id=version.version_id, role="resume"
        )
        unlink(session, link.link_id)
        # Version must still exist — only the link was removed.
        from database.models.document_version import DocumentVersion

        assert session.get(DocumentVersion, version.version_id) is not None

    def test_unlink_does_not_delete_underlying_job(self, session, job, version):
        link = link_version_to_job(
            session, job_id=job.job_id, version_id=version.version_id, role="resume"
        )
        unlink(session, link.link_id)
        from database.models.job import get_job

        assert get_job(session, job.job_id) is not None


# ─────────────────────────────────────────────────────────────────────────────
# get_links_for_job
# ─────────────────────────────────────────────────────────────────────────────


class TestGetLinksForJob:
    def test_empty_when_no_links(self, session, job):
        assert get_links_for_job(session, job.job_id) == []

    def test_returns_only_links_for_specified_job(self, session, user, version):
        job_a = create_job(session, user.user_id, "Role A", "Co A")
        job_b = create_job(session, user.user_id, "Role B", "Co B")
        link_version_to_job(
            session, job_id=job_a.job_id, version_id=version.version_id, role="resume"
        )
        link_version_to_job(
            session, job_id=job_b.job_id, version_id=version.version_id, role="resume"
        )
        a_links = get_links_for_job(session, job_a.job_id)
        b_links = get_links_for_job(session, job_b.job_id)
        assert len(a_links) == 1
        assert len(b_links) == 1
        assert a_links[0].job_id == job_a.job_id
        assert b_links[0].job_id == job_b.job_id

    def test_returns_all_versions_linked_to_job(self, session, job, doc):
        v1 = create_document_version(session, doc.document_id, content="v1")
        v2 = create_document_version(session, doc.document_id, content="v2")
        link_version_to_job(
            session, job_id=job.job_id, version_id=v1.version_id, role="resume"
        )
        link_version_to_job(
            session, job_id=job.job_id, version_id=v2.version_id, role="resume_v2"
        )
        links = get_links_for_job(session, job.job_id)
        version_ids = {link.version_id for link in links}
        assert version_ids == {v1.version_id, v2.version_id}


# ─────────────────────────────────────────────────────────────────────────────
# Cascade behavior on parent delete
# ─────────────────────────────────────────────────────────────────────────────


class TestCascadeOnJobDelete:
    def test_deleting_job_removes_links(self, session, job, version):
        link = link_version_to_job(
            session, job_id=job.job_id, version_id=version.version_id, role="resume"
        )
        assert delete_job(session, job.job_id) is True
        # Link must have been cascaded away.
        assert session.get(JobDocumentLink, link.link_id) is None

    def test_deleting_job_does_not_remove_version(self, session, job, version):
        link_version_to_job(
            session, job_id=job.job_id, version_id=version.version_id, role="resume"
        )
        delete_job(session, job.job_id)
        from database.models.document_version import DocumentVersion

        assert session.get(DocumentVersion, version.version_id) is not None


class TestCascadeOnDocumentDelete:
    def test_deleting_document_removes_links(self, session, job, user):
        # Build a doc + version that we can later hard-delete.
        d = create_document(session, user.user_id, "Throwaway.txt", "Resume")
        v = create_document_version(session, d.document_id, content="x")
        link = link_version_to_job(
            session, job_id=job.job_id, version_id=v.version_id, role="resume"
        )
        assert hard_delete_document(session, d.document_id) is True
        assert session.get(JobDocumentLink, link.link_id) is None

    def test_deleting_document_does_not_remove_job(self, session, job, user):
        d = create_document(session, user.user_id, "Throwaway.txt", "Resume")
        v = create_document_version(session, d.document_id, content="x")
        link_version_to_job(
            session, job_id=job.job_id, version_id=v.version_id, role="resume"
        )
        hard_delete_document(session, d.document_id)
        from database.models.job import get_job

        assert get_job(session, job.job_id) is not None


# ─────────────────────────────────────────────────────────────────────────────
# Cross-user data — covered at router layer in test_router_documents_security.
# These confirm the persistence layer itself is permissive (it does not
# enforce ownership; routers do). Documenting that is half the point of a
# test suite — drift here would silently move authorization out of the API.
# ─────────────────────────────────────────────────────────────────────────────


class TestPersistenceLayerHasNoOwnershipChecks:
    def test_can_link_other_users_version_to_own_job(self, session, user, other_user):
        """Persistence does not enforce that version + job share an owner.
        Ownership is enforced at the router; if this assertion ever fails
        because someone added a check here, the router check becomes
        redundant — and we should consciously decide where to enforce it.
        """
        my_job = create_job(session, user.user_id, "Role", "Co")
        their_doc = create_document(session, other_user.user_id, "Theirs.txt", "Resume")
        their_v = create_document_version(
            session, their_doc.document_id, content="theirs"
        )
        link = link_version_to_job(
            session, job_id=my_job.job_id, version_id=their_v.version_id
        )
        assert link is not None
        assert link.link_id is not None
