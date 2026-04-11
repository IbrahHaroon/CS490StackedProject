# Sprint 2 Updates — S2-007, S2-012, S2-016, S2-020

This document explains every change made during this sprint, what each piece does, and why it was built the way it was.

---

## Overview of What Was Built

| Story | Title | Area |
|-------|-------|------|
| S2-007 | Job Deadline & Recruiter Notes | Applications page |
| S2-012 | Follow-Up & Reminder Tracking | Applications page |
| S2-016 | Experience Section CRUD | Profile page |
| S2-020 | Section-Level Save/Validation UX for Profile | Profile page |

---

## Backend Changes

### S2-007 — Fix in `backend/routers/jobs.py`

**What was wrong:** The `PUT /jobs/applications/{job_id}` endpoint accepts a `deadline` (date) and `recruiter_notes` (text) in the request body, and both fields exist in the database. But the code that calls the database function was never forwarding those two values — they were being received and silently dropped.

**What was fixed:** Two arguments were added to the internal function call:

```python
updated = update_applied_job(
    session,
    job_id,
    application_status=body.application_status,
    years_of_experience=body.years_of_experience,
    deadline=body.deadline,           # added
    recruiter_notes=body.recruiter_notes,  # added
)
```

Now when a user saves a deadline or notes from the UI, they actually persist to the database.

---

### S2-012 — New file `backend/routers/follow_ups.py`

**What was missing:** The database model for follow-ups (`FollowUp`) and all its CRUD functions were already written, and the Pydantic schemas existed too. But there was no router file — meaning no API endpoints were exposed.

**What was created:** A new router file with four endpoints:

| Endpoint | What it does |
|----------|-------------|
| `POST /jobs/{job_id}/followups` | Creates a new follow-up tied to a specific job |
| `GET /jobs/{job_id}/followups` | Returns all follow-ups for a job |
| `PUT /followups/{followup_id}` | Updates description, due date, or completed status |
| `DELETE /followups/{followup_id}` | Removes a follow-up |

Each endpoint checks that the requesting user actually owns the job before allowing the action (ownership check via `job.user_id == current_user.user_id`). This pattern was copied directly from the interviews router.

---

### S2-020 — Router registrations in `backend/index.py`

**What was missing:** Three routers were fully written but never imported or mounted in the main app, so their endpoints were unreachable:

- `skills.py` — manages skill records per user
- `career_preferences.py` — manages target roles, location, work mode, salary preference
- `follow_ups.py` — the new router from S2-012

**What was added:** Three import statements and three `app.include_router(...)` calls in `index.py`. The education router was already registered, so that was left alone.

---

## Frontend Changes

### New shared component — `frontend/src/components/EditModal.jsx`

Both `Profile.jsx` and `Settings.jsx` had their own copy of the same modal component written inline. This was extracted into a single shared file so both pages can import it instead of duplicating code.

**What it does:** A generic pop-up form that accepts:
- A `title` (the heading shown at the top)
- A `fields` array describing each input (name, label, type, placeholder)
- An `onSave` callback that receives all the form values and returns either `null` (success) or an error string (shown in red inside the modal)
- An `onCancel` callback that closes the modal

Supported field types: `text` (default), `date`, `textarea`. The modal scrolls if there are many fields (important for Education which has 10 fields).

---

### S2-007 — Details section in `frontend/src/pages/Applications.jsx`

**What it adds:** A collapsible "Details" panel inside each job card on the Applications page.

**How it works:**
1. When the page loads, each job card already receives the `deadline` and `recruiter_notes` values from the dashboard API — they were always in the response, just never shown.
2. Clicking "Details ▸" expands the panel and shows:
   - **Deadline** — displayed as a formatted date, or "—" if not set
   - **Recruiter / Contact Notes** — shown as text, or "No notes yet"
3. Clicking "Edit" inside the panel switches to edit mode:
   - A date picker for deadline
   - A textarea for notes
   - Save and Cancel buttons
4. Saving calls `PUT /jobs/applications/{job_id}` with the current values. On success the panel returns to view mode. On error, a red message appears.

The values survive inside the card's local state — if you save and then toggle the panel closed and open again, your saved values are still there. A page refresh re-fetches from the database.

---

### S2-012 — Follow-Ups section in `frontend/src/pages/Applications.jsx`

**What it adds:** A collapsible "Follow-Ups" panel inside each job card, below the Details section.

**How it works:**
1. Clicking "Follow-Ups ▸" loads the list lazily — it only makes an API call the first time you open it (same pattern as the existing "View History" button). The count is shown in the button label once loaded.
2. The list shows each follow-up with:
   - A **checkbox** — clicking it toggles the `completed` field (calls `PUT /followups/{id}` immediately). Completed items show with strikethrough text.
   - The **description** text
   - The **due date** if one was set
   - A **✕ button** to delete it (calls `DELETE /followups/{id}`)
3. Clicking "+ Add Follow-Up" reveals an inline mini-form with a description field (required) and an optional date picker. Saving calls `POST /jobs/{job_id}/followups`. The new item appears in the list immediately without a page reload.

Validation: if you try to save a follow-up with an empty description, an error message appears and no API call is made.

---

### S2-020 — Profile sections in `frontend/src/pages/Profile.jsx`

Three new sections were added to the Profile page. Each section saves completely independently — saving Skills has no effect on Education or Career Preferences.

#### Education section

Displays a list of education records (degree, school, dates, GPA). Each record can be added, edited, or deleted.

- **Adding:** Click "+ Add" → a modal opens with fields for highest education level, degree, school name, field of study, start/end dates, GPA, and optionally the school's address.
- **Editing:** Click "Edit" on a record → same modal pre-filled with current values. Address fields are omitted since they cannot be changed after creation.
- **Deleting:** Click "Delete" → a confirmation dialog appears before anything is removed.
- **Validation:** Highest Education, Degree, School, Field of Study, and Start Date are all required. If any are missing when you hit Save, a red error message appears inside the modal and no API call is made.
- **Status feedback:** A green "Saved!" message appears below the section list after every successful save, then disappears after 3 seconds.

#### Skills section

Displays a list of skills. Each skill has a name (required) and optional category and proficiency level.

- **Adding / Editing:** Same modal pattern as Education but with just three fields: Skill Name, Category (e.g. "Backend"), Proficiency (e.g. "Advanced").
- **Deleting:** Confirmation dialog before removal.
- **Validation:** Only Skill Name is required.

#### Career Preferences section

A single record (not a list) that stores your job search preferences. All fields are optional.

- Fields: Target Roles, Location Preferences, Work Mode, Salary Preference
- **Saving:** Always uses `PUT` — the backend creates the record if it doesn't exist yet (upsert), so there's no separate "create" step for the user.
- Clicking "Edit" opens the modal pre-filled with current values.

---

### S2-016 — Experience section in `frontend/src/pages/Profile.jsx`

Displays a list of work experience entries. Appears at the top of the profile sections, above Education.

**Adding / Editing:** Modal with fields for Company, Job Title, Start Date, End Date, and Description (optional textarea). If you leave End Date blank, the entry shows "Present" and the backend stores `null` for that field. This is handled automatically — no separate "I currently work here" checkbox needed.

**Deleting:** Confirmation dialog, same pattern as Education and Skills.

**Validation:** Company, Job Title, and Start Date are all required.

**Reordering (↑/↓ buttons):** Each entry has small Up and Down arrow buttons on the left side. Clicking one swaps that entry's position with the one above or below it.

How reordering works under the hood:
- Each experience record has a `sort_order` number in the database (0, 1, 2, etc.)
- Clicking ↑ swaps the `sort_order` values of the current entry and the one above it, then PUTs both records to the backend at the same time
- The UI re-sorts immediately so you see the change without waiting
- On the next page load, the server returns the records already sorted by `sort_order`, so the order persists

The ↑ button is disabled on the first entry and the ↓ button is disabled on the last entry so you can't move items out of bounds.

---

## File Summary

| File | What changed |
|------|-------------|
| `backend/routers/jobs.py` | Fixed `update_application` to forward `deadline` and `recruiter_notes` |
| `backend/routers/follow_ups.py` | New file — 4 CRUD endpoints for follow-ups with ownership checks |
| `backend/index.py` | Registered `follow_ups`, `skills`, and `career_preferences` routers |
| `frontend/src/components/EditModal.jsx` | New file — shared modal component extracted from Settings.jsx |
| `frontend/src/pages/Settings.jsx` | Removed inline EditModal, added import from components |
| `frontend/src/pages/Applications.jsx` | Added Details section (S2-007) and Follow-Ups section (S2-012) to each job card |
| `frontend/src/pages/Applications.css` | Added styles for the new Details and Follow-Ups sections |
| `frontend/src/pages/Profile.jsx` | Added Experience (S2-016), Education, Skills, and Career Preferences (S2-020) sections |
