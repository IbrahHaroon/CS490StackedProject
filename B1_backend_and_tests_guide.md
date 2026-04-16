# B1 — Backend Handler & Unit Test Guide

---

## Show the Backend Handler — jobs.py lines 257–291

Open `backend/routers/jobs.py` and scroll to line 257.
Point to each part and say this:

**Line 257** — `PUT /applications/{job_id}`
> "This is the single endpoint that handles every stage change."

**Lines 264–268** — 404 check
> "First it checks the job exists."

**Lines 269–272** — 403 check
> "Then it verifies the logged-in user owns this job — another user can't change your application."

**Lines 273–280** — stage validation
> "Then it validates the stage against our allowed pipeline stages — anything outside that list gets rejected with a 422."

**Line 282** — `create_job_activity`
> "If the stage is valid, it writes a record to job_activity — that's what powers the timeline."

**Lines 283–290** — `update_applied_job`
> "Then it updates the job status and timestamp together — both happen or neither happens."

---

## Show the Unit Tests — test_router_jobs.py

Open `backend/tests/test_router_jobs.py` and point to these one at a time:

**Happy path — line 251**
```python
test_valid_stage_change_returns_200
```
> "This confirms a valid stage change returns 200 and the status is updated."

**Timestamp — line 276**
```python
test_stage_change_updates_stage_changed_at
```
> "This confirms the timestamp changes every time — we don't just update the stage, we record when it happened."

**Negative path 1 — line 264**
```python
test_invalid_stage_returns_422
```
> "This is the negative path — sending a made-up stage like 'NotAStage' gets rejected with a 422. Without this check anyone could put garbage data in the pipeline."

**Negative path 2 — line 298**
```python
test_other_users_application_returns_403
```
> "This is the ownership check — if user B tries to change user A's job they get a 403. This protects data integrity across accounts."

---

## One Thing to Say That Ties It All Together

> "The PUT endpoint is the single source of truth for stage changes. It validates the stage, records the history, and updates the timestamp atomically. Our tests cover the success case, the timestamp propagation, invalid input, and unauthorized access — so all four failure modes are caught before they reach production."
