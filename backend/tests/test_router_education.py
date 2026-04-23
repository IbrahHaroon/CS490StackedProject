"""Tests for POST /education/ and GET /education/{education_id}."""

from database.models.user import create_user

EDUCATION_URL = "/education"


def _education_payload(user_id, **overrides):
    base = {
        "user_id": user_id,
        "school": "State University",
        "degree": "Bachelor of Science",
        "field_of_study": "Computer Science",
        "school_location": "1 University Ave, TX 73301",
    }
    base.update(overrides)
    return base


class TestCreateEducation:
    def test_returns_201_on_success(self, client, session, user_with_auth):
        user_id, headers = user_with_auth
        response = client.post(
            f"{EDUCATION_URL}/", json=_education_payload(user_id), headers=headers
        )
        assert response.status_code == 201

    def test_response_contains_education_id(self, client, user_with_auth):
        user_id, headers = user_with_auth
        response = client.post(
            f"{EDUCATION_URL}/", json=_education_payload(user_id), headers=headers
        )
        assert "education_id" in response.json()

    def test_fields_stored_correctly(self, client, user_with_auth):
        user_id, headers = user_with_auth
        response = client.post(
            f"{EDUCATION_URL}/", json=_education_payload(user_id), headers=headers
        )
        body = response.json()
        assert body["degree"] == "Bachelor of Science"
        assert body["school"] == "State University"
        assert body["field_of_study"] == "Computer Science"

    def test_user_id_linked_correctly(self, client, user_with_auth):
        user_id, headers = user_with_auth
        response = client.post(
            f"{EDUCATION_URL}/", json=_education_payload(user_id), headers=headers
        )
        assert response.json()["user_id"] == user_id

    def test_missing_degree_returns_422(self, client, user_with_auth):
        user_id, headers = user_with_auth
        payload = _education_payload(user_id)
        del payload["degree"]
        response = client.post(
            f"{EDUCATION_URL}/", json=payload, headers=headers
        )
        assert response.status_code == 422


class TestReadEducation:
    def test_returns_200_for_existing_record(self, client, user_with_auth):
        user_id, headers = user_with_auth
        created = client.post(
            f"{EDUCATION_URL}/", json=_education_payload(user_id), headers=headers
        ).json()
        response = client.get(f"{EDUCATION_URL}/{created['education_id']}")
        assert response.status_code == 200

    def test_returns_correct_record(self, client, user_with_auth):
        user_id, headers = user_with_auth
        created = client.post(
            f"{EDUCATION_URL}/", json=_education_payload(user_id), headers=headers
        ).json()
        response = client.get(f"{EDUCATION_URL}/{created['education_id']}")
        assert response.json()["school"] == "State University"

    def test_returns_404_for_missing_record(self, client):
        response = client.get(f"{EDUCATION_URL}/99999")
        assert response.status_code == 404
