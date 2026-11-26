from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.entities import User
from app.schemas.payloads import AnalyticsSummaryOut
from app.api.deps import require_analyst_admin
from app.services import analytics_service

router = APIRouter(prefix="/analytics", tags=["BI & Telemetry Analytics"])


@router.get("/summary", response_model=AnalyticsSummaryOut)
def dashboard_summary(
    _admin: User = Depends(require_analyst_admin),
    db: Session = Depends(get_db),
):
    return analytics_service.get_dashboard_summary(db)


@router.get("/export/csv")
def export_csv(
    _admin: User = Depends(require_analyst_admin),
    db: Session = Depends(get_db),
):
    csv_text = analytics_service.export_telemetry_csv(db)
    return Response(
        content=csv_text,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=cognis_cohort_telemetry.csv"},
    )
