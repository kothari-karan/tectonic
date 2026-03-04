import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, Float, Integer, String
from sqlalchemy.dialects.postgresql import JSON as PG_JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class AgentType(str, enum.Enum):
    requester = "requester"
    provider = "provider"
    both = "both"


class Agent(Base):
    __tablename__ = "agents"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    agent_type: Mapped[AgentType] = mapped_column(
        Enum(AgentType, native_enum=False, length=20), nullable=False
    )
    wallet_address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    api_key_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    capabilities: Mapped[list] = mapped_column(PG_JSON, default=list)
    reputation_score: Mapped[float] = mapped_column(Float, default=0.0)
    engagements_posted: Mapped[int] = mapped_column(Integer, default=0)
    engagements_completed: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    posted_engagements = relationship(
        "Engagement", foreign_keys="Engagement.requester_id", back_populates="requester"
    )
    completed_engagements = relationship(
        "Engagement", foreign_keys="Engagement.provider_id", back_populates="provider"
    )
    proposals = relationship("Proposal", back_populates="provider")
    reputation_events = relationship("ReputationEvent", back_populates="agent")
    service_listings = relationship("ServiceListing", back_populates="provider")
