# B1 — Workflow and Data Integrity Evidence (2 Minutes)

---

## Step 1 — Live State Change (30 sec)

**In the browser:**
1. Log in as `usera@demo.com`
2. Open the **Google Software Engineer** job card
3. Change stage from `Interview` → `Offer`
4. Stay on this job — do not navigate away

**What you're proving:** Stage change works end-to-end from the UI

---

## Step 2 — Show Timestamp + Timeline Updated (30 sec)

**Still in browser:**
1. Show the `stage_changed_at` timestamp updated in the job overview
2. Click the **Activity Timeline** section on that job
3. Show the new `Offer` entry at the top with a timestamp

**What you're proving:** Every stage change is recorded with a timestamp — nothing is lost

---

## Step 3 — Show Dashboard Metrics Reflect It (20 sec)

**Navigate to dashboard:**
1. Show the stage count panel
2. Point out `Interview` count went down by 1, `Offer` went up by 1

**What you're proving:** Metrics are computed live from the database, not cached

---

## Step 4 — Show Backend Implementation (30 sec)

Open two files side by side in VS Code:

**File 1** — `backend/routers/jobs.py` (lines 114–146)
- PUT `/applications/{job_id}`
- Line 133: validates stage is in `PIPELINE_STAGES` — rejects bad input
- Line 139: calls `create_job_activity` — records the history
- Line 140: calls `update_applied_job` — updates status + timestamp
- Both happen in one request — atomic, no partial state

**File 2** — `backend/database/models/applied_jobs.py` (lines 190–230)
- `get_dashboard_metrics()`
- Counts are computed fresh from the DB every time — no stale data possible

---

## Step 5 — Show Unit Tests (30 sec)

Open `backend/tests/test_router_jobs.py` and point to these four tests:

| Test | What it covers |
|---|---|
| `test_valid_stage_change_returns_200` | Happy path — stage changes correctly |
| `test_stage_change_updates_stage_changed_at` | Timestamp propagates on every change |
| `test_invalid_stage_returns_422` | Negative path — bad stage is rejected |
| `test_other_users_application_returns_403` | Negative path — ownership enforced |

**Say:** *"We test both that valid transitions work and that invalid stages and unauthorized access are rejected — the negative paths protect the integrity of the pipeline."*

---

## One-Line Summary to Say Out Loud

> "When a stage changes, our PUT endpoint validates the stage, atomically updates the job status and timestamp, and writes an activity record — all in one transaction. Dashboard metrics read live from the database so they're always accurate. Our tests cover the happy path, invalid input, and unauthorized access."

---

## Pre-Demo Checklist

- [ ] Backend running locally
- [ ] Logged in as `usera@demo.com`
- [ ] VS Code open with `jobs.py` and `test_router_jobs.py` ready to tab to
- [ ] Google job is in `Interview` stage so you can change it live during the demo
