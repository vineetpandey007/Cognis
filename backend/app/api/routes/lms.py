from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload
from app.core.database import get_db
from app.models.entities import User, Enrollment
from app.schemas.payloads import ModuleProgressRequest, QuizSubmitRequest, EnrollmentOut
from app.api.deps import get_current_user
from app.services import lms_service

router = APIRouter(prefix="/lms", tags=["LMS Portal"])


def _serialize_enrollment(e: Enrollment) -> EnrollmentOut:
    pct = round((e.modules_completed / max(e.course.total_modules, 1)) * 100.0, 1)
    return EnrollmentOut(
        enrollment_id=e.enrollment_id,
        user_id=e.user_id,
        course_id=e.course_id,
        course_title=e.course.title,
        domain=e.course.domain,
        total_modules=e.course.total_modules,
        modules_completed=e.modules_completed,
        completion_pct=pct,
        avg_quiz_score=e.avg_quiz_score,
        crm_stage=e.crm_stage,
        last_active=e.last_active,
    )


@router.get("/my-courses", response_model=List[EnrollmentOut])
def my_courses(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = (
        db.query(Enrollment)
        .options(joinedload(Enrollment.course))
        .filter(Enrollment.user_id == current_user.user_id)
        .all()
    )
    return [_serialize_enrollment(r) for r in rows]


@router.post("/complete-module", response_model=EnrollmentOut)
def mark_module_complete(
    payload: ModuleProgressRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    enrollment = lms_service.complete_module(db, current_user.user_id, payload.course_id, payload.module_number)
    return _serialize_enrollment(enrollment)


@router.post("/submit-quiz", response_model=EnrollmentOut)
def submit_quiz(
    payload: QuizSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    enrollment = lms_service.submit_quiz(db, current_user.user_id, payload.course_id, payload.score)
    return _serialize_enrollment(enrollment)
