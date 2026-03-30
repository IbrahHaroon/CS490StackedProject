from fastapi import APIRouter, Depends, HTTPException, status
from typing import Any, Dict, List
from pydantic import BaseModel

from dependencies.auth import get_current_user
from services.authorization import authorize_resource_owner

router = APIRouter()

# Mock data for demonstration
mock_jobs = [
    {"id": 1, "title": "Job 1", "description": "Desc 1", "user_id": "user-1"},
    {"id": 2, "title": "Job 2", "description": "Desc 2", "user_id": "user-1"},
    {"id": 3, "title": "Job 3", "description": "Desc 3", "user_id": "user-2"},
]


class JobCreate(BaseModel):
    title: str
    description: str


class JobUpdate(BaseModel):
    title: str
    description: str


@router.get("/jobs", response_model=List[Dict])
async def get_jobs(current_user: Any = Depends(get_current_user)):
    """Get all jobs for the current user."""
    user_id = str(current_user.id)
    return [job for job in mock_jobs if job["user_id"] == user_id]


@router.get("/jobs/{job_id}")
async def get_job(job_id: int, current_user: Any = Depends(get_current_user)):
    """
    Get a specific job if owned by the current user.
    """
    job = next((j for j in mock_jobs if j["id"] == job_id), None)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    authorize_resource_owner(job["user_id"], str(current_user.id))
    return job


@router.post("/jobs")
async def create_job(job_data: JobCreate, current_user: Any = Depends(get_current_user)):
    """
    Create a new job for the current user.
    """
    new_id = max(j["id"] for j in mock_jobs) + 1 if mock_jobs else 1
    new_job = {
        "id": new_id,
        "title": job_data.title,
        "description": job_data.description,
        "user_id": str(current_user.id),
    }
    mock_jobs.append(new_job)
    return new_job


@router.put("/jobs/{job_id}")
async def update_job(job_id: int, job_data: JobUpdate, current_user: Any = Depends(get_current_user)):
    """
    Update a job if owned by the current user.
    """
    job = next((j for j in mock_jobs if j["id"] == job_id), None)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    authorize_resource_owner(job["user_id"], str(current_user.id))
    job["title"] = job_data.title
    job["description"] = job_data.description
    return job


@router.delete("/jobs/{job_id}")
async def delete_job(job_id: int, current_user: Any = Depends(get_current_user)):
    """
    Delete a job if owned by the current user.
    """
    job = next((j for j in mock_jobs if j["id"] == job_id), None)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    authorize_resource_owner(job["user_id"], str(current_user.id))
    mock_jobs.remove(job)
    return {"message": "Job deleted successfully"}