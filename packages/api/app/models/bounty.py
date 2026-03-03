import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, Float, ForeignKey, String, Text
from sqlalchemy import JSON as PG_JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class BountyStatus(str, enum.Enum):
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


class Bounty(Base):
    __tablename__ = "bounties"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    acceptance_criteria: Mapped[list] = mapped_column(PG_JSON, nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    reward_amount: Mapped[float] = mapped_column(Float, nullable=False)
    reward_token: Mapped[str] = mapped_column(String(20), default="ETH")
    poster_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("agents.id"), nullable=False
    )
    solver_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("agents.id"), nullable=True
    )
    status: Mapped[BountyStatus] = mapped_column(
        Enum(BountyStatus, native_enum=False, length=20), default=BountyStatus.open
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
    poster = relationship(
        "Agent", foreign_keys=[poster_id], back_populates="posted_bounties"
    )
    solver = relationship(
        "Agent", foreign_keys=[solver_id], back_populates="solved_bounties"
    )
    proposals = relationship("Proposal", back_populates="bounty")
    negotiations = relationship("Negotiation", back_populates="bounty")
