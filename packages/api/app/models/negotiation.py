import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy import JSON as PG_JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class NegotiationStatus(str, enum.Enum):
    active = "active"
    agreed = "agreed"
    rejected = "rejected"
    expired = "expired"


class TurnType(str, enum.Enum):
    offer = "offer"
    counter = "counter"
    accept = "accept"
    reject = "reject"


class Negotiation(Base):
    __tablename__ = "negotiations"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    engagement_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("engagements.id"), nullable=False
    )
    proposal_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("proposals.id"), nullable=False
    )
    requester_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("agents.id"), nullable=False
    )
    provider_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("agents.id"), nullable=False
    )
    status: Mapped[NegotiationStatus] = mapped_column(
        Enum(NegotiationStatus, native_enum=False, length=20),
        default=NegotiationStatus.active,
    )
    current_terms: Mapped[dict | None] = mapped_column(PG_JSON, nullable=True)
    turn_count: Mapped[int] = mapped_column(Integer, default=0)
    max_turns: Mapped[int] = mapped_column(Integer, default=10)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    engagement = relationship("Engagement", back_populates="negotiations")
    proposal = relationship("Proposal", back_populates="negotiations")
    turns = relationship(
        "NegotiationTurn", back_populates="negotiation", order_by="NegotiationTurn.sequence"
    )


class NegotiationTurn(Base):
    __tablename__ = "negotiation_turns"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    negotiation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("negotiations.id"), nullable=False
    )
    agent_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("agents.id"), nullable=False
    )
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    turn_type: Mapped[TurnType] = mapped_column(
        Enum(TurnType, native_enum=False, length=20), nullable=False
    )
    proposed_terms: Mapped[dict | None] = mapped_column(PG_JSON, nullable=True)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    negotiation = relationship("Negotiation", back_populates="turns")
