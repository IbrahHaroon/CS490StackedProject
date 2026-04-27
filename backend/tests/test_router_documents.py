"""Security, ownership, and happy-path tests for the /documents router."""

import io

DOCS_URL = "/documents"
PROFILE_PAYLOAD = {
    "first_name": "Alice",
    "last_name": "Smith",
    "dob": "1990-01-01",
    "address_line": "1 Test St",
    "state": "CA",
    "zip_code": "90001",
}


def _create_profile(client, user_id, headers):
    """Create a minimal profile for user (required by /documents/upload)."""
    client.post(
        "/profile/",
        json={**PROFILE_PAYLOAD, "user_id": user_id},
        headers=headers,
    )


def _create_text_document(client, headers, title="Test Doc", content="Hello world"):
    """Create a text-content (AI-style) document owned by the caller."""
    res = client.post(
        f"{DOCS_URL}",
        json={"title": title, "document_type": "Resume", "content": content},
        headers=headers,
    )
    assert res.status_code == 201
    return res.json()["document_id"]


def _upload_txt_document(client, user_id, headers, filename="test.txt"):
    """Upload a .txt file document (file-backed, requires profile)."""
    _create_profile(client, user_id, headers)
    res = client.post(
        f"{DOCS_URL}/upload",
        files={"file": (filename, io.BytesIO(b"plain text content"), "text/plain")},
        data={"document_type": "Resume"},
        headers=headers,
    )
    assert res.status_code == 201
    return res.json()["document_id"]


class TestDocumentsUnauthenticated:
    """Every protected endpoint must reject requests with no token (401)."""

    def test_list_me_requires_auth(self, client):
        assert client.get(f"{DOCS_URL}/me").status_code == 401

    def test_read_document_requires_auth(self, client):
        assert client.get(f"{DOCS_URL}/99999").status_code == 401

    def test_update_document_requires_auth(self, client):
        assert client.put(f"{DOCS_URL}/99999", json={"title": "x"}).status_code == 401

    def test_delete_document_requires_auth(self, client):
        assert client.delete(f"{DOCS_URL}/99999").status_code == 401

    def test_read_content_requires_auth(self, client):
        assert client.get(f"{DOCS_URL}/99999/content").status_code == 401

    def test_write_content_requires_auth(self, client):
        assert (
            client.put(f"{DOCS_URL}/99999/content", json={"content": "x"}).status_code
            == 401
        )

    def test_download_requires_auth(self, client):
        assert client.get(f"{DOCS_URL}/99999/download").status_code == 401

    def test_list_versions_requires_auth(self, client):
        assert client.get(f"{DOCS_URL}/99999/versions").status_code == 401

    def test_create_version_requires_auth(self, client):
        assert (
            client.post(f"{DOCS_URL}/99999/versions", json={"content": "x"}).status_code
            == 401
        )

    def test_list_tags_requires_auth(self, client):
        assert client.get(f"{DOCS_URL}/99999/tags").status_code == 401

    def test_create_tag_requires_auth(self, client):
        assert (
            client.post(f"{DOCS_URL}/99999/tags", json={"label": "t"}).status_code
            == 401
        )


class TestDocumentsNonExistent:
    """Requesting a document that does not exist must return 404, not 500."""

    def test_read_nonexistent_returns_404(self, client, user_with_auth):
        _, headers = user_with_auth
        assert client.get(f"{DOCS_URL}/99999", headers=headers).status_code == 404

    def test_update_nonexistent_returns_404(self, client, user_with_auth):
        _, headers = user_with_auth
        assert (
            client.put(
                f"{DOCS_URL}/99999", json={"title": "x"}, headers=headers
            ).status_code
            == 404
        )

    def test_delete_nonexistent_returns_404(self, client, user_with_auth):
        _, headers = user_with_auth
        assert client.delete(f"{DOCS_URL}/99999", headers=headers).status_code == 404

    def test_read_content_nonexistent_returns_404(self, client, user_with_auth):
        _, headers = user_with_auth
        assert (
            client.get(f"{DOCS_URL}/99999/content", headers=headers).status_code == 404
        )

    def test_download_nonexistent_returns_404(self, client, user_with_auth):
        _, headers = user_with_auth
        assert (
            client.get(f"{DOCS_URL}/99999/download", headers=headers).status_code == 404
        )


class TestDocumentsCrossUserOwnership:
    """User B must receive 403 on every endpoint that targets User A's document."""

    def _setup(self, client, user_with_auth):
        """Create a document owned by User A, return (doc_id, headers_a, user_a_id)."""
        user_a_id, headers_a = user_with_auth
        doc_id = _create_text_document(client, headers_a)
        return doc_id, headers_a, user_a_id

    def test_user_b_cannot_read_user_a_document(
        self, client, user_with_auth, other_user_with_auth
    ):
        doc_id, _, _ = self._setup(client, user_with_auth)
        _, headers_b = other_user_with_auth
        assert client.get(f"{DOCS_URL}/{doc_id}", headers=headers_b).status_code == 403

    def test_user_b_cannot_update_user_a_document(
        self, client, user_with_auth, other_user_with_auth
    ):
        doc_id, _, _ = self._setup(client, user_with_auth)
        _, headers_b = other_user_with_auth
        assert (
            client.put(
                f"{DOCS_URL}/{doc_id}", json={"title": "hacked"}, headers=headers_b
            ).status_code
            == 403
        )

    def test_user_b_cannot_delete_user_a_document(
        self, client, user_with_auth, other_user_with_auth
    ):
        doc_id, _, _ = self._setup(client, user_with_auth)
        _, headers_b = other_user_with_auth
        assert (
            client.delete(f"{DOCS_URL}/{doc_id}", headers=headers_b).status_code == 403
        )

    def test_user_b_cannot_read_content_of_user_a_document(
        self, client, user_with_auth, other_user_with_auth
    ):
        doc_id, _, _ = self._setup(client, user_with_auth)
        _, headers_b = other_user_with_auth
        assert (
            client.get(f"{DOCS_URL}/{doc_id}/content", headers=headers_b).status_code
            == 403
        )

    def test_user_b_cannot_write_content_of_user_a_document(
        self, client, user_with_auth, other_user_with_auth
    ):
        doc_id, _, _ = self._setup(client, user_with_auth)
        _, headers_b = other_user_with_auth
        assert (
            client.put(
                f"{DOCS_URL}/{doc_id}/content",
                json={"content": "injected"},
                headers=headers_b,
            ).status_code
            == 403
        )

    def test_user_b_cannot_download_user_a_document(
        self, client, user_with_auth, other_user_with_auth
    ):
        doc_id, _, _ = self._setup(client, user_with_auth)
        _, headers_b = other_user_with_auth
        assert (
            client.get(f"{DOCS_URL}/{doc_id}/download", headers=headers_b).status_code
            == 403
        )

    def test_user_b_cannot_list_versions_of_user_a_document(
        self, client, user_with_auth, other_user_with_auth
    ):
        doc_id, _, _ = self._setup(client, user_with_auth)
        _, headers_b = other_user_with_auth
        assert (
            client.get(f"{DOCS_URL}/{doc_id}/versions", headers=headers_b).status_code
            == 403
        )

    def test_user_b_cannot_create_version_for_user_a_document(
        self, client, user_with_auth, other_user_with_auth
    ):
        doc_id, _, _ = self._setup(client, user_with_auth)
        _, headers_b = other_user_with_auth
        assert (
            client.post(
                f"{DOCS_URL}/{doc_id}/versions",
                json={"content": "v2"},
                headers=headers_b,
            ).status_code
            == 403
        )

    def test_user_b_cannot_list_tags_of_user_a_document(
        self, client, user_with_auth, other_user_with_auth
    ):
        doc_id, _, _ = self._setup(client, user_with_auth)
        _, headers_b = other_user_with_auth
        assert (
            client.get(f"{DOCS_URL}/{doc_id}/tags", headers=headers_b).status_code
            == 403
        )

    def test_user_b_cannot_add_tag_to_user_a_document(
        self, client, user_with_auth, other_user_with_auth
    ):
        doc_id, _, _ = self._setup(client, user_with_auth)
        _, headers_b = other_user_with_auth
        assert (
            client.post(
                f"{DOCS_URL}/{doc_id}/tags",
                json={"label": "stolen"},
                headers=headers_b,
            ).status_code
            == 403
        )


class TestDocumentsHappyPath:
    """Owner can perform all CRUD operations on their own documents."""

    def test_owner_can_list_documents(self, client, user_with_auth):
        _, headers = user_with_auth
        assert client.get(f"{DOCS_URL}/me", headers=headers).status_code == 200

    def test_owner_can_create_text_document(self, client, user_with_auth):
        _, headers = user_with_auth
        res = client.post(
            f"{DOCS_URL}",
            json={"title": "My Resume", "document_type": "Resume", "content": "Hello"},
            headers=headers,
        )
        assert res.status_code == 201
        assert res.json()["title"] == "My Resume"

    def test_owner_can_read_document(self, client, user_with_auth):
        _, headers = user_with_auth
        doc_id = _create_text_document(client, headers)
        assert client.get(f"{DOCS_URL}/{doc_id}", headers=headers).status_code == 200

    def test_owner_can_update_document_title(self, client, user_with_auth):
        _, headers = user_with_auth
        doc_id = _create_text_document(client, headers)
        res = client.put(
            f"{DOCS_URL}/{doc_id}", json={"title": "Updated"}, headers=headers
        )
        assert res.status_code == 200
        assert res.json()["title"] == "Updated"

    def test_owner_can_read_document_content(self, client, user_with_auth):
        _, headers = user_with_auth
        doc_id = _create_text_document(client, headers, content="My content")
        res = client.get(f"{DOCS_URL}/{doc_id}/content", headers=headers)
        assert res.status_code == 200
        assert "My content" in res.json()["content"]

    def test_owner_can_download_text_document(self, client, user_with_auth):
        _, headers = user_with_auth
        doc_id = _create_text_document(client, headers, content="Download me")
        res = client.get(f"{DOCS_URL}/{doc_id}/download", headers=headers)
        assert res.status_code == 200
        assert "attachment" in res.headers.get("content-disposition", "").lower()

    def test_download_content_disposition_has_filename(self, client, user_with_auth):
        _, headers = user_with_auth
        doc_id = _create_text_document(client, headers, title="My Resume")
        res = client.get(f"{DOCS_URL}/{doc_id}/download", headers=headers)
        assert res.status_code == 200
        assert "filename" in res.headers.get("content-disposition", "").lower()

    def test_owner_can_soft_delete_document(self, client, user_with_auth):
        _, headers = user_with_auth
        doc_id = _create_text_document(client, headers)
        res = client.put(
            f"{DOCS_URL}/{doc_id}", json={"is_deleted": True}, headers=headers
        )
        assert res.status_code == 200
        assert res.json()["is_deleted"] is True

    def test_owner_can_hard_delete_document(self, client, user_with_auth):
        _, headers = user_with_auth
        doc_id = _create_text_document(client, headers)
        assert client.delete(f"{DOCS_URL}/{doc_id}", headers=headers).status_code == 204
        assert client.get(f"{DOCS_URL}/{doc_id}", headers=headers).status_code == 404

    def test_owner_can_add_tag(self, client, user_with_auth):
        _, headers = user_with_auth
        doc_id = _create_text_document(client, headers)
        res = client.post(
            f"{DOCS_URL}/{doc_id}/tags", json={"label": "priority"}, headers=headers
        )
        assert res.status_code == 201

    def test_owner_can_list_tags(self, client, user_with_auth):
        _, headers = user_with_auth
        doc_id = _create_text_document(client, headers)
        client.post(
            f"{DOCS_URL}/{doc_id}/tags", json={"label": "priority"}, headers=headers
        )
        res = client.get(f"{DOCS_URL}/{doc_id}/tags", headers=headers)
        assert res.status_code == 200
        assert any(t["label"] == "priority" for t in res.json())


class TestDocumentsTokenBlacklist:
    """A token that has been logged out must be rejected with 401."""

    def test_blacklisted_token_rejected_on_documents_me(self, client, user_with_auth):
        _, headers = user_with_auth
        # Confirm we can access before logout
        assert client.get(f"{DOCS_URL}/me", headers=headers).status_code == 200
        # Logout to blacklist the token
        client.post("/auth/logout", headers=headers)
        # Subsequent request must be rejected
        assert client.get(f"{DOCS_URL}/me", headers=headers).status_code == 401

    def test_blacklisted_token_rejected_on_document_read(self, client, user_with_auth):
        _, headers = user_with_auth
        doc_id = _create_text_document(client, headers)
        client.post("/auth/logout", headers=headers)
        assert client.get(f"{DOCS_URL}/{doc_id}", headers=headers).status_code == 401
