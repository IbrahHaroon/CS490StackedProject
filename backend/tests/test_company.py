"""Tests for company.py — create_company, get_company."""

from database.models.company import create_company, get_company

# ─────────────────────────────────────────────────────────────────────────────
# create_company
# ─────────────────────────────────────────────────────────────────────────────


class TestCreateCompany:
    def test_returns_company_object(self, session):
        company = create_company(session, "Acme Corp", "1 Business Rd", "NY", 10001)
        assert company is not None

    def test_company_id_assigned(self, session):
        company = create_company(session, "Acme Corp", "1 Business Rd", "NY", 10001)
        assert company.company_id is not None
        assert company.company_id >= 1

    def test_name_stored_correctly(self, session):
        company = create_company(session, "TechStart Inc", "2 Tech Ave", "CA", 94105)
        assert company.name == "TechStart Inc"

    def test_address_id_created_and_linked(self, session):
        company = create_company(session, "GlobalCo", "3 World Blvd", "TX", 73301)
        assert company.address_id is not None

    def test_multiple_companies_get_unique_ids(self, session):
        c1 = create_company(session, "Company A", "1 A St", "NJ", 1000)
        c2 = create_company(session, "Company B", "2 B St", "NY", 2000)
        assert c1.company_id != c2.company_id

    def test_company_persisted_to_database(self, session):
        company = create_company(session, "PersistCo", "4 Persist Ln", "FL", 33101)
        fetched = get_company(session, company.company_id)
        assert fetched is not None
        assert fetched.name == "PersistCo"


# ─────────────────────────────────────────────────────────────────────────────
# get_company
# ─────────────────────────────────────────────────────────────────────────────


class TestGetCompany:
    def test_returns_correct_company(self, session):
        company = create_company(session, "Acme Corp", "1 Business Rd", "NY", 10001)
        fetched = get_company(session, company.company_id)
        assert fetched.company_id == company.company_id

    def test_returns_none_for_missing_id(self, session):
        result = get_company(session, 99999)
        assert result is None

    def test_returns_none_for_id_zero(self, session):
        result = get_company(session, 0)
        assert result is None

    def test_name_matches_after_fetch(self, session):
        company = create_company(session, "Fetchable LLC", "5 Fetch St", "WA", 98101)
        fetched = get_company(session, company.company_id)
        assert fetched.name == "Fetchable LLC"

    def test_returns_none_for_negative_id(self, session):
        result = get_company(session, -1)
        assert result is None

    def test_two_companies_return_different_records(self, session):
        c1 = create_company(session, "Alpha Inc", "1 Alpha Rd", "NJ", 1111)
        c2 = create_company(session, "Beta Inc", "2 Beta Rd", "NY", 2222)
        f1 = get_company(session, c1.company_id)
        f2 = get_company(session, c2.company_id)
        assert f1.name != f2.name
