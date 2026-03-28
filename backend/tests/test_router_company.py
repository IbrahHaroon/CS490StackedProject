"""Tests for POST /company/ and GET /company/{company_id}."""


COMPANY_URL = "/company"

ADDRESS_PAYLOAD = {"address": "1 Corp Way", "state": "CA", "zip_code": 94105}


def _company_payload(**overrides):
    base = {"name": "Acme Corp", "address": ADDRESS_PAYLOAD}
    base.update(overrides)
    return base


# ─────────────────────────────────────────────────────────────────────────────
# POST /company/
# ─────────────────────────────────────────────────────────────────────────────

class TestCreateCompany:

    def test_returns_201_on_success(self, client):
        response = client.post(f"{COMPANY_URL}/", json=_company_payload())
        assert response.status_code == 201

    def test_response_contains_company_id(self, client):
        response = client.post(f"{COMPANY_URL}/", json=_company_payload())
        assert "company_id" in response.json()

    def test_company_name_stored(self, client):
        response = client.post(f"{COMPANY_URL}/", json=_company_payload())
        assert response.json()["name"] == "Acme Corp"

    def test_different_companies_get_unique_ids(self, client):
        c1 = client.post(f"{COMPANY_URL}/", json=_company_payload(name="Alpha Inc")).json()
        c2 = client.post(f"{COMPANY_URL}/", json=_company_payload(name="Beta LLC")).json()
        assert c1["company_id"] != c2["company_id"]

    def test_missing_name_returns_422(self, client):
        response = client.post(f"{COMPANY_URL}/", json={"address": ADDRESS_PAYLOAD})
        assert response.status_code == 422

    def test_missing_address_returns_422(self, client):
        response = client.post(f"{COMPANY_URL}/", json={"name": "Acme Corp"})
        assert response.status_code == 422


# ─────────────────────────────────────────────────────────────────────────────
# GET /company/{company_id}
# ─────────────────────────────────────────────────────────────────────────────

class TestReadCompany:

    def test_returns_200_for_existing_company(self, client):
        created = client.post(f"{COMPANY_URL}/", json=_company_payload()).json()
        response = client.get(f"{COMPANY_URL}/{created['company_id']}")
        assert response.status_code == 200

    def test_returns_correct_company(self, client):
        created = client.post(f"{COMPANY_URL}/", json=_company_payload(name="Targetcorp")).json()
        response = client.get(f"{COMPANY_URL}/{created['company_id']}")
        assert response.json()["name"] == "Targetcorp"

    def test_returns_404_for_missing_company(self, client):
        response = client.get(f"{COMPANY_URL}/99999")
        assert response.status_code == 404
