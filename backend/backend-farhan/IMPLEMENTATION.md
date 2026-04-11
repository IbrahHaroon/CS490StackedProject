# Backend-Farhan: Extended ATS Features Implementation

## Overview

This module extends the existing ATS backend with four major features:
1. Job sorting controls
2. Interview tracking
3. Outcome tracking
4. Document save from job context

## File Structure

```
backend-farhan/
├── __init__.py
├── schemas.py                  # Pydantic schemas for new features
├── database/
│   ├── __init__.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── interview.py        # Interview model and CRUD
│   │   ├── outcome.py          # Outcome model and CRUD
│   │   └── job_document.py     # JobDocument model and CRUD
│   └── services/
│       ├── __init__.py
│       └── job_sorter.py       # Sorting utility (database-level)
└── routers/
    ├── __init__.py
    ├── jobs.py                 # Sorting endpoint
    ├── interviews.py           # Interview CRUD endpoints
    ├── outcomes.py             # Outcome CRUD endpoints
    └── job_documents.py        # Job document CRUD endpoints
```

## Database Schema

### New Tables

#### `interview`
```sql
CREATE TABLE interview (
    interview_id SERIAL PRIMARY KEY,
    job_id INTEGER NOT NULL REFERENCES applied_jobs(job_id),
    round_type VARCHAR(100) NOT NULL,
    date_time TIMESTAMP NOT NULL,
    notes VARCHAR(2000)
);
```

#### `outcome`
```sql
CREATE TABLE outcome (
    outcome_id SERIAL PRIMARY KEY,
    job_id INTEGER NOT NULL UNIQUE REFERENCES applied_jobs(job_id),
    outcome_state VARCHAR(50) NOT NULL,
    outcome_notes VARCHAR(2000)
);
```

#### `job_document`
```sql
CREATE TABLE job_document (
    job_document_id SERIAL PRIMARY KEY,
    job_id INTEGER NOT NULL REFERENCES applied_jobs(job_id),
    title VARCHAR(255) NOT NULL,
    content VARCHAR(10000) NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);
```

### Modified Tables

#### `applied_jobs`
- Added relationships for: `interviews`, `outcome`, `job_documents`
- No schema changes (relationships are ORM-level)

## API Endpoints

### Feature 1: Job Sorting

#### GET /dashboard/sorted

Retrieve sorted job listings with database-level sorting.

**Query Parameters:**
- `sort_by` (optional): Field to sort by
  - `created_at` (default) - Application submission date
  - `last_activity` - Latest stage change timestamp
  - `deadline` - Position listing date
  - `company` - Company name alphabetically
- `order` (optional): Sort order
  - `desc` (default) - Descending
  - `asc` - Ascending

**Example Requests:**

```bash
# Default: sorted by creation date, descending
curl -X GET "http://localhost:8000/dashboard/sorted" \
  -H "Authorization: Bearer <token>"

# Sort by company name, ascending
curl -X GET "http://localhost:8000/dashboard/sorted?sort_by=company&order=asc" \
  -H "Authorization: Bearer <token>"

# Sort by deadline (position listing date), ascending
curl -X GET "http://localhost:8000/dashboard/sorted?sort_by=deadline&order=asc" \
  -H "Authorization: Bearer <token>"

# Sort by last activity, descending
curl -X GET "http://localhost:8000/dashboard/sorted?sort_by=last_activity&order=desc" \
  -H "Authorization: Bearer <token>"
```

**Response:**
```json
[
  {
    "job_id": 1,
    "user_id": 5,
    "position_id": 10,
    "years_of_experience": 3,
    "application_date": "2024-01-15",
    "application_status": "Interview",
    "stage_changed_at": "2024-02-01T10:30:00"
  }
]
```

---

### Feature 2: Interview Tracking

#### POST /jobs/{job_id}/interviews

Create a new interview for a job.

**Request Body:**
```json
{
  "job_id": 1,
  "round_type": "Technical Round",
  "date_time": "2024-03-15T14:00:00",
  "notes": "Focus on system design and coding"
}
```

**Example:**
```bash
curl -X POST "http://localhost:8000/jobs/1/interviews" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": 1,
    "round_type": "Technical Round",
    "date_time": "2024-03-15T14:00:00",
    "notes": "Focus on system design and coding"
  }'
```

**Response:** `201 Created`
```json
{
  "interview_id": 15,
  "job_id": 1,
  "round_type": "Technical Round",
  "date_time": "2024-03-15T14:00:00",
  "notes": "Focus on system design and coding"
}
```

#### GET /jobs/{job_id}/interviews

Retrieve all interviews for a job (ordered by date_time).

**Example:**
```bash
curl -X GET "http://localhost:8000/jobs/1/interviews" \
  -H "Authorization: Bearer <token>"
```

**Response:** `200 OK`
```json
[
  {
    "interview_id": 15,
    "job_id": 1,
    "round_type": "Technical Round",
    "date_time": "2024-03-15T14:00:00",
    "notes": "Focus on system design and coding"
  },
  {
    "interview_id": 16,
    "job_id": 1,
    "round_type": "HR Round",
    "date_time": "2024-03-22T10:00:00",
    "notes": "Discuss culture fit and compensation"
  }
]
```

#### PUT /interviews/{interview_id}

Update an existing interview.

**Request Body:**
```json
{
  "round_type": "Technical Round - Updated",
  "date_time": "2024-03-20T14:00:00",
  "notes": "Changed schedule"
}
```

**Example:**
```bash
curl -X PUT "http://localhost:8000/interviews/15" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "round_type": "Technical Round - Updated",
    "date_time": "2024-03-20T14:00:00",
    "notes": "Changed schedule"
  }'
```

**Response:** `200 OK`
```json
{
  "interview_id": 15,
  "job_id": 1,
  "round_type": "Technical Round - Updated",
  "date_time": "2024-03-20T14:00:00",
  "notes": "Changed schedule"
}
```

#### DELETE /interviews/{interview_id}

Delete an interview.

**Example:**
```bash
curl -X DELETE "http://localhost:8000/interviews/15" \
  -H "Authorization: Bearer <token>"
```

**Response:** `204 No Content`

---

### Feature 3: Outcome Tracking

#### POST /jobs/{job_id}/outcome

Set outcome for a job (one outcome per job).

**Request Body:**
```json
{
  "job_id": 1,
  "outcome_state": "Offer",
  "outcome_notes": "Negotiating salary"
}
```

Valid `outcome_state` values:
- `Applied`
- `Rejected`
- `Offer`
- `Accepted`
- `Withdrawn`

**Example:**
```bash
curl -X POST "http://localhost:8000/jobs/1/outcome" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": 1,
    "outcome_state": "Offer",
    "outcome_notes": "Negotiating salary"
  }'
```

**Response:** `201 Created`
```json
{
  "outcome_id": 8,
  "job_id": 1,
  "outcome_state": "Offer",
  "outcome_notes": "Negotiating salary"
}
```

#### GET /jobs/{job_id}/outcome

Retrieve outcome for a job.

**Example:**
```bash
curl -X GET "http://localhost:8000/jobs/1/outcome" \
  -H "Authorization: Bearer <token>"
```

**Response:** `200 OK`
```json
{
  "outcome_id": 8,
  "job_id": 1,
  "outcome_state": "Offer",
  "outcome_notes": "Negotiating salary"
}
```

#### PUT /outcome/{outcome_id}

Update an existing outcome.

**Request Body:**
```json
{
  "outcome_state": "Accepted",
  "outcome_notes": "Accepted offer with 15% salary increase"
}
```

**Example:**
```bash
curl -X PUT "http://localhost:8000/outcome/8" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "outcome_state": "Accepted",
    "outcome_notes": "Accepted offer with 15% salary increase"
  }'
```

**Response:** `200 OK`
```json
{
  "outcome_id": 8,
  "job_id": 1,
  "outcome_state": "Accepted",
  "outcome_notes": "Accepted offer with 15% salary increase"
}
```

#### DELETE /outcome/{outcome_id}

Delete an outcome.

**Example:**
```bash
curl -X DELETE "http://localhost:8000/outcome/8" \
  -H "Authorization: Bearer <token>"
```

**Response:** `204 No Content`

---

### Feature 4: Document Save from Job Context

#### POST /jobs/{job_id}/documents

Save a document (draft, generated content, etc.) linked to a job.

**Request Body:**
```json
{
  "job_id": 1,
  "title": "Cover Letter Draft",
  "content": "Dear Hiring Manager, I am writing to express my strong interest..."
}
```

**Example:**
```bash
curl -X POST "http://localhost:8000/jobs/1/documents" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": 1,
    "title": "Cover Letter Draft",
    "content": "Dear Hiring Manager, I am writing to express my strong interest..."
  }'
```

**Response:** `201 Created`
```json
{
  "job_document_id": 42,
  "job_id": 1,
  "title": "Cover Letter Draft",
  "content": "Dear Hiring Manager, I am writing to express my strong interest...",
  "created_at": "2024-02-15T09:30:00",
  "updated_at": "2024-02-15T09:30:00"
}
```

#### GET /jobs/{job_id}/documents

Retrieve all documents for a job (ordered by creation date, newest first).

**Example:**
```bash
curl -X GET "http://localhost:8000/jobs/1/documents" \
  -H "Authorization: Bearer <token>"
```

**Response:** `200 OK`
```json
[
  {
    "job_document_id": 42,
    "job_id": 1,
    "title": "Cover Letter Draft",
    "content": "Dear Hiring Manager...",
    "created_at": "2024-02-15T09:30:00",
    "updated_at": "2024-02-15T09:30:00"
  },
  {
    "job_document_id": 41,
    "job_id": 1,
    "title": "Resume Tailored",
    "content": "Tailored resume for this specific role...",
    "created_at": "2024-02-14T14:20:00",
    "updated_at": "2024-02-15T08:00:00"
  }
]
```

#### PUT /documents/{document_id}

Update an existing document.

**Request Body:**
```json
{
  "title": "Cover Letter Draft - Final",
  "content": "Updated content after review..."
}
```

**Example:**
```bash
curl -X PUT "http://localhost:8000/documents/42" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Cover Letter Draft - Final",
    "content": "Updated content after review..."
  }'
```

**Response:** `200 OK`
```json
{
  "job_document_id": 42,
  "job_id": 1,
  "title": "Cover Letter Draft - Final",
  "content": "Updated content after review...",
  "created_at": "2024-02-15T09:30:00",
  "updated_at": "2024-02-15T10:15:00"
}
```

#### DELETE /documents/{document_id}

Delete a document.

**Example:**
```bash
curl -X DELETE "http://localhost:8000/documents/42" \
  -H "Authorization: Bearer <token>"
```

**Response:** `204 No Content`

---

## Integration Notes

### Sorting Implementation

- Uses database-level sorting (no in-memory operations)
- Handles `null` values gracefully:
  - `last_activity`: Jobs with no activities sort to bottom (ascending) or top (descending)
  - Other fields: Standard SQL sorting behavior
- Uses `.unique()` after joins to prevent duplicate rows from multiple joins

### Outcome Constraints

- One outcome per job (unique constraint on `job_id`)
- Attempting to create a second outcome returns `409 Conflict`
- Use PUT to update existing outcome

### Authorization & Error Handling

All endpoints require:
- Valid JWT token in `Authorization: Bearer <token>` header
- User ownership verification (users can only access their own data)

Error responses:
- `404 Not Found`: Resource doesn't exist or belongs to another user
- `403 Forbidden`: User doesn't own the resource
- `409 Conflict`: Outcome already exists for job
- `422 Unprocessable Entity`: Invalid query params or request data

### Data Cascading

When a job application is deleted:
- All associated interviews are deleted
- All associated job documents are deleted
- All associated outcomes are deleted
- Job activity records are deleted (existing behavior)

---

## Schema Differences

The implementation follows the same patterns as existing code:

✅ Same model structure (SQLAlchemy ORM)
✅ Same CRUD function patterns
✅ Same response schema patterns (Pydantic with `from_attributes=True`)
✅ Same router patterns (dependency injection, auth checks)
✅ Same error handling (HTTPException with descriptive messages)
✅ Same timestamp handling (datetime.utcnow())

No tech stack changes or architectural deviations.
