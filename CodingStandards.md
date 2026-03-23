# CS490 Stacked Project

## 📌 Project Overview

This project is a candidate-focused Application Tracking System (ATS) that helps job seekers, manage their applications, generate AI-powered content, and gain insights into their job search process.

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

## 🚫 Out Of scope
- To keep the project focused and realistic, the following features are not included:

  -  Employer-side tools(no recruiter dashboard)
  -  Full job board integration(optional stretch)
  -  Advanced AI models(Using simple APIs instead)
  -  Complex colloborations/ too many team features

## 👥 Audience

### 🎯 Primary audience
- Active job seekers
  - Students and new graduates
  - Career switchers
  - Professionals applying for multiple roles

### 🎯 Secondary Audience
  - Passive job seekers exploring oppurtunities
  - Freelancer tracking job oppurtunities
  - Bootcamp students or career program participants


### 🧠 Key Problems
  - Losing track of job applications
  - Rewriting resumes repeatedly
  - Lack of visibility into application progress
  - Disogranized notes and deadlines
  - No data on what strategies are effective

### 💡 Value Proposition
- **Organization** - Centralized tracking system for applications
- **Automation** - AI-assisted resume and cover letter generation
- **Insight** - Data-driven understanding of job search performance
- **Control** - Candidate-focused tools instead of employer-centric systems  

## Coding Conventions
- General
- Write clean, simple, and readable code
- Keep functions small and focused
- Avoid deep nesting (use early returns)
- Use constants instead of hardcoded values
- Remove unused code

### Frontend (React)
- Use functional components and hooks
- Keep UI and logic separate (use hooks/services)
- Store API calls in services/

- Example:
- <img width="613" height="95" alt="image" src="https://github.com/user-attachments/assets/b46ee7c6-7adc-42c0-b919-0a17efd05c7f" />

### Backend (FastAPI)
- Keep routes thin; move logic to services/
- Use Pydantic models for validation
- Always use type hints

- Example:
- <img width="604" height="87" alt="image" src="https://github.com/user-attachments/assets/fc3e1704-95ef-4e1c-b9ef-a0a673e2511e" />

#### Functions
- One responsibility per function
- Use clear, descriptive names
- Example:
- <img width="644" height="226" alt="image" src="https://github.com/user-attachments/assets/b16a40f5-27ad-4a68-a17e-a97a427c7a06" />

#### Comments
- Keep comments minimal
- Explain why, not what

- Example (JavaScript):
  // retry request to handle temporary API failure 
  
#### Consistency
- Follow the same patterns as codebase
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
  Example: `users`, `job_applications`

- **Boolean variables:** use descriptive names  
  Example: `is_active`, `has_resume`, `can_edit`

### 🔧 Linting & Formatting

Frontend:
- Use ESLint for linting
- Use Prettier for formatting
- 2-space indentation
- Use semicolons consistently

Backend:
- Follow PEP 8 style guide
- https://peps.python.org/pep-0008/ 
- Use Black for formatting
- https://black.readthedocs.io/en/stable/
- Maximum line length: 88 characters(default black setting)

## ⚠️ Error Handling

Backend:
- Use FastAPI HTTPException for API errors
- Return clear and consistent error messages
- Avoid exposing internal server errors to users
- <img width="657" height="174" alt="image" src="https://github.com/user-attachments/assets/7c87fa26-b934-465f-b304-34aba2d15842" />


Frontend:
- Display user-friendly error messages
- Handle API errors gracefully (no crashes)
- Always account for loading, success, and error states
- <img width="667" height="199" alt="image" src="https://github.com/user-attachments/assets/24dd0a78-0fca-412b-9436-56a0a6826322" />

## 🔌 API Response Conventions

All API responses should follow a consistent JSON format.

Success:
{
  "success": true,
  "data": {...}
}

Error:
{
  "success": false,
  "error": "Bad Request",
  "message": "Invalid input"
}

Rules:
- Always return JSON responses
- Use consistent keys: success, data, error, message
- Use proper HTTP status codes (200, 201, 400, 404, 500)

## 📁 Project Folder Structure

```plaintext
cs490-stacked-project/
├── frontend/
│   ├── src/
│   │   ├── components/      # reusable UI components (buttons, cards, modals)
│   │   ├── pages/           # page-level views (Dashboard, Login, Board)
│   │   ├── layouts/         # layout wrappers (Navbar, Sidebar)
│   │   ├── hooks/           # custom React hooks
│   │   ├── services/        # API calls to backend
│   │   ├── utils/           # helper functions
│   │   ├── assets/          # images, icons, styles
│   │   └── App.jsx          # root React component
│   │
│   ├── package.json
│   └── vite.config.js (or similar)
│
├── backend/
│   ├── app/
│   │   ├── routers/         # API routes/endpoints
│   │   ├── models/          # SQLAlchemy database models
│   │   ├── schemas/         # Pydantic request/response models
│   │   ├── services/        # business logic
│   │   ├── dependencies/    # shared dependencies (auth, validation)
│   │   ├── db/              # database connection/config
│   │   ├── utils/           # helper functions
│   │   └── main.py          # FastAPI entry point
│   │
│   └── requirements.txt
│
├── tests/                  # unit and integration tests
├── .env                    # environment variables (not committed)
├── .gitignore
└── README.md
```

### 📌 Notes

- Frontend and backend are separated for clarity and scalability  
- Keep business logic out of UI components and API routes  
- Use `services/` for logic and `utils/` for helpers  
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
- Vercel
- Firebase

### APIs
- Gemini API

