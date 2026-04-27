"""Security and ownership enforcement tests for the documents router.

Tests critical authorization paths:
- Read, delete, content edit operations
- Tag management
- Job-document linking
- Download endpoints

Follows pattern from test_router_documents_duplicate_rename.py:
each test class covers one endpoint or logical group, with 403 (cross-user)
and 401 (unauthenticated) test methods.
"""


def _make_doc(client, headers):
    """Helper: create a simple document with content owned by the authenticated user."""
    r = client.post(
        "/documents",
        json={
            "title": "Test Doc",
            "document_type": "Resume",
            "status": "Draft",
            "content": "Sample resume content",
        },
        headers=headers,
    )
    assert r.status_code == 201
    return r.json()


def _make_job(client, headers):
    """Helper: create a simple job owned by the authenticated user."""
    r = client.post(
        "/jobs",
        json={"title": "Dev Role", "company_name": "TechCorp", "stage": "Applied"},
        headers=headers,
    )
    assert r.status_code == 201
    return r.json()


class TestReadDocumentOwnership:
    """GET /documents/{id} — read single document metadata."""

    def test_403_other_user_get_document(
        self, client, user_with_auth, other_user_with_auth
    ):
        """Reading another user's document returns 403."""
        _, owner_headers = user_with_auth
        _, attacker_headers = other_user_with_auth
        doc = _make_doc(client, owner_headers)
        res = client.get(f"/documents/{doc['document_id']}", headers=attacker_headers)
        assert res.status_code == 403

    def test_401_unauth_get_document(self, client, user_with_auth):
        """Reading without auth token returns 401."""
        _, headers = user_with_auth
        doc = _make_doc(client, headers)
        res = client.get(f"/documents/{doc['document_id']}")  # no headers
        assert res.status_code == 401

    def test_owner_can_get_own_document(self, client, user_with_auth):
        """Owner can read their own document."""
        _, headers = user_with_auth
        doc = _make_doc(client, headers)
        res = client.get(f"/documents/{doc['document_id']}", headers=headers)
        assert res.status_code == 200


class TestDeleteDocumentOwnership:
    """DELETE /documents/{id} — hard delete."""

    def test_403_other_user_delete(self, client, user_with_auth, other_user_with_auth):
        """Deleting another user's document returns 403."""
        _, owner_headers = user_with_auth
        _, attacker_headers = other_user_with_auth
        doc = _make_doc(client, owner_headers)
        res = client.delete(
            f"/documents/{doc['document_id']}", headers=attacker_headers
        )
        assert res.status_code == 403

    def test_401_unauth_delete(self, client, user_with_auth):
        """Deleting without auth returns 401."""
        _, headers = user_with_auth
        doc = _make_doc(client, headers)
        res = client.delete(f"/documents/{doc['document_id']}")  # no headers
        assert res.status_code == 401

    def test_owner_can_delete_own_document(self, client, user_with_auth):
        """Owner can delete their own document."""
        _, headers = user_with_auth
        doc = _make_doc(client, headers)
        res = client.delete(f"/documents/{doc['document_id']}", headers=headers)
        assert res.status_code == 204


class TestContentOwnership:
    """GET /documents/{id}/content and PUT /documents/{id}/content."""

    def test_403_other_user_get_content(
        self, client, user_with_auth, other_user_with_auth
    ):
        """Reading another user's content returns 403."""
        _, owner_headers = user_with_auth
        _, attacker_headers = other_user_with_auth
        doc = _make_doc(client, owner_headers)
        res = client.get(
            f"/documents/{doc['document_id']}/content", headers=attacker_headers
        )
        assert res.status_code == 403

    def test_401_unauth_get_content(self, client, user_with_auth):
        """Reading content without auth returns 401."""
        _, headers = user_with_auth
        doc = _make_doc(client, headers)
        res = client.get(f"/documents/{doc['document_id']}/content")  # no headers
        assert res.status_code == 401

    def test_403_other_user_put_content(
        self, client, user_with_auth, other_user_with_auth
    ):
        """Editing another user's content returns 403."""
        _, owner_headers = user_with_auth
        _, attacker_headers = other_user_with_auth
        doc = _make_doc(client, owner_headers)
        res = client.put(
            f"/documents/{doc['document_id']}/content",
            json={"content": "hacked"},
            headers=attacker_headers,
        )
        assert res.status_code == 403

    def test_401_unauth_put_content(self, client, user_with_auth):
        """Editing content without auth returns 401."""
        _, headers = user_with_auth
        doc = _make_doc(client, headers)
        res = client.put(
            f"/documents/{doc['document_id']}/content", json={"content": "new"}
        )  # no headers
        assert res.status_code == 401

    def test_owner_can_put_content(self, client, user_with_auth):
        """Owner can edit their own content."""
        _, headers = user_with_auth
        doc = _make_doc(client, headers)
        res = client.put(
            f"/documents/{doc['document_id']}/content",
            json={"content": "updated"},
            headers=headers,
        )
        assert res.status_code == 200


class TestTagsOwnership:
    """GET /documents/{id}/tags, POST /documents/{id}/tags, DELETE /documents/{id}/tags/{label}."""

    def test_403_other_user_list_tags(
        self, client, user_with_auth, other_user_with_auth
    ):
        """Listing tags for another user's doc returns 403."""
        _, owner_headers = user_with_auth
        _, attacker_headers = other_user_with_auth
        doc = _make_doc(client, owner_headers)
        res = client.get(
            f"/documents/{doc['document_id']}/tags", headers=attacker_headers
        )
        assert res.status_code == 403

    def test_401_unauth_list_tags(self, client, user_with_auth):
        """Listing tags without auth returns 401."""
        _, headers = user_with_auth
        doc = _make_doc(client, headers)
        res = client.get(f"/documents/{doc['document_id']}/tags")  # no headers
        assert res.status_code == 401

    def test_403_other_user_add_tag(self, client, user_with_auth, other_user_with_auth):
        """Adding a tag to another user's doc returns 403."""
        _, owner_headers = user_with_auth
        _, attacker_headers = other_user_with_auth
        doc = _make_doc(client, owner_headers)
        res = client.post(
            f"/documents/{doc['document_id']}/tags",
            json={"label": "hacked"},
            headers=attacker_headers,
        )
        assert res.status_code == 403

    def test_401_unauth_add_tag(self, client, user_with_auth):
        """Adding a tag without auth returns 401."""
        _, headers = user_with_auth
        doc = _make_doc(client, headers)
        res = client.post(
            f"/documents/{doc['document_id']}/tags", json={"label": "foo"}
        )
        assert res.status_code == 401

    def test_403_other_user_delete_tag(
        self, client, user_with_auth, other_user_with_auth
    ):
        """Deleting a tag from another user's doc returns 403."""
        _, owner_headers = user_with_auth
        _, attacker_headers = other_user_with_auth
        doc = _make_doc(client, owner_headers)
        # First, owner adds a tag
        client.post(
            f"/documents/{doc['document_id']}/tags",
            json={"label": "test"},
            headers=owner_headers,
        )
        # Then, attacker tries to delete it
        res = client.delete(
            f"/documents/{doc['document_id']}/tags/test", headers=attacker_headers
        )
        assert res.status_code == 403

    def test_owner_can_manage_tags(self, client, user_with_auth):
        """Owner can add and delete their own tags."""
        _, headers = user_with_auth
        doc = _make_doc(client, headers)
        # Add tag
        res = client.post(
            f"/documents/{doc['document_id']}/tags",
            json={"label": "important"},
            headers=headers,
        )
        assert res.status_code == 201
        # Delete tag
        res = client.delete(
            f"/documents/{doc['document_id']}/tags/important", headers=headers
        )
        assert res.status_code == 204


class TestJobLinkOwnership:
    """POST /documents/links, DELETE /documents/links/{id}, GET /documents/links/by-job/{id}."""

    def test_403_link_when_job_owned_by_other(
        self, client, user_with_auth, other_user_with_auth
    ):
        """Linking a doc to another user's job returns 403/404."""
        _, user_a_headers = user_with_auth
        _, user_b_headers = other_user_with_auth

        # User A creates doc and gets its version
        doc = _make_doc(client, user_a_headers)
        version = doc["current_version_id"]

        # User B creates job
        job = _make_job(client, user_b_headers)

        # User A tries to link their doc to User B's job → should fail
        res = client.post(
            "/documents/links",
            json={"job_id": int(job["job_id"]), "version_id": int(version)},
            headers=user_a_headers,
        )
        assert res.status_code == 404  # Job not found for user A

    def test_403_unlink_other_users_job(
        self, client, user_with_auth, other_user_with_auth
    ):
        """Unlinking from another user's job returns 403."""
        _, user_a_headers = user_with_auth
        _, user_b_headers = other_user_with_auth

        # User A creates doc and job, links them
        doc = _make_doc(client, user_a_headers)
        job = _make_job(client, user_a_headers)
        version = doc["current_version_id"]
        link_res = client.post(
            "/documents/links",
            json={"job_id": int(job["job_id"]), "version_id": int(version)},
            headers=user_a_headers,
        )
        assert link_res.status_code == 201
        link_id = link_res.json()["link_id"]

        # User B tries to unlink it
        res = client.delete(f"/documents/links/{link_id}", headers=user_b_headers)
        assert res.status_code == 403

    def test_403_list_links_for_other_users_job(
        self, client, user_with_auth, other_user_with_auth
    ):
        """Listing links for another user's job returns 403/404."""
        _, user_a_headers = user_with_auth
        _, user_b_headers = other_user_with_auth

        # User A creates and links doc to their job
        doc = _make_doc(client, user_a_headers)
        job = _make_job(client, user_a_headers)
        version = doc["current_version_id"]
        client.post(
            "/documents/links",
            json={"job_id": int(job["job_id"]), "version_id": int(version)},
            headers=user_a_headers,
        )

        # User B tries to list links for User A's job
        res = client.get(
            f"/documents/links/by-job/{int(job['job_id'])}", headers=user_b_headers
        )
        assert res.status_code == 404

    def test_403_list_links_detailed_for_other_users_job(
        self, client, user_with_auth, other_user_with_auth
    ):
        """Listing detailed links for another user's job returns 403/404."""
        _, user_a_headers = user_with_auth
        _, user_b_headers = other_user_with_auth

        # User A creates and links doc to their job
        doc = _make_doc(client, user_a_headers)
        job = _make_job(client, user_a_headers)
        version = doc["current_version_id"]
        client.post(
            "/documents/links",
            json={"job_id": int(job["job_id"]), "version_id": int(version)},
            headers=user_a_headers,
        )

        # User B tries to list detailed links for User A's job
        res = client.get(
            f"/documents/links/by-job/{int(job['job_id'])}/detailed",
            headers=user_b_headers,
        )
        assert res.status_code == 404

    def test_owner_can_link_and_unlink(self, client, user_with_auth):
        """Owner can link and unlink their doc to their job."""
        _, headers = user_with_auth
        doc = _make_doc(client, headers)
        job = _make_job(client, headers)
        version = doc["current_version_id"]

        # Link
        res = client.post(
            "/documents/links",
            json={"job_id": int(job["job_id"]), "version_id": int(version)},
            headers=headers,
        )
        assert res.status_code == 201
        link_id = res.json()["link_id"]

        # Unlink
        res = client.delete(f"/documents/links/{link_id}", headers=headers)
        assert res.status_code == 204


class TestDownloadOwnership:
    """GET /documents/{id}/download and GET /documents/{id}/versions/{vid}/download."""

    def test_403_other_user_download_current(
        self, client, user_with_auth, other_user_with_auth
    ):
        """Downloading another user's current version returns 403."""
        _, owner_headers = user_with_auth
        _, attacker_headers = other_user_with_auth
        doc = _make_doc(client, owner_headers)
        res = client.get(
            f"/documents/{doc['document_id']}/download", headers=attacker_headers
        )
        assert res.status_code == 403

    def test_401_unauth_download_current(self, client, user_with_auth):
        """Downloading without auth returns 401."""
        _, headers = user_with_auth
        doc = _make_doc(client, headers)
        res = client.get(f"/documents/{doc['document_id']}/download")  # no headers
        assert res.status_code == 401

    def test_403_other_user_download_version(
        self, client, user_with_auth, other_user_with_auth
    ):
        """Downloading another user's version returns 403."""
        _, owner_headers = user_with_auth
        _, attacker_headers = other_user_with_auth
        doc = _make_doc(client, owner_headers)
        version_id = int(doc["current_version_id"])
        res = client.get(
            f"/documents/{doc['document_id']}/versions/{version_id}/download",
            headers=attacker_headers,
        )
        assert res.status_code == 403

    def test_401_unauth_download_version(self, client, user_with_auth):
        """Downloading a version without auth returns 401."""
        _, headers = user_with_auth
        doc = _make_doc(client, headers)
        version_id = doc["current_version_id"]
        res = client.get(
            f"/documents/{doc['document_id']}/versions/{version_id}/download"
        )  # no headers
        assert res.status_code == 401

    def test_owner_can_download_current(self, client, user_with_auth):
        """Owner can download their current version."""
        _, headers = user_with_auth
        doc = _make_doc(client, headers)
        res = client.get(f"/documents/{doc['document_id']}/download", headers=headers)
        assert res.status_code == 200
        # FileResponse will have application/octet-stream or word doc content-type
        assert len(res.content) > 0

    def test_owner_can_download_version(self, client, user_with_auth):
        """Owner can download a specific version."""
        _, headers = user_with_auth
        doc = _make_doc(client, headers)
        version_id = int(doc["current_version_id"])
        res = client.get(
            f"/documents/{doc['document_id']}/versions/{version_id}/download",
            headers=headers,
        )
        assert res.status_code == 200
        # FileResponse will have binary content
        assert len(res.content) > 0


class TestRenameOwnership:
    """PUT /documents/{id} with title change."""

    def test_403_other_user_rename(self, client, user_with_auth, other_user_with_auth):
        """Renaming another user's document returns 403."""
        _, owner_headers = user_with_auth
        _, attacker_headers = other_user_with_auth
        doc = _make_doc(client, owner_headers)
        res = client.put(
            f"/documents/{doc['document_id']}",
            json={"title": "Hacked Title"},
            headers=attacker_headers,
        )
        assert res.status_code == 403

    def test_401_unauth_rename(self, client, user_with_auth):
        """Renaming without auth returns 401."""
        _, headers = user_with_auth
        doc = _make_doc(client, headers)
        res = client.put(
            f"/documents/{doc['document_id']}", json={"title": "New Title"}
        )  # no headers
        assert res.status_code == 401

    def test_owner_can_rename(self, client, user_with_auth):
        """Owner can rename their own document."""
        _, headers = user_with_auth
        doc = _make_doc(client, headers)
        res = client.put(
            f"/documents/{doc['document_id']}",
            json={"title": "New Title"},
            headers=headers,
        )
        assert res.status_code == 200


class TestArchiveOwnership:
    """PUT /documents/{id} with is_deleted flag (soft delete)."""

    def test_403_other_user_archive(self, client, user_with_auth, other_user_with_auth):
        """Archiving another user's document returns 403."""
        _, owner_headers = user_with_auth
        _, attacker_headers = other_user_with_auth
        doc = _make_doc(client, owner_headers)
        res = client.put(
            f"/documents/{doc['document_id']}",
            json={"is_deleted": True},
            headers=attacker_headers,
        )
        assert res.status_code == 403

    def test_401_unauth_archive(self, client, user_with_auth):
        """Archiving without auth returns 401."""
        _, headers = user_with_auth
        doc = _make_doc(client, headers)
        res = client.put(
            f"/documents/{doc['document_id']}", json={"is_deleted": True}
        )  # no headers
        assert res.status_code == 401

    def test_owner_can_archive_and_restore(self, client, user_with_auth):
        """Owner can archive and restore their own document."""
        _, headers = user_with_auth
        doc = _make_doc(client, headers)

        # Archive
        res = client.put(
            f"/documents/{doc['document_id']}",
            json={"is_deleted": True},
            headers=headers,
        )
        assert res.status_code == 200

        # Restore
        res = client.put(
            f"/documents/{doc['document_id']}",
            json={"is_deleted": False},
            headers=headers,
        )
        assert res.status_code == 200


class TestStatusChangeOwnership:
    """PUT /documents/{id} with status change."""

    def test_403_other_user_change_status(
        self, client, user_with_auth, other_user_with_auth
    ):
        """Changing another user's document status returns 403."""
        _, owner_headers = user_with_auth
        _, attacker_headers = other_user_with_auth
        doc = _make_doc(client, owner_headers)
        res = client.put(
            f"/documents/{doc['document_id']}",
            json={"status": "Final"},
            headers=attacker_headers,
        )
        assert res.status_code == 403

    def test_401_unauth_change_status(self, client, user_with_auth):
        """Changing status without auth returns 401."""
        _, headers = user_with_auth
        doc = _make_doc(client, headers)
        res = client.put(
            f"/documents/{doc['document_id']}", json={"status": "Final"}
        )  # no headers
        assert res.status_code == 401

    def test_owner_can_change_status(self, client, user_with_auth):
        """Owner can change their document's status."""
        _, headers = user_with_auth
        doc = _make_doc(client, headers)
        res = client.put(
            f"/documents/{doc['document_id']}",
            json={"status": "Final"},
            headers=headers,
        )
        assert res.status_code == 200


class TestDuplicateOwnership:
    """POST /documents/{id}/duplicate."""

    def test_403_other_user_duplicate(
        self, client, user_with_auth, other_user_with_auth
    ):
        """Duplicating another user's document returns 403."""
        _, owner_headers = user_with_auth
        _, attacker_headers = other_user_with_auth
        doc = _make_doc(client, owner_headers)
        res = client.post(
            f"/documents/{doc['document_id']}/duplicate", headers=attacker_headers
        )
        assert res.status_code == 403

    def test_401_unauth_duplicate(self, client, user_with_auth):
        """Duplicating without auth returns 401."""
        _, headers = user_with_auth
        doc = _make_doc(client, headers)
        res = client.post(f"/documents/{doc['document_id']}/duplicate")  # no headers
        assert res.status_code == 401

    def test_owner_can_duplicate(self, client, user_with_auth):
        """Owner can duplicate their own document."""
        _, headers = user_with_auth
        doc = _make_doc(client, headers)
        res = client.post(f"/documents/{doc['document_id']}/duplicate", headers=headers)
        assert res.status_code == 201
        dup_doc = res.json()
        assert dup_doc["title"] == f"{doc['title']} (copy)"
        assert dup_doc["document_id"] != doc["document_id"]


class TestVersionListOwnership:
    """GET /documents/{id}/versions — list version history."""

    def test_403_other_user_list_versions(
        self, client, user_with_auth, other_user_with_auth
    ):
        """Listing versions for another user's document returns 403."""
        _, owner_headers = user_with_auth
        _, attacker_headers = other_user_with_auth
        doc = _make_doc(client, owner_headers)
        res = client.get(
            f"/documents/{doc['document_id']}/versions", headers=attacker_headers
        )
        assert res.status_code == 403

    def test_401_unauth_list_versions(self, client, user_with_auth):
        """Listing versions without auth returns 401."""
        _, headers = user_with_auth
        doc = _make_doc(client, headers)
        res = client.get(f"/documents/{doc['document_id']}/versions")  # no headers
        assert res.status_code == 401

    def test_owner_can_list_versions(self, client, user_with_auth):
        """Owner can list their document's versions."""
        _, headers = user_with_auth
        doc = _make_doc(client, headers)
        res = client.get(f"/documents/{doc['document_id']}/versions", headers=headers)
        assert res.status_code == 200
        versions = res.json()
        assert len(versions) >= 1


class TestVersionContentOwnership:
    """GET /documents/{id}/versions/{vid}/content — read specific version content."""

    def test_403_other_user_get_version_content(
        self, client, user_with_auth, other_user_with_auth
    ):
        """Reading another user's version content returns 403."""
        _, owner_headers = user_with_auth
        _, attacker_headers = other_user_with_auth
        doc = _make_doc(client, owner_headers)
        version_id = int(doc["current_version_id"])
        res = client.get(
            f"/documents/{doc['document_id']}/versions/{version_id}/content",
            headers=attacker_headers,
        )
        assert res.status_code == 403

    def test_401_unauth_get_version_content(self, client, user_with_auth):
        """Reading version content without auth returns 401."""
        _, headers = user_with_auth
        doc = _make_doc(client, headers)
        version_id = int(doc["current_version_id"])
        res = client.get(
            f"/documents/{doc['document_id']}/versions/{version_id}/content"
        )  # no headers
        assert res.status_code == 401

    def test_owner_can_get_version_content(self, client, user_with_auth):
        """Owner can read their version's content."""
        _, headers = user_with_auth
        doc = _make_doc(client, headers)
        version_id = int(doc["current_version_id"])
        res = client.get(
            f"/documents/{doc['document_id']}/versions/{version_id}/content",
            headers=headers,
        )
        assert res.status_code == 200


class TestVersionRestoreOwnership:
    """POST /documents/{id}/versions/{vid}/restore — restore old version."""

    def test_403_other_user_restore_version(
        self, client, user_with_auth, other_user_with_auth
    ):
        """Restoring another user's version returns 403."""
        _, owner_headers = user_with_auth
        _, attacker_headers = other_user_with_auth
        doc = _make_doc(client, owner_headers)
        version_id = int(doc["current_version_id"])
        res = client.post(
            f"/documents/{doc['document_id']}/versions/{version_id}/restore",
            headers=attacker_headers,
        )
        assert res.status_code == 403

    def test_401_unauth_restore_version(self, client, user_with_auth):
        """Restoring without auth returns 401."""
        _, headers = user_with_auth
        doc = _make_doc(client, headers)
        version_id = int(doc["current_version_id"])
        res = client.post(
            f"/documents/{doc['document_id']}/versions/{version_id}/restore"
        )  # no headers
        assert res.status_code == 401

    def test_owner_can_restore_version(self, client, user_with_auth):
        """Owner can restore their document's version."""
        _, headers = user_with_auth
        doc = _make_doc(client, headers)
        version_id = int(doc["current_version_id"])
        # Note: restoring the current version should still work
        res = client.post(
            f"/documents/{doc['document_id']}/versions/{version_id}/restore",
            headers=headers,
        )
        assert res.status_code == 200
