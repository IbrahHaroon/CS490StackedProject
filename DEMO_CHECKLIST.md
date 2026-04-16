# Sprint 2 Demo Checklist - CS 490 ATS Capstone

**Demo Day:** Tomorrow | **Total Time Slot:** 15 minutes (8 min product + 7 min technical Q&A)

---

## Pre-Demo Verification (Complete Before Demo Day)

### ✅ Environment & Deployment

- [ ] Backend running locally on `http://127.0.0.1:8000`
- [ ] Frontend running locally on `http://localhost:3000`
- [ ] Database (PostgreSQL) connected and accessible
- [ ] No console errors on startup
- [ ] All API endpoints responding (check with `/docs` or Postman)

### ✅ Seed Data (Required for Demo)

**Jobs Database:**
- [ ] At least 8 jobs seeded across multiple stages:
  - [ ] 2 jobs in "Applied" stage
  - [ ] 2 jobs in "Interview Scheduled" stage
  - [ ] 2 jobs in "Offer" stage
  - [ ] 2 jobs in "Rejected/Withdrawn" stage
- [ ] Jobs span multiple companies (at least 3 different)
- [ ] Jobs have varying titles and descriptions for search/filter demo

**User Profile:**
- [ ] Name and basic info filled
- [ ] Phone number and summary added
- [ ] At least 2 Experience entries with:
  - [ ] Title, company, dates, description
  - [ ] Action verbs and quantifiable achievements
- [ ] At least 2 Education entries with:
  - [ ] Degree, school, field of study, GPA
  - [ ] Start/end dates
- [ ] At least 2 Skills with clear names
- [ ] Career Preferences set (location type, salary range, etc.)

**AI-Generated Documents:**
- [ ] At least 2 AI resume drafts saved:
  - [ ] 1 from job context (job-specific)
  - [ ] 1 general/profile-based
- [ ] At least 2 AI cover letter drafts saved:
  - [ ] 1 from job context (job-specific)
  - [ ] 1 general resume
- [ ] Documents linked to their respective jobs
- [ ] At least 1 document with an "Improved" version (using AI rewrite)

**Activity/Timeline Data:**
- [ ] At least 2 jobs with interview events scheduled
- [ ] At least 2 jobs with follow-up reminders/notes
- [ ] At least 1 job with outcome recorded (Offer/Rejection/etc.)
- [ ] Timeline shows activity in chronological order

### ✅ Technical Evidence Ready

**Test Suite:**
- [ ] All unit tests pass: `pytest` runs without errors
- [ ] At least 1 workflow test (state transition)
- [ ] At least 1 profile completion test
- [ ] At least 1 negative/error path test
- [ ] CI pipeline shows passing checks

**Backend Implementation:**
- [ ] Stage transition logic accessible (show in `backend/routers/`)
- [ ] Profile completion service ready to reference
- [ ] AI document generation endpoints documented
- [ ] Test files visible: `test_sprint2_*.py`

### ✅ Credentials & URLs (Keep in text file during demo)

```
FRONTEND_URL: http://localhost:3000
BACKEND_API: http://127.0.0.1:8000
DOCS: http://127.0.0.1:8000/docs

Test User Credentials:
Email: [your_test_email@example.com]
Password: [your_test_password]
(Or use signup if needed)

Account Setup Status:
- Profile: COMPLETE
- Experience: 2+ entries
- Education: 2+ entries
- Skills: 2+ entries
- Documents: 3+ AI-generated
- Jobs in Dashboard: 8+
```

### ✅ Demo Run Sheet (1 Page - Print it!)

See `DEMO_RUN_SHEET.md` for click-by-click instructions.

---

## Phase A - Product Demo (8 minutes)

### A1: Dashboard Search/Filter/Sort (2 min)
- [ ] Load dashboard showing 8+ jobs
- [ ] Demonstrate search by job title
- [ ] Apply at least 1 filter (e.g., stage, company)
- [ ] Apply 1 sort (e.g., newest, deadline)
- [ ] Show stage badges on job cards (Applied, Interview, Offer, etc.)

### A2: Job Detail & Workflow (2 min)
- [ ] Click into a job card to show Job Detail view
- [ ] Show job overview data (title, company, location, salary)
- [ ] Update a job stage (e.g., Applied → Interview Scheduled)
- [ ] Verify stage change persists after save
- [ ] Show deadline, recruiter contact, notes fields

### A3: Interview/Activity/Timeline (2 min)
- [ ] Add a new interview event in Job Detail
- [ ] Add a follow-up reminder/note
- [ ] Show timeline updates in real-time
- [ ] Record or update outcome state (e.g., Offer Received)

### A4: Profile + AI Documents (2 min)
- [ ] Show completed Profile sections (Experience, Education, Skills)
- [ ] From Job Detail, trigger "Generate AI Resume" using job context
- [ ] Generate "AI Cover Letter" from same job
- [ ] Show "Improve" action on a saved document
- [ ] Verify generated document saves and links to job
- [ ] Show dashboard metrics reflecting the workflow

---

## Phase B - Technical Evidence & Q&A (7 minutes)

### B1: Workflow & Data Integrity (2 min) - READY TO SHOW
Live Demo Path:
```
1. Change job stage in Job Detail
2. Observe timestamp + activity update
3. Check dashboard metrics reflect new stage
4. Show backend code: backend/routers/jobs.py → stage_transition logic
5. Show unit test: backend/tests/test_sprint2_stage_transitions.py
```

### B2: CI & Testing Evidence (3 min) - READY TO SHOW
Have ready:
- [ ] CI pipeline screenshot or live output
- [ ] Dashboard workflow test output
- [ ] Profile completion test output
- [ ] Negative-path test (e.g., unauthorized, validation error)
- [ ] Brief explanation of why negative test matters

Run before demo:
```bash
cd backend
pytest -v --tb=short
```

### B3: Architecture Q&A (2 min)
Prepare brief answers for likely questions:
- [ ] How does Sprint 2 extend Sprint 1 without breaking old flows?
- [ ] Where is stage transition logic implemented?
- [ ] How does Job Detail coordinate multiple features (timeline, interview, AI docs)?
- [ ] How do profile entities feed into AI generation?
- [ ] What technical debt did Sprint 2 introduce?

---

## Demo Day Timeline

| Time | Event |
|------|-------|
| -5 min | Setup/transition & final checks |
| 0:00 - 8:00 | **PHASE A - Product Demo (8 min)** |
| 8:00 - 15:00 | **PHASE B - Technical Q&A (7 min)** |
| 15:00+ | Transition to next team |

**⚠️ STRICT ENFORCEMENT:** If you exceed 8 minutes in Phase A, remaining items score as "not demonstrated."

---

## Final Pre-Demo Checklist (Morning of Demo)

- [ ] Backend and frontend both running
- [ ] Can login with test account
- [ ] Dashboard loads with seed jobs
- [ ] Can navigate to job detail without errors
- [ ] Can generate AI documents (API key working)
- [ ] Can stage-transition a job
- [ ] Tests pass locally
- [ ] Run sheet printed and ready
- [ ] Credentials/URLs in notepad
- [ ] Presenter speaks clearly and keeps pace
- [ ] Backup presenter briefed on flow
- [ ] Screen resolution suitable for projection
- [ ] No notifications/popups during demo

---

✅ **READY FOR DEMO DAY!**
