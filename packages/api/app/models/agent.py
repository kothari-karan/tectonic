import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, Float, Integer, String
from sqlalchemy.dialects.postgresql import JSON as PG_JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class AgentType(str, enum.Enum):
    poster = "poster"
    solver = "solver"
    both = "both"


class Agent(Base):
    __tablename__ = "agents"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    agent_type: Mapped[AgentType] = mapped_column(
        Enum(AgentType, native_enum=False, length=20), nullable=False
    )
    wallet_address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    api_key_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    capabilities: Mapped[list] = mapped_column(PG_JSON, default=list)
    reputation_score: Mapped[float] = mapped_column(Float, default=0.0)
    bounties_posted: Mapped[int] = mapped_column(Integer, default=0)
    bounties_completed: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    posted_bounties = relationship(
        "Bounty", foreign_keys="Bounty.poster_id", back_populates="poster"
    )
    solved_bounties = relationship(
        "Bounty", foreign_keys="Bounty.solver_id", back_populates="solver"
    )
    proposals = relationship("Proposal", back_populates="solver")
    reputation_events = relationship("ReputationEvent", back_populates="agent")
