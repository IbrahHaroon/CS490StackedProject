# Project Setup & Integration Guide

---

## Table of Contents

1. [Technology Stack Overview](#technology-stack-overview)
2. [Prerequisites](#prerequisites)
3. [PostgreSQL Installation](#postgresql-installation)
   - [Linux (Ubuntu)](#linux-ubuntu)
   - [Windows](#windows)
   - [macOS](#macos)
4. [Database Setup](#database-setup)
5. [Environment Configuration](#environment-configuration)
6. [Connection Details](#connection-details)
7. [For Backend Developers (FastAPI + SQLAlchemy)](#for-backend-developers-fastapi--sqlalchemy)
8. [For Frontend Developers (React)](#for-frontend-developers-react)
9. [AI Integration (Gemini API / Grok)](#ai-integration-gemini-api--grok)
10. [Deployment](#deployment)
11. [Common Issues & Troubleshooting](#common-issues--troubleshooting)
12. [Security Guidelines](#security-guidelines)

---

## Technology Stack Overview

| Layer | Technology | Purpose |
|---|---|---|
| **Frontend** | React | User interface |
| **Backend** | FastAPI + Pydantic | REST API and data validation |
| **Database** | PostgreSQL + SQLAlchemy | Data persistence and ORM |
| **AI Provider** | Gemini API / Grok | AI features (free tier available) |
| **Frontend Deploy** | Vercel | Frontend hosting and CI/CD |
| **Backend Deploy** | Railway | Backend hosting |
| **DB / Auth Host** | Supabase or Firebase | Managed database / authentication |

---

## Prerequisites

Before beginning, ensure you have the following installed:

- **Python 3.10+** — for FastAPI and SQLAlchemy
- **Node.js 18+** — for React
- **pip** and **npm** or **yarn** — package managers
- **Git** — version control
- Administrator/sudo privileges on your machine
- Internet connection

Optional but recommended:
- [Postman](https://www.postman.com/) or similar — for testing API endpoints
- [pgAdmin](https://www.pgadmin.org/) — GUI for managing PostgreSQL locally

---

## PostgreSQL Installation

### Linux (Ubuntu)

```bash
# 1. Update your package lists
sudo apt update

# 2. Install PostgreSQL server and additional utilities
sudo apt install postgresql postgresql-contrib

# 3. Verify the installation by checking the service status
sudo systemctl status postgresql

# 4. Start the PostgreSQL service
sudo service postgresql start
```

The status output should show `active (running)` to confirm success.

---

### Windows

1. Visit the official download page: [https://www.postgresql.org/download](https://www.postgresql.org/download)
2. Select **Windows** and download the installer for the latest stable version.
3. Run the installer and follow the on-screen prompts.
4. When prompted, set a password for the default `postgres` superuser — **save this somewhere safe.**
5. Leave the default port as `5432` unless you have a conflict.
6. After installation, PostgreSQL is accessible via **pgAdmin** or the **SQL Shell (psql)** from your Start menu.

---

### macOS

**Option A — Graphical Installer:**

Follow the official macOS instructions: [https://www.postgresql.org/download/macosx/](https://www.postgresql.org/download/macosx/)

**Option B — Homebrew (CLI):**

```bash
# 1. Install PostgreSQL
brew install postgresql

# 2. Start the PostgreSQL service
brew services start postgresql

# 3. Confirm it is running
brew services list
```

You should see `postgresql` listed as `started`.

---

## Database Setup

Once PostgreSQL is installed and running, complete the following steps.

### Step 1 — Open the PostgreSQL prompt

```bash
psql postgres
```

On Linux, switch to the `postgres` system user first:

```bash
sudo -u postgres psql
```

### Step 2 — Create the database and user

```sql
-- Create the application database
CREATE DATABASE jobsdb;

-- Create the application user with a password
CREATE USER myuser WITH PASSWORD 'mypassword';

-- Grant full privileges on the database to the user
GRANT ALL PRIVILEGES ON DATABASE jobsdb TO myuser;
```

> **Note:** Replace `'mypassword'` with a strong password. Never use this default in staging or production.

### Step 3 — Verify the setup

```sql
-- List all databases (myapp_db should appear)
\l

-- List all users (myuser should appear)
\du

-- Exit the psql prompt
\q
```

---

## Environment Configuration

All credentials and configuration are managed through `.env` files. These files must **never** be committed to version control. Confirm `.env` is in your `.gitignore` before pushing any code.

### Backend `.env` (inside the `/backend` folder)

```env
# Database — SQLAlchemy reads this single connection string directly.
# Format: postgresql://USER:PASSWORD@HOST:PORT/DATABASE_NAME
# You do not need to list host, port, etc. separately — they are all encoded here.
DATABASE_URL=postgresql://myuser:mypassword@localhost:5432/myapp_db

# AI Providers
GEMINI_API_KEY=your_gemini_api_key_here
GROK_API_KEY=your_grok_api_key_here

# App
ENVIRONMENT=development
```

### Frontend `.env` (inside the `/frontend` folder)

```env
REACT_APP_API_URL=http://localhost:8000
```

> For production, `REACT_APP_API_URL` will point to your Railway backend URL instead of localhost.

---

## Connection Details

Use the following for local development:

| Parameter | Value |
|-----------|-------|
| Host | `localhost` |
| Port | `5432` |
| Database | `myapp_db` |
| User | `myuser` |
| Password | *(set during setup — see your `.env`)* |
| SQLAlchemy URL format | `postgresql://USER:PASSWORD@HOST:PORT/DB_NAME` |

For staging or production, credentials are provided separately by the database team.

---

## For Backend Developers (FastAPI + SQLAlchemy)

### Installation

```bash
cd backend
python -m venv venv

# Activate the virtual environment
# Linux / macOS:
source venv/bin/activate
# Windows:
venv\Scripts\activate

pip install fastapi uvicorn sqlalchemy psycopg2-binary pydantic python-dotenv
```

Save dependencies to a requirements file:

```bash
pip freeze > requirements.txt
```

---

### SQLAlchemy Database Connection

Create a `database.py` file in your backend:

```python
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Dependency — inject this into your route functions
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

---

### Defining Models with SQLAlchemy + Pydantic

These live in two separate files. SQLAlchemy models define what the database table looks like. Pydantic schemas define what the API accepts and returns — they are separate on purpose so your database structure and your API contract can evolve independently.

**`models.py` — maps to a database table:**

```python
from sqlalchemy import Column, Integer, String
from database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
```

**`schemas.py` — validates request and response data:**

```python
from pydantic import BaseModel

class UserCreate(BaseModel):
    name: str
    email: str

class UserResponse(BaseModel):
    id: int
    name: str
    email: str

    class Config:
        from_attributes = True  # Lets Pydantic read SQLAlchemy model objects directly
```

---

### Example FastAPI Route

```python
# main.py
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db, engine
import models, schemas

models.Base.metadata.create_all(bind=engine)  # Creates tables if they don't exist

app = FastAPI()

@app.post("/users/", response_model=schemas.UserResponse)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = models.User(name=user.name, email=user.email)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.get("/users/{user_id}", response_model=schemas.UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
```

### Configuring CORS (Required)

Your React app runs on port `3000` and your FastAPI backend runs on port `8000`. Browsers will block these requests by default unless you explicitly allow it. Add this to `main.py` before you define any routes — this will affect everyone on the team from day one:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://your-vercel-app.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

> Update `allow_origins` with your real Vercel URL once it is deployed. Never use `allow_origins=["*"]` in production.

---

### Running the Backend Locally

```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`.  
Interactive API docs (auto-generated by FastAPI) are at `http://localhost:8000/docs`.

---

### Database Migrations with Alembic

For schema changes over time, use Alembic instead of re-running `create_all`.

```bash
pip install alembic

# Initialize Alembic in the backend folder
alembic init alembic

# Generate a migration after changing a model
alembic revision --autogenerate -m "describe your change here"

# Apply the migration
alembic upgrade head
```

> Always run and verify migrations locally before applying to staging or production. Notify the database team before any schema changes.

---

## For Frontend Developers (React)

**The frontend never connects directly to the database.** All data access goes through the FastAPI backend over HTTP.

### Installation

```bash
cd frontend
npm install
```

### Making API Calls

Use the `REACT_APP_API_URL` environment variable so the base URL is environment-aware without touching your code:

```javascript
// Fetch a single user
const getUser = async (userId) => {
  const response = await fetch(`${process.env.REACT_APP_API_URL}/users/${userId}`);
  if (!response.ok) throw new Error('Failed to fetch user');
  return response.json();
};

// Create a new user
const createUser = async (userData) => {
  const response = await fetch(`${process.env.REACT_APP_API_URL}/users/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(userData),
  });
  if (!response.ok) throw new Error('Failed to create user');
  return response.json();
};
```

### Running the Frontend Locally

```bash
npm start
```

The app will be available at `http://localhost:3000`.

> If you see `500 Internal Server Error` or `connection refused` from the API, that is a backend or database issue — check with the backend team.

---

## AI Integration (Gemini API / Grok)

All AI API calls are handled exclusively on the backend. API keys must never be sent to or accessed by the frontend.

### Gemini API (Free Tier Available)

Get your free API key at: [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)

```bash
pip install google-generativeai
```

```python
import google.generativeai as genai
import os

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-pro")

def generate_response(prompt: str) -> str:
    response = model.generate_content(prompt)
    return response.text
```

### Grok

Get your API key from: [https://console.x.ai](https://console.x.ai)

Grok uses an OpenAI-compatible SDK:

```bash
pip install openai
```

```python
from openai import OpenAI
import os

client = OpenAI(
    api_key=os.getenv("GROK_API_KEY"),
    base_url="https://api.x.ai/v1"
)

def generate_response(prompt: str) -> str:
    response = client.chat.completions.create(
        model="grok-beta",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content
```

### Exposing AI via FastAPI

The route below calls whichever `generate_response` function you have defined above. Import it at the top of the file and wire it in — the frontend sends a prompt, the backend calls the AI provider, and the result comes back. The API key never leaves the server:

```python
from fastapi import APIRouter
from pydantic import BaseModel
from ai import generate_response  # import whichever provider you are using

router = APIRouter()

class PromptRequest(BaseModel):
    prompt: str

@router.post("/ai/generate")
def ai_generate(request: PromptRequest):
    result = generate_response(request.prompt)  # calls Gemini or Grok
    return {"response": result}
```

Include this router in `main.py`:

```python
from ai_routes import router as ai_router
app.include_router(ai_router)
```

---

## Deployment

### Frontend → Vercel

1. Push your project to GitHub.
2. Go to [https://vercel.com](https://vercel.com) and import your repository.
3. Set the **Root Directory** to `frontend`.
4. Add the following environment variable in the Vercel dashboard:
   - `REACT_APP_API_URL` → your Railway backend URL (e.g., `https://your-app.railway.app`)
5. Deploy. Vercel will auto-deploy on every push to `main`.

---

### Backend → Railway

1. Go to [https://railway.app](https://railway.app) and create a new project.
2. Connect your GitHub repository and point it to the `backend` folder.
3. Add the following environment variables in the Railway dashboard:
   - `DATABASE_URL` → your Supabase or Railway PostgreSQL connection string
   - `GEMINI_API_KEY`
   - `GROK_API_KEY`
   - `ENVIRONMENT=production`
4. Set the start command to:
   ```
   uvicorn main:app --host 0.0.0.0 --port $PORT
   ```
5. Railway will auto-deploy on every push to `main`.

---

### Database → Supabase or Firebase

**Supabase (Recommended — PostgreSQL-native):**

1. Create a project at [https://supabase.com](https://supabase.com).
2. Go to **Settings → Database** to find your connection string.
3. Use the **Session mode** connection string (port `5432`) as your `DATABASE_URL`.
4. Run your Alembic migrations pointed at the Supabase URL to initialize the schema.

---

**Firebase — Read Before Choosing:**

Firebase uses Firestore, which is a NoSQL document database — it is not PostgreSQL and is not compatible with SQLAlchemy or Alembic. If your team chooses Firebase over Supabase, the entire backend data layer changes: you would use the Firebase Admin SDK instead of SQLAlchemy, and none of the model/migration patterns in this guide would apply.

**Supabase is the recommended choice for this stack.** Only choose Firebase if the team has a specific reason and has aligned on replacing the ORM layer entirely.

---

## Common Issues & Troubleshooting

**`psql: error: connection to server on socket failed`**  
PostgreSQL is not running. Start it:
```bash
# Linux
sudo service postgresql start
# macOS
brew services start postgresql
```

**`FATAL: password authentication failed for user "myuser"`**  
The password in your `.env` does not match the database. Reset it in psql:
```sql
ALTER USER myuser WITH PASSWORD 'newpassword';
```

**`sqlalchemy.exc.OperationalError: could not connect to server`**  
Check that `DATABASE_URL` in your `.env` is correctly formatted:
```
postgresql://myuser:mypassword@localhost:5432/myapp_db
```

**`port 5432 already in use`**  
Another process is using the PostgreSQL port. Check with:
```bash
sudo lsof -i :5432
```
Stop the conflicting service or update the port in your `.env`.

**FastAPI `/docs` not loading**  
Ensure `uvicorn main:app --reload` is running and there are no import errors on startup. Check the terminal output for details.

---

## Security Guidelines

- Never commit `.env` files or hardcode credentials anywhere in source code.
- Never expose `GEMINI_API_KEY`, `GROK_API_KEY`, or `DATABASE_URL` to the frontend — all AI and DB calls go through the backend only.
- Production and staging credentials are managed by the database team — request access through the proper channel.
- Do not create additional database users or modify the schema without notifying the database team.
- Rotate passwords and API keys regularly, and immediately after any team member offboards.
- Use HTTPS in all production environments — Vercel and Railway handle this automatically.

---
