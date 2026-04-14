# MJ Demo Script - Sprint 2

## Login Credentials
- User: `usera@demo.com` / `Demo1234!`
- Recruiter: `recruiter@demo.com` / `Demo1234!`

---

## PHASE A - Product Demo (Your Parts)

### A2: Job Detail - Deadline & Recruiter Notes (~1 min)

**What to say:**
> "I'll open a job card to show the deadline and recruiter contact notes fields I implemented."

**Steps:**
1. Click on a job card from the Dashboard
2. Expand the "Details" section
3. Click "Edit"
4. Enter deadline: `2026-05-15`
5. Enter recruiter notes: `Called Mike Chen (m.chen@meta.com) on 4/12. He's the hiring manager for the frontend team. Prefers candidates with React experience.`
6. Click "Save"
7. Collapse and re-expand Details to show it persisted

**What to say after:**
> "The deadline and recruiter notes are saved per job application and persist across page reloads."

---

### A3: Follow-Up / Reminder Tracking (~1.5 min)

**What to say:**
> "Now I'll show the follow-up and reminder tracking feature tied to this job."

**Steps:**
1. Still in the same job detail, scroll to the "Follow-Ups" section
2. Expand it
3. Click "+ Add Follow-Up"
4. Enter: `Send thank-you email to recruiter after phone screen` with due date `2026-04-18`
5. Click Save
6. Add another: `Prepare system design notes for onsite interview` with due date `2026-04-25`
7. Click Save
8. Check the checkbox on the first follow-up to mark it complete (shows strikethrough)
9. Delete the second follow-up with the X button

**What to say after:**
> "Follow-ups are linked to individual jobs. Users can create, complete, and delete them. Each one has an optional due date."

---

### A4: Experience Section in Profile (~1.5 min)

**What to say:**
> "Now I'll show the Experience CRUD section I built in the Profile page."

**Steps:**
1. Navigate to Profile page
2. Scroll to Experience section
3. Click "+ Add"
4. Fill in:
   - Company: `Amazon Web Services`
   - Job Title: `Software Engineering Intern`
   - Start Date: `2025-06-01`
   - End Date: `2025-08-15`
   - Description: `Built internal monitoring dashboard using React and Python. Reduced alert response time by 30%.`
5. Click Save - show "Saved!" message
6. Click "+ Add" again:
   - Company: `NJIT Computer Science Department`
   - Job Title: `Undergraduate Teaching Assistant`
   - Start Date: `2025-09-01`
   - End Date: (leave blank for current role)
   - Description: `Lead weekly lab sessions for CS 280 Data Structures. Grade assignments for 40+ students.`
7. Click Save
8. Use the arrow buttons to reorder entry 2 above entry 1
9. Click Edit on one entry, change the description, save
10. Delete one entry to show delete works

**What to say after:**
> "Each profile section saves independently with validation feedback. Experience entries support add, edit, delete, and reorder."

---

## PHASE B - Technical Evidence (Your Parts)

### B1: Workflow & Data Integrity (~1 min)

**What to say:**
> "I'll show how follow-up data flows from frontend to database."

**Files to show:**

1. **Router** - `backend/routers/follow_ups.py`
   - Show the POST endpoint (line 20-46): creates follow-up, validates job ownership via JWT
   - Show the PUT endpoint (line 68-93): updates completion status

2. **Model** - `backend/database/models/applied_jobs.py`
   - Show line 75-77: cascade delete on follow_ups relationship
   - Say: "When a job is deleted, all its follow-ups are automatically cleaned up"

3. **Model** - `backend/database/models/follow_up.py`
   - Show the FollowUp class (line 15-29): linked to jobs via foreign key
   - Show create_follow_up function (line 37-55): persists to database

---

### B2: Unit Tests (~1.5 min)

**What to say:**
> "I'll show the unit tests covering my features."

**Files to show:**

1. **`backend/tests/test_follow_up.py`** (14 tests)
   - Show a happy-path test: `test_create_sets_description` 
   - Show a negative test: `test_create_invalid_job_id_raises` or `test_delete_missing_id_returns_false`
   - Say: "This negative test verifies that creating a follow-up for a nonexistent job raises an error, protecting against orphaned data."

2. **`backend/tests/test_experience.py`** (15 tests)
   - Show: `test_update_sort_order` - proves reordering persists
   - Show: `test_delete_missing_id_returns_false` - negative path

3. **`backend/tests/test_applied_jobs.py`**
   - Show: `test_update_job_sets_deadline` (line 222-226)
   - Show: `test_update_job_sets_recruiter_notes` (line 228-233)

**Run tests live (optional but impressive):**
```bash
cd backend
source venv/bin/activate
python -m pytest tests/test_follow_up.py tests/test_experience.py -v
```

---

### B3: Architecture Q&A Prep

**If asked "How does Job Detail coordinate timeline, interview, and document actions?"**
> "Each feature is a separate section in the Applications page. They share the job_id but save independently through their own API endpoints. Follow-ups hit /jobs/{job_id}/followups, deadline and recruiter notes go through PUT /jobs/applications/{job_id}."

**If asked "How does Sprint 2 extend Sprint 1 without breaking prior flows?"**
> "We added new nullable columns like deadline and recruiter_notes to the existing applied_jobs table, so all Sprint 1 data still works. New features like follow-ups are separate tables with foreign keys. Nothing existing was changed, only extended."

**If asked "What technical debt did Sprint 2 introduce?"**
> "The Supabase connection pooling could use better configuration for production. Also, the follow-up feature doesn't have reminder notifications yet - it tracks tasks but doesn't alert users when they're due. That would be a Sprint 3 improvement."

---

## Pre-Demo Checklist
- [ ] Backend running (`uvicorn index:app --reload`)
- [ ] Frontend running (`npm run dev`)
- [ ] Logged in as `usera@demo.com`
- [ ] Seed data loaded (8+ jobs visible on dashboard)
- [ ] At least 2 experience entries in profile
- [ ] Terminal ready to run tests
- [ ] This script open on a second screen or printed
