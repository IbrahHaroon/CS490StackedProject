from datetime import date, datetime
from decimal import Decimal
from enum import Enum

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
    phone_number: str | None = None
    summary: str | None = None


class ProfileUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    dob: date | None = None
    phone_number: str | None = None
    summary: str | None = None


class ProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    profile_id: int
    user_id: int
    first_name: str
    last_name: str
    dob: date
    phone_number: str | None
    summary: str | None


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
    salary: Decimal | None = None
    education_req: str | None = None
    experience_req: str | None = None
    description: str | None = None


class PositionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    position_id: int
    company_id: int
    title: str
    listing_date: date
    salary: Decimal | None
    education_req: str | None
    experience_req: str | None
    description: str | None


class PositionWithCompanyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    position_id: int
    company_id: int
    company_name: str
    title: str
    listing_date: date
    salary: Decimal | None
    education_req: str | None
    experience_req: str | None
    description: str | None


# --------------------------------------------------------------------------- #
#  Applied Jobs                                                                 #
# --------------------------------------------------------------------------- #


class ApplicationCreate(BaseModel):
    user_id: int
    position_id: int
    years_of_experience: int = 0


class ApplicationUpdate(BaseModel):
    application_status: str | None = None
    years_of_experience: int | None = None


class ApplicationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    job_id: int
    user_id: int
    position_id: int
    years_of_experience: int
    application_date: date
    application_status: str
    stage_changed_at: datetime | None = None


class JobActivityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    activity_id: int
    job_id: int
    stage: str
    changed_at: datetime


# --------------------------------------------------------------------------- #
#  Interview Schemas                                                           #
# --------------------------------------------------------------------------- #


class InterviewCreate(BaseModel):
    job_id: int
    round_type: str
    date_time: datetime
    notes: str | None = None


class InterviewUpdate(BaseModel):
    round_type: str | None = None
    date_time: datetime | None = None
    notes: str | None = None


class InterviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    interview_id: int
    job_id: int
    round_type: str
    date_time: datetime
    notes: str | None


# --------------------------------------------------------------------------- #
#  Outcome Schemas                                                             #
# --------------------------------------------------------------------------- #


class OutcomeState(str, Enum):
    """Controlled outcome state values."""

    APPLIED = "Applied"
    REJECTED = "Rejected"
    OFFER = "Offer"
    ACCEPTED = "Accepted"
    WITHDRAWN = "Withdrawn"


class OutcomeCreate(BaseModel):
    job_id: int
    outcome_state: OutcomeState
    outcome_notes: str | None = None


class OutcomeUpdate(BaseModel):
    outcome_state: OutcomeState | None = None
    outcome_notes: str | None = None


class OutcomeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    outcome_id: int
    job_id: int
    outcome_state: str
    outcome_notes: str | None


# --------------------------------------------------------------------------- #
#  Job Document Schemas                                                        #
# --------------------------------------------------------------------------- #


class JobDocumentCreate(BaseModel):
    job_id: int
    title: str
    content: str


class JobDocumentUpdate(BaseModel):
    title: str | None = None
    content: str | None = None


class JobDocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    job_document_id: int
    job_id: int
    title: str
    content: str
    created_at: datetime
    updated_at: datetime


# --------------------------------------------------------------------------- #
#  Job Sorting Query Params                                                    #
# --------------------------------------------------------------------------- #


class SortParam(str, Enum):
    """Valid sort fields."""

    LAST_ACTIVITY = "last_activity"
    DEADLINE = "deadline"
    COMPANY = "company"
    CREATED_AT = "created_at"


class OrderParam(str, Enum):
    """Valid sort orders."""

    ASC = "asc"
    DESC = "desc"
