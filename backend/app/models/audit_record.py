from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, utc_now

if TYPE_CHECKING:
    from app.models.case import InvestigationCase


class AuditRecord(Base):
    """Immutable forensic audit record tracking all investigator and automated actions."""

    __tablename__ = "audit_records"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    case_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("investigation_cases.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
        index=True,
    )
    operator: Mapped[str] = mapped_column(String(100), default="system", nullable=False)
    action: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )  # CASE_CREATED, EVIDENCE_ACQUIRED, INTEGRITY_VERIFIED, EVIDENCE_ACCESSED, EXPORT_GENERATED, STATUS_CHANGED
    target_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )  # CASE, EVIDENCE, SECURITY_EVENT, SYSTEM
    target_id: Mapped[str] = mapped_column(String(100), default="", nullable=False)
    details: Mapped[str] = mapped_column(Text, default="", nullable=False)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    action_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    # Relationships
    case: Mapped[Optional["InvestigationCase"]] = relationship(
        "InvestigationCase",
        back_populates="audit_records",
    )

    __table_args__ = (
        Index("ix_audit_action_time", "action", "timestamp"),
    )

    def __repr__(self) -> str:
        return f"<AuditRecord(operator='{self.operator}', action='{self.action}', time='{self.timestamp}')>"
