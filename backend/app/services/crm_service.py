from typing import List
from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload
from app.models.entities import Enrollment, AuditLog, TelemetryEvent


def list_crm_candidates(db: Session) -> List[dict]:
    rows = (
        db.query(Enrollment)
        .options(joinedload(Enrollment.user), joinedload(Enrollment.course))
        .all()
    )
    result = []
    for e in rows:
        if e.user.role != "student":
            continue
        pct = round((e.modules_completed / max(e.course.total_modules, 1)) * 100.0, 1)
        result.append(
            {
                "enrollment_id": e.enrollment_id,
                "student_name": e.user.full_name,
                "email": e.user.email,
                "cohort": e.user.cohort,
                "course_title": e.course.title,
                "completion_pct": pct,
                "avg_quiz_score": e.avg_quiz_score,
                "crm_stage": e.crm_stage,
                "last_active": e.last_active,
            }
        )
    return result


def update_candidate_stage(
    db: Session, enrollment_id: int, new_stage: str, actor_user_id: int
) -> Enrollment:
    enrollment = db.query(Enrollment).filter(Enrollment.enrollment_id == enrollment_id).first()
    if not enrollment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enrollment record not found")

    old_stage = enrollment.crm_stage
    enrollment.crm_stage = new_stage

    db.add(
        AuditLog(
            actor_user_id=actor_user_id,
            target_enrollment_id=enrollment_id,
            action="CRM_STAGE_UPDATE",
            old_value=old_stage,
            new_value=new_stage,
        )
    )
    db.add(
        TelemetryEvent(
            user_id=enrollment.user_id,
            course_id=enrollment.course_id,
            event_type="crm_stage_change",
            metric_value=1.0,
        )
    )
    db.commit()
    db.refresh(enrollment)
    return enrollment
