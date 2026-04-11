# Demo Day Setup Guide

Quick-start guide for getting the app running on the presentation machine.
Estimated setup time: **under 10 minutes**.

---

## Prerequisites

Make sure the machine has these installed before demo day:

| Tool | Min Version | Check Command |
|------|-------------|---------------|
| Python | 3.11+ | `python3 --version` |
| Node.js | 18+ | `node --version` |
| Git | any | `git --version` |

**macOS — install missing tools via Homebrew:**
```bash
brew install python@3.11 node git
```

**Linux (Ubuntu) — install missing tools:**
```bash
sudo apt update && sudo apt install python3 python3-pip python3-venv nodejs npm git
```

---

## Step 1 — Clone the Repo

```bash
git clone https://github.com/IbrahHaroon/CS490StackedProject.git
cd CS490StackedProject
```

---

## Step 2 — Set Up the Backend

```bash
cd backend

# Create and activate virtual environment
python3 -m venv venv

# macOS / Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

## Step 3 — Configure Environment Variables

Create a `.env` file inside the `backend/` folder:

```bash
# Still inside backend/
cp ../.env.example .env
```

Then open `.env` and fill in the real values (get these from the shared team account):

```env
DATABASE_URL=postgresql://postgres:your-password@db.your-project-id.supabase.co:5432/postgres
SECRET_KEY=your-secret-key-for-jwt
GEMINI_API_KEY=your-gemini-api-key
CORS_ORIGINS=http://localhost:5173
BACKEND_URL=http://localhost:8000
```

> The database is hosted on Supabase — no local PostgreSQL install needed.

---

## Step 4 — Run the Backend

```bash
# Make sure venv is still active (you should see (venv) in your terminal)
cd backend
uvicorn index:app --reload --host 0.0.0.0 --port 8000
```

Verify it works — open your browser and go to:
```
http://localhost:8000/docs
```

You should see the FastAPI interactive docs page. If you do, the backend is running correctly.

---

## Step 5 — Set Up the Frontend

Open a **new terminal tab/window** and run:

```bash
cd CS490StackedProject/frontend
npm ci
```

Create a `.env` file inside `frontend/`:

```bash
echo "VITE_API_URL=http://localhost:8000" > .env
```

---

## Step 6 — Run the Frontend

```bash
# Still inside frontend/
npm run dev
```

Open your browser and go to:
```
http://localhost:5173
```

You should see the app running.

---

## Step 7 — Verify Everything Works

Run through this quick checklist before the demo starts:

- [ ] Backend running at `http://localhost:8000`
- [ ] Frontend running at `http://localhost:5173`
- [ ] Can register a new user (User A)
- [ ] Can login as User A
- [ ] Dashboard loads and shows job cards
- [ ] Can create a new job
- [ ] Can update a job's pipeline stage
- [ ] Profile page loads and saves
- [ ] Can register a second user (User B)
- [ ] User B cannot access User A's data (expect 403)

---

## Demo Accounts

Have these ready in a text file before the demo:

| Account | Email | Password |
|---------|-------|----------|
| User A | `usera@demo.com` | *(set during seed)* |
| User B | `userb@demo.com` | *(set during seed)* |

---

## Troubleshooting

**Backend won't start — `ModuleNotFoundError`**
```bash
# Make sure venv is activated
source backend/venv/bin/activate
pip install -r backend/requirements.txt
```

**Frontend shows blank page or API errors**
- Check that backend is running on port 8000
- Check that `VITE_API_URL=http://localhost:8000` is in `frontend/.env`

**Database connection error**
- Check `DATABASE_URL` in `backend/.env` matches the Supabase credentials
- Verify internet connection — the database is cloud-hosted

**Port already in use**
```bash
# Find and kill whatever is on port 8000
lsof -ti:8000 | xargs kill -9

# Find and kill whatever is on port 5173
lsof -ti:5173 | xargs kill -9
```

**macOS — `python3` not found**
```bash
brew install python@3.11
```

**macOS — `npm` not found**
```bash
brew install node
```
