from __future__ import annotations

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


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


# --------------------------------------------------------------------------- #
#  User                                                                         #
# --------------------------------------------------------------------------- #


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    email: str


# --------------------------------------------------------------------------- #
#  Profile  (address inlined)                                                   #
# --------------------------------------------------------------------------- #


class ProfileCreate(BaseModel):
    user_id: int
    first_name: str
    last_name: str
    dob: date
    phone_number: str | None = None
    summary: str | None = None
    address_line: str | None = None
    city: str | None = None
    state: str | None = None
    zip_code: str | None = None
    country: str | None = None


class ProfileUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    dob: date | None = None
    phone_number: str | None = None
    summary: str | None = None
    address_line: str | None = None
    city: str | None = None
    state: str | None = None
    zip_code: str | None = None
    country: str | None = None


class ProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    profile_id: int
    user_id: int
    first_name: str
    last_name: str
    dob: date
    phone_number: str | None
    summary: str | None
    address_line: str | None = None
    city: str | None = None
    state: str | None = None
    zip_code: str | None = None
    country: str | None = None


# --------------------------------------------------------------------------- #
#  Education                                                                    #
# --------------------------------------------------------------------------- #


class EducationCreate(BaseModel):
    user_id: int
    school: str
    degree: str
    field_of_study: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    gpa: str | None = None
    school_location: str | None = None
    sort_order: int = 0


class EducationUpdate(BaseModel):
    school: str | None = None
    degree: str | None = None
    field_of_study: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    clear_end_date: bool = False
    gpa: str | None = None
    school_location: str | None = None
    sort_order: int | None = None


class EducationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    education_id: int
    user_id: int
    school: str
    degree: str
    field_of_study: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    gpa: str | None = None
    school_location: str | None = None
    sort_order: int


# --------------------------------------------------------------------------- #
#  Job  (replaces Application/Position/Company)                                 #
# --------------------------------------------------------------------------- #


class JobCreate(BaseModel):
    title: str
    company_name: str
    location: str | None = None
    source_url: str | None = None
    description: str | None = None
    stage: str = "Interested"
    application_date: date | None = None
    deadline: date | None = None
    priority: str | None = None
    salary: Decimal | None = None
    years_of_experience: int | None = None
    notes: str | None = None


class CompanyResearchRequest(BaseModel):
    context: str | None = None


class JobUpdate(BaseModel):
    title: str | None = None
    company_name: str | None = None
    location: str | None = None
    source_url: str | None = None
    description: str | None = None
    stage: str | None = None
    application_date: date | None = None
    deadline: date | None = None
    priority: str | None = None
    salary: Decimal | None = None
    years_of_experience: int | None = None
    notes: str | None = None
    company_research_notes: str | None = None
    outcome_notes: str | None = None


class JobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    job_id: int
    user_id: int
    title: str
    company_name: str
    location: str | None
    source_url: str | None
    description: str | None
    stage: str
    stage_changed_at: datetime | None
    application_date: date | None
    deadline: date | None
    priority: str | None
    salary: Decimal | None
    years_of_experience: int | None
    notes: str | None
    company_research_notes: str | None
    outcome_notes: str | None
    created_at: datetime
    archived_at: datetime | None


# --------------------------------------------------------------------------- #
#  Job Activity                                                                 #
# --------------------------------------------------------------------------- #


class JobActivityCreate(BaseModel):
    job_id: int
    event_type: str = "stage_change"
    from_stage: str | None = None
    to_stage: str | None = None
    notes: str | None = None


class JobActivityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    activity_id: int
    job_id: int
    event_type: str
    from_stage: str | None
    to_stage: str | None
    notes: str | None
    occurred_at: datetime


# --------------------------------------------------------------------------- #
#  Interview                                                                    #
# --------------------------------------------------------------------------- #


class InterviewCreate(BaseModel):
    round_type: str
    scheduled_at: datetime
    interviewer: str | None = None
    mode: str | None = None
    prep_notes: str | None = None
    notes: str | None = None


class InterviewUpdate(BaseModel):
    round_type: str | None = None
    scheduled_at: datetime | None = None
    interviewer: str | None = None
    mode: str | None = None
    prep_notes: str | None = None
    notes: str | None = None


class InterviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    interview_id: int
    job_id: int
    round_type: str
    scheduled_at: datetime
    interviewer: str | None
    mode: str | None
    prep_notes: str | None
    notes: str | None


# --------------------------------------------------------------------------- #
#  Follow-Up                                                                    #
# --------------------------------------------------------------------------- #


class FollowUpCreate(BaseModel):
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
#  Document  /  DocumentVersion  /  DocumentTag  /  JobDocumentLink             #
# --------------------------------------------------------------------------- #


class DocumentCreate(BaseModel):
    title: str
    document_type: str
    status: str | None = "Draft"
    # Initial version content (one of the two should be supplied for non-empty docs)
    storage_location: str | None = None
    content: str | None = None
    source: str | None = None  # 'upload' | 'ai' | 'manual'
    # Optional initial tag set
    tags: list[str] | None = None
    # Optional initial job link
    job_id: int | None = None
    role: str | None = None  # link role: 'resume' | 'cover_letter' | etc.


class DocumentUpdate(BaseModel):
    title: str | None = None
    document_type: str | None = None
    status: str | None = None
    is_deleted: bool | None = None  # archive/restore via this flag


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    document_id: int
    user_id: int
    title: str
    document_type: str
    status: str
    current_version_id: int | None
    is_deleted: bool
    created_at: datetime
    updated_at: datetime


class DocumentVersionCreate(BaseModel):
    storage_location: str | None = None
    content: str | None = None
    source: str | None = None


class DocumentVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    version_id: int
    document_id: int
    version_number: int
    storage_location: str | None
    content: str | None
    source: str | None
    created_at: datetime


class DocumentTagCreate(BaseModel):
    label: str


class DocumentTagResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    tag_id: int
    document_id: int
    label: str


class JobDocumentLinkCreate(BaseModel):
    job_id: int
    version_id: int
    role: str | None = None


class JobDocumentLinkResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    link_id: int
    job_id: int
    version_id: int
    role: str | None
    linked_at: datetime


# --------------------------------------------------------------------------- #
#  Experience                                                                   #
# --------------------------------------------------------------------------- #


class ExperienceCreate(BaseModel):
    user_id: int
    company: str
    title: str
    location: str | None = None
    start_date: date
    end_date: date | None = None
    description: str | None = None
    sort_order: int = 0


class ExperienceUpdate(BaseModel):
    company: str | None = None
    title: str | None = None
    location: str | None = None
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
    location: str | None = None
    start_date: date
    end_date: date | None = None
    description: str | None = None
    sort_order: int


# --------------------------------------------------------------------------- #
#  Skill                                                                        #
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


# --------------------------------------------------------------------------- #
#  Dashboard Metrics                                                            #
# --------------------------------------------------------------------------- #


class DashboardMetricsResponse(BaseModel):
    total_applications: int
    stage_counts: dict[str, int]
    outcome_counts: dict[str, int]
    response_rate: float


class AnalyticsResponse(BaseModel):
    conversion_funnel: dict[str, float]
    overall_conversion_rate: float
    avg_days_in_stage: dict[str, float]
