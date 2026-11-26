from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from app.core.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(120), nullable=False)
    email = Column(String(160), unique=True, index=True, nullable=False)
    password_hash = Column(String(256), nullable=False)
    role = Column(String(32), nullable=False, default="student")
    cohort = Column(String(64), nullable=False, default="COG-DA-2026-Q4")
    is_verified = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    enrollments = relationship("Enrollment", back_populates="user", cascade="all, delete-orphan")


class OtpCode(Base):
    __tablename__ = "otp_codes"

    otp_id = Column(Integer, primary_key=True, index=True)
    email = Column(String(160), index=True, nullable=False)
    code_hash = Column(String(128), nullable=False)
    purpose = Column(String(32), index=True, nullable=False)
    attempts = Column(Integer, nullable=False, default=0)
    is_used = Column(Boolean, nullable=False, default=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)


class Course(Base):
    __tablename__ = "courses"

    course_id = Column(Integer, primary_key=True, index=True)
    title = Column(String(160), nullable=False)
    domain = Column(String(80), nullable=False)
    description = Column(Text, nullable=True)
    total_modules = Column(Integer, nullable=False, default=6)

    enrollments = relationship("Enrollment", back_populates="course", cascade="all, delete-orphan")


class Enrollment(Base):
    __tablename__ = "enrollments"

    enrollment_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False, index=True)
    course_id = Column(Integer, ForeignKey("courses.course_id"), nullable=False, index=True)
    modules_completed = Column(Integer, nullable=False, default=0)
    quizzes_taken = Column(Integer, nullable=False, default=0)
    avg_quiz_score = Column(Float, nullable=False, default=0.0)
    crm_stage = Column(String(32), nullable=False, default="Enrolled")
    last_active = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    user = relationship("User", back_populates="enrollments")
    course = relationship("Course", back_populates="enrollments")


class TelemetryEvent(Base):
    __tablename__ = "telemetry_events"

    event_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False, index=True)
    course_id = Column(Integer, ForeignKey("courses.course_id"), nullable=False, index=True)
    event_type = Column(String(48), nullable=False, index=True)
    metric_value = Column(Float, nullable=True)
    recorded_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    audit_id = Column(Integer, primary_key=True, index=True)
    actor_user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    target_enrollment_id = Column(Integer, ForeignKey("enrollments.enrollment_id"), nullable=False)
    action = Column(String(64), nullable=False)
    old_value = Column(String(64), nullable=True)
    new_value = Column(String(64), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
