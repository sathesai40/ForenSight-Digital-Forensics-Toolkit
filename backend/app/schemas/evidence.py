from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict


class EvidenceBase(BaseModel):
    case_id: int
    evidence_number: str
    source_filename: str
    mime_type: str = "application/octet-stream"
    sha256_hash: str = Field(..., min_length=64, max_length=64)
    md5_hash: Optional[str] = Field(None, max_length=32)
    acquired_by: str
    acquired_at: datetime
    chain_of_custody_notes: str = ""
    integrity_status: str = "VERIFIED"


class EvidenceCreate(EvidenceBase):
    stored_filename: str
    file_path: str
    file_size_bytes: int


class EvidenceResponse(EvidenceBase):
    id: int
    stored_filename: str
    file_path: str  # Safe vault-relative path, never absolute
    file_size_bytes: int
    is_read_only: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EvidenceVerificationResponse(BaseModel):
    evidence_id: int
    evidence_number: str
    status: str  # MATCH, MISMATCH, ERROR
    expected_sha256: str
    calculated_sha256: Optional[str] = None
    verified_at: datetime
    detail: str
    file_exists: bool


class EvidenceMetadataResponse(BaseModel):
    evidence_id: int
    evidence_number: str
    source_metadata: Dict[str, Any]
    vault_storage_metadata: Dict[str, Any]
    signature_analysis: Dict[str, Any]
    investigative_indicators: List[Dict[str, Any]]
