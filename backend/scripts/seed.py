"""
seed.py
-------
Populate ATS tables with demo data for Sprint 1 presentation.

Two accounts are created:
  - User A (usera@demo.com) — has profile, jobs at various pipeline stages
  - User B (userb@demo.com) — no data, used for ownership/isolation checks

Run from the backend directory with venv active:

    python scripts/seed.py

To reset and re-seed before the demo:
    1. Go to Supabase → SQL Editor and run: TRUNCATE TABLE "user" CASCADE;
    2. Run this script again.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql://user:postgres@localhost:5432/jobsdb",
)
os.environ.setdefault("SECRET_KEY", "seed-script-secret-change-me")

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy.orm import Session
from sqlalchemy import select

from database.auth import get_password_hash
from database.base import Base, engine
from database.models.applied_jobs import create_applied_jobs, update_applied_job
from database.models.company import create_company
from database.models.credentials import create_credentials, get_credentials_by_user_id
from database.models.documents import create_document
from database.models.education import create_education
from database.models.job_activity import create_job_activity
from database.models.position import create_position
from database.models.profile import create_profile, Profile
from database.models.user import create_user, get_user_by_email


def get_or_create_user(session: Session, email: str):
    existing = get_user_by_email(session, email)
    return existing if existing else create_user(session, email)


def seed():
    Base.metadata.create_all(engine)

    with Session(engine) as session:

        # ── Users & Credentials ───────────────────────────────────────────────
        print("── Users & Credentials ──────────────────────────────────────")

        user_a = get_or_create_user(session, "usera@demo.com")
        user_b = get_or_create_user(session, "userb@demo.com")

        for user in [user_a, user_b]:
            if not get_credentials_by_user_id(session, user.user_id):
                hashed = get_password_hash("Demo1234!")
                create_credentials(session, user.user_id, hashed)
                print(f"  user_id={user.user_id}  email={user.email}  → credentials created")
            else:
                print(f"  user_id={user.user_id}  email={user.email}  → already exists")

        # ── Profile (User A only) ─────────────────────────────────────────────
        print("\n── Profile ──────────────────────────────────────────────────")

        existing_profile = session.execute(
            select(Profile).where(Profile.user_id == user_a.user_id)
        ).scalar_one_or_none()

        if not existing_profile:
            profile = create_profile(
                session,
                user_id=user_a.user_id,
                first_name="Alex",
                last_name="Johnson",
                dob=date(1999, 6, 15),
                address="123 Main Street",
                state="NJ",
                zip_code=7030,
                phone_number="201-555-0101",
                summary="Computer Science senior seeking full-time software engineering roles. "
                        "Experienced in Python, React, and PostgreSQL.",
            )
            print(f"  profile_id={profile.profile_id}  name={profile.first_name} {profile.last_name}")
        else:
            print(f"  profile already exists for user_a, skipping")

        # ── Education (User A only) ───────────────────────────────────────────
        print("\n── Education ────────────────────────────────────────────────")

        edu = create_education(
            session,
            user_id=user_a.user_id,
            highest_education="Bachelor's",
            degree="Computer Science",
            college="New Jersey Institute of Technology",
            address="323 Dr Martin Luther King Jr Blvd",
            state="NJ",
            zip_code=7102,
        )
        print(f"  education_id={edu.education_id}  degree={edu.degree}  school={edu.school_or_college}")

        # ── Documents (User A only) ───────────────────────────────────────────
        print("\n── Documents ────────────────────────────────────────────────")

        for doc in [
            {"document_type": "resume", "document_location": "/uploads/alex_resume_v1.pdf"},
            {"document_type": "cover_letter", "document_location": "/uploads/alex_cover_google.pdf"},
            {"document_type": "resume", "document_location": "/uploads/alex_resume_v2_backend.pdf"},
        ]:
            d = create_document(
                session,
                user_id=user_a.user_id,
                document_type=doc["document_type"],
                document_location=doc["document_location"],
            )
            print(f"  doc_id={d.doc_id}  type={d.document_type}")

        # ── Companies ─────────────────────────────────────────────────────────
        print("\n── Companies ────────────────────────────────────────────────")

        companies_data = [
            {"name": "Google", "address": "1600 Amphitheatre Pkwy", "state": "CA", "zip_code": 94043},
            {"name": "Microsoft", "address": "1 Microsoft Way", "state": "WA", "zip_code": 98052},
            {"name": "Amazon", "address": "410 Terry Ave N", "state": "WA", "zip_code": 98109},
            {"name": "Meta", "address": "1 Hacker Way", "state": "CA", "zip_code": 94025},
        ]

        companies = []
        for c in companies_data:
            company = create_company(
                session,
                company_name=c["name"],
                address=c["address"],
                state=c["state"],
                zip_code=c["zip_code"],
            )
            companies.append(company)
            print(f"  company_id={company.company_id}  name={company.name}")

        # ── Positions ─────────────────────────────────────────────────────────
        print("\n── Positions ────────────────────────────────────────────────")

        positions_data = [
            {
                "company_idx": 0,
                "title": "Software Engineer",
                "salary": Decimal("140000.00"),
                "education_req": "Bachelor's in CS or related field",
                "experience_req": "2+ years",
                "description": "Build and scale Google's core infrastructure.",
                "listing_date": date(2026, 1, 10),
            },
            {
                "company_idx": 1,
                "title": "Backend Engineer",
                "salary": Decimal("135000.00"),
                "education_req": "Bachelor's in CS",
                "experience_req": "1+ years",
                "description": "Develop backend services for Microsoft Azure.",
                "listing_date": date(2026, 1, 20),
            },
            {
                "company_idx": 2,
                "title": "Software Development Engineer",
                "salary": Decimal("145000.00"),
                "education_req": "Bachelor's in CS or related field",
                "experience_req": "2+ years",
                "description": "Work on Amazon's e-commerce platform.",
                "listing_date": date(2026, 2, 1),
            },
            {
                "company_idx": 3,
                "title": "Frontend Engineer",
                "salary": Decimal("130000.00"),
                "education_req": "Bachelor's in any discipline",
                "experience_req": "1+ years React",
                "description": "Build user-facing features for Meta's social platforms.",
                "listing_date": date(2026, 2, 10),
            },
        ]

        positions = []
        for pos in positions_data:
            position = create_position(
                session,
                company_id=companies[pos["company_idx"]].company_id,
                title=pos["title"],
                salary=pos["salary"],
                education_req=pos["education_req"],
                experience_req=pos["experience_req"],
                description=pos["description"],
                listing_date=pos["listing_date"],
            )
            positions.append(position)
            print(f"  position_id={position.position_id}  title={position.title}")

        # ── Applications with Pipeline Stages (User A only) ───────────────────
        print("\n── Applications ─────────────────────────────────────────────")

        applications_data = [
            {"position_idx": 0, "years_of_experience": 2, "stage": "Interview"},
            {"position_idx": 1, "years_of_experience": 2, "stage": "Applied"},
            {"position_idx": 2, "years_of_experience": 2, "stage": "Offer"},
            {"position_idx": 3, "years_of_experience": 2, "stage": "Interested"},
        ]

        for app in applications_data:
            position = positions[app["position_idx"]]
            application = create_applied_jobs(
                session,
                user_id=user_a.user_id,
                position_id=position.position_id,
                years_of_experience=app["years_of_experience"],
            )

            # Record initial stage
            create_job_activity(session, application.job_id, "Interested")

            # Advance to target stage and log each transition
            stage_order = ["Interested", "Applied", "Interview", "Offer"]
            target = app["stage"]
            if target != "Interested":
                for stage in stage_order[1:stage_order.index(target) + 1]:
                    update_applied_job(session, application.job_id, application_status=stage)
                    create_job_activity(session, application.job_id, stage)

            print(
                f"  job_id={application.job_id}  "
                f"position={position.title}  "
                f"status={app['stage']}"
            )

        print("\n── Demo Accounts ────────────────────────────────────────────")
        print("  User A — usera@demo.com  / Demo1234!")
        print("  User B — userb@demo.com  / Demo1234!  (no data — for ownership check)")
        print("\n✓ Seed complete.")


if __name__ == "__main__":
    seed()
