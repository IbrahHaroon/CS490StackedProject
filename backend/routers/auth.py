from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()

@router.post("/register")
async def register():
    return {"message": "Register endpoint"}

@router.post("/login")
async def login():
    return {"message": "Login endpoint"}