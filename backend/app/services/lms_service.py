from datetime import datetime, timezone
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models.entities import Enrollment, Course, TelemetryEvent


def _evaluate_auto_promotion(enrollment: Enrollment, course: Course) -> bool:
    completion_pct = (enrollment.modules_completed / max(course.total_modules, 1)) * 100.0
    if (
        completion_pct >= 80.0
        and enrollment.avg_quiz_score >= 75.0
        and enrollment.crm_stage in ("Enrolled", "Screening")
    ):
        enrollment.crm_stage = "Interview_Ready"
        return True
    if completion_pct >= 40.0 and enrollment.crm_stage == "Enrolled":
        enrollment.crm_stage = "Screening"
        return True
    return False


def complete_module(db: Session, user_id: int, course_id: int, module_number: int) -> Enrollment:
    enrollment = (
        db.query(Enrollment)
        .filter(Enrollment.user_id == user_id, Enrollment.course_id == course_id)
        .first()
    )
    if not enrollment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enrollment not found")

    course = db.query(Course).filter(Course.course_id == course_id).first()
    if not course or module_number > course.total_modules:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid module number")

    if module_number > enrollment.modules_completed:
        enrollment.modules_completed = module_number

    enrollment.last_active = datetime.now(timezone.utc)
    promoted = _evaluate_auto_promotion(enrollment, course)

    db.add(
        TelemetryEvent(
            user_id=user_id,
            course_id=course_id,
            event_type="module_complete",
            metric_value=float(module_number),
        )
    )
    if promoted:
        db.add(
            TelemetryEvent(
                user_id=user_id,
                course_id=course_id,
                event_type="crm_stage_change",
                metric_value=1.0,
            )
        )

    db.commit()
    db.refresh(enrollment)
    return enrollment


def submit_quiz(db: Session, user_id: int, course_id: int, score: float) -> Enrollment:
    enrollment = (
        db.query(Enrollment)
        .filter(Enrollment.user_id == user_id, Enrollment.course_id == course_id)
        .first()
    )
    if not enrollment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enrollment not found")

    course = db.query(Course).filter(Course.course_id == course_id).first()
    total_points = enrollment.avg_quiz_score * enrollment.quizzes_taken + score
    enrollment.quizzes_taken += 1
    enrollment.avg_quiz_score = round(total_points / enrollment.quizzes_taken, 2)
    enrollment.last_active = datetime.now(timezone.utc)

    promoted = _evaluate_auto_promotion(enrollment, course)

    db.add(
        TelemetryEvent(
            user_id=user_id,
            course_id=course_id,
            event_type="quiz_submit",
            metric_value=score,
        )
    )
    if promoted:
        db.add(
            TelemetryEvent(
                user_id=user_id,
                course_id=course_id,
                event_type="crm_stage_change",
                metric_value=1.0,
            )
        )

    db.commit()
    db.refresh(enrollment)
    return enrollment
