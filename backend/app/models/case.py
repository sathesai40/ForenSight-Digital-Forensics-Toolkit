from typing import List, TYPE_CHECKING
from sqlalchemy import String, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.evidence import EvidenceRecord
    from app.models.security_event import SecurityEvent
    from app.models.audit_record import AuditRecord


class InvestigationCase(Base, TimestampMixin):
    """Investigation Case model representing a distinct forensic inquiry."""

    __tablename__ = "investigation_cases"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    case_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    investigator_name: Mapped[str] = mapped_column(String(100), nullable=False)
    lead_analyst: Mapped[str] = mapped_column(String(100), default="", nullable=False)
    status: Mapped[str] = mapped_column(
        String(30),
        default="OPEN",
        nullable=False,
        index=True,
    )  # OPEN, IN_PROGRESS, UNDER_REVIEW, CLOSED, ARCHIVED
    priority: Mapped[str] = mapped_column(
        String(20),
        default="MEDIUM",
        nullable=False,
        index=True,
    )  # LOW, MEDIUM, HIGH, CRITICAL

    # Relationships
    evidence_records: Mapped[List["EvidenceRecord"]] = relationship(
        "EvidenceRecord",
        back_populates="case",
        cascade="all, delete-orphan",
        order_by="EvidenceRecord.id",
    )
    security_events: Mapped[List["SecurityEvent"]] = relationship(
        "SecurityEvent",
        back_populates="case",
        cascade="all, delete-orphan",
        order_by="SecurityEvent.timestamp.desc()",
    )
    audit_records: Mapped[List["AuditRecord"]] = relationship(
        "AuditRecord",
        back_populates="case",
        order_by="AuditRecord.timestamp.desc()",
    )

    __table_args__ = (
        Index("ix_case_status_priority", "status", "priority"),
    )

    def __repr__(self) -> str:
        return f"<InvestigationCase(number='{self.case_number}', title='{self.title}', status='{self.status}')>"
