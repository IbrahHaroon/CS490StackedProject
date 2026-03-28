"""Tests for address.py — create_address, get_address, update_address."""

import pytest
from database.models.address import create_address, get_address, update_address


# ─────────────────────────────────────────────────────────────────────────────
# create_address
# ─────────────────────────────────────────────────────────────────────────────

class TestCreateAddress:

    def test_returns_address_object(self, session):
        addr = create_address(session, "123 Main St", "NJ", 8534)
        assert addr is not None

    def test_address_id_is_assigned(self, session):
        addr = create_address(session, "123 Main St", "NJ", 8534)
        assert addr.address_id is not None
        assert addr.address_id >= 1

    def test_address_fields_stored_correctly(self, session):
        addr = create_address(session, "456 Oak Ave", "NY", 10001)
        assert addr.address == "456 Oak Ave"
        assert addr.state == "NY"
        assert addr.zip_code == 10001

    def test_multiple_addresses_get_unique_ids(self, session):
        addr1 = create_address(session, "1 First St", "NJ", 8001)
        addr2 = create_address(session, "2 Second St", "PA", 19103)
        assert addr1.address_id != addr2.address_id

    def test_address_persisted_to_database(self, session):
        addr = create_address(session, "789 Pine Rd", "CA", 90210)
        fetched = get_address(session, addr.address_id)
        assert fetched is not None
        assert fetched.address == "789 Pine Rd"

    def test_identical_addresses_get_separate_rows(self, session):
        addr1 = create_address(session, "Same St", "NJ", 8534)
        addr2 = create_address(session, "Same St", "NJ", 8534)
        assert addr1.address_id != addr2.address_id


# ─────────────────────────────────────────────────────────────────────────────
# get_address
# ─────────────────────────────────────────────────────────────────────────────

class TestGetAddress:

    def test_returns_correct_address(self, session):
        addr = create_address(session, "10 Elm St", "TX", 73301)
        fetched = get_address(session, addr.address_id)
        assert fetched.address_id == addr.address_id

    def test_returns_none_for_missing_id(self, session):
        result = get_address(session, 99999)
        assert result is None

    def test_returns_none_for_id_zero(self, session):
        result = get_address(session, 0)
        assert result is None

    def test_fields_match_after_fetch(self, session):
        addr = create_address(session, "22 Maple Dr", "FL", 33101)
        fetched = get_address(session, addr.address_id)
        assert fetched.address == "22 Maple Dr"
        assert fetched.state == "FL"
        assert fetched.zip_code == 33101

    def test_two_different_ids_return_different_records(self, session):
        a1 = create_address(session, "A St", "NJ", 1111)
        a2 = create_address(session, "B St", "NY", 2222)
        f1 = get_address(session, a1.address_id)
        f2 = get_address(session, a2.address_id)
        assert f1.address != f2.address

    def test_returns_none_for_negative_id(self, session):
        result = get_address(session, -1)
        assert result is None


# ─────────────────────────────────────────────────────────────────────────────
# update_address
# ─────────────────────────────────────────────────────────────────────────────

class TestUpdateAddress:

    def test_update_returns_true_on_success(self, session):
        addr = create_address(session, "Old St", "NJ", 8000)
        addr.address = "New St"
        result = update_address(session, addr)
        assert result is True

    def test_address_field_is_updated(self, session):
        addr = create_address(session, "Old St", "NJ", 8000)
        addr.address = "Updated Blvd"
        update_address(session, addr)
        fetched = get_address(session, addr.address_id)
        assert fetched.address == "Updated Blvd"

    def test_state_field_is_updated(self, session):
        addr = create_address(session, "5 Park Ave", "NJ", 8000)
        addr.state = "PA"
        update_address(session, addr)
        fetched = get_address(session, addr.address_id)
        assert fetched.state == "PA"

    def test_zip_code_field_is_updated(self, session):
        addr = create_address(session, "5 Park Ave", "NJ", 8000)
        addr.zip_code = 19103
        update_address(session, addr)
        fetched = get_address(session, addr.address_id)
        assert fetched.zip_code == 19103

    def test_update_all_fields_at_once(self, session):
        addr = create_address(session, "Old", "NJ", 1000)
        addr.address = "New Ave"
        addr.state = "CA"
        addr.zip_code = 90001
        update_address(session, addr)
        fetched = get_address(session, addr.address_id)
        assert fetched.address == "New Ave"
        assert fetched.state == "CA"
        assert fetched.zip_code == 90001

    def test_other_records_unaffected_by_update(self, session):
        a1 = create_address(session, "First St", "NJ", 1111)
        a2 = create_address(session, "Second St", "NY", 2222)
        a1.address = "Changed St"
        update_address(session, a1)
        fetched_a2 = get_address(session, a2.address_id)
        assert fetched_a2.address == "Second St"
