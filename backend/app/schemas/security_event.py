from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class SecurityEventBase(BaseModel):
    case_id: int
    evidence_id: Optional[int] = None
    timestamp: datetime
    event_type: str
    severity: str = "INFO"
    source_ip: Optional[str] = None
    destination_ip: Optional[str] = None
    user_account: Optional[str] = None
    description: str
    raw_data: str = ""
    indicator_tags: str = ""


class SecurityEventCreate(SecurityEventBase):
    pass


class SecurityEventResponse(SecurityEventBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LogAnalysisSummaryResponse(BaseModel):
    case_id: int
    total_parsed: int
    events_stored: int
    indicators_detected: int
    findings: List[Dict[str, Any]]
    events: List[SecurityEventResponse]
