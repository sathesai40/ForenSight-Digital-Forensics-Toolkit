from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel


class TimelineItemResponse(BaseModel):
    id: str
    timestamp: datetime
    category: str  # EVIDENCE_ACQUISITION, SECURITY_EVENT, INTEGRITY_CHECK, AUDIT_ACTION
    title: str
    severity: str  # INFO, LOW, MEDIUM, HIGH, CRITICAL
    description: str
    source: Optional[str] = None
    metadata: Dict[str, Any] = {}


class CaseTimelineResponse(BaseModel):
    case_id: int
    case_number: str
    total_events: int
    timeline: List[TimelineItemResponse]
