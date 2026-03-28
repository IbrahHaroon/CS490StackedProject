"""Tests for /jobs/positions/ and /jobs/applications/ endpoints."""

from database.models.user import create_user


JOBS_URL = "/jobs"

ADDRESS_PAYLOAD     = {"address": "1 Corp Way", "state": "CA", "zip_code": 94105}
COMPANY_PAYLOAD     = {"name": "Jobs Corp", "address": ADDRESS_PAYLOAD}
POSITION_PAYLOAD_BASE = {
    "title": "Software Engineer",
    "listing_date": "2025-01-01",
    "salary": "95000.00",
    "education_req": "Bachelor's",
    "experience_req": "2+ years",
    "description": "Build great software.",
}


def _create_company(client):
    return client.post("/company/", json=COMPANY_PAYLOAD).json()


def _create_position(client, company_id):
    payload = {**POSITION_PAYLOAD_BASE, "company_id": company_id}
    return client.post(f"{JOBS_URL}/positions/", json=payload).json()


# ─────────────────────────────────────────────────────────────────────────────
# POST /jobs/positions/
# ─────────────────────────────────────────────────────────────────────────────

class TestCreatePosition:

    def test_returns_201_on_success(self, client):
        company = _create_company(client)
        payload = {**POSITION_PAYLOAD_BASE, "company_id": company["company_id"]}
        response = client.post(f"{JOBS_URL}/positions/", json=payload)
        assert response.status_code == 201

    def test_response_contains_position_id(self, client):
        company = _create_company(client)
        position = _create_position(client, company["company_id"])
        assert "position_id" in position

    def test_title_stored_correctly(self, client):
        company = _create_company(client)
        position = _create_position(client, company["company_id"])
        assert position["title"] == "Software Engineer"

    def test_salary_stored_correctly(self, client):
        company = _create_company(client)
        position = _create_position(client, company["company_id"])
        assert float(position["salary"]) == 95000.00

    def test_optional_fields_can_be_omitted(self, client):
        company = _create_company(client)
        payload = {"company_id": company["company_id"], "title": "Intern", "listing_date": "2025-06-01"}
        response = client.post(f"{JOBS_URL}/positions/", json=payload)
        assert response.status_code == 201
        body = response.json()
        assert body["salary"] is None
        assert body["description"] is None

    def test_missing_title_returns_422(self, client):
        company = _create_company(client)
        payload = {"company_id": company["company_id"], "listing_date": "2025-01-01"}
        response = client.post(f"{JOBS_URL}/positions/", json=payload)
        assert response.status_code == 422


# ─────────────────────────────────────────────────────────────────────────────
# GET /jobs/positions/{position_id}
# ─────────────────────────────────────────────────────────────────────────────

class TestReadPosition:

    def test_returns_200_for_existing_position(self, client):
        company = _create_company(client)
        position = _create_position(client, company["company_id"])
        response = client.get(f"{JOBS_URL}/positions/{position['position_id']}")
        assert response.status_code == 200

    def test_returns_correct_position(self, client):
        company = _create_company(client)
        position = _create_position(client, company["company_id"])
        response = client.get(f"{JOBS_URL}/positions/{position['position_id']}")
        assert response.json()["title"] == "Software Engineer"

    def test_returns_404_for_missing_position(self, client):
        response = client.get(f"{JOBS_URL}/positions/99999")
        assert response.status_code == 404


# ─────────────────────────────────────────────────────────────────────────────
# POST /jobs/applications/
# ─────────────────────────────────────────────────────────────────────────────

class TestApplyForJob:

    def test_returns_201_on_success(self, client, session):
        user = create_user(session, "applicant@example.com")
        company = _create_company(client)
        position = _create_position(client, company["company_id"])
        payload = {"user_id": user.user_id, "position_id": position["position_id"], "years_of_experience": 3}
        response = client.post(f"{JOBS_URL}/applications/", json=payload)
        assert response.status_code == 201

    def test_response_contains_job_id(self, client, session):
        user = create_user(session, "applicant@example.com")
        company = _create_company(client)
        position = _create_position(client, company["company_id"])
        payload = {"user_id": user.user_id, "position_id": position["position_id"], "years_of_experience": 3}
        application = client.post(f"{JOBS_URL}/applications/", json=payload).json()
        assert "job_id" in application

    def test_application_status_initialized_to_pending(self, client, session):
        user = create_user(session, "applicant@example.com")
        company = _create_company(client)
        position = _create_position(client, company["company_id"])
        payload = {"user_id": user.user_id, "position_id": position["position_id"], "years_of_experience": 3}
        application = client.post(f"{JOBS_URL}/applications/", json=payload).json()
        assert application["application_status"] == "pending review"

    def test_missing_field_returns_422(self, client, session):
        user = create_user(session, "applicant@example.com")
        response = client.post(f"{JOBS_URL}/applications/", json={"user_id": user.user_id})
        assert response.status_code == 422


# ─────────────────────────────────────────────────────────────────────────────
# GET /jobs/applications/{user_id}
# ─────────────────────────────────────────────────────────────────────────────

class TestReadApplications:

    def test_returns_empty_list_for_user_with_no_applications(self, client, session):
        user = create_user(session, "noapps@example.com")
        response = client.get(f"{JOBS_URL}/applications/{user.user_id}")
        assert response.status_code == 200
        assert response.json() == []

    def test_returns_correct_number_of_applications(self, client, session):
        user = create_user(session, "manyapps@example.com")
        company = _create_company(client)
        position = _create_position(client, company["company_id"])
        for yoe in [1, 2, 3]:
            client.post(f"{JOBS_URL}/applications/", json={
                "user_id": user.user_id, "position_id": position["position_id"], "years_of_experience": yoe
            })
        response = client.get(f"{JOBS_URL}/applications/{user.user_id}")
        assert len(response.json()) == 3

    def test_returns_only_applications_for_correct_user(self, client, session):
        u1 = create_user(session, "apps1@example.com")
        u2 = create_user(session, "apps2@example.com")
        company = _create_company(client)
        position = _create_position(client, company["company_id"])
        client.post(f"{JOBS_URL}/applications/", json={"user_id": u1.user_id, "position_id": position["position_id"], "years_of_experience": 1})
        client.post(f"{JOBS_URL}/applications/", json={"user_id": u2.user_id, "position_id": position["position_id"], "years_of_experience": 2})
        client.post(f"{JOBS_URL}/applications/", json={"user_id": u2.user_id, "position_id": position["position_id"], "years_of_experience": 3})
        assert len(client.get(f"{JOBS_URL}/applications/{u1.user_id}").json()) == 1
        assert len(client.get(f"{JOBS_URL}/applications/{u2.user_id}").json()) == 2
