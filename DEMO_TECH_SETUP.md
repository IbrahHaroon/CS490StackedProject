# Demo Day Technical Setup & Troubleshooting

## Quick Startup Script

**Run this the morning of demo to verify everything works:**

### Terminal 1 - Backend
```bash
cd d:\490Project\backend
python index.py
```

**Expected output:**
```
INFO:     Application startup complete [or similar]
INFO:     Uvicorn running on http://127.0.0.1:8000
```

**If error:** Check `.env` file has required vars: `DATABASE_URL`, `SECRET_KEY`, `OPENAI_API_KEY`

---

### Terminal 2 - Frontend
```bash
cd d:\490Project\frontend
npm run dev
```

**Expected output:**
```
VITE v4.x.x  ready in xxx ms

➜  Local:   http://localhost:5173 [or 3000]
```

**If error:** Run `npm install` first

---

## Quick Health Checks

### ✅ Backend API
```bash
curl http://127.0.0.1:8000/docs
```
If you see Swagger UI page → Backend is running ✓

### ✅ Database Connection
```bash
# From backend terminal, try:
cd backend
python -c "from database.database import SessionLocal; db = SessionLocal(); print('DB OK')"
```
If no error → Database is connected ✓

### ✅ Seed Data
```bash
# From backend terminal:
python -c "
from database.database import SessionLocal
from database.models.position import get_all_positions
db = SessionLocal()
jobs = get_all_positions(db)
print(f'Jobs in DB: {len(jobs)}')
"
```
Should show: `Jobs in DB: 8+` ✓

### ✅ Tests Pass
```bash
cd backend
pytest -v --tb=short 2>&1 | tail -20
```
Last lines should show: `passed` (not `failed`) ✓

---

## Common Errors & Fixes

### Error: ModuleNotFoundError: No module named 'X'
```bash
cd backend
pip install -r requirements.txt
```

### Error: PostgreSQL connection failed
- Verify PostgreSQL is running
- Check `DATABASE_URL` in `backend/.env`
- Default: `postgresql://user:postgres@localhost:5432/jobsdb`

### Error: OPENAI_API_KEY not configured
- Add to `backend/.env`: `OPENAI_API_KEY=sk-...`
- If missing, AI generation will show error (acceptable for demo with explanation)

### Frontend shows "Cannot connect to API"
- Verify backend is running on `http://127.0.0.1:8000`
- Check CORS is enabled in backend (should be by default)
- Try hard refresh: Ctrl+Shift+R

### Slow AI Generation
- First request to OpenAI may take 10-15 seconds
- Subsequent requests faster
- Demo this by saying "OpenAI is generating..." while waiting

---

## Demo Day Morning Checklist (30 minutes before)

```
INFRASTRUCTURE:
[ ] PostgreSQL running
[ ] Backend starts without errors
[ ] Frontend loads at http://localhost:3000 (or 5173)
[ ] Can access http://127.0.0.1:8000/docs

USER ACCOUNT:
[ ] Test user can login
[ ] Profile has 2+ experience, 2+ education, 2+ skills
[ ] Profile data shows on Profile page

SEED DATA:
[ ] Dashboard shows 8+ jobs
[ ] Jobs have various stages (Applied, Interview, Offer, Rejected)
[ ] Can search and filter jobs work
[ ] Try generating 1 AI resume to verify API key works

TESTS:
[ ] Run: pytest (all pass)
[ ] Duration: <10 seconds for full suite
[ ] Show output to verify

DEMO EQUIPMENT:
[ ] Projector/screen connected
[ ] Laptop screen resolution is 1920x1080+
[ ] Can share screen or window
[ ] Speaker volume works
[ ] Backup has copy of run sheet

BACKUP FILES READY:
[ ] Credentials text file with URLs and passwords
[ ] This troubleshooting file (for reference)
[ ] DEMO_RUN_SHEET.md (printed or on screen)
```

---

## During Demo - Quick Fixes

**If something breaks mid-demo:**

1. **Job Detail won't load:** Refresh page (F5), click another job
2. **AI generation hangs:** Say "Taking longer than expected" and move to next part while it loads in background
3. **Dashboard metrics wrong:** Go back to Dashboard, say "Looks like we need to refresh" and do hard refresh
4. **Database connection lost:** Restart backend (Ctrl+C, python index.py)
5. **Button doesn't work:** Try clicking again or reload page—don't sit there waiting

**General rule:** Keep talking, don't go silent. Have backup ready to take over if needed.

---

## Post-Demo

- [ ] Push any final code changes
- [ ] Save screenshots of successful demo for portfolio
- [ ] Note any bugs for Sprint 3
- [ ] Close databases/servers properly
- [ ] Thank your teammates and instructors

---

## Resources

- **Schema/DB:** `docs/DatabaseOverview.md` or `docs/ErDiagram.md`
- **API Endpoints:** `http://127.0.0.1:8000/docs`
- **Tests:** `backend/tests/` for examples
- **PR:** Check GitHub for Sprint 2 changes

**Good luck! You're ready! 🚀**
