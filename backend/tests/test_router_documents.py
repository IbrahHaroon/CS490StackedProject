"""Tests for POST /documents/, GET /documents/{doc_id}, GET /documents/user/{user_id}."""

from database.models.user import create_user


DOCUMENTS_URL = "/documents"


def _document_payload(user_id, **overrides):
    base = {
        "user_id": user_id,
        "document_type": "resume",
        "document_location": "/uploads/resume.pdf",
    }
    base.update(overrides)
    return base


# ─────────────────────────────────────────────────────────────────────────────
# POST /documents/
# ─────────────────────────────────────────────────────────────────────────────

class TestCreateDocument:

    def test_returns_201_on_success(self, client, session):
        user = create_user(session, "doc_c@example.com")
        response = client.post(f"{DOCUMENTS_URL}/", json=_document_payload(user.user_id))
        assert response.status_code == 201

    def test_response_contains_doc_id(self, client, session):
        user = create_user(session, "doc_c@example.com")
        response = client.post(f"{DOCUMENTS_URL}/", json=_document_payload(user.user_id))
        assert "doc_id" in response.json()

    def test_fields_stored_correctly(self, client, session):
        user = create_user(session, "doc_c@example.com")
        response = client.post(f"{DOCUMENTS_URL}/", json=_document_payload(user.user_id))
        body = response.json()
        assert body["document_type"] == "resume"
        assert body["document_location"] == "/uploads/resume.pdf"

    def test_user_id_linked_correctly(self, client, session):
        user = create_user(session, "doc_c@example.com")
        response = client.post(f"{DOCUMENTS_URL}/", json=_document_payload(user.user_id))
        assert response.json()["user_id"] == user.user_id

    def test_missing_document_type_returns_422(self, client, session):
        user = create_user(session, "doc_c@example.com")
        payload = _document_payload(user.user_id)
        del payload["document_type"]
        response = client.post(f"{DOCUMENTS_URL}/", json=payload)
        assert response.status_code == 422


# ─────────────────────────────────────────────────────────────────────────────
# GET /documents/{doc_id}
# ─────────────────────────────────────────────────────────────────────────────

class TestReadDocument:

    def test_returns_200_for_existing_document(self, client, session):
        user = create_user(session, "doc_r@example.com")
        created = client.post(f"{DOCUMENTS_URL}/", json=_document_payload(user.user_id)).json()
        response = client.get(f"{DOCUMENTS_URL}/{created['doc_id']}")
        assert response.status_code == 200

    def test_returns_correct_document(self, client, session):
        user = create_user(session, "doc_r@example.com")
        created = client.post(f"{DOCUMENTS_URL}/", json=_document_payload(user.user_id, document_type="cover_letter")).json()
        response = client.get(f"{DOCUMENTS_URL}/{created['doc_id']}")
        assert response.json()["document_type"] == "cover_letter"

    def test_returns_404_for_missing_document(self, client):
        response = client.get(f"{DOCUMENTS_URL}/99999")
        assert response.status_code == 404


# ─────────────────────────────────────────────────────────────────────────────
# GET /documents/user/{user_id}
# ─────────────────────────────────────────────────────────────────────────────

class TestReadAllDocuments:

    def test_returns_empty_list_for_user_with_no_documents(self, client, session):
        user = create_user(session, "nodocs@example.com")
        response = client.get(f"{DOCUMENTS_URL}/user/{user.user_id}")
        assert response.status_code == 200
        assert response.json() == []

    def test_returns_correct_number_of_documents(self, client, session):
        user = create_user(session, "manydocs@example.com")
        for i in range(3):
            client.post(f"{DOCUMENTS_URL}/", json=_document_payload(user.user_id, document_location=f"/uploads/file{i}.pdf"))
        response = client.get(f"{DOCUMENTS_URL}/user/{user.user_id}")
        assert len(response.json()) == 3

    def test_returns_only_documents_for_correct_user(self, client, session):
        u1 = create_user(session, "docs1@example.com")
        u2 = create_user(session, "docs2@example.com")
        client.post(f"{DOCUMENTS_URL}/", json=_document_payload(u1.user_id))
        client.post(f"{DOCUMENTS_URL}/", json=_document_payload(u2.user_id))
        client.post(f"{DOCUMENTS_URL}/", json=_document_payload(u2.user_id, document_location="/uploads/cv.pdf"))
        assert len(client.get(f"{DOCUMENTS_URL}/user/{u1.user_id}").json()) == 1
        assert len(client.get(f"{DOCUMENTS_URL}/user/{u2.user_id}").json()) == 2

    def test_all_returned_items_belong_to_user(self, client, session):
        user = create_user(session, "ownership@example.com")
        for i in range(2):
            client.post(f"{DOCUMENTS_URL}/", json=_document_payload(user.user_id, document_location=f"/f{i}.pdf"))
        docs = client.get(f"{DOCUMENTS_URL}/user/{user.user_id}").json()
        for doc in docs:
            assert doc["user_id"] == user.user_id
