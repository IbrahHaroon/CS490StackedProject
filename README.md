# CS490 Stacked Project — ATS (Applicant Tracking System)

A full-stack Applicant Tracking System built for CS490. Users can register, log in, manage their profile, upload documents, and apply to job listings.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 19, React Router, Vite |
| Backend | FastAPI (Python) |
| Database | PostgreSQL |
| Auth | JWT (Bearer tokens) + bcrypt |
| Email | Gmail SMTP (password reset) |

---

## Project Structure

```
490Project/
├── backend/
│   ├── database/        # SQLAlchemy models, DB connection, auth utilities
│   ├── routers/         # FastAPI route handlers (auth, users, profile, jobs, etc.)
│   ├── utils/           # Email utility
│   ├── tests/           # Pytest test suite
│   ├── schemas.py       # Pydantic request/response schemas
│   └── index.py         # App entry point
└── frontend/
    └── src/
        └── pages/       # React pages (Dashboard, Profile, Settings, etc.)
```

---

## Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL running locally

---

### Backend Setup

1. **Create and activate a virtual environment**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate       # Mac/Linux
   venv\Scripts\activate          # Windows
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Create your `.env` file** inside `backend/`
   ```
   DATABASE_URL=postgresql://<db_user>:<db_password>@localhost:5432/<db_name>
   SECRET_KEY=<your_secret_key>
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   GEMINI_API_KEY=<your_gemini_api_key>

   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USER=your_gmail@gmail.com
   SMTP_PASSWORD=your_gmail_app_password
   FRONTEND_URL=http://localhost:3000
   ```

4. **Run the backend**
   ```bash
   python index.py
   ```
   API will be live at `http://127.0.0.1:8000`
   Interactive docs at `http://127.0.0.1:8000/docs`

---

### Frontend Setup

1. **Install dependencies**
   ```bash
   cd frontend
   npm install
   ```

2. **Run the frontend**
   ```bash
   npm run dev
   ```
   App will be live at `http://localhost:3000`

---

## API Overview

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| POST | `/auth/register` | Create a new account | No |
| POST | `/auth/login` | Log in, get JWT token | No |
| GET | `/auth/me` | Get current user info | Yes |
| POST | `/auth/logout` | Log out | Yes |
| POST | `/auth/forgot-password` | Request a password reset email | No |
| POST | `/auth/reset-password` | Reset password using token from email | No |
| GET | `/users/{user_id}` | Get user by ID | No |
| GET/POST | `/profile` | Manage user profile | Yes |
| GET/POST | `/education` | Manage education records | Yes |
| GET/POST | `/documents` | Manage uploaded documents | Yes |
| GET/POST | `/jobs` | Browse and apply to job listings | Yes |
| GET/POST | `/company` | Manage companies | Yes |

---

## Password Reset (SMTP Setup)

Password reset emails are sent via Gmail SMTP. Each developer needs their own Gmail App Password in their local `.env`. The `.env` file is gitignored — never commit it.

### Step 1 — Enable 2-Step Verification on your Google account

1. Go to [myaccount.google.com](https://myaccount.google.com)
2. Click **Security** in the left sidebar
3. Under "How you sign in to Google", click **2-Step Verification**
4. Follow the prompts to turn it on (required before App Passwords are available)

### Step 2 — Generate a Gmail App Password

1. Go to [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
   - Or navigate: **Security → 2-Step Verification → scroll down to App passwords**
2. Sign in again if prompted
3. Under "App name", type something like `490Project SMTP`
4. Click **Create**
5. Google shows a **16-character password** — copy it immediately, it won't be shown again

### Step 3 — Add your credentials to `backend/.env`

```
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_gmail@gmail.com
SMTP_PASSWORD=xxxx xxxx xxxx xxxx
```

> Spaces in the App Password are fine — Gmail ignores them.

---

## Running Tests

```bash
cd backend
pytest
```

---

## Environment Variables Reference

| Variable | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string |
| `SECRET_KEY` | JWT signing secret |
| `ALGORITHM` | JWT algorithm (default `HS256`) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token lifetime in minutes |
| `GEMINI_API_KEY` | Google Gemini API key |
| `SMTP_HOST` | SMTP server (default `smtp.gmail.com`) |
| `SMTP_PORT` | SMTP port (default `587`) |
| `SMTP_USER` | Gmail address to send from |
| `SMTP_PASSWORD` | Gmail App Password |
| `FRONTEND_URL` | Frontend base URL for reset links |
