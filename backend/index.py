import os
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Ensure the backend directory is in sys.path so `database`, `routers`, and
# `schemas` are always importable regardless of where the process is launched from.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# from database import Base, engine
from routers import (
    auth,
    career_preferences,
    company,
    documents,
    education,
    experience,
    follow_ups,
    interviews,
    job_documents,
    jobs,
    jobs_sorter,
    outcomes,
    profile,
    recruiter,
    skills,
    users,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create tables if they don't exist
    # Base.metadata.create_all(bind=engine)
    yield
    # Shutdown logic goes here if needed


app = FastAPI(title="ATS API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(jobs.router, prefix="/jobs", tags=["Jobs"])
app.include_router(jobs_sorter.router, prefix="/dashboard", tags=["Dashboard"])
app.include_router(interviews.router, prefix="/jobs", tags=["Interviews"])
app.include_router(outcomes.router, prefix="/jobs", tags=["Outcomes"])
app.include_router(job_documents.router, prefix="/jobs", tags=["Job Documents"])
app.include_router(profile.router, prefix="/profile", tags=["Profile"])
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(education.router, prefix="/education", tags=["Education"])
app.include_router(documents.router, prefix="/documents", tags=["Documents"])
app.include_router(company.router, prefix="/company", tags=["Company"])
app.include_router(recruiter.router, prefix="/recruiter", tags=["Recruiter"])
app.include_router(experience.router, prefix="/experience", tags=["Experience"])
app.include_router(skills.router, prefix="/skills", tags=["Skills"])
app.include_router(
    career_preferences.router, prefix="/career-preferences", tags=["Career Preferences"]
)
app.include_router(follow_ups.router, prefix="", tags=["Follow-Ups"])


@app.get("/")
def root():
    return {"status": "Backend Online"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("index:app", host="127.0.0.1", port=8000, reload=True)
