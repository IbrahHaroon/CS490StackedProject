"""Endpoint tests for S3-007 — Document duplicate and rename actions.

Covers:
- POST /documents/{id}/duplicate — copies title (with " (copy)" suffix), type,
  status, and the source's current version content into a new document
- PUT  /documents/{id}        — renames a document (and tolerates partial
  metadata updates without nulling other fields)
- 401 / 403 / 404 paths for cross-user, missing, and unauthenticated access
"""

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

DOC_BODY = {
    "title": "Resume.txt",
    "document_type": "Resume",
    "status": "Draft",
    "content": "v1 body",
    "source": "manual",
}


def _make_doc(client, headers, **overrides):
    """POST /documents and return the created document JSON."""
    body = {**DOC_BODY, **overrides}
    res = client.post("/documents", json=body, headers=headers)
    assert res.status_code == 201, res.text
    return res.json()


def _list_versions(client, headers, document_id):
    return client.get(f"/documents/{document_id}/versions", headers=headers).json()


# ─────────────────────────────────────────────────────────────────────────────
# POST /documents/{id}/duplicate
# ─────────────────────────────────────────────────────────────────────────────


class TestDuplicateDocument:
    def test_returns_201(self, client, user_with_auth):
        _, headers = user_with_auth
        doc = _make_doc(client, headers)
        res = client.post(f"/documents/{doc['document_id']}/duplicate", headers=headers)
        assert res.status_code == 201

    def test_response_has_new_document_id(self, client, user_with_auth):
        _, headers = user_with_auth
        doc = _make_doc(client, headers)
        res = client.post(f"/documents/{doc['document_id']}/duplicate", headers=headers)
        assert res.json()["document_id"] != doc["document_id"]

    def test_title_has_copy_suffix(self, client, user_with_auth):
        _, headers = user_with_auth
        doc = _make_doc(client, headers, title="My Resume")
        res = client.post(f"/documents/{doc['document_id']}/duplicate", headers=headers)
        assert res.json()["title"] == "My Resume (copy)"

    def test_document_type_copied(self, client, user_with_auth):
        _, headers = user_with_auth
        doc = _make_doc(client, headers, document_type="Cover Letter")
        res = client.post(f"/documents/{doc['document_id']}/duplicate", headers=headers)
        assert res.json()["document_type"] == "Cover Letter"

    def test_status_copied(self, client, user_with_auth):
        _, headers = user_with_auth
        doc = _make_doc(client, headers, status="Final")
        res = client.post(f"/documents/{doc['document_id']}/duplicate", headers=headers)
        assert res.json()["status"] == "Final"

    def test_owner_is_current_user(self, client, user_with_auth):
        user_id, headers = user_with_auth
        doc = _make_doc(client, headers)
        res = client.post(f"/documents/{doc['document_id']}/duplicate", headers=headers)
        assert res.json()["user_id"] == user_id

    def test_content_copied_into_v1_of_new_doc(self, client, user_with_auth):
        _, headers = user_with_auth
        doc = _make_doc(client, headers, content="original body")
        new_doc = client.post(
            f"/documents/{doc['document_id']}/duplicate", headers=headers
        ).json()
        # GET the new doc's current content — should match the source's body
        content = client.get(
            f"/documents/{new_doc['document_id']}/content", headers=headers
        ).json()
        assert content["content"] == "original body"

    def test_duplicate_starts_at_v1_with_source_duplicate(self, client, user_with_auth):
        _, headers = user_with_auth
        doc = _make_doc(client, headers)
        new_doc = client.post(
            f"/documents/{doc['document_id']}/duplicate", headers=headers
        ).json()
        versions = _list_versions(client, headers, new_doc["document_id"])
        assert len(versions) == 1
        assert versions[0]["version_number"] == 1
        assert versions[0]["source"] == "duplicate"

    def test_404_for_nonexistent_source(self, client, user_with_auth):
        _, headers = user_with_auth
        res = client.post("/documents/99999/duplicate", headers=headers)
        assert res.status_code == 404

    def test_403_for_other_user_document(
        self, client, user_with_auth, other_user_with_auth
    ):
        _, owner_headers = user_with_auth
        _, attacker_headers = other_user_with_auth
        doc = _make_doc(client, owner_headers)
        res = client.post(
            f"/documents/{doc['document_id']}/duplicate", headers=attacker_headers
        )
        assert res.status_code == 403

    def test_unauth_returns_401(self, client, user_with_auth):
        _, headers = user_with_auth
        doc = _make_doc(client, headers)
        # No Authorization header
        res = client.post(f"/documents/{doc['document_id']}/duplicate")
        assert res.status_code == 401


# ─────────────────────────────────────────────────────────────────────────────
# PUT /documents/{id}  (rename + partial metadata update)
# ─────────────────────────────────────────────────────────────────────────────


class TestRenameDocument:
    def test_returns_200(self, client, user_with_auth):
        _, headers = user_with_auth
        doc = _make_doc(client, headers)
        res = client.put(
            f"/documents/{doc['document_id']}",
            json={"title": "Renamed.txt"},
            headers=headers,
        )
        assert res.status_code == 200

    def test_title_persisted(self, client, user_with_auth):
        _, headers = user_with_auth
        doc = _make_doc(client, headers, title="Old Name")
        client.put(
            f"/documents/{doc['document_id']}",
            json={"title": "New Name"},
            headers=headers,
        )
        # Subsequent GET reflects the rename
        fetched = client.get(f"/documents/{doc['document_id']}", headers=headers).json()
        assert fetched["title"] == "New Name"

    def test_other_metadata_unchanged(self, client, user_with_auth):
        _, headers = user_with_auth
        doc = _make_doc(client, headers, document_type="Cover Letter", status="Final")
        client.put(
            f"/documents/{doc['document_id']}",
            json={"title": "Renamed"},
            headers=headers,
        )
        fetched = client.get(f"/documents/{doc['document_id']}", headers=headers).json()
        assert fetched["document_type"] == "Cover Letter"
        assert fetched["status"] == "Final"
        assert fetched["is_deleted"] is False

    def test_partial_update_only_changes_title(self, client, user_with_auth):
        """A PUT with ONLY the `title` key should not null out other columns."""
        _, headers = user_with_auth
        doc = _make_doc(client, headers, document_type="Resume", status="Draft")
        res = client.put(
            f"/documents/{doc['document_id']}",
            json={"title": "Just the title"},
            headers=headers,
        )
        body = res.json()
        assert body["title"] == "Just the title"
        # Type/status preserved by the endpoint's "if value is not None" guard
        assert body["document_type"] == "Resume"
        assert body["status"] == "Draft"

    def test_404_for_nonexistent_doc(self, client, user_with_auth):
        _, headers = user_with_auth
        res = client.put("/documents/99999", json={"title": "X"}, headers=headers)
        assert res.status_code == 404

    def test_403_for_other_user_document(
        self, client, user_with_auth, other_user_with_auth
    ):
        _, owner_headers = user_with_auth
        _, attacker_headers = other_user_with_auth
        doc = _make_doc(client, owner_headers)
        res = client.put(
            f"/documents/{doc['document_id']}",
            json={"title": "Hijacked"},
            headers=attacker_headers,
        )
        assert res.status_code == 403

    def test_unauth_returns_401(self, client, user_with_auth):
        _, headers = user_with_auth
        doc = _make_doc(client, headers)
        res = client.put(f"/documents/{doc['document_id']}", json={"title": "X"})
        assert res.status_code == 401
