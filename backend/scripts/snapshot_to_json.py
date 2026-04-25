"""Extract every legacy v1 table needed for re-import into a single JSON snapshot.

Run this BEFORE the schema cutover (`schema_v2.sql`). It is read-only — no DDL,
no INSERTs, no UPDATEs.

The snapshot is consumed by `import_from_snapshot.py` after the v2 schema is
built. We write JSON (not raw SQL) because the v2 column shapes differ from v1
in ways that are easier to map in Python than in SQL.

Tables skipped on purpose:
  recruiter, recruiter_credentials, recruiter_password_reset_token —
  no destination in the candidate-only v2 schema.

Usage:
  python backend/scripts/snapshot_to_json.py
"""

from __future__ import annotations

import json
import os
import sys
from datetime import date, datetime
from decimal import Decimal
from typing import Any

# Make `database` importable when invoked as a script.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text  # noqa: E402

from database.database import engine  # noqa: E402

BACKUP_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backups"
)


# --- legacy table extractions -------------------------------------------------
#
# Each entry is (output_key, sql). Order is informational only — the consumer
# rebuilds FKs from the legacy IDs preserved in each row.
#
# `applied_jobs` is denormalized via JOIN so the consumer can build a single
# `job` row per record without re-querying.
EXTRACTIONS: list[tuple[str, str]] = [
    ("user", 'SELECT * FROM "user" ORDER BY user_id'),
    ("credentials", "SELECT * FROM credentials ORDER BY credential_id"),
    (
        "password_reset_token",
        "SELECT * FROM password_reset_token ORDER BY token_id",
    ),
    ("token_blacklist", "SELECT * FROM token_blacklist ORDER BY id"),
    ("address", "SELECT * FROM address ORDER BY address_id"),
    ("profile", "SELECT * FROM profile ORDER BY profile_id"),
    ("education", "SELECT * FROM education ORDER BY education_id"),
    ("experience", "SELECT * FROM experience ORDER BY experience_id"),
    ("skills", "SELECT * FROM skills ORDER BY skill_id"),
    ("career_preferences", "SELECT * FROM career_preferences ORDER BY preference_id"),
    (
        "applied_jobs",
        # Flatten position + company so the consumer can build one v2 `job` row
        # per applied_jobs record. Aliases keep the original column names visible.
        """
        SELECT
            aj.job_id              AS legacy_job_id,
            aj.user_id             AS user_id,
            aj.position_id         AS legacy_position_id,
            aj.years_of_experience AS years_of_experience,
            aj.application_date    AS application_date,
            aj.application_status  AS application_status,
            aj.stage_changed_at    AS stage_changed_at,
            aj.deadline            AS deadline,
            aj.recruiter_notes     AS recruiter_notes,
            aj.outcome_notes       AS outcome_notes,
            p.title                AS position_title,
            p.salary               AS position_salary,
            p.education_req        AS position_education_req,
            p.experience_req       AS position_experience_req,
            p.description          AS position_description,
            p.listing_date         AS position_listing_date,
            p.location             AS position_location,
            p.location_type        AS position_location_type,
            c.company_id           AS legacy_company_id,
            c.name                 AS company_name
        FROM applied_jobs aj
        JOIN "position" p ON p.position_id = aj.position_id
        JOIN company    c ON c.company_id  = p.company_id
        ORDER BY aj.job_id
        """,
    ),
    ("job_activity", "SELECT * FROM job_activity ORDER BY activity_id"),
    ("interview", "SELECT * FROM interview ORDER BY interview_id"),
    ("follow_up", "SELECT * FROM follow_up ORDER BY followup_id"),
    # 1:1 with applied_jobs; v2 mapping likely folds outcome_state into job.stage
    # and outcome_notes into job.outcome_notes — decided in Phase 3.
    ("outcome", "SELECT * FROM outcome ORDER BY outcome_id"),
    ("documents", "SELECT * FROM documents ORDER BY doc_id"),
    # Optional tables — present only on databases that have run the sprint-3 additions.
    (
        "document_version",
        "SELECT * FROM document_version ORDER BY version_id",
    ),
    (
        "document_job_link",
        "SELECT * FROM document_job_link ORDER BY link_id",
    ),
    ("job_document", "SELECT * FROM job_document ORDER BY job_document_id"),
]

OPTIONAL_TABLES = {"document_version", "document_job_link", "job_document"}


def _table_exists(conn, table_name: str) -> bool:
    row = conn.execute(
        text(
            """
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = 'public' AND table_name = :t
            LIMIT 1
            """
        ),
        {"t": table_name},
    ).first()
    return row is not None


def _coerce(value: Any) -> Any:
    """Make any psycopg-returned value JSON-serializable."""
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        # Preserve precision as a string; the importer can cast back to Numeric.
        return str(value)
    if isinstance(value, (bytes, bytearray, memoryview)):
        return bytes(value).hex()
    return value


def main() -> int:
    os.makedirs(BACKUP_DIR, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    out_path = os.path.join(BACKUP_DIR, f"snapshot_{timestamp}.json")

    snapshot: dict[str, list[dict[str, Any]]] = {}
    counts: dict[str, int] = {}

    with engine.connect() as conn:
        for key, sql in EXTRACTIONS:
            primary_table = key
            # For the joined applied_jobs query the table to existence-check is applied_jobs.
            if not _table_exists(conn, primary_table):
                if key in OPTIONAL_TABLES:
                    print(f"  skip   {key:<22} (table not present)")
                    snapshot[key] = []
                    counts[key] = 0
                    continue
                print(
                    f"WARN   {key:<22} table not present in source DB — writing []",
                    file=sys.stderr,
                )
                snapshot[key] = []
                counts[key] = 0
                continue

            rows = conn.execute(text(sql)).mappings().all()
            serialized = [
                {col: _coerce(val) for col, val in row.items()} for row in rows
            ]
            snapshot[key] = serialized
            counts[key] = len(serialized)
            print(f"  ok     {key:<22} {len(serialized):>6} rows")

    snapshot["_meta"] = {
        "snapshot_taken_at": datetime.utcnow().isoformat() + "Z",
        "schema_version": "v1",
        "row_counts": counts,
    }

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, ensure_ascii=False, indent=2)

    print()
    print(f"Wrote {out_path}")
    print(f"Total rows: {sum(counts.values())}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
