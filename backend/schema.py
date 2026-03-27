from pydantic import BaseModel
from typing import Optional

# Job Schemas
class JobBase(BaseModel):
    title: str
    company: str
    description: Optional[str] = None

class JobCreate(JobBase):
    pass

class Job(JobBase):
    id: int
    owner_id: int
    class Config:
        from_attributes = True

# Auth Schemas
class UserCreate(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str