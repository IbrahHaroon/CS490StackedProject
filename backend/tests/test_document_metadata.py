"""Tests for Document Metadata Model and Persistence."""

from datetime import datetime

import pytest
from sqlalchemy.orm import Session

from database.models.document import create_document, update_document
from database.models.document_tag import add_tag, get_tags_for_document, remove_tag
from database.models.user import User


@pytest.fixture
def test_document(session: Session, test_user: User):
    """Create a test document."""
    return create_document(
        session,
        user_id=test_user.user_id,
        title="Test Resume",
        document_type="Resume",
        status="Draft",
    )


class TestDocumentMetadata:
    """Test document metadata fields."""

    def test_title_required(self, session: Session, test_user: User):
        """Title is required and stored."""
        doc = create_document(
            session,
            user_id=test_user.user_id,
            title="My Resume",
            document_type="Resume",
        )
        assert doc.title == "My Resume"

    def test_type_required(self, session: Session, test_user: User):
        """Document type is required and stored."""
        doc = create_document(
            session,
            user_id=test_user.user_id,
            title="My Resume",
            document_type="Resume",
        )
        assert doc.document_type == "Resume"

    def test_status_defaults_to_draft(self, session: Session, test_user: User):
        """Status defaults to 'Draft' if not specified."""
        doc = create_document(
            session,
            user_id=test_user.user_id,
            title="New Doc",
            document_type="Cover Letter",
        )
        assert doc.status == "Draft"

    def test_status_can_be_set(self, session: Session, test_user: User):
        """Status can be set on creation."""
        doc = create_document(
            session,
            user_id=test_user.user_id,
            title="New Doc",
            document_type="Cover Letter",
            status="Ready",
        )
        assert doc.status == "Ready"

    def test_ownership_set_on_creation(self, session: Session, test_user: User):
        """User ownership is set and immutable."""
        doc = create_document(
            session,
            user_id=test_user.user_id,
            title="Owned Doc",
            document_type="Resume",
        )
        assert doc.user_id == test_user.user_id
        assert doc.user == test_user


class TestDocumentTimestamps:
    """Test created_at and updated_at timestamps."""

    def test_created_at_set_on_creation(self, session: Session, test_user: User):
        """created_at is set when document is created."""
        before = datetime.utcnow()
        doc = create_document(
            session, user_id=test_user.user_id, title="New Doc", document_type="Resume"
        )
        after = datetime.utcnow()

        assert doc.created_at is not None
        assert before <= doc.created_at <= after

    def test_updated_at_set_on_creation(self, session: Session, test_user: User):
        """updated_at is set when document is created."""
        before = datetime.utcnow()
        doc = create_document(
            session, user_id=test_user.user_id, title="New Doc", document_type="Resume"
        )
        after = datetime.utcnow()

        assert doc.updated_at is not None
        assert before <= doc.updated_at <= after

    def test_updated_at_changes_on_update(self, session: Session, test_document):
        """updated_at changes when document is updated."""
        original_updated = test_document.updated_at

        import time

        time.sleep(0.01)  # Ensure time difference

        updated = update_document(
            session, test_document.document_id, title="Updated Title"
        )

        assert updated.updated_at > original_updated
        assert updated.title == "Updated Title"


class TestDocumentUpdate:
    """Test updating document metadata."""

    def test_update_title(self, session: Session, test_document):
        """Title can be updated."""
        updated = update_document(session, test_document.document_id, title="New Title")
        assert updated.title == "New Title"

    def test_update_type(self, session: Session, test_document):
        """Document type can be updated."""
        updated = update_document(
            session, test_document.document_id, document_type="Cover Letter"
        )
        assert updated.document_type == "Cover Letter"

    def test_update_status(self, session: Session, test_document):
        """Status can be updated."""
        updated = update_document(session, test_document.document_id, status="Ready")
        assert updated.status == "Ready"

    def test_update_multiple_fields(self, session: Session, test_document):
        """Multiple fields can be updated at once."""
        updated = update_document(
            session,
            test_document.document_id,
            title="New Title",
            status="Submitted",
            document_type="Resume v2",
        )
        assert updated.title == "New Title"
        assert updated.status == "Submitted"
        assert updated.document_type == "Resume v2"

    def test_update_none_skips_field(self, session: Session, test_document):
        """Passing None for a field doesn't update it."""
        original_title = test_document.title
        updated = update_document(
            session, test_document.document_id, title=None, status="Ready"
        )
        assert updated.title == original_title
        assert updated.status == "Ready"


class TestDocumentTags:
    """Test document tags (many-to-many)."""

    def test_add_single_tag(self, session: Session, test_document):
        """A tag can be added to a document."""
        tag = add_tag(session, test_document.document_id, "important")
        assert tag is not None
        assert tag.label == "important"
        assert tag.document_id == test_document.document_id

    def test_add_multiple_tags(self, session: Session, test_document):
        """Multiple tags can be added to one document."""
        add_tag(session, test_document.document_id, "important")
        add_tag(session, test_document.document_id, "google")
        add_tag(session, test_document.document_id, "tech")

        tags = get_tags_for_document(session, test_document.document_id)
        assert len(tags) == 3
        labels = {tag.label for tag in tags}
        assert labels == {"important", "google", "tech"}

    def test_duplicate_tag_returns_existing(self, session: Session, test_document):
        """Adding duplicate tag returns existing tag."""
        tag1 = add_tag(session, test_document.document_id, "important")
        tag2 = add_tag(session, test_document.document_id, "important")

        assert tag1.tag_id == tag2.tag_id
        tags = get_tags_for_document(session, test_document.document_id)
        assert len(tags) == 1

    def test_remove_tag(self, session: Session, test_document):
        """A tag can be removed from a document."""
        add_tag(session, test_document.document_id, "important")

        success = remove_tag(session, test_document.document_id, "important")
        assert success is True

        tags = get_tags_for_document(session, test_document.document_id)
        assert len(tags) == 0

    def test_remove_nonexistent_tag_fails(self, session: Session, test_document):
        """Removing non-existent tag returns False."""
        success = remove_tag(session, test_document.document_id, "nonexistent")
        assert success is False

    def test_get_tags_empty_list(self, session: Session, test_document):
        """New document has empty tag list."""
        tags = get_tags_for_document(session, test_document.document_id)
        assert tags == []

    def test_tag_labels_trimmed(self, session: Session, test_document):
        """Tag labels are trimmed of whitespace."""
        tag = add_tag(session, test_document.document_id, "  important  ")
        assert tag.label == "important"

    def test_empty_tag_label_ignored(self, session: Session, test_document):
        """Empty tag labels are ignored."""
        tag = add_tag(session, test_document.document_id, "  ")
        assert tag is None


class TestDocumentSoftDelete:
    """Test soft delete (archiving) functionality."""

    def test_soft_delete_flag(self, session: Session, test_document):
        """Document can be soft deleted via is_deleted flag."""
        updated = update_document(session, test_document.document_id, is_deleted=True)
        assert updated.is_deleted is True

    def test_soft_delete_restore(self, session: Session, test_document):
        """Soft deleted document can be restored."""
        update_document(session, test_document.document_id, is_deleted=True)
        restored = update_document(session, test_document.document_id, is_deleted=False)
        assert restored.is_deleted is False


class TestDocumentIsolation:
    """Test that documents are isolated per user."""

    def test_documents_isolated_by_user(self, session: Session):
        """Each user's documents are separate."""
        from database.models.document import get_documents_for_user
        from database.models.user import create_user

        user1 = create_user(session, "user1@example.com")
        user2 = create_user(session, "user2@example.com")

        doc1 = create_document(
            session, user_id=user1.user_id, title="User1 Doc", document_type="Resume"
        )
        doc2 = create_document(
            session, user_id=user2.user_id, title="User2 Doc", document_type="Resume"
        )

        user1_docs = get_documents_for_user(session, user1.user_id)
        user2_docs = get_documents_for_user(session, user2.user_id)

        assert len(user1_docs) == 1
        assert len(user2_docs) == 1
        assert user1_docs[0].document_id == doc1.document_id
        assert user2_docs[0].document_id == doc2.document_id

    def test_deleted_excluded_from_default_queries(
        self, session: Session, test_user: User
    ):
        """Soft deleted documents are excluded by default."""
        from database.models.document import get_documents_for_user

        doc1 = create_document(
            session, user_id=test_user.user_id, title="Active", document_type="Resume"
        )
        doc2 = create_document(
            session, user_id=test_user.user_id, title="Archived", document_type="Resume"
        )

        update_document(session, doc2.document_id, is_deleted=True)

        active_docs = get_documents_for_user(session, test_user.user_id)
        assert len(active_docs) == 1
        assert active_docs[0].document_id == doc1.document_id

    def test_deleted_included_with_flag(self, session: Session, test_user: User):
        """Soft deleted documents can be included with flag."""
        from database.models.document import get_documents_for_user

        doc1 = create_document(
            session, user_id=test_user.user_id, title="Active", document_type="Resume"
        )
        doc2 = create_document(
            session, user_id=test_user.user_id, title="Archived", document_type="Resume"
        )

        update_document(session, doc2.document_id, is_deleted=True)

        all_docs = get_documents_for_user(
            session, test_user.user_id, include_deleted=True
        )
        assert len(all_docs) == 2
        assert any(doc.document_id == doc1.document_id for doc in all_docs)
        assert any(doc.document_id == doc2.document_id for doc in all_docs)
