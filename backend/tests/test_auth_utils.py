"""Tests for database/auth.py — password hashing and JWT utilities."""

from database.auth import (
    create_access_token,
    decode_access_token,
    get_password_hash,
    verify_password,
)

# ─────────────────────────────────────────────────────────────────────────────
# get_password_hash
# ─────────────────────────────────────────────────────────────────────────────


class TestGetPasswordHash:
    def test_returns_a_string(self):
        result = get_password_hash("mysecret")
        assert isinstance(result, str)

    def test_hash_differs_from_plain_password(self):
        result = get_password_hash("mysecret")
        assert result != "mysecret"

    def test_same_password_produces_different_hashes(self):
        # bcrypt salts each hash, so two calls must never be identical
        h1 = get_password_hash("mysecret")
        h2 = get_password_hash("mysecret")
        assert h1 != h2

    def test_hash_is_nonempty(self):
        result = get_password_hash("x")
        assert len(result) > 0

    def test_hash_starts_with_bcrypt_prefix(self):
        result = get_password_hash("mysecret")
        assert result.startswith("$2")


# ─────────────────────────────────────────────────────────────────────────────
# verify_password
# ─────────────────────────────────────────────────────────────────────────────


class TestVerifyPassword:
    def test_correct_password_returns_true(self):
        hashed = get_password_hash("correct")
        assert verify_password("correct", hashed) is True

    def test_wrong_password_returns_false(self):
        hashed = get_password_hash("correct")
        assert verify_password("wrong", hashed) is False

    def test_empty_password_returns_false_against_real_hash(self):
        hashed = get_password_hash("correct")
        assert verify_password("", hashed) is False

    def test_case_sensitive(self):
        hashed = get_password_hash("Secret")
        assert verify_password("secret", hashed) is False

    def test_verify_works_across_independent_hashes(self):
        h1 = get_password_hash("pass")
        h2 = get_password_hash("pass")
        # Both hashes are valid for the same password even though they differ
        assert verify_password("pass", h1) is True
        assert verify_password("pass", h2) is True


# ─────────────────────────────────────────────────────────────────────────────
# create_access_token
# ─────────────────────────────────────────────────────────────────────────────


class TestCreateAccessToken:
    def test_returns_a_string(self):
        token = create_access_token({"sub": "1"})
        assert isinstance(token, str)

    def test_token_has_three_jwt_parts(self):
        token = create_access_token({"sub": "1"})
        parts = token.split(".")
        assert len(parts) == 3

    def test_token_is_nonempty(self):
        token = create_access_token({"sub": "1"})
        assert len(token) > 0

    def test_different_payloads_produce_different_tokens(self):
        t1 = create_access_token({"sub": "1"})
        t2 = create_access_token({"sub": "2"})
        assert t1 != t2


# ─────────────────────────────────────────────────────────────────────────────
# decode_access_token
# ─────────────────────────────────────────────────────────────────────────────


class TestDecodeAccessToken:
    def test_valid_token_returns_dict(self):
        token = create_access_token({"sub": "42"})
        result = decode_access_token(token)
        assert isinstance(result, dict)

    def test_valid_token_contains_sub_claim(self):
        token = create_access_token({"sub": "42"})
        result = decode_access_token(token)
        assert result["sub"] == "42"

    def test_valid_token_contains_exp_claim(self):
        token = create_access_token({"sub": "1"})
        result = decode_access_token(token)
        assert "exp" in result

    def test_invalid_token_returns_none(self):
        result = decode_access_token("not.a.token")
        assert result is None

    def test_tampered_token_returns_none(self):
        token = create_access_token({"sub": "1"})
        tampered = token[:-4] + "xxxx"
        assert decode_access_token(tampered) is None

    def test_empty_string_returns_none(self):
        assert decode_access_token("") is None

    def test_roundtrip_preserves_custom_claims(self):
        token = create_access_token({"sub": "7", "role": "admin"})
        result = decode_access_token(token)
        assert result["sub"] == "7"
        assert result["role"] == "admin"
