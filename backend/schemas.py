from datetime import date, datetime
from decimal import Decimal

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
    field_of_study: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    gpa: str | None = None


class EducationUpdate(BaseModel):
    highest_education: str | None = None
    degree: str | None = None
    school_or_college: str | None = None
    field_of_study: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    clear_end_date: bool = False
    gpa: str | None = None


class EducationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    education_id: int
    user_id: int
    highest_education: str
    degree: str
    school_or_college: str
    field_of_study: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    gpa: str | None = None


# --------------------------------------------------------------------------- #
#  Documents                                                                    #
# --------------------------------------------------------------------------- #


class DocumentCreate(BaseModel):
    user_id: int
    document_type: str
    document_location: str | None = None
    job_id: int | None = None
    document_name: str | None = None
    content: str | None = None


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    doc_id: int
    user_id: int
    document_name: str | None = None
    document_type: str
    document_location: str | None = None
    content: str | None = None
    job_id: int | None = None


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
#  Recruiter                                                                    #
# --------------------------------------------------------------------------- #


class RecruiterCreate(BaseModel):
    user_id: int
    company_id: int
    first_name: str
    last_name: str
    job_title: str | None = None


class RecruiterUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    job_title: str | None = None


class RecruiterResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    recruiter_id: int
    user_id: int
    company_id: int
    first_name: str
    last_name: str
    job_title: str | None = None


class RecruiterApplicationStatusUpdate(BaseModel):
    application_status: str
    outcome_notes: str | None = None


class RecruiterActivityCreate(BaseModel):
    event_type: str = "stage_change"
    notes: str | None = None


# --------------------------------------------------------------------------- #
#  Position                                                                     #
# --------------------------------------------------------------------------- #


class PositionCreate(BaseModel):
    company_id: int
    title: str
    listing_date: date
    location_type: str | None = None
    location: str | None = None
    salary: Decimal | None = None
    education_req: str | None = None
    experience_req: str | None = None
    description: str | None = None


class PositionUpdate(BaseModel):
    company_id: int | None = None
    title: str | None = None
    listing_date: date | None = None
    location_type: str | None = None
    location: str | None = None
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
    location_type: str | None = None
    location: str | None = None
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
    location_type: str | None = None
    location: str | None = None
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
    deadline: date | None = None
    recruiter_notes: str | None = None
    outcome_notes: str | None = None


class ApplicationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    job_id: int
    user_id: int
    position_id: int
    years_of_experience: int
    application_date: date
    application_status: str
    stage_changed_at: datetime | None = None
    deadline: date | None = None
    recruiter_notes: str | None = None
    outcome_notes: str | None = None


class JobActivityCreate(BaseModel):
    job_id: int
    stage: str
    event_type: str = "stage_change"
    notes: str | None = None


class JobActivityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    activity_id: int
    job_id: int
    stage: str
    changed_at: datetime
    event_type: str
    notes: str | None = None


# --------------------------------------------------------------------------- #
#  Interview                                                                    #
# --------------------------------------------------------------------------- #


class InterviewCreate(BaseModel):
    job_id: int
    round_type: str
    scheduled_at: datetime
    notes: str | None = None


class InterviewUpdate(BaseModel):
    round_type: str | None = None
    scheduled_at: datetime | None = None
    notes: str | None = None


class InterviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    interview_id: int
    job_id: int
    round_type: str
    scheduled_at: datetime
    notes: str | None = None


# --------------------------------------------------------------------------- #
#  Follow-Up                                                                    #
# --------------------------------------------------------------------------- #


class FollowUpCreate(BaseModel):
    job_id: int
    description: str
    due_date: date | None = None


class FollowUpUpdate(BaseModel):
    description: str | None = None
    due_date: date | None = None
    completed: bool | None = None


class FollowUpResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    followup_id: int
    job_id: int
    description: str
    due_date: date | None = None
    completed: bool


# --------------------------------------------------------------------------- #
#  Experience                                                                   #
# --------------------------------------------------------------------------- #


class ExperienceCreate(BaseModel):
    user_id: int
    company: str
    title: str
    start_date: date
    end_date: date | None = None
    description: str | None = None
    sort_order: int = 0


class ExperienceUpdate(BaseModel):
    company: str | None = None
    title: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    clear_end_date: bool = False
    description: str | None = None
    sort_order: int | None = None


class ExperienceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    experience_id: int
    user_id: int
    company: str
    title: str
    start_date: date
    end_date: date | None = None
    description: str | None = None
    sort_order: int


# --------------------------------------------------------------------------- #
#  Skills                                                                       #
# --------------------------------------------------------------------------- #


class SkillCreate(BaseModel):
    user_id: int
    name: str
    category: str | None = None
    proficiency: str | None = None
    sort_order: int = 0


class SkillUpdate(BaseModel):
    name: str | None = None
    category: str | None = None
    proficiency: str | None = None
    sort_order: int | None = None


class SkillResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    skill_id: int
    user_id: int
    name: str
    category: str | None = None
    proficiency: str | None = None
    sort_order: int


# --------------------------------------------------------------------------- #
#  Career Preferences                                                           #
# --------------------------------------------------------------------------- #


class CareerPreferencesCreate(BaseModel):
    user_id: int
    target_roles: str | None = None
    location_preferences: str | None = None
    work_mode: str | None = None
    salary_preference: str | None = None


class CareerPreferencesUpdate(BaseModel):
    target_roles: str | None = None
    location_preferences: str | None = None
    work_mode: str | None = None
    salary_preference: str | None = None


class CareerPreferencesResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    preference_id: int
    user_id: int
    target_roles: str | None = None
    location_preferences: str | None = None
    work_mode: str | None = None
    salary_preference: str | None = None
