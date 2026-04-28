import os
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Ensure the backend directory is in sys.path so `database`, `routers`, and
# `schemas` are always importable regardless of where the process is launched from.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.database import get_settings  # noqa: E402, I001
from logging_config import setup_logging  # noqa: E402
from middleware.error_handler import register_exception_handlers  # noqa: E402
from middleware.request_logger import RequestLoggingMiddleware  # noqa: E402
from routers import (  # noqa: E402
    auth,
    career_preferences,
    documents,
    education,
    experience,
    follow_ups,
    frontend_logs,
    interviews,
    jobs,
    jobs_sorter,
    library,
    profile,
    skills,
    users,
)

setup_logging()

_settings = get_settings()
_raw_origins = _settings.cors_origins
_allow_origins = (
    ["*"]
    if _raw_origins.strip() == "*"
    else [o.strip() for o in _raw_origins.split(",") if o.strip()]
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title="Candidate Job Tracker API", lifespan=lifespan)

register_exception_handlers(app)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)

# Include Routers
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(jobs.router, prefix="/jobs", tags=["Jobs"])
app.include_router(jobs_sorter.router, prefix="/dashboard", tags=["Dashboard"])
app.include_router(interviews.router, prefix="", tags=["Interviews"])
app.include_router(profile.router, prefix="/profile", tags=["Profile"])
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(education.router, prefix="/education", tags=["Education"])
app.include_router(documents.router, prefix="/documents", tags=["Documents"])
app.include_router(experience.router, prefix="/experience", tags=["Experience"])
app.include_router(skills.router, prefix="/skills", tags=["Skills"])
app.include_router(
    career_preferences.router, prefix="/career-preferences", tags=["Career Preferences"]
)
app.include_router(follow_ups.router, prefix="", tags=["Follow-Ups"])
app.include_router(library.router, prefix="/library", tags=["Library"])
app.include_router(frontend_logs.router, prefix="/logs", tags=["Logs"])


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "candidate-tracker"}


@app.get("/")
def root():
    return {"status": "Backend Online"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("index:app", host="127.0.0.1", port=8000, reload=True)
