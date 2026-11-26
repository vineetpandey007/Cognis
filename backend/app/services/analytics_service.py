import io
from datetime import datetime, timezone
import pandas as pd
from sqlalchemy.orm import Session, joinedload
from app.models.entities import Enrollment


def _build_dataframe(db: Session) -> pd.DataFrame:
    rows = (
        db.query(Enrollment)
        .options(joinedload(Enrollment.user), joinedload(Enrollment.course))
        .all()
    )
    records = []
    now = datetime.now(timezone.utc)
    for e in rows:
        if e.user.role != "student":
            continue
        last_act = e.last_active
        if last_act.tzinfo is None:
            last_act = last_act.replace(tzinfo=timezone.utc)
        days_inactive = (now - last_act).days
        completion_pct = round((e.modules_completed / max(e.course.total_modules, 1)) * 100.0, 1)
        is_at_risk = (days_inactive > 5 and completion_pct < 100.0) or (
            e.quizzes_taken > 0 and e.avg_quiz_score < 60.0
        )
        records.append(
            {
                "enrollment_id": e.enrollment_id,
                "student_name": e.user.full_name,
                "email": e.user.email,
                "cohort": e.user.cohort,
                "course_title": e.course.title,
                "domain": e.course.domain,
                "modules_completed": e.modules_completed,
                "total_modules": e.course.total_modules,
                "completion_pct": completion_pct,
                "avg_quiz_score": e.avg_quiz_score,
                "crm_stage": e.crm_stage,
                "days_inactive": days_inactive,
                "is_at_risk": is_at_risk,
            }
        )
    return pd.DataFrame(records)


def get_dashboard_summary(db: Session) -> dict:
    df = _build_dataframe(db)
    if df.empty:
        return {
            "total_learners": 0,
            "active_enrollments": 0,
            "avg_completion_rate": 0.0,
            "avg_quiz_score": 0.0,
            "interview_ready_count": 0,
            "placed_count": 0,
            "at_risk_count": 0,
            "cohort_breakdown": [],
            "stage_funnel": [],
            "at_risk_learners": [],
        }

    cohort_grp = (
        df.groupby("cohort", as_index=False)
        .agg(
            learners=("email", "nunique"),
            avg_completion=("completion_pct", "mean"),
            avg_score=("avg_quiz_score", "mean"),
        )
        .round(1)
    )

    stage_order = ["Enrolled", "Screening", "Interview_Ready", "Placed"]
    stage_counts = df["crm_stage"].value_counts().to_dict()
    stage_funnel = [{"stage": st, "count": int(stage_counts.get(st, 0))} for st in stage_order]

    at_risk_df = (
        df[df["is_at_risk"]]
        .sort_values(by=["days_inactive", "avg_quiz_score"], ascending=[False, True])
        .head(10)
    )

    return {
        "total_learners": int(df["email"].nunique()),
        "active_enrollments": int(len(df)),
        "avg_completion_rate": round(float(df["completion_pct"].mean()), 1),
        "avg_quiz_score": round(float(df["avg_quiz_score"].mean()), 1),
        "interview_ready_count": int((df["crm_stage"] == "Interview_Ready").sum()),
        "placed_count": int((df["crm_stage"] == "Placed").sum()),
        "at_risk_count": int(df["is_at_risk"].sum()),
        "cohort_breakdown": cohort_grp.to_dict(orient="records"),
        "stage_funnel": stage_funnel,
        "at_risk_learners": at_risk_df[
            ["student_name", "cohort", "course_title", "completion_pct", "avg_quiz_score", "days_inactive"]
        ].to_dict(orient="records"),
    }


def export_telemetry_csv(db: Session) -> str:
    df = _build_dataframe(db)
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    return buf.getvalue()
