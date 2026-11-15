from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class CaseBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=255, description="Investigation case title")
    description: str = Field("", description="Detailed incident background or hypothesis")
    investigator_name: str = Field(..., min_length=2, max_length=100, description="Lead investigator handling the case")
    lead_analyst: str = Field("", max_length=100, description="Forensics analyst assigned")
    priority: str = Field("MEDIUM", description="Case priority: LOW, MEDIUM, HIGH, CRITICAL")


class CaseCreate(CaseBase):
    case_number: Optional[str] = Field(None, description="Custom case identifier or auto-generated")


class CaseUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=255)
    description: Optional[str] = None
    investigator_name: Optional[str] = None
    lead_analyst: Optional[str] = None
    status: Optional[str] = None  # OPEN, IN_PROGRESS, UNDER_REVIEW, CLOSED, ARCHIVED
    priority: Optional[str] = None


class CaseResponse(CaseBase):
    id: int
    case_number: str
    status: str
    created_at: datetime
    updated_at: datetime
    evidence_count: int = 0
    events_count: int = 0

    model_config = ConfigDict(from_attributes=True)
