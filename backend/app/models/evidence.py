from datetime import datetime
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import String, Text, BigInteger, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin, utc_now

if TYPE_CHECKING:
    from app.models.case import InvestigationCase
    from app.models.security_event import SecurityEvent


class EvidenceRecord(Base, TimestampMixin):
    """Forensic evidence artifact tracked with cryptographic integrity."""

    __tablename__ = "evidence_records"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    case_id: Mapped[int] = mapped_column(
        ForeignKey("investigation_cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    evidence_number: Mapped[str] = mapped_column(String(50), nullable=False)
    source_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), default="application/octet-stream", nullable=False)
    sha256_hash: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    md5_hash: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    acquired_by: Mapped[str] = mapped_column(String(100), nullable=False)
    acquired_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )
    chain_of_custody_notes: Mapped[str] = mapped_column(Text, default="", nullable=False)
    integrity_status: Mapped[str] = mapped_column(
        String(30),
        default="VERIFIED",
        nullable=False,
        index=True,
    )  # VERIFIED, PENDING, COMPROMISED
    is_read_only: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    case: Mapped["InvestigationCase"] = relationship(
        "InvestigationCase",
        back_populates="evidence_records",
    )
    security_events: Mapped[List["SecurityEvent"]] = relationship(
        "SecurityEvent",
        back_populates="evidence",
        order_by="SecurityEvent.timestamp.desc()",
    )

    __table_args__ = (
        Index("ix_case_evidence_number", "case_id", "evidence_number", unique=True),
    )

    def __repr__(self) -> str:
        return f"<EvidenceRecord(num='{self.evidence_number}', file='{self.source_filename}', sha256='{self.sha256_hash[:8]}...')>"
