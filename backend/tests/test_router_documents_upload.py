"""
Integration tests for the authenticated document upload flow.

Covers:
- Sign in → upload file → file appears in /documents/me
- Path on disk follows ./{L}/{F}/{Full Name}/{user_id}/{filename}
- Upload without auth returns 401
- Upload without a profile returns 400
- /documents/me requires auth
"""

import io
import os
from datetime import date

from database.models.profile import create_profile

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

REGISTER_URL = "/auth/register"
LOGIN_URL = "/auth/login"

_EMAIL = "upload_user@example.com"
_PASSWORD = "testpass123"
_FIRST = "Jane"
_LAST = "Doe"


def _register_login(client) -> dict:
    """Register + login, return auth headers."""
    client.post(REGISTER_URL, json={"email": _EMAIL, "password": _PASSWORD})
    res = client.post(LOGIN_URL, data={"username": _EMAIL, "password": _PASSWORD})
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _add_profile(session, user_id: int):
    """Create a minimal profile so uploads can build the file path."""
    create_profile(
        session,
        user_id=user_id,
        first_name=_FIRST,
        last_name=_LAST,
        dob=date(1990, 1, 1),
        address="123 Main St",
        state="NY",
        zip_code=10001,
    )


def _fake_file(name: str = "resume.pdf", content: bytes = b"fake pdf content"):
    return ("file", (name, io.BytesIO(content), "application/pdf"))


def _upload(client, headers: dict, filename="resume.pdf", doc_type="Resume"):
    return client.post(
        "/documents/upload",
        files=[_fake_file(filename)],
        data={"document_type": doc_type},
        headers=headers,
    )


# ---------------------------------------------------------------------------
# Auth guard tests
# ---------------------------------------------------------------------------


class TestUploadAuthGuard:
    def test_upload_without_token_returns_401(self, client):
        res = client.post(
            "/documents/upload",
            files=[_fake_file()],
            data={"document_type": "Resume"},
        )
        assert res.status_code == 401

    def test_get_my_documents_without_token_returns_401(self, client):
        res = client.get("/documents/me")
        assert res.status_code == 401

    def test_upload_with_invalid_token_returns_401(self, client):
        res = client.post(
            "/documents/upload",
            files=[_fake_file()],
            data={"document_type": "Resume"},
            headers={"Authorization": "Bearer bad.token.here"},
        )
        assert res.status_code == 401


# ---------------------------------------------------------------------------
# Upload requires a profile
# ---------------------------------------------------------------------------


class TestUploadRequiresProfile:
    def test_upload_without_profile_returns_400(self, client):
        headers = _register_login(client)
        res = _upload(client, headers)
        assert res.status_code == 400
        assert "profile" in res.json()["detail"].lower()


# ---------------------------------------------------------------------------
# Successful upload flow
# ---------------------------------------------------------------------------


class TestUploadSuccess:
    def test_returns_201_on_success(self, client, session):
        headers = _register_login(client)
        user = client.get("/auth/me", headers=headers).json()
        _add_profile(session, user["user_id"])

        res = _upload(client, headers)
        assert res.status_code == 201

    def test_response_contains_doc_id(self, client, session):
        headers = _register_login(client)
        user = client.get("/auth/me", headers=headers).json()
        _add_profile(session, user["user_id"])

        res = _upload(client, headers)
        assert "doc_id" in res.json()

    def test_document_type_stored_correctly(self, client, session):
        headers = _register_login(client)
        user = client.get("/auth/me", headers=headers).json()
        _add_profile(session, user["user_id"])

        res = _upload(client, headers, doc_type="Cover Letter")
        assert res.json()["document_type"] == "Cover Letter"

    def test_document_linked_to_correct_user(self, client, session):
        headers = _register_login(client)
        user = client.get("/auth/me", headers=headers).json()
        _add_profile(session, user["user_id"])

        res = _upload(client, headers)
        assert res.json()["user_id"] == user["user_id"]

    def test_file_saved_to_expected_path(self, client, session, tmp_path, monkeypatch):
        """File must land at UPLOAD_BASE/{L}/{F}/{First Last}/{user_id}/{filename}."""
        monkeypatch.setattr("routers.documents.UPLOAD_BASE", str(tmp_path))

        headers = _register_login(client)
        user = client.get("/auth/me", headers=headers).json()
        _add_profile(session, user["user_id"])

        _upload(client, headers, filename="my_resume.pdf")

        expected = os.path.join(
            str(tmp_path),
            _LAST[0].upper(),
            _FIRST[0].upper(),
            f"{_FIRST} {_LAST}",
            str(user["user_id"]),
            "my_resume.pdf",
        )
        assert os.path.isfile(expected), f"File not found at: {expected}"

    def test_file_content_matches_upload(self, client, session, tmp_path, monkeypatch):
        monkeypatch.setattr("routers.documents.UPLOAD_BASE", str(tmp_path))

        headers = _register_login(client)
        user = client.get("/auth/me", headers=headers).json()
        _add_profile(session, user["user_id"])

        content = b"hello world pdf"
        res = client.post(
            "/documents/upload",
            files=[("file", ("test.pdf", io.BytesIO(content), "application/pdf"))],
            data={"document_type": "Resume"},
            headers=headers,
        )
        assert res.status_code == 201

        saved_path = res.json()["document_location"]
        # monkeypatch replaced UPLOAD_BASE, so rebuild the path
        saved_path = saved_path.replace(
            os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads"
            ),
            str(tmp_path),
        )
        with open(saved_path, "rb") as f:
            assert f.read() == content


# ---------------------------------------------------------------------------
# GET /documents/me — sign-in flow
# ---------------------------------------------------------------------------


class TestGetMyDocuments:
    def test_returns_empty_list_when_no_documents(self, client):
        headers = _register_login(client)
        res = client.get("/documents/me", headers=headers)
        assert res.status_code == 200
        assert res.json() == []

    def test_returns_uploaded_documents(self, client, session):
        headers = _register_login(client)
        user = client.get("/auth/me", headers=headers).json()
        _add_profile(session, user["user_id"])

        _upload(client, headers, filename="cv.pdf", doc_type="Resume")
        _upload(client, headers, filename="cover.pdf", doc_type="Cover Letter")

        res = client.get("/documents/me", headers=headers)
        assert res.status_code == 200
        assert len(res.json()) == 2

    def test_only_returns_current_users_documents(self, client, session):
        # User A uploads a document
        headers_a = _register_login(client)
        user_a = client.get("/auth/me", headers=headers_a).json()
        _add_profile(session, user_a["user_id"])
        _upload(client, headers_a, filename="a.pdf")

        # User B registers and has no documents
        client.post(
            REGISTER_URL,
            json={"email": "user_b_upload@example.com", "password": _PASSWORD},
        )
        res_b = client.post(
            LOGIN_URL,
            data={"username": "user_b_upload@example.com", "password": _PASSWORD},
        )
        headers_b = {"Authorization": f"Bearer {res_b.json()['access_token']}"}

        docs_b = client.get("/documents/me", headers=headers_b).json()
        assert docs_b == []

    def test_all_returned_documents_belong_to_current_user(self, client, session):
        headers = _register_login(client)
        user = client.get("/auth/me", headers=headers).json()
        _add_profile(session, user["user_id"])

        _upload(client, headers, filename="r1.pdf")
        _upload(client, headers, filename="r2.pdf")

        docs = client.get("/documents/me", headers=headers).json()
        for doc in docs:
            assert doc["user_id"] == user["user_id"]
