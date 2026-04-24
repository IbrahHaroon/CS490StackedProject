# Database Migrations & Rollback Runbook

This document is the operational playbook for changing the production
Supabase database. It covers **how to write a migration**, **how to apply it
safely**, and **how to roll back** when something goes wrong.

> **Audience:** anyone touching the schema. Read it once before your first
> migration; refer back to the rollback section *before* you click Run.

---

## TL;DR — the safe migration loop

```
1. Write a numbered migration SQL file in backend/scripts/
2. Take a backup    →  ./backend/scripts/backup_db.sh
3. Apply it          →  paste into Supabase SQL Editor
4. Smoke-test the affected feature in the app
5. Update backend/scripts/schema_v2.sql to reflect the new state
6. Commit the migration file + the schema_v2.sql diff together
```

If step 4 fails, jump to **[Rollback](#rollback)** and restore the backup.

---

## What lives where

| Path | Purpose |
|---|---|
| `backend/scripts/schema_v2.sql` | The **canonical** current schema. Treat it like a snapshot — never run it against a populated DB; use it for fresh installs and as the source of truth for "what the schema should look like right now." |
| `backend/scripts/migrate_*.sql` | Individual, numbered migration steps. Apply in filename order. |
| `backend/scripts/backup_db.sh` | Plain-SQL `pg_dump` of the live DB to `backend/backups/backup_<timestamp>.sql`. |
| `backend/scripts/snapshot_to_json.py` | JSON snapshot of all tables (used during the v2 cutover; useful for cross-environment moves). |
| `backend/scripts/import_from_snapshot.py` | Re-populates an empty v2 schema from a JSON snapshot. Use for full DR; not for partial rollback. |
| `backend/backups/` | Local backup destination. **Gitignored** — never commit backups (they contain real user data). |

---

## Writing a migration

### 1. Naming convention

```
backend/scripts/migrate_<NNN>_<short_description>.sql
```

- `<NNN>` is the next 3-digit sequence number (`001`, `002`, …) so files
  sort and apply in order.
- `<short_description>` is snake_case and describes intent: `add_job_priority`,
  `rename_documents_to_document`, `drop_unused_position_table`.

Example: `migrate_002_add_document_title.sql`.

> The repo has one example: [`migrate_add_document_title.sql`](../backend/scripts/migrate_add_document_title.sql).
> New files should adopt the numbered prefix going forward.

### 2. File template

Every migration file must contain four sections, in order:

```sql
-- =============================================================================
-- MIGRATION 002: Add priority column to job
--
-- Purpose:   Allow users to rank jobs by priority (Low/Med/High).
-- Touches:   job (1 column added)
-- Reversible: yes — see ROLLBACK block below.
--
-- HOW TO RUN (Supabase):
--   1. Take a backup: ./backend/scripts/backup_db.sh
--   2. Supabase → SQL Editor → paste THIS WHOLE FILE → Run
--   3. Smoke-test: open Applications, set a job's priority, refresh
-- =============================================================================

BEGIN;

ALTER TABLE job
    ADD COLUMN IF NOT EXISTS priority VARCHAR(20);

COMMIT;

-- =============================================================================
-- ROLLBACK (paste into SQL Editor and Run if the migration above caused harm):
-- =============================================================================
-- BEGIN;
-- ALTER TABLE job DROP COLUMN IF EXISTS priority;
-- COMMIT;
```

Key rules:

- **Wrap the live migration in `BEGIN; ... COMMIT;`** so a partial failure
  doesn't leave the schema half-mutated.
- **Use `IF NOT EXISTS` / `IF EXISTS`** wherever possible. Migrations should
  be safe to re-run.
- **Always include a commented-out `ROLLBACK` block** — even when "obvious."
  The future-you racing to undo a bad migration at midnight will thank you.
- **Don't rely on application code** for data backfills. If you need to
  populate a new column for existing rows, do it in SQL inside the same
  transaction.

### 3. Special cases

| If you're… | Do this |
|---|---|
| **Adding a NOT NULL column to an existing table** | Two steps: (1) add the column nullable + backfill in one migration, (2) add the `NOT NULL` constraint in a second migration. Easier rollback, no surprise failure on populated tables. |
| **Renaming a column** | Don't. Add the new column, copy data, ship the app reading both, then drop the old column in a later migration. (Atomic renames break any deployed code that still references the old name.) |
| **Dropping a table or column** | Use a two-week soak: ship the app code that no longer reads/writes it, wait, then drop. Preserve a backup *before* the drop. |
| **Adding an index** | Use `CREATE INDEX CONCURRENTLY` (cannot run inside a transaction — drop the `BEGIN;`/`COMMIT;` for that file). Otherwise you'll lock writes for the whole table. |
| **Restructuring data across many tables** | Don't do it as an inline migration. Take a JSON snapshot via `snapshot_to_json.py`, drop+recreate via `schema_v2.sql`, re-import via `import_from_snapshot.py`. That's the v2-cutover playbook from earlier this sprint. |

---

## Applying a migration

### Pre-flight checklist

- [ ] You're applying to the **right Supabase project** (`lddzvjoiprnvbhfrbztu`
      for prod). Double-check the URL bar in the Supabase dashboard.
- [ ] You took a backup *immediately before* the migration:
      ```bash
      ./backend/scripts/backup_db.sh
      ```
      You should see a new file in `backend/backups/backup_<timestamp>.sql`.
- [ ] You've reviewed the migration file end-to-end. The `ROLLBACK` block
      compiles in your head (mentally trace each statement).
- [ ] The branch that needs this migration is **not yet merged to main**
      *or* you have a deploy plan that includes both the SQL and the code.

### Run it

1. Go to **Supabase → your project → SQL Editor → New query**.
2. Paste the **entire contents** of `backend/scripts/migrate_NNN_*.sql` —
   header comments and all (so the next person reviewing query history sees
   the rationale).
3. Click **Run**. The transaction either commits fully or rolls back fully.
4. Confirm Supabase shows `Success. No rows returned` (for DDL) or the
   expected row count.

> **Why Supabase SQL Editor and not the CLI?** The Supabase SQL Editor runs
> as `supabase_admin`, which bypasses the `REVOKE CREATE` lockdown applied
> to `postgres`/`service_role`/`anon`/`authenticated`/`public` (see
> [`SharedDatabaseCleanup.md`](SharedDatabaseCleanup.md)). DDL from any other
> connection will silently fail or get rejected.

### Post-migration

- [ ] **Smoke-test** the affected feature end-to-end in the app
      (`cd backend && venv/bin/python index.py` + `cd frontend && npm run dev`).
- [ ] **Update `backend/scripts/schema_v2.sql`** to reflect the new state
      (so a fresh `psql -f schema_v2.sql` on a blank DB produces the
      post-migration schema).
- [ ] **Commit both files together**:
      ```bash
      git add backend/scripts/migrate_NNN_*.sql backend/scripts/schema_v2.sql
      git commit -m "db: <what the migration does>"
      ```
- [ ] **Tell the team** in the group chat: "Applied migration NNN to prod;
      pull main and restart your backend."

---

## Rollback

There are three rollback paths. Pick based on **how bad** the breakage is and
**how much data was written** since the migration ran.

### Path A — Reverse migration (preferred when possible)

Use when: the migration's effect is contained (one column added, one index
created, etc.) and **no application data has been written using the new
shape yet**.

1. Open the same migration file.
2. Copy the commented-out `ROLLBACK` block.
3. Supabase → SQL Editor → uncomment → paste → Run.
4. Update `schema_v2.sql` to reflect the rollback.
5. `git revert` the application code that depended on the migration.

This is fast (seconds) and surgical. Always try it first.

### Path B — Restore from the pre-migration backup

Use when: Path A isn't feasible (migration restructured data, dropped a
column you can't reconstruct, etc.) **and** you took a backup right before
the migration **and** you can tolerate losing any writes that happened since.

> **Warning:** restoring a backup discards every write that occurred after
> the backup was taken. For a single-user app this is usually a few minutes
> of demo data; for a busier app it could be a problem. Quantify what you'd
> lose before you press the button.

```bash
# 1. Take a "before-restore" backup so you can compare/recover later
./backend/scripts/backup_db.sh

# 2. Wipe the schema (in Supabase SQL Editor — uses supabase_admin)
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;
GRANT USAGE ON SCHEMA public TO postgres, anon, authenticated, service_role;
GRANT ALL ON SCHEMA public TO supabase_admin;

# 3. Restore the pre-migration dump (run from your laptop, not Supabase)
PGPASSWORD=<from .env> psql "<DATABASE_URL>" \
    -f backend/backups/backup_<pre_migration_timestamp>.sql

# 4. Re-apply the REVOKE lockdown (see SharedDatabaseCleanup.md)
```

After step 3, the DB is back to the pre-migration state. Re-deploy whichever
application code matches that schema (usually the previous git commit).

### Path C — Full rebuild from JSON snapshot

Use when: the SQL backup is also corrupted or the schema needs a structural
reset. This is the v2-cutover playbook.

```bash
# 1. Drop and recreate the schema (Supabase SQL Editor)
DROP SCHEMA public CASCADE; CREATE SCHEMA public;
GRANT USAGE ON SCHEMA public TO postgres, anon, authenticated, service_role;
GRANT ALL ON SCHEMA public TO supabase_admin;

# 2. Apply the canonical schema (Supabase SQL Editor)
# Paste the contents of backend/scripts/schema_v2.sql

# 3. Re-import data from the latest JSON snapshot
backend/venv/bin/python backend/scripts/import_from_snapshot.py

# 4. Re-apply REVOKE lockdown (see SharedDatabaseCleanup.md)
```

Path C is a last resort — it requires having a recent JSON snapshot
(`snapshot_to_json.py`) and is the most operationally involved. Reserve it
for true disasters.

---

## Backups

### When to take one (manually)

- **Always** before applying any migration.
- Before any destructive cleanup operation (truncating, dropping, mass
  updates).
- Before handing the database to someone else for the first time.

### How

```bash
./backend/scripts/backup_db.sh
# → backend/backups/backup_<UTC-timestamp>.sql
```

The script reads `DATABASE_URL` from `backend/.env`, masks the password in
its log output, and uses the highest-version `pg_dump` available on the
system (Postgres requires the dump client to be ≥ the server's major
version — Supabase is currently Postgres 17).

### Where they live

- Local: `backend/backups/` (gitignored).
- Off-machine: nowhere automated yet. **Action item** — see "Future
  improvements" below.

### Retention

Keep the last 5–10 backups locally. Older than that, delete to save disk —
a few weeks of single-user data is small (tens of MB), but the directory
will grow indefinitely if you don't prune.

---

## Future improvements (not blocking S3 acceptance)

These are good-to-have, not required by the story:

1. **Automated nightly backup via GitHub Actions.** A workflow that runs
   `backup_db.sh` daily and uploads the result as a workflow artifact (free,
   90-day retention). Insulates against laptop failure.
2. **Adopt Alembic** if migrations become frequent. The numbered-SQL system
   above is fine for this scale (single-user app, ~12 tables, < 1 migration
   per sprint). Alembic adds value once you're rolling 5+ migrations a sprint
   or coordinating across multiple developers.
3. **Per-PR schema diff bot.** A CI check that runs `pg_dump --schema-only`
   against `schema_v2.sql` and fails if the live schema and the canonical
   file diverge.

---

## Cross-references

- [`SharedDatabaseCleanup.md`](SharedDatabaseCleanup.md) — what to do when a
  teammate's stale code recreates legacy tables. Includes the REVOKE block
  you'll need after any full restore.
- [`DatabaseOverview.md`](DatabaseOverview.md) — the schema itself
  (table relationships, FK constraints, why each table exists).
- [`backend/scripts/schema_v2.sql`](../backend/scripts/schema_v2.sql) — the
  canonical schema source of truth.
