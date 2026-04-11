# Session Notes — Sprint 2 Implementation
Date: 2026-04-10

---

## Overview
This session completed all 4 assigned Sprint 2 tasks, fixed CI failures, resolved schema drift,
and set up a clean git commit strategy to avoid conflicts with classmates.

---

## Task 1 — Job Deadline & Recruiter/Contact Notes
**File:** `frontend/src/pages/Applications.jsx`

### What we did
- Added a collapsible "Details" section to each application card
- Fields: deadline (date input) and recruiter notes (textarea)
- View mode shows current values, edit mode allows inline editing
- Save button calls `PUT /jobs/applications/{job_id}` to persist changes

### Why
The backend already had `deadline` and `recruiter_notes` columns on `applied_jobs`
but the frontend had no way to view or edit them. Users needed to track application
deadlines and notes from recruiters.

---

## Task 2 — Follow-Up & Reminder Tracking
**Files:** `frontend/src/pages/Applications.jsx`, `backend/routers/follow_ups.py`

### What we did
- Added a collapsible "Follow-Ups" section to each application card
- Users can create follow-up tasks with a description and optional due date
- Checkbox to toggle completed/incomplete (strikethrough when done)
- Delete button to remove follow-ups
- Lazy loads — only fetches from API when the section is first opened
- Registered `follow_ups.py` router in `backend/index.py`

### Why
Users needed a way to track action items tied to a specific job application
(e.g. "Send thank-you email", "Follow up if no response"). The backend model
and router already existed but were not wired into the frontend or index.py.

---

## Task 3 — Experience Section CRUD
**File:** `frontend/src/pages/Profile.jsx`

### What we did
- Added Experience section card to Profile page
- Add, Edit, Delete entries via EditModal
- Reorder entries with ↑/↓ buttons (swaps sort_order, PUTs both to backend)
- Fields: Company, Job Title, Start Date, End Date (blank = current), Description
- "Saved!" status message appears and auto-clears after 3 seconds

### Why
S2-016 required users to manage their employment history on their profile.
The `experience.py` router was already committed in Sprint 2 with full CRUD.
This task wired up the frontend to those existing endpoints.

---

## Task 4 — Section-Level Save/Validation UX for Profile
**Files:** `frontend/src/pages/Profile.jsx`, `frontend/src/components/EditModal.jsx`

### What we did
- Each profile section (Experience, Education, Skills, Career Prefs) saves independently
- Validation shows inline error messages for required fields before making API call
- `EditModal` extracted into its own reusable component (`frontend/src/components/EditModal.jsx`)
  so both Profile.jsx and Settings.jsx can use it without duplicating code
- Added `safe()` fetch wrapper so one failed fetch doesn't crash the whole page
- Added `userId` guard at top of `saveProfile` to prevent 422 errors on POST
- Normalized `err.detail` to always be a string (Pydantic returns arrays on 422)

### Why
Previously, saving profile info with an empty Date of Birth caused a 422 from
the backend. The array error detail caused React to crash with a blank screen.
Sections also had no visual feedback when saving succeeded or failed.

---

## Bug Fixes

### Dashboard stuck on "Loading..."
**File:** `frontend/src/pages/Dashboard.jsx`

**Problem:** The `fetchAll` function had no try/catch. If any fetch threw an
error, `setLoading(false)` never ran and the page stayed blank forever.

**Fix:** Wrapped the entire fetch block in try/catch/finally so `setLoading(false)`
always runs regardless of errors.

### Dashboard crash on null document_location
**File:** `frontend/src/pages/Dashboard.jsx`

**Problem:** `doc.document_location.split("/").pop()` crashed when
`document_location` was null (cover letter drafts don't have a file path).

**Fix:** Added null check:
```js
doc.document_location ? doc.document_location.split("/").pop() : "Unnamed document"
```

---

## Recruiter Auth Separation
**Files:** Multiple backend + frontend files

### What we did
- Separated recruiter accounts from user accounts completely
- Recruiter table now has its own `email` field (removed `user_id` FK)
- Added `recruiter_credentials` table (mirrors `credentials` for users)
- Added `recruiter_password_reset_token` table
- JWT tokens now carry `account_type: "user"` or `"recruiter"` field
- `get_current_user` rejects recruiter tokens (and vice versa)
- Added 4 new auth endpoints: `POST /auth/recruiter/register`,
  `POST /auth/recruiter/login`, `GET /auth/recruiter/me`,
  `POST /auth/recruiter/logout`
- Added "I am a recruiter" checkbox on SignIn page
- Navbar shows "Add Posting" only when `isRecruiter === true` in localStorage
- ProtectedRoute now validates token via `/auth/me` API call and auto-clears
  stale tokens

### Why
Previously recruiters shared auth with candidates via a `user_id` FK. This meant
a recruiter token could access candidate endpoints and vice versa. The separation
ensures token isolation — a recruiter can't access profile/applications pages
and a candidate can't access recruiter endpoints.

---

## Schema Changes
**File:** `backend/scripts/schema.sql`

### What we changed
- Added `recruiter_credentials` table
- Added `recruiter_password_reset_token` table
- Removed `user_id` FK from `recruiter` table, added `email` column
- Added `location_type VARCHAR(20)` and `location VARCHAR(255)` to `position` table
  (these existed in the ORM model but were missing from the schema — caused 500 errors)
- Made `document_location` nullable on `documents` table
  (cover letter drafts have no file path, only text content)

### Why
The ORM models and the actual database schema had drifted apart. Columns that
existed in SQLAlchemy models were missing from the SQL schema, causing 500 errors
when those columns were queried.

---

## Seed Data Fix
**File:** `backend/scripts/seed.sql`

### What we changed
- Added recruiter seed row using new `email` field (removed `user_id`)
- Added `recruiter_credentials` seed row
- Fixed bcrypt hash for all accounts — old hash `$2b$12$mupvTK...` did not
  match "Demo1234!" causing all logins to fail
- Correct hash: `$2b$12$EY2gk/D84cdS16h89DIILucUTdjf.FGvnPTdm2dxQrvVJ0XdrZnxq`

### Why
The seed file had a wrong bcrypt hash that caused every demo account login to
return 401. Verified the correct hash by running bcrypt.checkpw() directly.

---

## CI Fixes

### Ruff formatting failure
**File:** `backend/routers/auth.py`

**Fix:** Ran `ruff format backend/routers/auth.py`

### Prettier formatting failures
**Files:** `EditModal.jsx`, `ProtectedRoute.jsx`, `Applications.jsx`,
`Profile.jsx`, `SignIn.jsx`

**Fix:** Ran `npx prettier --write` on all 5 files

### Backend test import error
**File:** `backend/tests/test_recruiter.py`

**Problem:** Test imported `get_recruiter_by_user_id` which no longer exists
after the recruiter model rewrite.

**Fix:** Rewrote test file to use `get_recruiter_by_email` and updated all
`create_recruiter` calls to use `email` instead of `user_id`.

### Backend router test failures
**File:** `backend/tests/test_router_recruiter.py`

**Problem:** All tests used old flow (`POST /recruiter/` with `user_id`) which
no longer exists. Tests were getting 404 on every call.

**Fix:** Rewrote `_create_recruiter_with_auth` helper to use
`POST /auth/recruiter/register` + `POST /auth/recruiter/login`. Updated all
test classes to use recruiter tokens instead of user tokens.

---

## Git Strategy
**Branch:** `feature/sprint2-tasks`

### What files were committed (yours only)
- All backend auth/recruiter separation files
- `follow_ups.py` router
- `schema.sql`, `seed.sql`
- All frontend files (Profile, Applications, Dashboard, Navbar, SignIn,
  ProtectedRoute, EditModal)
- `index.py` (with only `follow_ups` added — `skills` and `career_preferences`
  intentionally excluded)

### What was left out (classmates own these)
- `backend/routers/education.py`
- `backend/routers/skills.py`
- `backend/routers/career_preferences.py`

### Why
Committing classmates' router files would either overwrite their work or cause
merge conflicts when they push. `index.py` was edited to only register
`follow_ups` so the backend starts cleanly without their routers present.

---

## Pending (waiting on classmates)
- `backend/routers/skills.py` — needed for Skills section in Profile to save
- `backend/routers/education.py` — needed for Education section in Profile to save
- `backend/routers/career_preferences.py` — needed for Career Prefs to save

Once classmates push their routers, pull their changes and verify all three
sections work end to end on the Profile page before demo.
