from __future__ import annotations
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr

# --------------------------------------------------------------------------- #
#  Auth                                                                         #
# --------------------------------------------------------------------------- #


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


# --------------------------------------------------------------------------- #
#  User                                                                         #
# --------------------------------------------------------------------------- #


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    email: str


# --------------------------------------------------------------------------- #
#  Address  (used as a nested input inside Profile, Education, and Company)    #
# --------------------------------------------------------------------------- #


class AddressCreate(BaseModel):
    address: str
    state: str
    zip_code: int


class AddressResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    address_id: int
    address: str
    state: str
    zip_code: int


# --------------------------------------------------------------------------- #
#  Profile                                                                      #
# --------------------------------------------------------------------------- #


class ProfileCreate(BaseModel):
    user_id: int
    first_name: str
    last_name: str
    dob: date
    address: AddressCreate
    phone_number: Optional[str] = None
    summary: Optional[str] = None


class ProfileUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    dob: Optional[date] = None
    phone_number: Optional[str] = None
    summary: Optional[str] = None


class ProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    profile_id: int
    user_id: int
    first_name: str
    last_name: str
    dob: date
    phone_number: Optional[str]
    summary: Optional[str]


# --------------------------------------------------------------------------- #
#  Education                                                                    #
# --------------------------------------------------------------------------- #


class EducationCreate(BaseModel):
    user_id: int
    highest_education: str
    degree: str
    school_or_college: str
    address: AddressCreate


class EducationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    education_id: int
    user_id: int
    highest_education: str
    degree: str
    school_or_college: str


# --------------------------------------------------------------------------- #
#  Documents                                                                    #
# --------------------------------------------------------------------------- #


class DocumentCreate(BaseModel):
    user_id: int
    document_type: str
    document_location: str


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    doc_id: int
    user_id: int
    document_type: str
    document_location: str


# --------------------------------------------------------------------------- #
#  Company                                                                      #
# --------------------------------------------------------------------------- #


class CompanyCreate(BaseModel):
    name: str
    address: AddressCreate


class CompanyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    company_id: int
    name: str


# --------------------------------------------------------------------------- #
#  Position                                                                     #
# --------------------------------------------------------------------------- #


class PositionCreate(BaseModel):
    company_id: int
    title: str
    listing_date: date
    salary: Optional[Decimal] = None
    education_req: Optional[str] = None
    experience_req: Optional[str] = None
    description: Optional[str] = None


class PositionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    position_id: int
    company_id: int
    title: str
    listing_date: date
    salary: Optional[Decimal]
    education_req: Optional[str]
    experience_req: Optional[str]
    description: Optional[str]


# --------------------------------------------------------------------------- #
#  Applied Jobs                                                                 #
# --------------------------------------------------------------------------- #


class ApplicationCreate(BaseModel):
    user_id: int
    position_id: int
    years_of_experience: int


class ApplicationUpdate(BaseModel):
    application_status: Optional[str] = None
    years_of_experience: Optional[int] = None


class ApplicationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    job_id: int
    user_id: int
    position_id: int
    years_of_experience: int
    application_date: date
    application_status: str
    stage_changed_at: Optional[datetime] = None


class JobActivityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    activity_id: int
    job_id: int
    stage: str
    changed_at: datetime
