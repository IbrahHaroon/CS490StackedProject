"""Tests for POST /education/ and GET /education/{education_id}."""

from database.models.user import create_user


EDUCATION_URL = "/education"

ADDRESS_PAYLOAD = {"address": "1 University Ave", "state": "TX", "zip_code": 73301}


def _education_payload(user_id, **overrides):
    base = {
        "user_id": user_id,
        "highest_education": "Bachelor's",
        "degree": "Computer Science",
        "school_or_college": "State University",
        "address": ADDRESS_PAYLOAD,
    }
    base.update(overrides)
    return base


# ─────────────────────────────────────────────────────────────────────────────
# POST /education/
# ─────────────────────────────────────────────────────────────────────────────

class TestCreateEducation:

    def test_returns_201_on_success(self, client, session):
        user = create_user(session, "edu_c@example.com")
        response = client.post(f"{EDUCATION_URL}/", json=_education_payload(user.user_id))
        assert response.status_code == 201

    def test_response_contains_education_id(self, client, session):
        user = create_user(session, "edu_c@example.com")
        response = client.post(f"{EDUCATION_URL}/", json=_education_payload(user.user_id))
        assert "education_id" in response.json()

    def test_fields_stored_correctly(self, client, session):
        user = create_user(session, "edu_c@example.com")
        response = client.post(f"{EDUCATION_URL}/", json=_education_payload(user.user_id))
        body = response.json()
        assert body["degree"] == "Computer Science"
        assert body["school_or_college"] == "State University"
        assert body["highest_education"] == "Bachelor's"

    def test_user_id_linked_correctly(self, client, session):
        user = create_user(session, "edu_c@example.com")
        response = client.post(f"{EDUCATION_URL}/", json=_education_payload(user.user_id))
        assert response.json()["user_id"] == user.user_id

    def test_missing_degree_returns_422(self, client, session):
        user = create_user(session, "edu_c@example.com")
        payload = _education_payload(user.user_id)
        del payload["degree"]
        response = client.post(f"{EDUCATION_URL}/", json=payload)
        assert response.status_code == 422


# ─────────────────────────────────────────────────────────────────────────────
# GET /education/{education_id}
# ─────────────────────────────────────────────────────────────────────────────

class TestReadEducation:

    def test_returns_200_for_existing_record(self, client, session):
        user = create_user(session, "edu_r@example.com")
        created = client.post(f"{EDUCATION_URL}/", json=_education_payload(user.user_id)).json()
        response = client.get(f"{EDUCATION_URL}/{created['education_id']}")
        assert response.status_code == 200

    def test_returns_correct_record(self, client, session):
        user = create_user(session, "edu_r@example.com")
        created = client.post(f"{EDUCATION_URL}/", json=_education_payload(user.user_id)).json()
        response = client.get(f"{EDUCATION_URL}/{created['education_id']}")
        assert response.json()["school_or_college"] == "State University"

    def test_returns_404_for_missing_record(self, client):
        response = client.get(f"{EDUCATION_URL}/99999")
        assert response.status_code == 404
