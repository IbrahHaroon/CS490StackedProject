"""Tests for POST /profile/, GET /profile/{id}, and PUT /profile/{id}."""

PROFILE_URL = "/profile"
ADDRESS_PAYLOAD = {"address": "123 Main St", "state": "TX", "zip_code": 73301}


def _profile_payload(user_id, **overrides):
    base = {
        "user_id": user_id,
        "first_name": "Jane",
        "last_name": "Doe",
        "dob": "1990-06-15",
        "address": ADDRESS_PAYLOAD,
    }
    base.update(overrides)
    return base


# ─────────────────────────────────────────────────────────────────────────────
# POST /profile/
# ─────────────────────────────────────────────────────────────────────────────

class TestCreateProfile:

    def test_returns_201_on_success(self, client, user_with_auth):
        user_id, headers = user_with_auth
        response = client.post(f"{PROFILE_URL}/", json=_profile_payload(user_id), headers=headers)
        assert response.status_code == 201

    def test_response_contains_profile_id(self, client, user_with_auth):
        user_id, headers = user_with_auth
        response = client.post(f"{PROFILE_URL}/", json=_profile_payload(user_id), headers=headers)
        assert "profile_id" in response.json()

    def test_first_and_last_name_stored(self, client, user_with_auth):
        user_id, headers = user_with_auth
        response = client.post(f"{PROFILE_URL}/", json=_profile_payload(user_id), headers=headers)
        body = response.json()
        assert body["first_name"] == "Jane"
        assert body["last_name"] == "Doe"

    def test_optional_phone_number_stored(self, client, user_with_auth):
        user_id, headers = user_with_auth
        payload = _profile_payload(user_id, phone_number="555-1234")
        response = client.post(f"{PROFILE_URL}/", json=payload, headers=headers)
        assert response.json()["phone_number"] == "555-1234"

    def test_optional_summary_stored(self, client, user_with_auth):
        user_id, headers = user_with_auth
        payload = _profile_payload(user_id, summary="Experienced developer.")
        response = client.post(f"{PROFILE_URL}/", json=payload, headers=headers)
        assert response.json()["summary"] == "Experienced developer."

    def test_optional_fields_default_to_none(self, client, user_with_auth):
        user_id, headers = user_with_auth
        response = client.post(f"{PROFILE_URL}/", json=_profile_payload(user_id), headers=headers)
        body = response.json()
        assert body["phone_number"] is None
        assert body["summary"] is None

    def test_missing_required_field_returns_422(self, client, user_with_auth):
        user_id, headers = user_with_auth
        payload = _profile_payload(user_id)
        del payload["first_name"]
        response = client.post(f"{PROFILE_URL}/", json=payload, headers=headers)
        assert response.status_code == 422

    def test_unauthenticated_request_returns_401(self, client, user_with_auth):
        user_id, _ = user_with_auth
        response = client.post(f"{PROFILE_URL}/", json=_profile_payload(user_id))
        assert response.status_code == 401

    def test_creating_profile_for_other_user_returns_403(self, client, user_with_auth, other_user_with_auth):
        _, headers_a = user_with_auth
        user_b_id, _ = other_user_with_auth
        response = client.post(f"{PROFILE_URL}/", json=_profile_payload(user_b_id), headers=headers_a)
        assert response.status_code == 403


# ─────────────────────────────────────────────────────────────────────────────
# GET /profile/{profile_id}
# ─────────────────────────────────────────────────────────────────────────────

class TestReadProfile:

    def test_returns_200_for_own_profile(self, client, user_with_auth):
        user_id, headers = user_with_auth
        created = client.post(f"{PROFILE_URL}/", json=_profile_payload(user_id), headers=headers).json()
        response = client.get(f"{PROFILE_URL}/{created['profile_id']}", headers=headers)
        assert response.status_code == 200

    def test_returns_correct_profile(self, client, user_with_auth):
        user_id, headers = user_with_auth
        created = client.post(f"{PROFILE_URL}/", json=_profile_payload(user_id), headers=headers).json()
        response = client.get(f"{PROFILE_URL}/{created['profile_id']}", headers=headers)
        assert response.json()["user_id"] == user_id

    def test_returns_404_for_missing_profile(self, client, user_with_auth):
        _, headers = user_with_auth
        response = client.get(f"{PROFILE_URL}/99999", headers=headers)
        assert response.status_code == 404

    def test_unauthenticated_request_returns_401(self, client, user_with_auth):
        user_id, headers = user_with_auth
        created = client.post(f"{PROFILE_URL}/", json=_profile_payload(user_id), headers=headers).json()
        response = client.get(f"{PROFILE_URL}/{created['profile_id']}")
        assert response.status_code == 401

    def test_user_b_cannot_read_user_a_profile(self, client, user_with_auth, other_user_with_auth):
        """Ownership enforcement: User B must receive 403 when reading User A's profile."""
        user_a_id, headers_a = user_with_auth
        _, headers_b = other_user_with_auth
        created = client.post(f"{PROFILE_URL}/", json=_profile_payload(user_a_id), headers=headers_a).json()
        response = client.get(f"{PROFILE_URL}/{created['profile_id']}", headers=headers_b)
        assert response.status_code == 403


# ─────────────────────────────────────────────────────────────────────────────
# PUT /profile/{profile_id}
# ─────────────────────────────────────────────────────────────────────────────

class TestUpdateProfile:

    def _create(self, client, user_id, headers):
        return client.post(f"{PROFILE_URL}/", json=_profile_payload(user_id), headers=headers).json()

    def test_returns_200_on_success(self, client, user_with_auth):
        user_id, headers = user_with_auth
        profile = self._create(client, user_id, headers)
        response = client.put(f"{PROFILE_URL}/{profile['profile_id']}", json={"first_name": "Janet"}, headers=headers)
        assert response.status_code == 200

    def test_first_name_updated(self, client, user_with_auth):
        user_id, headers = user_with_auth
        profile = self._create(client, user_id, headers)
        client.put(f"{PROFILE_URL}/{profile['profile_id']}", json={"first_name": "Janet"}, headers=headers)
        response = client.get(f"{PROFILE_URL}/{profile['profile_id']}", headers=headers)
        assert response.json()["first_name"] == "Janet"

    def test_summary_updated(self, client, user_with_auth):
        user_id, headers = user_with_auth
        profile = self._create(client, user_id, headers)
        client.put(f"{PROFILE_URL}/{profile['profile_id']}", json={"summary": "Updated summary."}, headers=headers)
        response = client.get(f"{PROFILE_URL}/{profile['profile_id']}", headers=headers)
        assert response.json()["summary"] == "Updated summary."

    def test_returns_404_for_missing_profile(self, client, user_with_auth):
        _, headers = user_with_auth
        response = client.put(f"{PROFILE_URL}/99999", json={"first_name": "X"}, headers=headers)
        assert response.status_code == 404

    def test_unauthenticated_update_returns_401(self, client, user_with_auth):
        user_id, headers = user_with_auth
        profile = self._create(client, user_id, headers)
        response = client.put(f"{PROFILE_URL}/{profile['profile_id']}", json={"first_name": "X"})
        assert response.status_code == 401

    def test_user_b_cannot_update_user_a_profile(self, client, user_with_auth, other_user_with_auth):
        """Ownership enforcement: User B must receive 403 when updating User A's profile."""
        user_a_id, headers_a = user_with_auth
        _, headers_b = other_user_with_auth
        profile = self._create(client, user_a_id, headers_a)
        response = client.put(f"{PROFILE_URL}/{profile['profile_id']}", json={"first_name": "Hacked"}, headers=headers_b)
        assert response.status_code == 403
