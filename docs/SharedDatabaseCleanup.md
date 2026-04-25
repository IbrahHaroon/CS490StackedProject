# Shared-Database Cleanup Guide (Windows teammate edition)

We share one Supabase project across the team. When a teammate runs **stale
code** (a branch that still has v1 models like `applied_jobs.py`,
`recruiter.py`, `company.py`, `position.py`, `documents.py`), their backend
calls SQLAlchemy's `Base.metadata.create_all()` at startup and **re-creates
the legacy tables** in the shared Supabase. You drop them, they come back the
next time that teammate restarts. This document is the cure.

> **TL;DR**
> 1. The teammate runs the **Local Cleanup** steps below in Windows PowerShell.
> 2. You run the **DB Cleanup** SQL block in Supabase.
> 3. Optionally add the **Defensive Backend Assertion** so you find out
>    immediately the next time someone slips.

---

## Local Cleanup — for the Windows teammate to run

Send this entire section to the affected teammate. All commands are for
**Windows PowerShell** (right-click Start → "Windows PowerShell" or "Terminal").
Total time ~5 minutes.

> If you are using Git Bash or WSL instead of PowerShell, scroll to the
> Bash variant at the bottom of each step.

### Step 1 — Save uncommitted work

```powershell
cd C:\path\to\CS490StackedProject
git status
```

If anything shows up as modified, either commit it
(`git add . ; git commit -m "WIP"`) or stash it (`git stash`). Do not skip
this — the next step refuses to proceed if you have uncommitted changes.

### Step 2 — Pull the latest code

If your branch is `main`:

```powershell
git checkout main
git pull origin main
```

If you are on your own feature branch, rebase it onto the latest main:

```powershell
git fetch origin
git rebase origin/main
```

If the rebase has conflicts you cannot resolve, merge instead:

```powershell
git merge origin/main
```

### Step 3 — Verify the legacy model files are gone

```powershell
$legacy = @(
  'backend\database\models\applied_jobs.py',
  'backend\database\models\recruiter.py',
  'backend\database\models\company.py',
  'backend\database\models\position.py',
  'backend\database\models\documents.py'
)
foreach ($f in $legacy) {
  if (Test-Path $f) { Write-Host "BAD - still there: $f" -Foreground Red }
  else              { Write-Host "OK   - gone:        $f" -Foreground Green }
}
```

All five lines should print `OK - gone`. If any print `BAD`, the rebase did
not fully apply — try the rebase again or ask for help.

### Step 4 — Clear cached Python bytecode

This is the silent killer. Even after deleting source files, Python may still
load them from `__pycache__`:

```powershell
Get-ChildItem -Path backend -Recurse -Force -Directory -Filter __pycache__ |
  Remove-Item -Recurse -Force
Get-ChildItem -Path backend -Recurse -Force -Filter *.pyc |
  Remove-Item -Force
```

### Step 5 — Reinstall dependencies (in case `requirements.txt` changed)

```powershell
backend\venv\Scripts\pip.exe install -r backend\requirements.txt
```

> If your venv is named or located differently, adjust the path. The Windows
> venv puts executables in `Scripts\`, not `bin\` like macOS/Linux.

### Step 6 — Restart the backend

Stop any old uvicorn worker first, then start fresh:

```powershell
# Stop any python.exe running our app
Get-Process python -ErrorAction SilentlyContinue |
  Where-Object { $_.Path -like "*\backend\venv\*" } |
  Stop-Process -Force

# Start fresh
backend\venv\Scripts\python.exe backend\index.py
```

You should see `INFO: Uvicorn running on http://127.0.0.1:8000`. If it errors
with `ImportError: cannot import name 'AppliedJobs'` (or any other legacy
class), something old is still cached — re-run Step 4 and try again.

### Step 7 — Smoke-test you are on v2

In a **new** PowerShell window (so the backend keeps running):

```powershell
$paths = (Invoke-RestMethod http://127.0.0.1:8000/openapi.json).paths.PSObject.Properties.Name
$paths | Where-Object { $_ -like '/jobs*' } | Sort-Object | Select-Object -First 20
```

You should see v2 paths like `/jobs/{job_id}` and `/jobs/{job_id}/activity`.
You should NOT see legacy paths like `/jobs/positions/` or
`/jobs/applications/{job_id}`.

### Done

Your local backend is now on v2. Restart it whenever you switch branches and
re-run Step 4 if you ever check out an old branch and switch back.

---

## Bash / Git Bash / WSL alternative

If you are using Git Bash or WSL instead of PowerShell, the macOS/Linux
commands work as-is. Replace each block above with these:

```bash
# Step 3 — verify legacy gone
for f in applied_jobs.py recruiter.py company.py position.py documents.py; do
  test -f "backend/database/models/$f" \
    && echo "BAD - $f still there" \
    || echo "OK  - $f gone"
done

# Step 4 — clear bytecode
find backend -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null
find backend -name '*.pyc' -delete

# Step 5 — reinstall deps (note: even on Windows Git Bash, the venv folder is Scripts, not bin)
backend/venv/Scripts/pip install -r backend/requirements.txt

# Step 6 — restart
taskkill //F //IM python.exe 2>/dev/null || true   # in Git Bash on Windows
backend/venv/Scripts/python backend/index.py

# Step 7 — smoke test
curl -s http://127.0.0.1:8000/openapi.json | python -c "import sys,json; print('\n'.join(sorted(p for p in json.load(sys.stdin)['paths'] if p.startswith('/jobs'))))"
```

---

## DB Cleanup — for whoever owns the shared Supabase

After every teammate finishes the Local Cleanup steps, drop the resurrected
legacy tables in one transaction. Run this in **Supabase Dashboard → SQL
Editor**:

```sql
BEGIN;
DROP TABLE IF EXISTS recruiter_credentials, recruiter, outcome,
                     job_document, documents, applied_jobs,
                     "position", company, address, skills CASCADE;
COMMIT;
```

Verify the result in **Table Editor** — you should see exactly 17 v2 tables:

```
career_preferences
credentials
document
document_tag
document_version
education
experience
follow_up
interview
job
job_activity
job_document_link
password_reset_token
profile
skill
token_blacklist
user
```

If any of these come back later, repeat the Local Cleanup with whichever
teammate is restarting their stale backend.

---

## Defensive Backend Assertion (optional but recommended)

Add this to `backend/index.py`'s `lifespan` so the backend refuses to start if
any legacy table is present in the shared DB. The next time someone slips,
your app fails loudly instead of silently fragmenting your data:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    from sqlalchemy import inspect
    from database.database import engine

    forbidden = {
        "recruiter", "recruiter_credentials", "applied_jobs",
        "company", "position", "outcome",
        "documents", "job_document", "address", "skills",
    }
    found = forbidden & set(inspect(engine).get_table_names())
    if found:
        raise RuntimeError(
            f"Legacy tables present in shared DB: {sorted(found)}. "
            "Someone is running stale code — run the DROP block in Supabase, "
            "then have whoever's running their backend redo the cleanup steps "
            "in docs/SharedDatabaseCleanup.md."
        )
    yield
```

The check costs one round-trip at startup (~50ms). Tradeoff: if a teammate
*needs* to test against legacy tables for some reason, this will block their
backend too.

---

## Appendix — Why this happens

SQLAlchemy keeps every model registered with `Base.metadata`. When any backend
calls `Base.metadata.create_all(engine)` (or runs a script that does, like
some `seed.py` variants on old branches), Postgres receives a `CREATE TABLE
IF NOT EXISTS` for every model in scope.

- Tables that already exist (your v2 tables): untouched.
- Tables that are missing (the legacy ones, because we dropped them):
  **created**.

The result is a partial schema corruption — your v2 tables are intact, but
v1-era tables get re-added empty. The teammate sees them through their old
UI and may add data; you do not see that data through the v2 UI. Eventually
the data fragments across two parallel schemas.

The Local Cleanup steps stop the teammate's backend from registering those
v1 models in the first place. The DB Cleanup wipes the empty corruption.
The Defensive Assertion makes future occurrences loud.

---

## Appendix — If you want a permanent prevention layer

The cleanup steps above rely on every teammate keeping their checkout up to
date. If you want a bulletproof fix that works regardless of what anyone runs
locally, revoke `CREATE TABLE` permission on the role used by the runtime:

```sql
-- Run in Supabase SQL Editor (which uses supabase_admin and is unaffected)
REVOKE CREATE ON SCHEMA public FROM postgres, anon, authenticated, public;
```

After this, no backend can create tables — it will get
`permission denied for schema public`. Schema migrations can still be run
from the Supabase SQL Editor (which uses a different role).

If a teammate genuinely needs DDL for a legitimate purpose, they should run
their migration in the SQL Editor, not from a Python script.
