import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, Float, ForeignKey, String, Text
from sqlalchemy import JSON as PG_JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class EngagementType(str, enum.Enum):
    open = "open"
    direct = "direct"
    invited = "invited"


class EngagementStatus(str, enum.Enum):
    open = "open"
    proposed = "proposed"
    negotiating = "negotiating"
    agreed = "agreed"
    in_progress = "in_progress"
    delivered = "delivered"
    verified = "verified"
    settled = "settled"
    cancelled = "cancelled"
    disputed = "disputed"


class Engagement(Base):
    __tablename__ = "engagements"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    acceptance_criteria: Mapped[list] = mapped_column(PG_JSON, nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    reward_amount: Mapped[float] = mapped_column(Float, nullable=False)
    reward_token: Mapped[str] = mapped_column(String(20), default="ETH")
    engagement_type: Mapped[EngagementType] = mapped_column(
        Enum(EngagementType, native_enum=False, length=20), default=EngagementType.open
    )
    target_provider_ids: Mapped[list | None] = mapped_column(PG_JSON, nullable=True)
    requester_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("agents.id"), nullable=False
    )
    provider_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("agents.id"), nullable=True
    )
    status: Mapped[EngagementStatus] = mapped_column(
        Enum(EngagementStatus, native_enum=False, length=20), default=EngagementStatus.open
    )
    deadline: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    escrow_address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    deliverable_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    requester = relationship(
        "Agent", foreign_keys=[requester_id], back_populates="posted_engagements"
    )
    provider = relationship(
        "Agent", foreign_keys=[provider_id], back_populates="completed_engagements"
    )
    proposals = relationship("Proposal", back_populates="engagement")
    negotiations = relationship("Negotiation", back_populates="engagement")
