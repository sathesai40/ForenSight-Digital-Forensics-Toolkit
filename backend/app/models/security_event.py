from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, utc_now

if TYPE_CHECKING:
    from app.models.case import InvestigationCase
    from app.models.evidence import EvidenceRecord


class SecurityEvent(Base):
    """Normalized security log event or forensic telemetry finding."""

    __tablename__ = "security_events"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    case_id: Mapped[int] = mapped_column(
        ForeignKey("investigation_cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    evidence_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("evidence_records.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    event_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )  # AUTHENTICATION, NETWORK_CONNECTION, PROCESS_EXECUTION, FILE_MODIFICATION, PRIVILEGE_ESCALATION, SUSPICIOUS_INDICATOR
    severity: Mapped[str] = mapped_column(
        String(20),
        default="INFO",
        nullable=False,
        index=True,
    )  # INFO, LOW, MEDIUM, HIGH, CRITICAL
    source_ip: Mapped[Optional[str]] = mapped_column(String(45), nullable=True, index=True)
    destination_ip: Mapped[Optional[str]] = mapped_column(String(45), nullable=True, index=True)
    user_account: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    raw_data: Mapped[str] = mapped_column(Text, default="", nullable=False)
    indicator_tags: Mapped[str] = mapped_column(Text, default="", nullable=False)  # Comma-separated or serialized
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    # Relationships
    case: Mapped["InvestigationCase"] = relationship(
        "InvestigationCase",
        back_populates="security_events",
    )
    evidence: Mapped[Optional["EvidenceRecord"]] = relationship(
        "EvidenceRecord",
        back_populates="security_events",
    )

    __table_args__ = (
        Index("ix_event_case_time", "case_id", "timestamp"),
        Index("ix_event_type_severity", "event_type", "severity"),
    )

    def __repr__(self) -> str:
        return f"<SecurityEvent(type='{self.event_type}', severity='{self.severity}', time='{self.timestamp}')>"
