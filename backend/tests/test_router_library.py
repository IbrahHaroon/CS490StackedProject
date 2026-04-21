"""Integration tests for the /library router — upload workflow and validation."""

import io

import pytest

# ── Helpers ───────────────────────────────────────────────────────────────────

_UPLOAD_URL = "/library/upload"
_SUPPORTED_URL = "/library/supported-types"

_PROFILE_PAYLOAD = {
    "first_name": "Jane",
    "last_name": "Doe",
    "dob": "1990-01-01",
    "address": {"address": "123 Main St", "state": "NY", "zip_code": 10001},
}


def _register_and_login(client, email: str, password: str = "testpass123"):
    reg = client.post("/auth/register", json={"email": email, "password": password})
    user_id = reg.json()["user_id"]
    login = client.post("/auth/login", data={"username": email, "password": password})
    token = login.json()["access_token"]
    return user_id, {"Authorization": f"Bearer {token}"}


def _upload(
    client,
    headers,
    *,
    filename: str = "resume.pdf",
    content: bytes = b"PDF file content",
    content_type: str = "application/pdf",
    document_type: str = "Resume",
    tags: str | None = None,
):
    data = {"document_type": document_type}
    if tags is not None:
        data["tags"] = tags
    return client.post(
        _UPLOAD_URL,
        files={"file": (filename, io.BytesIO(content), content_type)},
        data=data,
        headers=headers,
    )


@pytest.fixture
def user_with_profile(client):
    """Registered, authenticated user who has a profile (required for upload path)."""
    user_id, headers = _register_and_login(client, "lib_upload@test.com")
    client.post(
        "/profile/",
        json={**_PROFILE_PAYLOAD, "user_id": user_id},
        headers=headers,
    )
    return user_id, headers


# ── GET /library/supported-types ──────────────────────────────────────────────


class TestSupportedTypes:
    def test_returns_200(self, client):
        response = client.get(_SUPPORTED_URL)
        assert response.status_code == 200

    def test_extensions_key_present(self, client):
        data = client.get(_SUPPORTED_URL).json()
        assert "extensions" in data

    def test_max_size_mb_is_ten(self, client):
        data = client.get(_SUPPORTED_URL).json()
        assert data["max_size_mb"] == 10

    def test_pdf_in_extensions(self, client):
        data = client.get(_SUPPORTED_URL).json()
        assert ".pdf" in data["extensions"]

    def test_docx_in_extensions(self, client):
        data = client.get(_SUPPORTED_URL).json()
        assert ".docx" in data["extensions"]

    def test_txt_in_extensions(self, client):
        data = client.get(_SUPPORTED_URL).json()
        assert ".txt" in data["extensions"]

    def test_md_in_extensions(self, client):
        data = client.get(_SUPPORTED_URL).json()
        assert ".md" in data["extensions"]

    def test_exe_not_in_extensions(self, client):
        data = client.get(_SUPPORTED_URL).json()
        assert ".exe" not in data["extensions"]


# ── POST /library/upload — authentication ─────────────────────────────────────


class TestLibraryUploadAuth:
    def test_unauthenticated_returns_401(self, client):
        response = client.post(
            _UPLOAD_URL,
            files={"file": ("r.pdf", io.BytesIO(b"data"), "application/pdf")},
            data={"document_type": "Resume"},
        )
        assert response.status_code == 401


# ── POST /library/upload — extension validation ───────────────────────────────


class TestLibraryUploadExtensionValidation:
    def test_exe_returns_415(self, client, user_with_profile):
        _, headers = user_with_profile
        resp = _upload(
            client,
            headers,
            filename="virus.exe",
            content=b"MZ",
            content_type="application/octet-stream",
        )
        assert resp.status_code == 415

    def test_zip_returns_415(self, client, user_with_profile):
        _, headers = user_with_profile
        resp = _upload(
            client,
            headers,
            filename="archive.zip",
            content=b"PK",
            content_type="application/zip",
        )
        assert resp.status_code == 415

    def test_js_returns_415(self, client, user_with_profile):
        _, headers = user_with_profile
        resp = _upload(
            client,
            headers,
            filename="script.js",
            content=b"alert(1)",
            content_type="text/javascript",
        )
        assert resp.status_code == 415

    def test_pdf_extension_is_accepted(self, client, user_with_profile):
        _, headers = user_with_profile
        resp = _upload(client, headers, filename="cv.pdf")
        assert resp.status_code != 415

    def test_docx_extension_is_accepted(self, client, user_with_profile):
        _, headers = user_with_profile
        resp = _upload(
            client,
            headers,
            filename="cv.docx",
            content=b"docx content",
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
        assert resp.status_code != 415

    def test_txt_extension_is_accepted(self, client, user_with_profile):
        _, headers = user_with_profile
        resp = _upload(
            client,
            headers,
            filename="notes.txt",
            content=b"plain text",
            content_type="text/plain",
        )
        assert resp.status_code != 415

    def test_md_extension_is_accepted(self, client, user_with_profile):
        _, headers = user_with_profile
        resp = _upload(
            client,
            headers,
            filename="readme.md",
            content=b"# Resume",
            content_type="text/markdown",
        )
        assert resp.status_code != 415

    def test_415_detail_lists_allowed_types(self, client, user_with_profile):
        _, headers = user_with_profile
        resp = _upload(
            client,
            headers,
            filename="bad.exe",
            content=b"x",
            content_type="application/octet-stream",
        )
        assert ".pdf" in resp.json()["detail"]


# ── POST /library/upload — size and content validation ────────────────────────


class TestLibraryUploadSizeValidation:
    def test_empty_file_returns_400(self, client, user_with_profile):
        _, headers = user_with_profile
        resp = _upload(client, headers, content=b"")
        assert resp.status_code == 400

    def test_oversized_file_returns_413(self, client, user_with_profile):
        _, headers = user_with_profile
        big = b"x" * (11 * 1024 * 1024)  # 11 MB — exceeds 10 MB cap
        resp = _upload(client, headers, content=big)
        assert resp.status_code == 413

    def test_413_detail_mentions_size_limit(self, client, user_with_profile):
        _, headers = user_with_profile
        big = b"x" * (11 * 1024 * 1024)
        resp = _upload(client, headers, content=big)
        assert "10 MB" in resp.json()["detail"]

    def test_exactly_max_size_is_accepted(self, client, user_with_profile):
        _, headers = user_with_profile
        at_limit = b"x" * (10 * 1024 * 1024)  # exactly 10 MB
        resp = _upload(client, headers, content=at_limit)
        assert resp.status_code != 413


# ── POST /library/upload — successful uploads ─────────────────────────────────


class TestLibraryUploadSuccess:
    def test_returns_201(self, client, user_with_profile):
        _, headers = user_with_profile
        resp = _upload(client, headers)
        assert resp.status_code == 201

    def test_response_contains_doc_id(self, client, user_with_profile):
        _, headers = user_with_profile
        resp = _upload(client, headers)
        assert "doc_id" in resp.json()

    def test_doc_id_is_positive_integer(self, client, user_with_profile):
        _, headers = user_with_profile
        resp = _upload(client, headers)
        assert isinstance(resp.json()["doc_id"], int)
        assert resp.json()["doc_id"] > 0

    def test_document_name_matches_uploaded_filename(self, client, user_with_profile):
        _, headers = user_with_profile
        resp = _upload(client, headers, filename="my_resume.pdf")
        assert resp.json()["document_name"] == "my_resume.pdf"

    def test_document_type_matches_form_value(self, client, user_with_profile):
        _, headers = user_with_profile
        resp = _upload(client, headers, document_type="Cover Letter")
        assert resp.json()["document_type"] == "Cover Letter"

    def test_user_id_matches_authenticated_user(self, client, user_with_profile):
        user_id, headers = user_with_profile
        resp = _upload(client, headers)
        assert resp.json()["user_id"] == user_id

    def test_document_location_is_set(self, client, user_with_profile):
        _, headers = user_with_profile
        resp = _upload(client, headers)
        assert resp.json()["document_location"] is not None

    def test_status_defaults_to_draft(self, client, user_with_profile):
        _, headers = user_with_profile
        resp = _upload(client, headers)
        assert resp.json()["status"] == "Draft"

    def test_tags_stored_when_provided(self, client, user_with_profile):
        _, headers = user_with_profile
        resp = _upload(client, headers, tags="python,backend")
        assert resp.json()["tags"] == "python,backend"

    def test_tags_null_when_omitted(self, client, user_with_profile):
        _, headers = user_with_profile
        resp = _upload(client, headers)
        assert resp.json()["tags"] is None

    def test_created_at_is_present(self, client, user_with_profile):
        _, headers = user_with_profile
        resp = _upload(client, headers)
        assert resp.json()["created_at"] is not None

    def test_is_archived_defaults_false(self, client, user_with_profile):
        _, headers = user_with_profile
        resp = _upload(client, headers)
        assert resp.json()["is_archived"] is False

    def test_two_uploads_receive_distinct_doc_ids(self, client, user_with_profile):
        _, headers = user_with_profile
        r1 = _upload(client, headers, filename="a.pdf")
        r2 = _upload(client, headers, filename="b.pdf")
        assert r1.json()["doc_id"] != r2.json()["doc_id"]

    def test_upload_visible_via_documents_me(self, client, user_with_profile):
        _, headers = user_with_profile
        _upload(client, headers)
        me = client.get("/documents/me", headers=headers)
        assert me.status_code == 200
        assert len(me.json()) >= 1


# ── POST /library/upload — filename sanitisation ──────────────────────────────


class TestFilenamesanitisation:
    def test_path_traversal_in_filename_is_stripped(self, client, user_with_profile):
        _, headers = user_with_profile
        resp = _upload(
            client,
            headers,
            filename="../../etc/passwd.txt",
            content=b"data",
            content_type="text/plain",
        )
        # Must succeed (txt is allowed) and the stored name must be safe
        assert resp.status_code == 201
        stored_name = resp.json()["document_name"]
        assert ".." not in stored_name
        assert "/" not in stored_name

    def test_null_byte_in_filename_is_stripped(self, client, user_with_profile):
        _, headers = user_with_profile
        resp = _upload(
            client,
            headers,
            filename="resume\x00.pdf",
            content=b"data",
        )
        assert resp.status_code == 201
        assert "\x00" not in resp.json()["document_name"]
