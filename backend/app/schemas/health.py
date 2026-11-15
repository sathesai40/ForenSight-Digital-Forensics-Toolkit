from datetime import datetime
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class HealthDiagnostics(BaseModel):
    database: str
    database_path: str
    vault_storage: str
    vault_path: str
    free_storage_bytes: Optional[int] = None


class HealthResponse(BaseModel):
    status: str = Field(..., description="Overall system health status: healthy, degraded, or unhealthy")
    app_name: str
    version: str
    environment: str
    timestamp: datetime = Field(..., description="UTC server timestamp in ISO 8601")
    database_connected: bool
    vault_ready: bool
    cases_count: int = 0
    evidence_count: int = 0
    diagnostics: HealthDiagnostics
