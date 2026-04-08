from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict

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
