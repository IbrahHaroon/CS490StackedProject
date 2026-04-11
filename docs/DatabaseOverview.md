# Database Overview

## Auth / Identity

- **user** — core account record, just email + user_id. Every person (job seeker or recruiter) starts here
- **credentials** — stores the hashed password tied to a user
- **token_blacklist** — tracks invalidated JWTs (logged-out tokens) so they can't be reused
- **password_reset** — stores temporary reset tokens when a user requests a password change

## Job Seeker Profile

- **profile** — personal info for a job seeker (name, phone, bio, etc.)
- **address** — physical address, shared by profile and education records
- **education** — a degree/school record for a user (school, degree, GPA, dates)
- **experience** — a past job/role entry (company, title, dates, description)
- **skills** — individual skills attached to a user (skill name, proficiency level)
- **career_preferences** — what the user is looking for (job type, work mode, salary range, etc.)
- **documents** — uploaded files (resume, cover letter) with a path and optional link to a job application

## Job Listings

- **company** — a company record (name, address)
- **position** — a job listing posted by a company (title, salary, requirements, location type)
- **recruiter** — a company employee who manages positions and applications, linked to both a user and a company

## Application Tracking

- **applied_jobs** — the core application record linking a user to a position, with status (Interested → Applied → Offer), experience, deadline, recruiter notes
- **job_activity** — a log entry every time an application status changes (timestamp, stage, event type, notes)
- **follow_up** — a follow-up action tied to an application (date, method, notes)
- **interview** — an interview tied to an application (type, date/time, location, notes, outcome)
