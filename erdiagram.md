```mermaid
erDiagram
  USER {
    int user_id PK
    string email
  }
  CREDENTIALS {
    int credential_id PK
    int user_id FK
    string hashed_password
  }
  PASSWORD_RESET_TOKEN {
    int token_id PK
    int user_id FK
    string token_hash
    datetime expires_at
    bool used
  }
  TOKEN_BLACKLIST {
    int id PK
    string jti
    datetime expires_at
  }

  PROFILE {
    int profile_id PK
    int user_id FK
    string first_name
    string last_name
    date dob
    string phone_number
    string summary
    string address_line
    string city
    string state
    string zip_code
    string country
  }
  EDUCATION {
    int education_id PK
    int user_id FK
    string school
    string degree
    string field_of_study
    date start_date
    date end_date
    string gpa
    string school_location
    int sort_order
  }
  EXPERIENCE {
    int experience_id PK
    int user_id FK
    string company
    string title
    string location
    date start_date
    date end_date
    string description
    int sort_order
  }
  SKILL {
    int skill_id PK
    int user_id FK
    string name
    string category
    string proficiency
    int sort_order
  }
  CAREER_PREFERENCES {
    int preference_id PK
    int user_id FK
    string target_roles
    string location_preferences
    string work_mode
    string salary_preference
  }

  JOB {
    int job_id PK
    int user_id FK
    string title
    string company_name
    string location
    string source_url
    string description
    string stage
    datetime stage_changed_at
    date application_date
    date deadline
    string priority
    decimal salary
    int years_of_experience
    string notes
    string company_research_notes
    string outcome_notes
    datetime created_at
    datetime archived_at
  }
  JOB_ACTIVITY {
    int activity_id PK
    int job_id FK
    string event_type
    string from_stage
    string to_stage
    string notes
    datetime occurred_at
  }
  INTERVIEW {
    int interview_id PK
    int job_id FK
    string round_type
    datetime scheduled_at
    string interviewer
    string mode
    string prep_notes
    string notes
  }
  FOLLOW_UP {
    int followup_id PK
    int job_id FK
    string description
    date due_date
    bool completed
  }

  DOCUMENT {
    int document_id PK
    int user_id FK
    string title
    string document_type
    string status
    int current_version_id FK
    bool is_deleted
    datetime created_at
    datetime updated_at
  }
  DOCUMENT_VERSION {
    int version_id PK
    int document_id FK
    int version_number
    string storage_location
    string content
    string source
    datetime created_at
  }
  DOCUMENT_TAG {
    int tag_id PK
    int document_id FK
    string label
  }
  JOB_DOCUMENT_LINK {
    int link_id PK
    int job_id FK
    int version_id FK
    string role
    datetime linked_at
  }

  USER ||--|| PROFILE : "has"
  USER ||--|| CREDENTIALS : "authenticates with"
  USER ||--o{ PASSWORD_RESET_TOKEN : "requests"
  USER ||--o{ EDUCATION : "has"
  USER ||--o{ EXPERIENCE : "has"
  USER ||--o{ SKILL : "has"
  USER ||--o| CAREER_PREFERENCES : "has"
  USER ||--o{ JOB : "tracks"
  USER ||--o{ DOCUMENT : "owns"

  JOB ||--o{ JOB_ACTIVITY : "has history"
  JOB ||--o{ INTERVIEW : "schedules"
  JOB ||--o{ FOLLOW_UP : "has"
  JOB ||--o{ JOB_DOCUMENT_LINK : "uses"

  DOCUMENT ||--o{ DOCUMENT_VERSION : "versions"
  DOCUMENT ||--o{ DOCUMENT_TAG : "tagged"
  DOCUMENT_VERSION ||--o{ JOB_DOCUMENT_LINK : "attached to"
```

## Design notes

This schema reflects the candidate-facing model from [PURPOSE.md](PURPOSE.md): a single-user, private job-search workspace. Every record is account-scoped via `user_id`. There is no cross-user visibility and no shared catalog of companies or postings.

### Removed from prior schema
- **`COMPANY`** — companies are free-text strings on the `JOB` row. AI "company research" in Sprint 3 is generated text, not a shared directory.
- **`POSITION`** — there is no employer-owned listing. A `JOB` is the user's own opportunity record.
- **`APPLIED_JOBS`** — collapsed into `JOB`. "Applications" and "jobs" are the same thing now (PURPOSE.md §3 mental-model table).
- **`RECRUITER`, `RECRUITER_CREDENTIALS`, `RECRUITER_PASSWORD_RESET_TOKEN`** — no second user role.
- **`ADDRESS`** — denormalized onto `PROFILE`/`EDUCATION`/`EXPERIENCE`. The address table existed mostly to share rows with `COMPANY`; without that, the join cost has no payoff for a single-user app.

### Key changes
- **`JOB`** owns `company_name`, `location`, `source_url`, `description` directly. `application_date` is nullable (Interested-stage jobs aren't applied yet).
- **`DOCUMENT` / `DOCUMENT_VERSION` / `JOB_DOCUMENT_LINK`** support N:N between jobs and document *versions*, with version history per document. `DOCUMENT.current_version_id` lets the library show the latest version without scanning. `JOB_DOCUMENT_LINK.role` distinguishes resume vs. cover-letter attachment.
- **`JOB_ACTIVITY`** gains `from_stage`/`to_stage` so the timeline can render transitions, not just snapshots.
- **`SKILLS` → `SKILL`** for naming consistency.

### Tradeoff
Free-text `company_name` means "Google" and "google inc" won't auto-merge. Acceptable for a personal tracker; if per-company grouping is needed later, add a per-user `COMPANY_REF` table — *not* a shared one.
