# CS490 Stacked Project

## 📌 Project Overview

This project is a candidate-focused Application Tracking System (ATS) that helps job seekers manage their applications, generate AI-powered content, and gain insights into their job search process.

## 🎯 Scope

The platform focuses on providing job seekers with tools to organize and optimize their job search process.

Key capabilities include:

- Managing and tracking job applications
- Organizing application workflows through a board-style interface
- Gathering resumes and cover letters using AI
- Providing insights and analytics on job search performance

## ⚙️ Features

### 1. Application Tracking
  - Add/edit job applications
  - Track status (Applied, Interview, Offer, Rejected)
  - Store company, role, dates, and notes

### 2. Workflow / Board View
   - Kanban-style board
   - Columns: To Apply, Applied, Interviewing, Offer, Rejected

### 3. AI-Powered Tools
   - Resume tailoring
   - Cover letter generation

### 4. Job Search Organization 
   - Save job postings
   - Tag or categorize applications
   - Notes per job

### 5. Insights / Analytics
   - Application success rate
   - Interview rate
   - Time to response
   - Trends (Which roles get responses)

### 6. Basic User System
   - User accounts/login
   - Personal dashboard

## 🚫 Out of Scope
- To keep the project focused and realistic, the following features are not included:

  -  Full job board integration (optional stretch)
  -  Advanced AI models (using simple APIs instead)
  -  Complex collaborations / too many team features

## 👥 Audience

### 🎯 Primary audience
- Active job seekers
  - Students and new graduates
  - Career switchers
  - Professionals applying for multiple roles

### 🎯 Secondary Audience
  - Passive job seekers exploring opportunities
  - Freelancer tracking job opportunities
  - Bootcamp students or career program participants


### 🧠 Key Problems
  - Losing track of job applications
  - Rewriting resumes repeatedly
  - Lack of visibility into application progress
  - Disorganized notes and deadlines
  - No data on what strategies are effective

### 💡 Value Proposition
- **Organization** - Centralized tracking system for applications
- **Automation** - AI-assisted resume and cover letter generation
- **Insight** - Data-driven understanding of job search performance
- **Control** - Candidate-focused tools instead of employer-centric systems  

## Coding Conventions

### General
- Write clean, simple, and readable code
- Keep functions small and focused
- Avoid deep nesting (use early returns)
- Use constants instead of hardcoded values
- Remove unused code

### Frontend (React)
- Use functional components and hooks
- Keep UI and logic separate (use hooks/services)
- Store API calls in `services/`

**Example:**
```javascript
function JobCard({ title, company }) {
  return <div>{title} at {company}</div>;
}
```

### Backend (FastAPI)
- Keep routes thin; move business logic to `database/models/`
- Use Pydantic models for validation
- Always use type hints

**Example:**
```python
def create_application(data: ApplicationCreate) -> ApplicationResponse:
    return create_applied_jobs(session, data.user_id, data.position_id)
```

### Functions
- One responsibility per function
- Use clear, descriptive names

**Bad:**
```python
def process(data):
    pass
```

**Good:**
```python
def process_job_application(application_data):
    pass
```

### Comments
- Keep comments minimal
- Explain why, not what

**Example:**
```javascript
// Retry request to handle a temporary API failure.
```

### Consistency
- Follow the same patterns across the codebase
- Reuse existing code instead of duplicating logic

## 🏷️ Naming Conventions

Consistent naming improves readability, maintainability, and collaboration across the team.

### Frontend (React / JavaScript)

- **React components:** use PascalCase  
  Example: `JobCard.jsx`, `ApplicationBoard.jsx`

- **Component file names:** use PascalCase  
  Example: `LoginForm.jsx`, `DashboardLayout.jsx`

- **Variables and functions:** use camelCase  
  Example: `addUser`, `searchJobs`, `handleSubmit`

- **Custom hooks:** use camelCase and start with `use`  
  Example: `useAuth`, `useApplications`

- **Boolean variables:** start with `is`, `has`, or `can`  
  Example: `isLoading`, `hasError`, `canEdit`

- **Constants:** use UPPER_SNAKE_CASE for true constants  
  Example: `API_URL`, `MAX_RETRIES`, `DEFAULT_STATUS`

- **Regular variables declared with const:** still use camelCase  
  Example: `userName`, `totalPrice`, `selectedJob`

- **Objects and arrays:** use camelCase variable names  
  Example: `userProfile`, `jobApplications`

- **Event handler functions:** prefix with `handle` when appropriate  
  Example: `handleLogin`, `handleDeleteApplication`

---

### Backend (Python / FastAPI)

All Python code should follow the PEP 8 style guide:  
https://peps.python.org/pep-0008/

- **Variables and functions:** use snake_case  
  Example: `get_user`, `create_application`

- **File names:** use snake_case  
  Example: `main.py`, `application_service.py`

- **Classes:** use PascalCase  
  Example: `UserService`, `ApplicationCreate`

- **Pydantic schemas:** use PascalCase  
  Example: `ApplicationCreate`, `ApplicationResponse`

- **SQLAlchemy models:** use PascalCase  
  Example: `User`, `Application`, `SavedJob`

- **Constants:** use UPPER_SNAKE_CASE  
  Example: `DEFAULT_PAGE_SIZE`, `JWT_SECRET_KEY`

- **Router variables:** use descriptive snake_case  
  Example: `application_router`, `auth_router`

- **Database table names:** use snake_case  
  Example: `user`, `applied_jobs`, `career_preferences`

- **Boolean variables:** use descriptive names  
  Example: `is_active`, `has_resume`, `can_edit`

### 🔧 Linting & Formatting

### Frontend
- Use ESLint for linting (with `eslint-plugin-react` and `eslint-plugin-react-hooks`)
- Use Prettier for formatting
- 2-space indentation
- Use semicolons consistently
- Run locally: `cd frontend && npm run lint` and `npm run format`

### Backend
- Follow the PEP 8 style guide
- Use Ruff for linting and formatting (replaces Black + flake8)
- Maximum line length: 88 characters
- Run locally: `ruff check backend/` and `ruff format backend/`

Both are enforced automatically in CI on every pull request.


## ⚠️ Error Handling

### Backend
- Use FastAPI `HTTPException` for API errors
- Return clear and consistent error messages
- Avoid exposing internal server errors to users

**Example:**
```json
{
  "success": false,
  "error": "Not Found",
  "message": "Job application does not exist"
}
```

### Frontend
- Display user-friendly error messages
- Handle API errors gracefully (no crashes)
- Always account for loading, success, and error states

**Example:**
```javascript
try {
  const response = await api.getApplications();
} catch (error) {
  console.error(error);
  setError("Something went wrong. Please try again.");
}
```

## 🔌 API Response Conventions

FastAPI returns Pydantic model instances directly — no wrapper object.

**Success (200/201):** the serialized Pydantic response model
```json
{
  "job_id": 1,
  "user_id": 3,
  "application_status": "Applied"
}
```

**Error:** FastAPI's standard `HTTPException` shape
```json
{
  "detail": "Application not found"
}
```

**Rules:**
- Always return JSON responses via Pydantic `response_model`
- Use proper HTTP status codes (`200`, `201`, `204`, `400`, `401`, `403`, `404`, `422`, `500`)
- Raise `HTTPException` for all error cases — never return error dicts manually

## 📁 Project Folder Structure

```plaintext
cs490-stacked-project/
├── frontend/
│   ├── src/
│   │   ├── components/      # reusable UI components (buttons, cards, modals)
│   │   └── pages/           # page-level views (Dashboard, Login, Board)
│   │
│   ├── eslint.config.js
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
│
├── backend/
│   ├── database/            # database connection, config, and ORM models
│   │   └── models/          # SQLAlchemy model definitions (one file per model)
│   ├── routers/             # API route handlers (one file per resource)
│   ├── schemas.py           # Pydantic request/response models
│   ├── scripts/             # one-off utility scripts
│   ├── tests/               # unit and integration tests
│   ├── uploads/             # user-uploaded files
│   ├── utils/               # shared helper functions
│   ├── index.py             # FastAPI entry point
│   └── requirements.txt
│
└── .env                    # environment variables (not committed)
```

### 📌 Notes

- Frontend and backend are separated for clarity and scalability  
- Keep business logic out of UI components and API routes  
- Use `utils/` for shared helpers  
- Follow this structure consistently across the team  

## 🧰 Tech Stack

### Frontend
- React  
- Tailwind CSS 
- JavaScript / HTML / CSS

### Backend
- FastAPI (Python)

### Database
- PostgreSQL

### ORM
- SQLAlchemy

### Deployment / Services
- Vercel (frontend)
- Supabase (PostgreSQL hosting)

### APIs
- Gemini API
