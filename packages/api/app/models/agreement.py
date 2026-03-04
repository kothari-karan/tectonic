import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy import JSON as PG_JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class AgreementStatus(str, enum.Enum):
    active = "active"
    paused = "paused"
    terminated = "terminated"


class AgreementRateType(str, enum.Enum):
    retainer_monthly = "retainer_monthly"
    per_task = "per_task"
    hourly = "hourly"


class StandingAgreement(Base):
    __tablename__ = "standing_agreements"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    requester_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("agents.id"), nullable=False
    )
    provider_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("agents.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    scope_description: Mapped[str] = mapped_column(Text, nullable=False)
    rate_type: Mapped[AgreementRateType] = mapped_column(
        Enum(AgreementRateType, native_enum=False, length=30), nullable=False
    )
    rate: Mapped[float] = mapped_column(Float, nullable=False)
    max_tasks_per_period: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_spend_per_period: Mapped[float | None] = mapped_column(Float, nullable=True)
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[AgreementStatus] = mapped_column(
        Enum(AgreementStatus, native_enum=False, length=20),
        default=AgreementStatus.active,
    )
    agreed_terms: Mapped[dict | None] = mapped_column(PG_JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    requester = relationship("Agent", foreign_keys=[requester_id])
    provider = relationship("Agent", foreign_keys=[provider_id])
    tasks = relationship("AgreementTask", back_populates="agreement")


class AgreementTask(Base):
    __tablename__ = "agreement_tasks"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    agreement_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("standing_agreements.id"), nullable=False
    )
    engagement_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("engagements.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    agreement = relationship("StandingAgreement", back_populates="tasks")
    engagement = relationship("Engagement")
