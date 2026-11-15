from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.audit_record import AuditRecord
from app.schemas.audit_record import AuditRecordResponse

router = APIRouter(prefix="/audit", tags=["Audit Trail"])


@router.get("", response_model=List[AuditRecordResponse])
def get_audit_trail(
    case_id: Optional[int] = Query(None, description="Filter audit logs by case ID"),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> List[AuditRecordResponse]:
    """Retrieve immutable audit log records."""
    query = db.query(AuditRecord)
    if case_id is not None:
        query = query.filter(AuditRecord.case_id == case_id)
    records = query.order_by(AuditRecord.timestamp.desc()).limit(limit).all()
    return [AuditRecordResponse.model_validate(r) for r in records]
