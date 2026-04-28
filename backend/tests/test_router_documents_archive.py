"""Router-level behavior tests for document archive/restore (soft delete).

Existing `test_router_documents_security.py::TestArchiveOwnership` covers
auth (401/403) and the happy-path 200, but does not verify that archive
actually flips `is_deleted` on the underlying record or that archived
documents disappear from the default listing. PRD §4.3 calls these out
explicitly: "Soft delete and restore" with library-level visibility rules.

These tests fill that behavior gap.
"""


def _make_doc(client, headers, title="Archive Target"):
    r = client.post(
        "/documents",
        json={
            "title": title,
            "document_type": "Resume",
            "status": "Draft",
            "content": "body",
        },
        headers=headers,
    )
    assert r.status_code == 201
    return r.json()


def _list_my_docs(client, headers, *, include_archived=False):
    url = "/documents/me"
    if include_archived:
        url += "?include_archived=true"
    r = client.get(url, headers=headers)
    assert r.status_code == 200
    return r.json()


# ─────────────────────────────────────────────────────────────────────────────
# Archive flips is_deleted
# ─────────────────────────────────────────────────────────────────────────────


class TestArchiveSetsFlag:
    def test_archive_sets_is_deleted_true(self, client, user_with_auth):
        _, headers = user_with_auth
        doc = _make_doc(client, headers)
        assert doc["is_deleted"] is False  # baseline

        r = client.put(
            f"/documents/{doc['document_id']}",
            json={"is_deleted": True},
            headers=headers,
        )
        assert r.status_code == 200
        assert r.json()["is_deleted"] is True

    def test_subsequent_get_reflects_archive(self, client, user_with_auth):
        _, headers = user_with_auth
        doc = _make_doc(client, headers)
        client.put(
            f"/documents/{doc['document_id']}",
            json={"is_deleted": True},
            headers=headers,
        )
        r = client.get(f"/documents/{doc['document_id']}", headers=headers)
        assert r.status_code == 200
        assert r.json()["is_deleted"] is True


# ─────────────────────────────────────────────────────────────────────────────
# Listing visibility rules — the load-bearing PRD requirement
# ─────────────────────────────────────────────────────────────────────────────


class TestArchiveHidesFromDefaultList:
    def test_archived_doc_excluded_from_default_listing(self, client, user_with_auth):
        _, headers = user_with_auth
        keep = _make_doc(client, headers, title="Keep")
        archive_me = _make_doc(client, headers, title="Archive me")

        # Pre-archive: both visible.
        ids_before = {d["document_id"] for d in _list_my_docs(client, headers)}
        assert keep["document_id"] in ids_before
        assert archive_me["document_id"] in ids_before

        client.put(
            f"/documents/{archive_me['document_id']}",
            json={"is_deleted": True},
            headers=headers,
        )

        # Post-archive: archived one is hidden.
        ids_after = {d["document_id"] for d in _list_my_docs(client, headers)}
        assert keep["document_id"] in ids_after
        assert archive_me["document_id"] not in ids_after

    def test_archived_doc_visible_with_include_deleted_flag(
        self, client, user_with_auth
    ):
        _, headers = user_with_auth
        doc = _make_doc(client, headers)
        client.put(
            f"/documents/{doc['document_id']}",
            json={"is_deleted": True},
            headers=headers,
        )
        ids = {
            d["document_id"]
            for d in _list_my_docs(client, headers, include_archived=True)
        }
        assert doc["document_id"] in ids


# ─────────────────────────────────────────────────────────────────────────────
# Restore reverses archive
# ─────────────────────────────────────────────────────────────────────────────


class TestRestoreReappearsInList:
    def test_restore_clears_is_deleted(self, client, user_with_auth):
        _, headers = user_with_auth
        doc = _make_doc(client, headers)
        client.put(
            f"/documents/{doc['document_id']}",
            json={"is_deleted": True},
            headers=headers,
        )
        r = client.put(
            f"/documents/{doc['document_id']}",
            json={"is_deleted": False},
            headers=headers,
        )
        assert r.status_code == 200
        assert r.json()["is_deleted"] is False

    def test_restored_doc_reappears_in_default_listing(self, client, user_with_auth):
        _, headers = user_with_auth
        doc = _make_doc(client, headers)
        client.put(
            f"/documents/{doc['document_id']}",
            json={"is_deleted": True},
            headers=headers,
        )
        ids_archived = {d["document_id"] for d in _list_my_docs(client, headers)}
        assert doc["document_id"] not in ids_archived

        client.put(
            f"/documents/{doc['document_id']}",
            json={"is_deleted": False},
            headers=headers,
        )
        ids_restored = {d["document_id"] for d in _list_my_docs(client, headers)}
        assert doc["document_id"] in ids_restored


# ─────────────────────────────────────────────────────────────────────────────
# Idempotency / preservation
# ─────────────────────────────────────────────────────────────────────────────


class TestArchivePreservesContent:
    def test_archive_does_not_delete_versions(self, client, user_with_auth):
        _, headers = user_with_auth
        doc = _make_doc(client, headers)
        v_before = client.get(
            f"/documents/{doc['document_id']}/versions", headers=headers
        ).json()
        assert len(v_before) >= 1

        client.put(
            f"/documents/{doc['document_id']}",
            json={"is_deleted": True},
            headers=headers,
        )

        # Archive is soft — versions remain queryable to the owner.
        v_after = client.get(
            f"/documents/{doc['document_id']}/versions", headers=headers
        ).json()
        assert len(v_after) == len(v_before)

    def test_archive_preserves_title(self, client, user_with_auth):
        _, headers = user_with_auth
        doc = _make_doc(client, headers, title="Distinctive Title")
        client.put(
            f"/documents/{doc['document_id']}",
            json={"is_deleted": True},
            headers=headers,
        )
        r = client.get(f"/documents/{doc['document_id']}", headers=headers)
        assert r.json()["title"] == "Distinctive Title"


class TestArchiveIdempotency:
    def test_archiving_already_archived_doc_is_noop(self, client, user_with_auth):
        _, headers = user_with_auth
        doc = _make_doc(client, headers)
        # Archive twice
        for _ in range(2):
            r = client.put(
                f"/documents/{doc['document_id']}",
                json={"is_deleted": True},
                headers=headers,
            )
            assert r.status_code == 200
            assert r.json()["is_deleted"] is True

    def test_restoring_already_active_doc_is_noop(self, client, user_with_auth):
        _, headers = user_with_auth
        doc = _make_doc(client, headers)
        # Restore an already-active doc
        r = client.put(
            f"/documents/{doc['document_id']}",
            json={"is_deleted": False},
            headers=headers,
        )
        assert r.status_code == 200
        assert r.json()["is_deleted"] is False
