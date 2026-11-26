from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.entities import User
from app.schemas.payloads import CrmCandidateOut, CrmStageUpdateRequest
from app.api.deps import require_analyst_admin
from app.services import crm_service

router = APIRouter(prefix="/crm", tags=["CRM Placement Pipeline"])


@router.get("/candidates", response_model=List[CrmCandidateOut])
def get_candidates(
    _admin: User = Depends(require_analyst_admin),
    db: Session = Depends(get_db),
):
    return crm_service.list_crm_candidates(db)


@router.patch("/candidates/{enrollment_id}/stage")
def patch_candidate_stage(
    enrollment_id: int,
    payload: CrmStageUpdateRequest,
    admin: User = Depends(require_analyst_admin),
    db: Session = Depends(get_db),
):
    updated = crm_service.update_candidate_stage(db, enrollment_id, payload.new_stage, admin.user_id)
    return {"enrollment_id": updated.enrollment_id, "crm_stage": updated.crm_stage}
