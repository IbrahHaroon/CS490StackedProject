"""Router tests for /recruiter endpoints."""

from datetime import date

RECRUITER_URL = "/recruiter"
COMPANY_URL = "/company"
JOBS_URL = "/jobs"
AUTH_URL = "/auth"

ADDRESS_PAYLOAD = {"address": "1 Corp Ave", "state": "NJ", "zip_code": 8001}
COMPANY_PAYLOAD = {"name": "Acme Corp", "address": ADDRESS_PAYLOAD}
POSITION_PAYLOAD_BASE = {
    "title": "Software Engineer",
    "listing_date": str(date.today()),
}

# --------------------------------------------------------------------------- #
#  Helpers                                                                      #
# --------------------------------------------------------------------------- #


def _register_and_login(client, email, password="testpass123"):
    """Register and log in a regular job-seeker user. Returns (user_id, headers)."""
    reg = client.post(
        f"{AUTH_URL}/register", json={"email": email, "password": password}
    )
    user_id = reg.json()["user_id"]
    login = client.post(
        f"{AUTH_URL}/login", data={"username": email, "password": password}
    )
    token = login.json()["access_token"]
    return user_id, {"Authorization": f"Bearer {token}"}


def _create_company(client):
    res = client.post(f"{COMPANY_URL}/", json=COMPANY_PAYLOAD)
    return res.json()


def _create_recruiter_with_auth(
    client, email="rec@example.com", password="testpass123"
):
    """Register and log in a recruiter. Returns (recruiter_id, company_id, headers)."""
    company = _create_company(client)
    reg = client.post(
        f"{AUTH_URL}/recruiter/register",
        json={
            "email": email,
            "password": password,
            "company_id": company["company_id"],
            "first_name": "Jane",
            "last_name": "Doe",
        },
    )
    recruiter_id = reg.json()["recruiter_id"]
    login = client.post(
        f"{AUTH_URL}/recruiter/login",
        data={"username": email, "password": password},
    )
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    return recruiter_id, company["company_id"], headers


def _create_position(client, company_id, headers):
    payload = {**POSITION_PAYLOAD_BASE, "company_id": company_id}
    res = client.post(f"{RECRUITER_URL}/positions/", json=payload, headers=headers)
    return res.json()


# --------------------------------------------------------------------------- #
#  TestCreateRecruiterProfile                                                   #
# --------------------------------------------------------------------------- #


class TestCreateRecruiterProfile:
    def test_returns_201_on_success(self, client):
        company = _create_company(client)
        res = client.post(
            f"{AUTH_URL}/recruiter/register",
            json={
                "email": "newrec@example.com",
                "password": "testpass123",
                "company_id": company["company_id"],
                "first_name": "Jane",
                "last_name": "Doe",
            },
        )
        assert res.status_code == 201

    def test_response_contains_recruiter_id(self, client):
        company = _create_company(client)
        res = client.post(
            f"{AUTH_URL}/recruiter/register",
            json={
                "email": "newrecid@example.com",
                "password": "testpass123",
                "company_id": company["company_id"],
                "first_name": "Jane",
                "last_name": "Doe",
            },
        )
        assert "recruiter_id" in res.json()

    def test_fields_stored_correctly(self, client):
        company = _create_company(client)
        res = client.post(
            f"{AUTH_URL}/recruiter/register",
            json={
                "email": "recfields@example.com",
                "password": "testpass123",
                "company_id": company["company_id"],
                "first_name": "Alice",
                "last_name": "Smith",
                "job_title": "Recruiter",
            },
        )
        data = res.json()
        assert data["first_name"] == "Alice"
        assert data["last_name"] == "Smith"
        assert data["job_title"] == "Recruiter"

    def test_returns_400_on_duplicate(self, client):
        company = _create_company(client)
        payload = {
            "email": "dup@example.com",
            "password": "testpass123",
            "company_id": company["company_id"],
            "first_name": "Jane",
            "last_name": "Doe",
        }
        client.post(f"{AUTH_URL}/recruiter/register", json=payload)
        res = client.post(f"{AUTH_URL}/recruiter/register", json=payload)
        assert res.status_code == 400

    def test_missing_required_field_returns_422(self, client):
        res = client.post(
            f"{AUTH_URL}/recruiter/register",
            json={"email": "missing@example.com"},
        )
        assert res.status_code == 422


# --------------------------------------------------------------------------- #
#  TestGetRecruiterMe                                                           #
# --------------------------------------------------------------------------- #


class TestGetRecruiterMe:
    def test_returns_200_with_token(self, client):
        _, _, headers = _create_recruiter_with_auth(client, "getme@example.com")
        res = client.get(f"{RECRUITER_URL}/me", headers=headers)
        assert res.status_code == 200

    def test_returns_correct_fields(self, client):
        _, company_id, headers = _create_recruiter_with_auth(
            client, "getmefields@example.com"
        )
        data = client.get(f"{RECRUITER_URL}/me", headers=headers).json()
        assert data["first_name"] == "Jane"
        assert data["last_name"] == "Doe"
        assert data["company_id"] == company_id

    def test_returns_401_unauthenticated(self, client):
        res = client.get(f"{RECRUITER_URL}/me")
        assert res.status_code == 401

    def test_returns_401_for_non_recruiter_user(self, client):
        _, headers = _register_and_login(client, "norec@example.com")
        res = client.get(f"{RECRUITER_URL}/me", headers=headers)
        assert res.status_code == 401


# --------------------------------------------------------------------------- #
#  TestUpdateRecruiterMe                                                        #
# --------------------------------------------------------------------------- #


class TestUpdateRecruiterMe:
    def test_update_first_name(self, client):
        _, _, headers = _create_recruiter_with_auth(client, "updfn@example.com")
        res = client.put(
            f"{RECRUITER_URL}/me", json={"first_name": "Janet"}, headers=headers
        )
        assert res.status_code == 200
        assert res.json()["first_name"] == "Janet"

    def test_update_job_title(self, client):
        _, _, headers = _create_recruiter_with_auth(client, "updjt@example.com")
        res = client.put(
            f"{RECRUITER_URL}/me",
            json={"job_title": "Talent Lead"},
            headers=headers,
        )
        assert res.json()["job_title"] == "Talent Lead"

    def test_returns_401_unauthenticated(self, client):
        res = client.put(f"{RECRUITER_URL}/me", json={"first_name": "X"})
        assert res.status_code == 401


# --------------------------------------------------------------------------- #
#  TestRecruiterPositions                                                       #
# --------------------------------------------------------------------------- #


class TestRecruiterPositions:
    def test_create_position_returns_201(self, client):
        _, company_id, headers = _create_recruiter_with_auth(
            client, "posCreate@example.com"
        )
        pos = _create_position(client, company_id, headers)
        assert "position_id" in pos

    def test_create_position_stores_location_type(self, client):
        _, company_id, headers = _create_recruiter_with_auth(
            client, "posLoc@example.com"
        )
        payload = {
            **POSITION_PAYLOAD_BASE,
            "company_id": company_id,
            "location_type": "Remote",
        }
        res = client.post(f"{RECRUITER_URL}/positions/", json=payload, headers=headers)
        assert res.json()["location_type"] == "Remote"

    def test_invalid_location_type_returns_422(self, client):
        _, company_id, headers = _create_recruiter_with_auth(
            client, "posLocBad@example.com"
        )
        payload = {
            **POSITION_PAYLOAD_BASE,
            "company_id": company_id,
            "location_type": "Mars",
        }
        res = client.post(f"{RECRUITER_URL}/positions/", json=payload, headers=headers)
        assert res.status_code == 422

    def test_list_positions_returns_only_company_positions(self, client):
        _, company_id, headers = _create_recruiter_with_auth(
            client, "posList@example.com"
        )
        _create_position(client, company_id, headers)
        _create_position(client, company_id, headers)
        res = client.get(f"{RECRUITER_URL}/positions/", headers=headers)
        assert res.status_code == 200
        assert len(res.json()) == 2

    def test_update_position_returns_200(self, client):
        _, company_id, headers = _create_recruiter_with_auth(
            client, "posUpd@example.com"
        )
        pos = _create_position(client, company_id, headers)
        res = client.put(
            f"{RECRUITER_URL}/positions/{pos['position_id']}",
            json={"title": "Senior Engineer"},
            headers=headers,
        )
        assert res.status_code == 200
        assert res.json()["title"] == "Senior Engineer"

    def test_update_position_403_cross_company(self, client):
        _, company_id_a, headers_a = _create_recruiter_with_auth(
            client, "posA@example.com"
        )
        _, _, headers_b = _create_recruiter_with_auth(client, "posB@example.com")
        pos = _create_position(client, company_id_a, headers_a)
        res = client.put(
            f"{RECRUITER_URL}/positions/{pos['position_id']}",
            json={"title": "Hacked"},
            headers=headers_b,
        )
        assert res.status_code == 403

    def test_delete_position_returns_204(self, client):
        _, company_id, headers = _create_recruiter_with_auth(
            client, "posDel@example.com"
        )
        pos = _create_position(client, company_id, headers)
        res = client.delete(
            f"{RECRUITER_URL}/positions/{pos['position_id']}", headers=headers
        )
        assert res.status_code == 204

    def test_delete_position_403_cross_company(self, client):
        _, company_id_a, headers_a = _create_recruiter_with_auth(
            client, "posDelA@example.com"
        )
        _, _, headers_b = _create_recruiter_with_auth(client, "posDelB@example.com")
        pos = _create_position(client, company_id_a, headers_a)
        res = client.delete(
            f"{RECRUITER_URL}/positions/{pos['position_id']}", headers=headers_b
        )
        assert res.status_code == 403


# --------------------------------------------------------------------------- #
#  TestRecruiterApplications                                                    #
# --------------------------------------------------------------------------- #


class TestRecruiterApplications:
    def _setup_application(self, client):
        """Create a recruiter, a position, a job seeker, and an application."""
        rec_id, company_id, rec_headers = _create_recruiter_with_auth(
            client, "appRec@example.com"
        )
        pos = _create_position(client, company_id, rec_headers)

        seeker_id, seeker_headers = _register_and_login(client, "seeker@example.com")
        client.post(
            f"{JOBS_URL}/applications/",
            json={
                "user_id": seeker_id,
                "position_id": pos["position_id"],
                "years_of_experience": 2,
            },
            headers=seeker_headers,
        )
        apps = client.get(
            f"{RECRUITER_URL}/positions/{pos['position_id']}/applications",
            headers=rec_headers,
        ).json()
        return (
            apps[0]["job_id"],
            pos["position_id"],
            rec_headers,
            company_id,
            seeker_headers,
        )

    def test_view_applications_returns_200(self, client):
        job_id, position_id, rec_headers, _, _ = self._setup_application(client)
        res = client.get(
            f"{RECRUITER_URL}/positions/{position_id}/applications",
            headers=rec_headers,
        )
        assert res.status_code == 200
        assert len(res.json()) == 1

    def test_view_applications_403_cross_company(self, client):
        _, position_id, _, _, _ = self._setup_application(client)
        _, _, other_headers = _create_recruiter_with_auth(
            client, "otherRec@example.com"
        )
        res = client.get(
            f"{RECRUITER_URL}/positions/{position_id}/applications",
            headers=other_headers,
        )
        assert res.status_code == 403

    def test_update_status_returns_200(self, client):
        job_id, _, rec_headers, _, _ = self._setup_application(client)
        res = client.put(
            f"{RECRUITER_URL}/applications/{job_id}/status",
            json={"application_status": "Interview"},
            headers=rec_headers,
        )
        assert res.status_code == 200
        assert res.json()["application_status"] == "Interview"

    def test_update_status_records_activity(self, client):
        job_id, _, rec_headers, _, seeker_headers = self._setup_application(client)
        client.put(
            f"{RECRUITER_URL}/applications/{job_id}/status",
            json={"application_status": "Interview"},
            headers=rec_headers,
        )
        activity = client.get(
            f"{JOBS_URL}/applications/{job_id}/activity",
            headers=seeker_headers,
        ).json()
        stages = [a["stage"] for a in activity]
        assert "Interview" in stages

    def test_update_status_invalid_stage_returns_422(self, client):
        job_id, _, rec_headers, _, _ = self._setup_application(client)
        res = client.put(
            f"{RECRUITER_URL}/applications/{job_id}/status",
            json={"application_status": "InvalidStage"},
            headers=rec_headers,
        )
        assert res.status_code == 422

    def test_update_status_403_cross_company(self, client):
        job_id, _, _, _, _ = self._setup_application(client)
        _, _, other_headers = _create_recruiter_with_auth(
            client, "otherRecStat@example.com"
        )
        res = client.put(
            f"{RECRUITER_URL}/applications/{job_id}/status",
            json={"application_status": "Rejected"},
            headers=other_headers,
        )
        assert res.status_code == 403


# --------------------------------------------------------------------------- #
#  TestRecruiterActivity                                                        #
# --------------------------------------------------------------------------- #


class TestRecruiterActivity:
    def _setup_application(self, client, rec_email, seeker_email):
        rec_id, company_id, rec_headers = _create_recruiter_with_auth(client, rec_email)
        pos = _create_position(client, company_id, rec_headers)
        seeker_id, seeker_headers = _register_and_login(client, seeker_email)
        client.post(
            f"{JOBS_URL}/applications/",
            json={
                "user_id": seeker_id,
                "position_id": pos["position_id"],
                "years_of_experience": 1,
            },
            headers=seeker_headers,
        )
        apps = client.get(
            f"{RECRUITER_URL}/positions/{pos['position_id']}/applications",
            headers=rec_headers,
        ).json()
        return apps[0]["job_id"], rec_headers, company_id, seeker_headers

    def test_add_activity_returns_201(self, client):
        job_id, rec_headers, _, _ = self._setup_application(
            client, "actRec@example.com", "actSeeker@example.com"
        )
        res = client.post(
            f"{RECRUITER_URL}/applications/{job_id}/activity",
            json={"event_type": "note", "notes": "Strong candidate."},
            headers=rec_headers,
        )
        assert res.status_code == 201

    def test_activity_note_stored(self, client):
        job_id, rec_headers, _, seeker_headers = self._setup_application(
            client, "actNote@example.com", "actNoteSeeker@example.com"
        )
        client.post(
            f"{RECRUITER_URL}/applications/{job_id}/activity",
            json={"event_type": "note", "notes": "Reviewed resume."},
            headers=rec_headers,
        )
        activity = client.get(
            f"{JOBS_URL}/applications/{job_id}/activity",
            headers=seeker_headers,
        ).json()
        notes = [a["notes"] for a in activity]
        assert "Reviewed resume." in notes

    def test_activity_stage_uses_current_job_status(self, client):
        job_id, rec_headers, _, _ = self._setup_application(
            client, "actStage@example.com", "actStageSeeker@example.com"
        )
        res = client.post(
            f"{RECRUITER_URL}/applications/{job_id}/activity",
            json={"event_type": "note"},
            headers=rec_headers,
        )
        assert res.json()["stage"] == "Applied"

    def test_add_activity_403_cross_company(self, client):
        job_id, _, _, _ = self._setup_application(
            client, "act403Rec@example.com", "act403Seeker@example.com"
        )
        _, _, other_headers = _create_recruiter_with_auth(
            client, "act403Other@example.com"
        )
        res = client.post(
            f"{RECRUITER_URL}/applications/{job_id}/activity",
            json={"event_type": "note"},
            headers=other_headers,
        )
        assert res.status_code == 403
