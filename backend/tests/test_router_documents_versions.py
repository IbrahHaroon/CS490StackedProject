"""Endpoint tests for the version-history surface of /documents (S3-003).

Covers:
- POST /documents/{id}/versions  → version_number auto-increment, ownership
- GET  /documents/{id}/versions  → desc-sorted list, ownership
- GET  /documents/{id}/versions/{vid}/content → returns version body
- POST /documents/{id}/versions/{vid}/restore → updates current_version_id
- 404 / 403 paths for cross-user, cross-document, and missing version IDs
"""

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

DOC_BODY = {
    "title": "Resume.txt",
    "document_type": "Resume",
    "content": "v1 body",
    "source": "manual",
}


def _make_doc(client, headers, **overrides):
    """POST /documents and return the created document JSON."""
    body = {**DOC_BODY, **overrides}
    res = client.post("/documents", json=body, headers=headers)
    assert res.status_code == 201, res.text
    return res.json()


def _add_version(client, headers, document_id, *, content="next", source="edit"):
    res = client.post(
        f"/documents/{document_id}/versions",
        json={"content": content, "source": source},
        headers=headers,
    )
    return res


# ─────────────────────────────────────────────────────────────────────────────
# POST /documents/{id}/versions — append a new version
# ─────────────────────────────────────────────────────────────────────────────


class TestCreateVersion:
    def test_returns_201(self, client, user_with_auth):
        _, headers = user_with_auth
        doc = _make_doc(client, headers)
        res = _add_version(client, headers, doc["document_id"])
        assert res.status_code == 201

    def test_first_appended_version_is_two(self, client, user_with_auth):
        """The doc's initial create produced v1; this should produce v2."""
        _, headers = user_with_auth
        doc = _make_doc(client, headers)
        res = _add_version(client, headers, doc["document_id"], content="v2")
        assert res.json()["version_number"] == 2

    def test_third_version_increments_to_three(self, client, user_with_auth):
        _, headers = user_with_auth
        doc = _make_doc(client, headers)
        _add_version(client, headers, doc["document_id"], content="v2")
        res = _add_version(client, headers, doc["document_id"], content="v3")
        assert res.json()["version_number"] == 3

    def test_content_persisted(self, client, user_with_auth):
        _, headers = user_with_auth
        doc = _make_doc(client, headers)
        res = _add_version(client, headers, doc["document_id"], content="hello v2")
        assert res.json()["content"] == "hello v2"

    def test_source_persisted(self, client, user_with_auth):
        _, headers = user_with_auth
        doc = _make_doc(client, headers)
        res = _add_version(
            client, headers, doc["document_id"], content="x", source="ai"
        )
        assert res.json()["source"] == "ai"

    def test_unauth_returns_401(self, client, user_with_auth):
        _, headers = user_with_auth
        doc = _make_doc(client, headers)
        res = client.post(
            f"/documents/{doc['document_id']}/versions", json={"content": "x"}
        )
        assert res.status_code == 401

    def test_other_user_cannot_append(
        self, client, user_with_auth, other_user_with_auth
    ):
        _, owner_headers = user_with_auth
        _, attacker_headers = other_user_with_auth
        doc = _make_doc(client, owner_headers)
        res = _add_version(client, attacker_headers, doc["document_id"])
        assert res.status_code == 403


# ─────────────────────────────────────────────────────────────────────────────
# GET /documents/{id}/versions — list (desc by version_number)
# ─────────────────────────────────────────────────────────────────────────────


class TestListVersions:
    def test_returns_initial_v1(self, client, user_with_auth):
        _, headers = user_with_auth
        doc = _make_doc(client, headers)
        res = client.get(f"/documents/{doc['document_id']}/versions", headers=headers)
        assert res.status_code == 200
        assert len(res.json()) == 1
        assert res.json()[0]["version_number"] == 1

    def test_desc_order_after_appends(self, client, user_with_auth):
        _, headers = user_with_auth
        doc = _make_doc(client, headers)
        _add_version(client, headers, doc["document_id"], content="v2")
        _add_version(client, headers, doc["document_id"], content="v3")
        res = client.get(f"/documents/{doc['document_id']}/versions", headers=headers)
        assert [v["version_number"] for v in res.json()] == [3, 2, 1]

    def test_other_user_gets_403(self, client, user_with_auth, other_user_with_auth):
        _, owner_headers = user_with_auth
        _, attacker_headers = other_user_with_auth
        doc = _make_doc(client, owner_headers)
        res = client.get(
            f"/documents/{doc['document_id']}/versions", headers=attacker_headers
        )
        assert res.status_code == 403


# ─────────────────────────────────────────────────────────────────────────────
# GET /documents/{id}/versions/{vid}/content
# ─────────────────────────────────────────────────────────────────────────────


class TestReadVersionContent:
    def test_returns_text_content(self, client, user_with_auth):
        _, headers = user_with_auth
        doc = _make_doc(client, headers, content="initial body")
        # Find v1's id from the list endpoint
        v1_id = client.get(
            f"/documents/{doc['document_id']}/versions", headers=headers
        ).json()[0]["version_id"]
        res = client.get(
            f"/documents/{doc['document_id']}/versions/{v1_id}/content",
            headers=headers,
        )
        assert res.status_code == 200
        assert res.json()["content"] == "initial body"
        assert res.json()["format"] == "text"

    def test_can_read_old_version_after_appending(self, client, user_with_auth):
        """Adding v2 should not change what /versions/{v1_id}/content returns."""
        _, headers = user_with_auth
        doc = _make_doc(client, headers, content="OLD")
        v1_id = client.get(
            f"/documents/{doc['document_id']}/versions", headers=headers
        ).json()[0]["version_id"]
        _add_version(client, headers, doc["document_id"], content="NEW")
        res = client.get(
            f"/documents/{doc['document_id']}/versions/{v1_id}/content",
            headers=headers,
        )
        assert res.json()["content"] == "OLD"

    def test_404_for_nonexistent_version(self, client, user_with_auth):
        _, headers = user_with_auth
        doc = _make_doc(client, headers)
        res = client.get(
            f"/documents/{doc['document_id']}/versions/99999/content",
            headers=headers,
        )
        assert res.status_code == 404

    def test_404_for_cross_document_version(self, client, user_with_auth):
        """Version belongs to a different document of the same user."""
        _, headers = user_with_auth
        d1 = _make_doc(client, headers, title="A.txt")
        d2 = _make_doc(client, headers, title="B.txt")
        d2_v1_id = client.get(
            f"/documents/{d2['document_id']}/versions", headers=headers
        ).json()[0]["version_id"]
        res = client.get(
            f"/documents/{d1['document_id']}/versions/{d2_v1_id}/content",
            headers=headers,
        )
        assert res.status_code == 404

    def test_403_for_other_user(self, client, user_with_auth, other_user_with_auth):
        _, owner_headers = user_with_auth
        _, attacker_headers = other_user_with_auth
        doc = _make_doc(client, owner_headers)
        v1_id = client.get(
            f"/documents/{doc['document_id']}/versions", headers=owner_headers
        ).json()[0]["version_id"]
        res = client.get(
            f"/documents/{doc['document_id']}/versions/{v1_id}/content",
            headers=attacker_headers,
        )
        assert res.status_code == 403


# ─────────────────────────────────────────────────────────────────────────────
# POST /documents/{id}/versions/{vid}/restore
# ─────────────────────────────────────────────────────────────────────────────


class TestRestoreVersion:
    def _setup_doc_with_two_versions(self, client, headers):
        doc = _make_doc(client, headers, content="v1 body")
        v1_id = client.get(
            f"/documents/{doc['document_id']}/versions", headers=headers
        ).json()[0]["version_id"]
        _add_version(client, headers, doc["document_id"], content="v2 body")
        return doc["document_id"], v1_id

    def test_returns_200_with_updated_document(self, client, user_with_auth):
        _, headers = user_with_auth
        doc_id, v1_id = self._setup_doc_with_two_versions(client, headers)
        res = client.post(
            f"/documents/{doc_id}/versions/{v1_id}/restore", headers=headers
        )
        assert res.status_code == 200
        assert res.json()["current_version_id"] == v1_id

    def test_subsequent_get_document_reflects_restore(self, client, user_with_auth):
        _, headers = user_with_auth
        doc_id, v1_id = self._setup_doc_with_two_versions(client, headers)
        client.post(f"/documents/{doc_id}/versions/{v1_id}/restore", headers=headers)
        doc_after = client.get(f"/documents/{doc_id}", headers=headers).json()
        assert doc_after["current_version_id"] == v1_id

    def test_content_endpoint_returns_restored_version_body(
        self, client, user_with_auth
    ):
        """After restoring v1, GET /content (current) should return v1's body."""
        _, headers = user_with_auth
        doc_id, v1_id = self._setup_doc_with_two_versions(client, headers)
        client.post(f"/documents/{doc_id}/versions/{v1_id}/restore", headers=headers)
        content = client.get(f"/documents/{doc_id}/content", headers=headers).json()
        assert content["content"] == "v1 body"

    def test_404_for_nonexistent_version(self, client, user_with_auth):
        _, headers = user_with_auth
        doc = _make_doc(client, headers)
        res = client.post(
            f"/documents/{doc['document_id']}/versions/99999/restore",
            headers=headers,
        )
        assert res.status_code == 404

    def test_404_for_cross_document_version(self, client, user_with_auth):
        _, headers = user_with_auth
        d1 = _make_doc(client, headers, title="A.txt")
        d2 = _make_doc(client, headers, title="B.txt")
        d2_v1_id = client.get(
            f"/documents/{d2['document_id']}/versions", headers=headers
        ).json()[0]["version_id"]
        res = client.post(
            f"/documents/{d1['document_id']}/versions/{d2_v1_id}/restore",
            headers=headers,
        )
        assert res.status_code == 404

    def test_403_for_other_user(self, client, user_with_auth, other_user_with_auth):
        _, owner_headers = user_with_auth
        _, attacker_headers = other_user_with_auth
        doc_id, v1_id = self._setup_doc_with_two_versions(client, owner_headers)
        res = client.post(
            f"/documents/{doc_id}/versions/{v1_id}/restore", headers=attacker_headers
        )
        assert res.status_code == 403
