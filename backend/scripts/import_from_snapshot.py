"""Re-populate the v2 schema from a snapshot produced by `snapshot_to_json.py`.

Run AFTER `schema_v2.sql` has been applied. The destination DB must contain
the v2 tables, all empty.

Strategy
--------
- Original PKs are preserved everywhere they exist on both sides
  (`user`, `credentials`, `profile`, `education`, `experience`, `skills`,
   `career_preferences`, `applied_jobs`→`job`, `job_activity`, `interview`,
   `follow_up`, `documents`→`document`). This means child FKs map directly
   without lookup tables.
- Tables that change shape:
    address      → inlined onto profile / education
    applied_jobs → joined with position+company → `job` (denormalized strings)
    outcome      → folded into `job.stage` (terminal states only) and
                   `job.outcome_notes`
    documents    → `document` + a v1 `document_version` per row
                   (+ `document_tag` rows split from CSV)
    document_job_link / documents.job_id / job_document → `job_document_link`
    job_document → new `document` (type='ai_draft') + `document_version`
                   + `job_document_link` per row
- Sequences are bumped to MAX(pk)+1 at the end so future inserts work.
- The whole import runs inside a single transaction. Any error rolls back.

Usage:
  python backend/scripts/import_from_snapshot.py [path/to/snapshot.json]

If no path is given, the newest `backend/backups/snapshot_*.json` is used.
"""

from __future__ import annotations

import glob
import json
import os
import sys
from typing import Any

# Make `database` importable when invoked as a script.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text  # noqa: E402

from database.database import engine  # noqa: E402

BACKUP_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backups"
)

# Outcome states that are authoritative for `job.stage` (override the legacy
# applied_jobs.application_status, which often lags).
TERMINAL_OUTCOME_STATES = {"Rejected", "Offer", "Accepted", "Withdrawn"}


# --------------------------------------------------------------------------- #
#  Helpers                                                                     #
# --------------------------------------------------------------------------- #

def _latest_snapshot() -> str:
    matches = sorted(glob.glob(os.path.join(BACKUP_DIR, "snapshot_*.json")))
    if not matches:
        sys.exit(f"ERROR: no snapshot_*.json found in {BACKUP_DIR}")
    return matches[-1]


def _executemany(conn, sql: str, rows: list[dict[str, Any]]) -> None:
    if rows:
        conn.execute(text(sql), rows)


def _bump_sequence(conn, table: str, pk_col: str) -> None:
    """Set the table's serial sequence to MAX(pk)+1 so new auto-inserts work."""
    conn.execute(
        text(
            f"""
            SELECT setval(
                pg_get_serial_sequence(:tbl, :col),
                COALESCE((SELECT MAX({pk_col}) FROM {table}), 0) + 1,
                false
            )
            """
        ),
        {"tbl": table, "col": pk_col},
    )


# --------------------------------------------------------------------------- #
#  Per-table inserters                                                         #
# --------------------------------------------------------------------------- #

def insert_users(conn, rows):
    _executemany(
        conn,
        'INSERT INTO "user" (user_id, email) VALUES (:user_id, :email)',
        [{"user_id": r["user_id"], "email": r["email"]} for r in rows],
    )


def insert_credentials(conn, rows):
    _executemany(
        conn,
        "INSERT INTO credentials (credential_id, user_id, hashed_password) "
        "VALUES (:credential_id, :user_id, :hashed_password)",
        rows,
    )


def insert_password_reset_tokens(conn, rows):
    _executemany(
        conn,
        "INSERT INTO password_reset_token "
        "(token_id, user_id, token_hash, expires_at, used) "
        "VALUES (:token_id, :user_id, :token_hash, :expires_at, :used)",
        rows,
    )


def insert_token_blacklist(conn, rows):
    _executemany(
        conn,
        "INSERT INTO token_blacklist (id, jti, expires_at) "
        "VALUES (:id, :jti, :expires_at)",
        rows,
    )


def insert_profiles(conn, rows, address_map):
    payload = []
    for r in rows:
        addr = address_map.get(r["address_id"], {}) if r.get("address_id") else {}
        zip_code = addr.get("zip_code")
        payload.append(
            {
                "profile_id": r["profile_id"],
                "user_id": r["user_id"],
                "first_name": r["first_name"],
                "last_name": r["last_name"],
                "dob": r["dob"],
                "phone_number": r.get("phone_number"),
                "summary": r.get("summary"),
                "address_line": addr.get("address"),
                "city": None,
                "state": addr.get("state"),
                "zip_code": str(zip_code) if zip_code is not None else None,
                "country": None,
            }
        )
    _executemany(
        conn,
        """
        INSERT INTO profile
          (profile_id, user_id, first_name, last_name, dob, phone_number,
           summary, address_line, city, state, zip_code, country)
        VALUES
          (:profile_id, :user_id, :first_name, :last_name, :dob, :phone_number,
           :summary, :address_line, :city, :state, :zip_code, :country)
        """,
        payload,
    )


def insert_education(conn, rows, address_map):
    payload = []
    for r in rows:
        addr = address_map.get(r["address_id"], {}) if r.get("address_id") else {}
        loc_parts = [
            addr.get("address"),
            addr.get("state"),
            str(addr["zip_code"]) if addr.get("zip_code") is not None else None,
        ]
        school_location = ", ".join(p for p in loc_parts if p) or None
        payload.append(
            {
                "education_id": r["education_id"],
                "user_id": r["user_id"],
                "school": r["school_or_college"],
                "degree": r["degree"],
                "field_of_study": r.get("field_of_study"),
                "start_date": r.get("start_date"),
                "end_date": r.get("end_date"),
                "gpa": r.get("gpa"),
                "school_location": school_location,
                "sort_order": 0,
            }
        )
    _executemany(
        conn,
        """
        INSERT INTO education
          (education_id, user_id, school, degree, field_of_study,
           start_date, end_date, gpa, school_location, sort_order)
        VALUES
          (:education_id, :user_id, :school, :degree, :field_of_study,
           :start_date, :end_date, :gpa, :school_location, :sort_order)
        """,
        payload,
    )


def insert_experience(conn, rows):
    _executemany(
        conn,
        """
        INSERT INTO experience
          (experience_id, user_id, company, title, location,
           start_date, end_date, description, sort_order)
        VALUES
          (:experience_id, :user_id, :company, :title, :location,
           :start_date, :end_date, :description, :sort_order)
        """,
        [
            {
                "experience_id": r["experience_id"],
                "user_id": r["user_id"],
                "company": r["company"],
                "title": r["title"],
                "location": None,  # not present in v1
                "start_date": r["start_date"],
                "end_date": r.get("end_date"),
                "description": r.get("description"),
                "sort_order": r.get("sort_order", 0),
            }
            for r in rows
        ],
    )


def insert_skills(conn, rows):
    _executemany(
        conn,
        """
        INSERT INTO skill
          (skill_id, user_id, name, category, proficiency, sort_order)
        VALUES
          (:skill_id, :user_id, :name, :category, :proficiency, :sort_order)
        """,
        rows,
    )


def insert_career_prefs(conn, rows):
    _executemany(
        conn,
        """
        INSERT INTO career_preferences
          (preference_id, user_id, target_roles, location_preferences,
           work_mode, salary_preference)
        VALUES
          (:preference_id, :user_id, :target_roles, :location_preferences,
           :work_mode, :salary_preference)
        """,
        rows,
    )


def insert_jobs(conn, applied_jobs, outcome_by_legacy_job):
    payload = []
    for r in applied_jobs:
        legacy_job_id = r["legacy_job_id"]
        stage = r["application_status"]
        outcome_notes = r.get("outcome_notes")
        outcome = outcome_by_legacy_job.get(legacy_job_id)
        if outcome:
            # Terminal outcome wins over the application_status snapshot.
            if outcome["outcome_state"] in TERMINAL_OUTCOME_STATES:
                stage = outcome["outcome_state"]
            outcome_notes = outcome.get("outcome_notes") or outcome_notes
        payload.append(
            {
                "job_id": legacy_job_id,
                "user_id": r["user_id"],
                "title": r["position_title"],
                "company_name": r["company_name"],
                "location": r.get("position_location"),
                "source_url": None,
                "description": r.get("position_description"),
                "stage": stage,
                "stage_changed_at": r.get("stage_changed_at"),
                "application_date": r.get("application_date"),
                "deadline": r.get("deadline"),
                "priority": None,
                "salary": r.get("position_salary"),
                "years_of_experience": r.get("years_of_experience"),
                "notes": r.get("recruiter_notes"),
                "company_research_notes": None,  # no v1 source; populated via S3-011 UX
                "outcome_notes": outcome_notes,
                "created_at": r.get("application_date"),  # best available
                "archived_at": None,
            }
        )
    _executemany(
        conn,
        """
        INSERT INTO job
          (job_id, user_id, title, company_name, location, source_url,
           description, stage, stage_changed_at, application_date, deadline,
           priority, salary, years_of_experience, notes, company_research_notes,
           outcome_notes, created_at, archived_at)
        VALUES
          (:job_id, :user_id, :title, :company_name, :location, :source_url,
           :description, :stage, :stage_changed_at, :application_date, :deadline,
           :priority, :salary, :years_of_experience, :notes, :company_research_notes,
           :outcome_notes, :created_at, :archived_at)
        """,
        payload,
    )


def insert_job_activity(conn, rows, valid_job_ids):
    skipped = 0
    payload = []
    for r in rows:
        if r["job_id"] not in valid_job_ids:
            skipped += 1
            continue
        payload.append(
            {
                "activity_id": r["activity_id"],
                "job_id": r["job_id"],
                "event_type": r.get("event_type") or "stage_change",
                "from_stage": None,
                "to_stage": r["stage"],
                "notes": r.get("notes"),
                "occurred_at": r["changed_at"],
            }
        )
    _executemany(
        conn,
        """
        INSERT INTO job_activity
          (activity_id, job_id, event_type, from_stage, to_stage, notes, occurred_at)
        VALUES
          (:activity_id, :job_id, :event_type, :from_stage, :to_stage, :notes, :occurred_at)
        """,
        payload,
    )
    return skipped


def insert_interviews(conn, rows, valid_job_ids):
    skipped = 0
    payload = []
    for r in rows:
        if r["job_id"] not in valid_job_ids:
            skipped += 1
            continue
        payload.append(
            {
                "interview_id": r["interview_id"],
                "job_id": r["job_id"],
                "round_type": r["round_type"],
                "scheduled_at": r["scheduled_at"],
                "interviewer": None,
                "mode": None,
                "prep_notes": None,  # no v1 source; populated via S3-013 UX
                "notes": r.get("notes"),
            }
        )
    _executemany(
        conn,
        """
        INSERT INTO interview
          (interview_id, job_id, round_type, scheduled_at, interviewer, mode, prep_notes, notes)
        VALUES
          (:interview_id, :job_id, :round_type, :scheduled_at, :interviewer, :mode, :prep_notes, :notes)
        """,
        payload,
    )
    return skipped


def insert_follow_ups(conn, rows, valid_job_ids):
    skipped = 0
    payload = []
    for r in rows:
        if r["job_id"] not in valid_job_ids:
            skipped += 1
            continue
        payload.append(
            {
                "followup_id": r["followup_id"],
                "job_id": r["job_id"],
                "description": r["description"],
                "due_date": r.get("due_date"),
                "completed": r.get("completed", False),
            }
        )
    _executemany(
        conn,
        """
        INSERT INTO follow_up
          (followup_id, job_id, description, due_date, completed)
        VALUES
          (:followup_id, :job_id, :description, :due_date, :completed)
        """,
        payload,
    )
    return skipped


def import_documents_pipeline(
    conn,
    documents,
    legacy_versions,
    document_job_links,
    job_documents,
    valid_job_ids,
    job_user_map,
):
    """The most involved bit. See module docstring for the mapping.

    Returns a dict of counters: documents_in, versions_created, tags_created,
    job_links_created, job_links_skipped, ai_drafts_created.
    """
    stats = {
        "documents_in": 0,
        "versions_created": 0,
        "tags_created": 0,
        "job_links_created": 0,
        "job_links_skipped": 0,
        "ai_drafts_created": 0,
    }

    # ---- 1. document rows (preserve doc_id) ---------------------------------
    doc_payload = []
    for r in documents:
        title = r.get("document_name") or f"{r['document_type']} #{r['doc_id']}"
        doc_payload.append(
            {
                "document_id": r["doc_id"],
                "user_id": r["user_id"],
                "title": title,
                "document_type": r["document_type"],
                "status": r.get("status") or "Draft",
                "current_version_id": None,
                "is_deleted": bool(r.get("is_archived", False)),
                "created_at": r.get("created_at"),
                "updated_at": r.get("updated_at") or r.get("created_at"),
            }
        )
    _executemany(
        conn,
        """
        INSERT INTO document
          (document_id, user_id, title, document_type, status,
           current_version_id, is_deleted, created_at, updated_at)
        VALUES
          (:document_id, :user_id, :title, :document_type, :status,
           :current_version_id, :is_deleted, :created_at, :updated_at)
        """,
        doc_payload,
    )
    stats["documents_in"] = len(doc_payload)

    # Bump the document_id sequence so the upcoming AI-draft auto-inserts
    # don't collide with the preserved IDs.
    if doc_payload:
        _bump_sequence(conn, "document", "document_id")

    # ---- 2. seed v1 document_version per legacy document --------------------
    # All inserts use auto-PK; we capture the new version_id with RETURNING so
    # we can then set document.current_version_id.
    doc_to_latest_version: dict[int, int] = {}
    for r in documents:
        new_version_id = conn.execute(
            text(
                """
                INSERT INTO document_version
                  (document_id, version_number, storage_location, content,
                   source, created_at)
                VALUES
                  (:document_id, 1, :storage_location, :content, :source,
                   :created_at)
                RETURNING version_id
                """
            ),
            {
                "document_id": r["doc_id"],
                "storage_location": r.get("document_location"),
                "content": r.get("content"),
                "source": "upload",
                "created_at": r.get("created_at"),
            },
        ).scalar_one()
        doc_to_latest_version[r["doc_id"]] = new_version_id
        stats["versions_created"] += 1

    # ---- 3. legacy document_version rows (additional versions) --------------
    # Empty in this snapshot but handled defensively.
    for v in legacy_versions:
        new_version_id = conn.execute(
            text(
                """
                INSERT INTO document_version
                  (document_id, version_number, storage_location, content,
                   source, created_at)
                VALUES
                  (:document_id, :version_number, :storage_location, :content,
                   :source, :created_at)
                RETURNING version_id
                """
            ),
            {
                "document_id": v["doc_id"],
                # If the legacy version_number was 1 we now have two v1 rows
                # for the same document — bump to avoid the UNIQUE collision.
                "version_number": (v.get("version_number") or 1) + 1,
                "storage_location": v.get("document_location"),
                "content": v.get("content"),
                "source": "upload",
                "created_at": v.get("created_at"),
            },
        ).scalar_one()
        doc_to_latest_version[v["doc_id"]] = new_version_id
        stats["versions_created"] += 1

    # ---- 4. set document.current_version_id ---------------------------------
    for doc_id, ver_id in doc_to_latest_version.items():
        conn.execute(
            text(
                "UPDATE document SET current_version_id = :v WHERE document_id = :d"
            ),
            {"v": ver_id, "d": doc_id},
        )

    # ---- 5. tags from CSV ---------------------------------------------------
    tag_payload = []
    seen_tags: set[tuple[int, str]] = set()
    for r in documents:
        if not r.get("tags"):
            continue
        for raw in str(r["tags"]).split(","):
            label = raw.strip()
            if not label:
                continue
            key = (r["doc_id"], label.lower())
            if key in seen_tags:
                continue
            seen_tags.add(key)
            tag_payload.append({"document_id": r["doc_id"], "label": label})
    _executemany(
        conn,
        "INSERT INTO document_tag (document_id, label) VALUES (:document_id, :label)",
        tag_payload,
    )
    stats["tags_created"] = len(tag_payload)

    # ---- 6. job_document_link from legacy document_job_link + documents.job_id ----
    # Build a set of (job_id, version_id, role) so we don't double-link.
    link_keys: set[tuple[int, int, str | None]] = set()
    link_payload = []

    def add_link(job_id, doc_id, role, linked_at):
        if job_id not in valid_job_ids:
            stats["job_links_skipped"] += 1
            return
        version_id = doc_to_latest_version.get(doc_id)
        if version_id is None:
            stats["job_links_skipped"] += 1
            return
        key = (job_id, version_id, role)
        if key in link_keys:
            return
        link_keys.add(key)
        link_payload.append(
            {
                "job_id": job_id,
                "version_id": version_id,
                "role": role,
                "linked_at": linked_at,
            }
        )

    # Doc-type lookup so we can derive `role` from the parent document.
    doc_type_by_id = {r["doc_id"]: r["document_type"] for r in documents}

    for link in document_job_links:
        add_link(
            link["job_id"],
            link["doc_id"],
            doc_type_by_id.get(link["doc_id"]),
            link.get("linked_at"),
        )
    for r in documents:
        if r.get("job_id") is not None:
            add_link(
                r["job_id"],
                r["doc_id"],
                r["document_type"],
                r.get("updated_at") or r.get("created_at"),
            )

    _executemany(
        conn,
        """
        INSERT INTO job_document_link
          (job_id, version_id, role, linked_at)
        VALUES
          (:job_id, :version_id, :role, :linked_at)
        """,
        link_payload,
    )
    stats["job_links_created"] = len(link_payload)

    # ---- 7. job_document → new document + version + link --------------------
    for jd in job_documents:
        legacy_job_id = jd["job_id"]
        if legacy_job_id not in valid_job_ids:
            stats["job_links_skipped"] += 1
            continue
        owner_user_id = job_user_map.get(legacy_job_id)
        if owner_user_id is None:
            stats["job_links_skipped"] += 1
            continue

        new_document_id = conn.execute(
            text(
                """
                INSERT INTO document
                  (user_id, title, document_type, status, current_version_id,
                   is_deleted, created_at, updated_at)
                VALUES
                  (:user_id, :title, 'ai_draft', 'Draft', NULL, FALSE,
                   :created_at, :updated_at)
                RETURNING document_id
                """
            ),
            {
                "user_id": owner_user_id,
                "title": jd.get("title") or f"AI Draft (job {legacy_job_id})",
                "created_at": jd.get("created_at"),
                "updated_at": jd.get("updated_at") or jd.get("created_at"),
            },
        ).scalar_one()

        new_version_id = conn.execute(
            text(
                """
                INSERT INTO document_version
                  (document_id, version_number, storage_location, content,
                   source, created_at)
                VALUES
                  (:document_id, 1, NULL, :content, 'ai', :created_at)
                RETURNING version_id
                """
            ),
            {
                "document_id": new_document_id,
                "content": jd.get("content"),
                "created_at": jd.get("created_at"),
            },
        ).scalar_one()

        conn.execute(
            text(
                "UPDATE document SET current_version_id = :v WHERE document_id = :d"
            ),
            {"v": new_version_id, "d": new_document_id},
        )
        conn.execute(
            text(
                """
                INSERT INTO job_document_link
                  (job_id, version_id, role, linked_at)
                VALUES
                  (:job_id, :version_id, 'ai_draft', :linked_at)
                """
            ),
            {
                "job_id": legacy_job_id,
                "version_id": new_version_id,
                "linked_at": jd.get("updated_at") or jd.get("created_at"),
            },
        )
        stats["ai_drafts_created"] += 1
        stats["versions_created"] += 1

    return stats


# --------------------------------------------------------------------------- #
#  Main                                                                        #
# --------------------------------------------------------------------------- #

def main(argv: list[str]) -> int:
    snapshot_path = argv[1] if len(argv) > 1 else _latest_snapshot()
    print(f"Loading {snapshot_path}")
    with open(snapshot_path, encoding="utf-8") as f:
        snap = json.load(f)

    address_map = {a["address_id"]: a for a in snap.get("address", [])}
    outcome_by_legacy_job = {o["job_id"]: o for o in snap.get("outcome", [])}
    valid_job_ids = {j["legacy_job_id"] for j in snap.get("applied_jobs", [])}
    job_user_map = {j["legacy_job_id"]: j["user_id"] for j in snap.get("applied_jobs", [])}

    legacy_counts = snap.get("_meta", {}).get("row_counts", {})

    # Single transaction — anything raises → full rollback.
    with engine.begin() as conn:
        insert_users(conn, snap.get("user", []))
        insert_credentials(conn, snap.get("credentials", []))
        insert_password_reset_tokens(conn, snap.get("password_reset_token", []))
        insert_token_blacklist(conn, snap.get("token_blacklist", []))

        insert_profiles(conn, snap.get("profile", []), address_map)
        insert_education(conn, snap.get("education", []), address_map)
        insert_experience(conn, snap.get("experience", []))
        insert_skills(conn, snap.get("skills", []))
        insert_career_prefs(conn, snap.get("career_preferences", []))

        insert_jobs(conn, snap.get("applied_jobs", []), outcome_by_legacy_job)
        skipped_activity = insert_job_activity(conn, snap.get("job_activity", []), valid_job_ids)
        skipped_interview = insert_interviews(conn, snap.get("interview", []), valid_job_ids)
        skipped_followup = insert_follow_ups(conn, snap.get("follow_up", []), valid_job_ids)

        doc_stats = import_documents_pipeline(
            conn,
            snap.get("documents", []),
            snap.get("document_version", []),
            snap.get("document_job_link", []),
            snap.get("job_document", []),
            valid_job_ids,
            job_user_map,
        )

        # Bump every preserved-PK sequence so future auto-inserts work.
        for table, pk in [
            ('"user"', "user_id"),
            ("credentials", "credential_id"),
            ("password_reset_token", "token_id"),
            ("token_blacklist", "id"),
            ("profile", "profile_id"),
            ("education", "education_id"),
            ("experience", "experience_id"),
            ("skill", "skill_id"),
            ("career_preferences", "preference_id"),
            ("job", "job_id"),
            ("job_activity", "activity_id"),
            ("interview", "interview_id"),
            ("follow_up", "followup_id"),
            ("document", "document_id"),
            ("document_version", "version_id"),
            ("document_tag", "tag_id"),
            ("job_document_link", "link_id"),
        ]:
            _bump_sequence(conn, table, pk)

    # Verify final counts
    print()
    print("=== verification (legacy → v2 row counts) ===")
    expectations = [
        ("user", "user", legacy_counts.get("user", 0)),
        ("credentials", "credentials", legacy_counts.get("credentials", 0)),
        ("password_reset_token", "password_reset_token", legacy_counts.get("password_reset_token", 0)),
        ("token_blacklist", "token_blacklist", legacy_counts.get("token_blacklist", 0)),
        ("profile", "profile", legacy_counts.get("profile", 0)),
        ("education", "education", legacy_counts.get("education", 0)),
        ("experience", "experience", legacy_counts.get("experience", 0)),
        ("skills", "skill", legacy_counts.get("skills", 0)),
        ("career_preferences", "career_preferences", legacy_counts.get("career_preferences", 0)),
        ("applied_jobs", "job", legacy_counts.get("applied_jobs", 0)),
        ("job_activity", "job_activity", legacy_counts.get("job_activity", 0) - skipped_activity),
        ("interview", "interview", legacy_counts.get("interview", 0) - skipped_interview),
        ("follow_up", "follow_up", legacy_counts.get("follow_up", 0) - skipped_followup),
        ("documents (+ai_drafts)", "document",
            legacy_counts.get("documents", 0) + doc_stats["ai_drafts_created"]),
    ]

    with engine.connect() as conn:
        for legacy_label, v2_table, expected in expectations:
            actual = conn.execute(text(f'SELECT COUNT(*) FROM "{v2_table}"')).scalar_one()
            status = "ok" if actual == expected else "MISMATCH"
            print(f"  [{status}] {legacy_label:<24} expected={expected:>4}  actual={actual:>4}")
        # Pure-v2 tables (no direct 1:1 source)
        for v2_table in ("document_version", "document_tag", "job_document_link"):
            actual = conn.execute(text(f'SELECT COUNT(*) FROM "{v2_table}"')).scalar_one()
            print(f"  [info] {v2_table:<24} actual={actual:>4}")

    print()
    print("Document pipeline stats:")
    for k, v in doc_stats.items():
        print(f"  {k:<22} {v}")
    if skipped_activity or skipped_interview or skipped_followup:
        print()
        print("Skipped child rows due to missing parent job:")
        print(f"  job_activity: {skipped_activity}")
        print(f"  interview:    {skipped_interview}")
        print(f"  follow_up:    {skipped_followup}")

    print()
    print("Import complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
