import shutil
from datetime import datetime, timezone
from pathlib import Path
from fastapi import APIRouter, Depends, status
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.config import settings
from app.database import get_db
from app.models.case import InvestigationCase
from app.models.evidence import EvidenceRecord
from app.schemas.health import HealthResponse, HealthDiagnostics

router = APIRouter(tags=["Health & Diagnostics"])


@router.get("/health", response_model=HealthResponse, status_code=status.HTTP_200_OK)
def get_health_status(db: Session = Depends(get_db)) -> HealthResponse:
    """Forensic System Health & Diagnostic Verification.

    Validates database connectivity, evidence vault read/write permissions,
    and returns system telemetry in UTC.
    """
    now_utc = datetime.now(timezone.utc)
    db_connected = False
    cases_count = 0
    evidence_count = 0

    # Test database connectivity
    try:
        db.execute(text("SELECT 1"))
        db_connected = True
        cases_count = db.query(InvestigationCase).count()
        evidence_count = db.query(EvidenceRecord).count()
    except Exception:
        db_connected = False

    # Test vault storage availability
    vault_path = Path(settings.evidence_vault_dir).resolve()
    vault_ready = vault_path.exists() and vault_path.is_dir()
    free_bytes = None
    try:
        total, used, free = shutil.disk_usage(vault_path.parent if not vault_path.exists() else vault_path)
        free_bytes = free
    except Exception:
        free_bytes = None

    is_healthy = db_connected and vault_ready
    status_str = "healthy" if is_healthy else ("degraded" if db_connected or vault_ready else "unhealthy")

    return HealthResponse(
        status=status_str,
        app_name=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
        timestamp=now_utc,
        database_connected=db_connected,
        vault_ready=vault_ready,
        cases_count=cases_count,
        evidence_count=evidence_count,
        diagnostics=HealthDiagnostics(
            database="sqlite",
            database_path=str(Path(settings.sqlite_db_path).resolve()),
            vault_storage="filesystem",
            vault_path=str(vault_path),
            free_storage_bytes=free_bytes,
        ),
    )
