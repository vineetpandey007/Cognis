from datetime import datetime
from typing import Literal, List
from pydantic import BaseModel, EmailStr, Field, field_validator
from app.core.mailer import validate_strong_password


class UserRegister(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    role: Literal["student", "analyst_admin"] = "student"
    cohort: str = Field(default="COG-DA-2026-Q4", min_length=2, max_length=64)

    @field_validator("password")
    @classmethod
    def check_password_strength(cls, v: str) -> str:
        return validate_strong_password(v)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class OtpRequestPayload(BaseModel):
    email: EmailStr
    purpose: Literal["verify_email", "login", "reset_password"]


class VerifyOtpPayload(BaseModel):
    email: EmailStr
    otp_code: str = Field(..., min_length=6, max_length=6, pattern=r"^\d{6}$")


class ResetPasswordPayload(BaseModel):
    email: EmailStr
    otp_code: str = Field(..., min_length=6, max_length=6, pattern=r"^\d{6}$")
    new_password: str = Field(..., min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def check_new_password_strength(cls, v: str) -> str:
        return validate_strong_password(v)


class OtpDispatchResponse(BaseModel):
    message: str
    email: str
    delivery_mode: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    full_name: str
    user_id: int


class UserOut(BaseModel):
    user_id: int
    full_name: str
    email: EmailStr
    role: str
    cohort: str
    is_verified: bool

    model_config = {"from_attributes": True}


class ModuleProgressRequest(BaseModel):
    course_id: int
    module_number: int = Field(..., ge=1, le=50)


class QuizSubmitRequest(BaseModel):
    course_id: int
    score: float = Field(..., ge=0.0, le=100.0)


class EnrollmentOut(BaseModel):
    enrollment_id: int
    user_id: int
    course_id: int
    course_title: str
    domain: str
    total_modules: int
    modules_completed: int
    completion_pct: float
    avg_quiz_score: float
    crm_stage: str
    last_active: datetime


class CrmStageUpdateRequest(BaseModel):
    new_stage: Literal["Enrolled", "Screening", "Interview_Ready", "Placed"]


class CrmCandidateOut(BaseModel):
    enrollment_id: int
    student_name: str
    email: str
    cohort: str
    course_title: str
    completion_pct: float
    avg_quiz_score: float
    crm_stage: str
    last_active: datetime


class AnalyticsSummaryOut(BaseModel):
    total_learners: int
    active_enrollments: int
    avg_completion_rate: float
    avg_quiz_score: float
    interview_ready_count: int
    placed_count: int
    at_risk_count: int
    cohort_breakdown: List[dict]
    stage_funnel: List[dict]
    at_risk_learners: List[dict]
