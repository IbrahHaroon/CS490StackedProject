"""Minimal v2 seed: one demo candidate with profile, education, experience,
skills, career preferences, and a handful of jobs across pipeline stages.

Run after schema_v2.sql against an empty DB:
    python backend/scripts/seed.py
"""

from __future__ import annotations

import os
import sys
from datetime import date, datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.auth import get_password_hash  # noqa: E402
from database.database import SessionLocal  # noqa: E402
from database.models.career_preferences import create_career_preferences  # noqa: E402
from database.models.credentials import Credentials  # noqa: E402
from database.models.education import create_education  # noqa: E402
from database.models.experience import create_experience  # noqa: E402
from database.models.follow_up import create_follow_up  # noqa: E402
from database.models.interview import create_interview  # noqa: E402
from database.models.job import create_job, update_job  # noqa: E402
from database.models.job_activity import create_job_activity  # noqa: E402
from database.models.profile import create_profile  # noqa: E402
from database.models.skill import create_skill  # noqa: E402
from database.models.user import create_user  # noqa: E402

DEMO_EMAIL = "demo@example.com"
DEMO_PASSWORD = "demopass123"


def main() -> int:
    session = SessionLocal()
    try:
        user = create_user(session, DEMO_EMAIL)
        session.add(
            Credentials(
                user_id=user.user_id,
                hashed_password=get_password_hash(DEMO_PASSWORD),
            )
        )
        session.commit()
        print(f"user_id={user.user_id}  email={user.email}")

        profile = create_profile(
            session,
            user.user_id,
            first_name="Alex",
            last_name="Johnson",
            dob=date(1999, 6, 15),
            phone_number="201-555-0101",
            summary="Computer Science senior seeking full-time software engineering roles.",
            address_line="123 Main Street",
            city="Hoboken",
            state="NJ",
            zip_code="07030",
            country="USA",
        )
        print(f"profile_id={profile.profile_id}")

        edu = create_education(
            session,
            user.user_id,
            school="New Jersey Institute of Technology",
            degree="Bachelor of Science",
            field_of_study="Computer Science",
            start_date=date(2021, 9, 1),
            end_date=date(2025, 5, 15),
            gpa="3.7/4.0",
            school_location="Newark, NJ",
        )
        print(f"education_id={edu.education_id}")

        exp = create_experience(
            session,
            user.user_id,
            company="TechStartup Inc.",
            title="Software Engineering Intern",
            start_date=date(2024, 6, 1),
            end_date=date(2024, 8, 31),
            description=(
                "Built REST APIs with FastAPI and PostgreSQL; "
                "improved query performance by 30%."
            ),
            location="Remote",
            sort_order=0,
        )
        print(f"experience_id={exp.experience_id}")

        for i, (name, category, prof) in enumerate(
            [
                ("Python", "Programming Languages", "Advanced"),
                ("React", "Frontend", "Intermediate"),
                ("PostgreSQL", "Databases", "Intermediate"),
                ("Docker", "DevOps", "Beginner"),
            ]
        ):
            create_skill(
                session,
                user.user_id,
                name,
                category=category,
                proficiency=prof,
                sort_order=i,
            )

        create_career_preferences(
            session,
            user_id=user.user_id,
            target_roles="Software Engineer, Backend Engineer",
            location_preferences="NYC Metro, Remote",
            work_mode="Hybrid",
            salary_preference="$120k–$150k",
        )

        jobs_seed = [
            ("Software Engineer", "Google", "Mountain View, CA", "Interested", None),
            (
                "Backend Engineer",
                "Microsoft",
                "Redmond, WA",
                "Applied",
                date(2026, 1, 22),
            ),
            ("Senior Engineer", "Stripe", "Remote", "Interview", date(2026, 2, 10)),
            (
                "Full Stack Engineer",
                "Netflix",
                "Los Gatos, CA",
                "Offer",
                date(2026, 1, 30),
            ),
            (
                "Software Developer",
                "Meta",
                "Menlo Park, CA",
                "Rejected",
                date(2026, 1, 5),
            ),
        ]
        for title, company, location, stage, applied in jobs_seed:
            job = create_job(
                session,
                user_id=user.user_id,
                title=title,
                company_name=company,
                location=location,
                stage=stage,
                application_date=applied,
                years_of_experience=1,
                notes="Referral via mutual connection."
                if company == "Google"
                else None,
            )
            create_job_activity(session, job.job_id, to_stage=stage, notes="Seeded")
            print(f"  job_id={job.job_id}  {company} — {title}  [{stage}]")

            if stage == "Interview":
                create_interview(
                    session,
                    job_id=job.job_id,
                    round_type="Technical Phone Screen",
                    scheduled_at=datetime(2026, 2, 14, 14, 0),
                    interviewer="Jane Smith",
                    mode="phone",
                    prep_notes="Review Stripe API design; prep 2 system-design questions.",
                )
                create_follow_up(
                    session,
                    job_id=job.job_id,
                    description="Send thank-you email after phone screen",
                    due_date=date(2026, 2, 15),
                )
            if stage == "Offer":
                update_job(
                    session,
                    job.job_id,
                    outcome_notes="Offer received: $135k base + RSUs.",
                )

        session.commit()
        print("\nseed complete.")
        return 0
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    sys.exit(main())
