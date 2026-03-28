"""
seed.py
-------
Populate every ATS table with sample data.

Run from the project root:

    DATABASE_URL=postgresql://user:password@localhost:5432/jobsdb \
    SECRET_KEY=any-secret \
    python scripts/seed.py

The script is idempotent for the email-unique constraint: it skips users
whose email already exists and re-uses any rows already present rather than
duplicating them.
"""

import os
import sys

# Allow the script to be run from the project root without installing the package.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Environment must be set before project modules are imported so pydantic-settings
# can initialise without a .env file.
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql://user:postgres@localhost:5432/jobsdb",
)
os.environ.setdefault("SECRET_KEY", "seed-script-secret-change-me")

from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from database.base import Base, engine
from database.auth import get_password_hash
from database.models.address import create_address
from database.models.user import create_user, get_user_by_email
from database.models.credentials import create_credentials
from database.models.profile import create_profile
from database.models.education import create_education
from database.models.documents import create_document
from database.models.company import create_company
from database.models.position import create_position
from database.models.applied_jobs import create_applied_jobs


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_or_create_user(session: Session, email: str):
    existing = get_user_by_email(session, email)
    return existing if existing else create_user(session, email)


# ---------------------------------------------------------------------------
# Seed data
# ---------------------------------------------------------------------------

USERS = [
    "alice@example.com",
    "bob@example.com",
    "carol@example.com",
]

PROFILES = [
    {
        "first_name": "Alice",
        "last_name": "Anderson",
        "dob": date(1990, 4, 15),
        "address": "101 Maple Street",
        "state": "CA",
        "zip_code": 94101,
        "phone_number": "415-555-0101",
        "summary": "Senior software engineer with 10 years in backend systems.",
    },
    {
        "first_name": "Bob",
        "last_name": "Baker",
        "dob": date(1985, 11, 3),
        "address": "202 Oak Avenue",
        "state": "TX",
        "zip_code": 73301,
        "phone_number": "512-555-0202",
        "summary": "Full-stack developer specialising in React and Node.",
    },
    {
        "first_name": "Carol",
        "last_name": "Chen",
        "dob": date(1995, 7, 22),
        "address": "303 Pine Road",
        "state": "NY",
        "zip_code": 10001,
        "phone_number": "212-555-0303",
        "summary": "Data scientist with expertise in ML pipelines and Python.",
    },
]

EDUCATIONS = [
    {
        "highest_education": "Master's",
        "degree": "Computer Science",
        "college": "UC Berkeley",
        "address": "1 University Ave",
        "state": "CA",
        "zip_code": 94720,
    },
    {
        "highest_education": "Bachelor's",
        "degree": "Software Engineering",
        "college": "University of Texas",
        "address": "1 University Station",
        "state": "TX",
        "zip_code": 78712,
    },
    {
        "highest_education": "PhD",
        "degree": "Data Science",
        "college": "Columbia University",
        "address": "116th St & Broadway",
        "state": "NY",
        "zip_code": 10027,
    },
]

DOCUMENTS = [
    [
        {"document_type": "resume",       "document_location": "/uploads/alice_resume.pdf"},
        {"document_type": "cover_letter", "document_location": "/uploads/alice_cover.pdf"},
    ],
    [
        {"document_type": "resume",       "document_location": "/uploads/bob_resume.pdf"},
        {"document_type": "portfolio",    "document_location": "/uploads/bob_portfolio.pdf"},
    ],
    [
        {"document_type": "resume",       "document_location": "/uploads/carol_resume.pdf"},
        {"document_type": "transcript",   "document_location": "/uploads/carol_transcript.pdf"},
    ],
]

COMPANIES = [
    {"name": "Acme Corp",       "address": "500 Market St",   "state": "CA", "zip_code": 94105},
    {"name": "Globex Inc",      "address": "700 Congress Ave", "state": "TX", "zip_code": 78701},
    {"name": "Initech Ltd",     "address": "350 5th Ave",      "state": "NY", "zip_code": 10118},
]

POSITIONS = [
    {
        "title": "Backend Engineer",
        "salary": Decimal("120000.00"),
        "education_req": "Bachelor's in CS or related field",
        "experience_req": "3+ years Python / FastAPI",
        "description": "Build and maintain REST APIs for our core platform.",
        "listing_date": date(2026, 1, 10),
    },
    {
        "title": "Frontend Engineer",
        "salary": Decimal("110000.00"),
        "education_req": "Bachelor's in any discipline",
        "experience_req": "2+ years React",
        "description": "Develop responsive UIs and collaborate with design.",
        "listing_date": date(2026, 1, 15),
    },
    {
        "title": "Data Scientist",
        "salary": Decimal("135000.00"),
        "education_req": "Master's or PhD in a quantitative field",
        "experience_req": "4+ years ML/data pipelines",
        "description": "Design ML models to improve candidate matching.",
        "listing_date": date(2026, 2, 1),
    },
]

APPLICATIONS = [
    {"user_idx": 0, "position_idx": 0, "years_of_experience": 8},   # Alice → Backend
    {"user_idx": 1, "position_idx": 1, "years_of_experience": 5},   # Bob   → Frontend
    {"user_idx": 2, "position_idx": 2, "years_of_experience": 6},   # Carol → Data Scientist
    {"user_idx": 0, "position_idx": 2, "years_of_experience": 8},   # Alice → Data Scientist (cross-apply)
]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def seed():
    # Ensure tables exist (no-op if they're already there).
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        print("── Users & Credentials ──────────────────────────────────────")
        users = []
        for email in USERS:
            user = get_or_create_user(session, email)
            users.append(user)
            print(f"  user_id={user.user_id}  email={user.email}")

            # Create credentials only if none exist yet.
            from database.models.credentials import get_credentials_by_user_id
            if not get_credentials_by_user_id(session, user.user_id):
                hashed = get_password_hash("Password123!")
                create_credentials(session, user.user_id, hashed)
                print(f"    → credentials created")

        print("\n── Profiles ─────────────────────────────────────────────────")
        for user, p in zip(users, PROFILES):
            # Skip if profile already exists (unique constraint on user_id).
            from database.models.profile import get_profile
            from sqlalchemy import select
            from database.models.profile import Profile
            existing = session.execute(
                select(Profile).where(Profile.user_id == user.user_id)
            ).scalar_one_or_none()
            if existing:
                print(f"  profile already exists for user_id={user.user_id}, skipping")
                continue
            profile = create_profile(
                session,
                user_id=user.user_id,
                first_name=p["first_name"],
                last_name=p["last_name"],
                dob=p["dob"],
                address=p["address"],
                state=p["state"],
                zip_code=p["zip_code"],
                phone_number=p["phone_number"],
                summary=p["summary"],
            )
            print(f"  profile_id={profile.profile_id}  name={profile.first_name} {profile.last_name}")

        print("\n── Education ────────────────────────────────────────────────")
        for user, e in zip(users, EDUCATIONS):
            edu = create_education(
                session,
                user_id=user.user_id,
                highest_education=e["highest_education"],
                degree=e["degree"],
                college=e["college"],
                address=e["address"],
                state=e["state"],
                zip_code=e["zip_code"],
            )
            print(f"  education_id={edu.education_id}  degree={edu.degree}  school={edu.school_or_college}")

        print("\n── Documents ────────────────────────────────────────────────")
        for user, doc_list in zip(users, DOCUMENTS):
            for d in doc_list:
                doc = create_document(
                    session,
                    user_id=user.user_id,
                    document_type=d["document_type"],
                    document_location=d["document_location"],
                )
                print(f"  doc_id={doc.doc_id}  type={doc.document_type}  user_id={doc.user_id}")

        print("\n── Companies ────────────────────────────────────────────────")
        companies = []
        for c in COMPANIES:
            company = create_company(
                session,
                company_name=c["name"],
                address=c["address"],
                state=c["state"],
                zip_code=c["zip_code"],
            )
            companies.append(company)
            print(f"  company_id={company.company_id}  name={company.name}")

        print("\n── Positions ────────────────────────────────────────────────")
        positions = []
        for company, pos in zip(companies, POSITIONS):
            position = create_position(
                session,
                company_id=company.company_id,
                title=pos["title"],
                salary=pos["salary"],
                education_req=pos["education_req"],
                experience_req=pos["experience_req"],
                description=pos["description"],
                listing_date=pos["listing_date"],
            )
            positions.append(position)
            print(f"  position_id={position.position_id}  title={position.title}  company_id={position.company_id}")

        print("\n── Applications ─────────────────────────────────────────────")
        for app in APPLICATIONS:
            user = users[app["user_idx"]]
            position = positions[app["position_idx"]]
            application = create_applied_jobs(
                session,
                user_id=user.user_id,
                position_id=position.position_id,
                years_of_experience=app["years_of_experience"],
            )
            print(
                f"  job_id={application.job_id}  "
                f"user_id={application.user_id}  "
                f"position_id={application.position_id}  "
                f"status={application.application_status}"
            )

        print("\n✓ Seed complete.")


if __name__ == "__main__":
    seed()
