# Sprint 2 Demo Run Sheet - Click-by-Click Script

**Presenter:** [Your Name] | **Backup:** [Teammate Name]  
**Demo Date:** Tomorrow | **Time Slot:** [Your time] | **Duration:** 15 minutes (8 min demo + 7 min Q&A)

---

## PHASE A - PRODUCT DEMO (8 MINUTES)

### ⏱️ A1: Dashboard Search/Filter/Sort & Status Indicators (2 minutes)

**START:** Timer = 0:00 | Page: Dashboard

**Click Flow:**
```
1. [0:00] Open http://localhost:3000 and login
   - Email: [test_email@example.com]
   - Password: [test_password]
   - Expected: Dashboard loads with 8+ job cards

2. [0:15] Point out stage badges on cards
   - Show different colors/states: Applied (blue), Interview (yellow), Offer (green), Rejected (red)
   - Say: "Each card shows the current workflow stage with visual indicators"

3. [0:30] Search by job title
   - Find search box at top of dashboard
   - Type a job title from your seed data (e.g., "Engineer", "Manager")
   - Hit Enter or click search button
   - Expected: Results filter in real-time

4. [0:50] Apply a filter
   - Click "Filter" or stage dropdown
   - Select one stage (e.g., "Interview Scheduled")
   - Expected: Dashboard shows only jobs in that stage
   - Say: "Now filtering by stage - we see only the 2 Interview Scheduled jobs"

5. [1:10] Apply a sort
   - Click "Sort" dropdown (if available)
   - Select sort option (e.g., "Newest First", "Deadline Soon")
   - Expected: Job card order changes
   - Say: "Sorting by deadline so we see urgent opportunities first"

6. [1:50] Reset and prepare for A2
   - Clear search/filter (click "Reset" or remove filters)
   - Dashboard returns to full view
   - Say: "Ready to dive into a specific job"

**END A1:** Timer should be ~2:00
```

---

### ⏱️ A2: Job Detail & Workflow (Stage Transitions, Deadlines, Contact) (2 minutes)

**START:** Timer = 2:00 | Page: Dashboard (reset view)

**Click Flow:**
```
1. [2:00] Click on one job card to expand/open Job Detail
   - Choose a job ideally in "Applied" stage (so you can transition it)
   - Expected: Job Detail page opens with full job info

2. [2:15] Point out key job information
   - Title, Company, Location, Salary range
   - Job description (scroll if needed)
   - Say: "You can see the full job posting, including salary and location"

3. [2:30] Show overview/edit section
   - Point to editable fields (title, company, recruiter notes)
   - Say: "The overview tab lets you track recruiter info and update notes"

4. [2:45] Change the job stage (CRITICAL DEMO POINT)
   - Find Stage dropdown or state selector
   - Current: "Applied" (or whatever it is)
   - Click and select next stage: "Interview Scheduled"
   - Click Save
   - Expected: Stage updates, possibly timestamp updates, activity log shows change
   - Say: "When we update the stage, it tracks when the transition happened"

5. [3:10] Verify deadline and contact fields
   - Scroll to find Deadline field (date picker)
   - Show Recruiter/Contact Notes section
   - Say: "You can set reminders and track recruiter contact info here"

6. [3:25] Prepare for A3
   - Stay on this Job Detail page
   - Say: "Now let's add interview details to track progress"

**END A2:** Timer should be ~4:00
```

---

### ⏱️ A3: Interview/Activity/Timeline/Outcome (2 minutes)

**START:** Timer = 4:00 | Page: Job Detail (same job from A2)

**Click Flow:**
```
1. [4:00] Scroll down to find "Interviews" or "Activity" section
   - Expected: Empty or shows past interviews
   - Look for "Add Interview" or "Schedule Interview" button
   - Say: "Let's schedule an interview for this opportunity"

2. [4:15] Click "Add Interview" button
   - Fill in form:
     * Date: (pick a date, e.g., tomorrow or next week)
     * Time: (pick a time, e.g., 2:00 PM)
     * Type: (e.g., Phone Screen, Technical Interview, Final Round)
     * Notes: (e.g., "Interviewer: Jane Smith from HR")
   - Click Save
   - Expected: Interview appears in timeline

3. [4:40] Add a follow-up reminder
   - Look for "Follow-ups" or "Reminders" section
   - Click "Add Follow-up"
   - Fill in:
     * Reminder date (e.g., day after interview)
     * Reminder text (e.g., "Send thank you email")
   - Click Save
   - Expected: Reminder appears in timeline

4. [5:00] Show timeline with all activity
   - Scroll to "Timeline" or "Activity History"
   - Point out entries:
     * Job application date
     * Stage change (Applied → Interview Scheduled)
     * Interview scheduled
     * Follow-up reminder
   - Say: "The timeline shows all activity in chronological order, so you never lose track"

5. [5:20] Record an outcome (if applicable)
   - Look for "Outcome" section or dropdown
   - If this job is ready for outcome, select:
     * Offer Received
     * Rejected
     * Withdrawn
     * Pending (still active)
   - Say: "You can track whether you got the offer or were rejected"

6. [5:40] Prepare for A4
   - Stay on page or navigate to AI Documents
   - Say: "Let's generate AI documents tailored to this job"

**END A3:** Timer should be ~6:00
```

---

### ⏱️ A4: Profile Completion + AI Document Generation & Save (2 minutes)

**START:** Timer = 6:00 | Page: Job Detail or Documents page

**Click Flow:**
```
1. [6:00] Navigate to Profile page briefly
   - Click "Profile" in navigation
   - Show Profile page with completed sections:
     * Experience (2+ entries shown)
     * Education (2+ entries shown)
     * Skills (list of skills visible)
     * Career Preferences (location type, salary expectations)
   - Say: "We've completed all profile sections which feed into AI generation"
   - (Spend ~20 seconds max)

2. [6:20] Go back to Job Detail
   - Click back or navigate to the job again
   - Look for "AI Resume" or "Generate Documents" button
   - Say: "Now watch how we use your profile + this job to generate a tailored resume"

3. [6:35] Click "Generate AI Resume"
   - Modal/form opens with options:
     * Target Job: [Job name] (auto-populated from this job)
     * Additional Instructions (optional): (e.g., "Emphasize backend experience")
   - Click "Generate"
   - Expected: Spinner/loading, then resume content appears
   - Say: "OpenAI is now generating a custom resume using your profile and this job's description"

4. [7:05] Show generated resume and save it
   - Resume text appears in preview
   - Click "Save as Document" or "Save"
   - Expected: Document saves, confirmation message shows
   - Say: "The resume is saved and linked to this job application"

5. [7:20] Generate AI Cover Letter (QUICK)
   - Click "Generate AI Cover Letter" button
   - Modal opens (same format)
   - Click "Generate"
   - Wait for result
   - Say: "Cover letter is generated with the job company name and role"

6. [7:40] Show "Improve" action (if time)
   - On one generated document, show "Improve" or "Rewrite" button
   - Click it briefly to show the modal
   - Say: "You can use AI to improve and iterate on documents"

7. [7:50] Check dashboard metrics
   - Navigate back to Dashboard (1-2 clicks)
   - Point out top metrics:
     * Total opportunities
     * Applications in each stage
     * Recent activity count
   - Say: "Dashboard metrics track your progress across all opportunities"

**END A4:** Timer should be ~8:00
```

---

## PHASE B - TECHNICAL EVIDENCE & Q&A (7 MINUTES)

**NOTE:** Instructor drives this section. Your job is to present evidence and answer questions concisely.

### ⏱️ B1: Workflow & Data Integrity Evidence (2 minutes)

**EVIDENCE READY:**

Show the following in sequence when asked "How does workflow integrity work?":

1. **Show GUI Evidence (1 minute):**
   - Navigate to a job in Dashboard
   - Change stage (we just did this in A2)
   - Go back to Dashboard and refresh
   - Job still shows new stage (data persisted)
   - Say: "Stage change persists across page reloads - database wrote it correctly"

2. **Show Backend Code (1 minute):**
   - Open file: `backend/routers/jobs.py` (or job_documents.py if appropriate)
   - Find stage transition endpoint
   - Point to code that validates stage, updates timestamp, saves to DB
   - Say: "Here's where we enforce the stage transition - we validate the state change and persist it"
   - Suggested line highlight: Where `session.commit()` is called

3. **Show Unit Test (1 minute wait, instructor may ask for it):**
   - Open: `backend/tests/test_sprint2_stage_transitions.py`
   - Show test that verifies:
     * Valid stage transition succeeds
     * Invalid transition is rejected
     * Timestamp updates
   - Say: "This test ensures the workflow logic handles both happy path and error cases"

---

### ⏱️ B2: CI & Testing Evidence (3 minutes)

**EVIDENCE READY - Have these terminals/outputs ready:**

1. **Run tests locally (before or during demo):**
   ```bash
   cd backend
   pytest -v --tb=short
   ```
   - Screenshot or console output showing:
     * Passed tests (green ✓)
     * Test names including "sprint2" and "workflow"
     * No errors
   - Say: "All tests pass, including Sprint 2 workflow tests"

2. **Show CI Pipeline (if available):**
   - Go to GitHub Actions tab or GitLab CI
   - Show workflow passing
   - Screenshot or live view
   - Say: "CI automatically runs tests on every commit - all passing"

3. **Point to specific tests (3 examples):**
   - Dashboard workflow test (file: `test_sprint2_*.py`)
   - Profile completion test
   - Error/negative path test (e.g., unauthorized stage transition)
   - For each: Show test name and 2-3 lines of code
   - Say: "This test verifies [feature], ensuring we handle [edge case]"

---

### ⏱️ B3: Q&A - Prepare Answers (2 minutes)

**Likely Questions (answer in 30-60 seconds each):**

**Q: How does Sprint 2 extend Sprint 1 without breaking old flows?**
> Answer: "Sprint 1 established user auth and basic job browsing. Sprint 2 added profile completion and AI documents layer on top without removing any Sprint 1 features. The dashboard still works, jobs still load—we just added workflow state machine and candidate profile features."

**Q: Where is stage transition logic implemented and why?**
> Answer: "Backend: `backend/routers/jobs.py` → method: `update_job_stage()`. We put it on backend because stage state is critical to data integrity—we validate the transition is valid before persisting to DB. Frontend just calls this endpoint."

**Q: How does Job Detail coordinate timeline, interview, and document actions?**
> Answer: "Job Detail page loads the job, then queries related entities: interviews, timeline/activities, documents. Each feature updates the same job_id record in DB, so timeline captures all events (stage change, interview add, document save, etc.)."

**Q: How do profile entities feed AI generation inputs?**
> Answer: "Profile page stores Experience, Education, Skills. When you click 'Generate Resume,' backend fetches these records, formats them, and sends to OpenAI along with the job description. AI uses all that context to write a tailored resume."

**Q: What technical debt did Sprint 2 introduce?**
> Answer: "[Example] "We don't validate file types on document upload yet—Sprint 3 will add that. Also, real-time collaboration isn't implemented—if two people edit the same profile, last write wins."

---

## TIMING BACKUP PLAN

If you fall behind:

- **Skip detailed Job Description in A2** → quickly show stage buttons instead
- **Skip "Improve" action in A4** → just show generate + save
- **Skip second AI document** → focus on resume only
- **If questions run long in B3** → brief answers, say "We can discuss more after"

---

## CONFIDENCE CHECKLIST (Morning of Demo)

Before you start:

- [ ] Both servers running and responsive
- [ ] Can login without errors
- [ ] Dashboard shows 8+ seeded jobs
- [ ] Can click into job detail without lag/errors
- [ ] Can generate AI resume (takes ~10-15 seconds, don't panic)
- [ ] Stage dropdown works and saves changes
- [ ] Interview/activity sections visible
- [ ] Timeline shows activity correctly
- [ ] Tests pass: `pytest`
- [ ] Presenter and backup both reviewed this script
- [ ] Screen shares, projector setup works
- [ ] No console errors in either browser/terminal

✅ **YOU GOT THIS! GOOD LUCK TOMORROW!**
