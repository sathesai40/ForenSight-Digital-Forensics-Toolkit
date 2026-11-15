from datetime import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from app.schemas.case import CaseResponse
from app.schemas.audit_record import AuditRecordResponse


class DashboardStatsResponse(BaseModel):
    total_cases: int
    cases_by_status: Dict[str, int]
    cases_by_priority: Dict[str, int]
    total_evidence: int
    evidence_by_status: Dict[str, int]
    total_evidence_bytes: int
    total_events: int
    events_by_severity: Dict[str, int]
    events_by_type: Dict[str, int]
    recent_activity: List[AuditRecordResponse]
    recent_cases: List[CaseResponse]
    system_status: Dict[str, Any]
