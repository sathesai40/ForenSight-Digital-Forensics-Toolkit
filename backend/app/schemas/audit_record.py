from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class AuditRecordBase(BaseModel):
    case_id: Optional[int] = None
    operator: str = "system"
    action: str
    target_type: str
    target_id: str
    details: str = ""
    ip_address: Optional[str] = None
    action_hash: Optional[str] = None


class AuditRecordCreate(AuditRecordBase):
    pass


class AuditRecordResponse(AuditRecordBase):
    id: int
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)
