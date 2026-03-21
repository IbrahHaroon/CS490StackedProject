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

## Coding Standards

### Naming Conventions
  - React components: PascalCase (e.g., JobCard.jsx)
  - JavaScript variables/functions: camelCase (addUser,searchBar())
  - Javascript constants
    - True constants: UPPERCASE (e.g, PI, API_URL)
    - Regular constants: camelCase (e.g, const userName, const totalPrice)
    - Boolean constans: start with "is", "has", "can" (e.g, isActive, hasPermission, canEdit)
    - Object & arrays: camelCase (e.g, const userProfile = { name: "Alice", age:26 }, const itemList = {"apple", "orange"});
    - Class-level or module constants: UPPERCASE {e.g, const DEFAULT_TIMEOUT, const ERROR_MESSAGE})   
  
  - Python backend
    variables/functions: snake_case
  - Constants: UPPER_SNAKE_CASE

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

Example:
{
  "success": false,
  "error": "Not Found",
  "message": "Job application does not exist"
}

- Avoid exposing internal server errors to users

Frontend:
- Display user-friendly error messages
- Handle API errors gracefully (no crashes)

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

