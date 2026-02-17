"""
Pydantic Schemas.

Request/response models for FastAPI endpoints.
"""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from datetime import datetime


# Request Models

class AddressSchema(BaseModel):
    """Address information."""
    street: str
    city: str
    state: str
    zip: str


class ApplicantSchema(BaseModel):
    """Applicant personal information."""
    first_name: str
    last_name: str
    email: str
    phone: str
    ssn: str
    date_of_birth: str = Field(..., description="YYYY-MM-DD format")
    current_address: AddressSchema


class EmploymentSchema(BaseModel):
    """Employment information."""
    employer_name: str
    job_title: str
    employment_status: str = Field(..., description="full-time, part-time, self-employed")
    annual_income: float
    years_employed: float
    employer_phone: str


class RentalHistorySchema(BaseModel):
    """Rental history information."""
    current_landlord: Optional[str] = None
    current_landlord_phone: Optional[str] = None
    monthly_rent: Optional[float] = None
    years_at_current: Optional[float] = None
    reason_for_leaving: Optional[str] = None


class AdditionalInfoSchema(BaseModel):
    """Additional applicant information."""
    pets: bool = False
    smoker: bool = False
    bankruptcy_history: bool = False
    eviction_history: bool = False


class ApplicationSubmitRequest(BaseModel):
    """Application submission request."""
    applicant: ApplicantSchema
    employment: EmploymentSchema
    rental_history: Optional[RentalHistorySchema] = None
    additional_info: Optional[AdditionalInfoSchema] = None


class ScreeningRequest(BaseModel):
    """Screening execution request."""
    application_id: str
    options: Optional[Dict[str, Any]] = Field(default_factory=dict)


# Response Models

class AgentResultSchema(BaseModel):
    """Individual agent result."""
    agent_name: str
    status: str
    data: Dict[str, Any]
    execution_time_ms: Optional[float] = None


class ScreeningResultSchema(BaseModel):
    """Complete screening result."""
    application_id: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    agent_results: List[AgentResultSchema]
    final_decision: Optional[Dict[str, Any]] = None


class ApplicationResponse(BaseModel):
    """Application submission response."""
    application_id: str
    status: str
    message: str
    created_at: datetime


class ScreeningResponse(BaseModel):
    """Screening execution response."""
    application_id: str
    status: str
    message: str
    screening_result: Optional[ScreeningResultSchema] = None


class ErrorResponse(BaseModel):
    """Error response."""
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
