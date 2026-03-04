import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ReputationEventType(str, enum.Enum):
    engagement_completed = "engagement_completed"
    engagement_posted = "engagement_posted"
    dispute_won = "dispute_won"
    dispute_lost = "dispute_lost"


class ReputationEvent(Base):
    __tablename__ = "reputation_events"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    agent_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("agents.id"), nullable=False
    )
    event_type: Mapped[ReputationEventType] = mapped_column(
        Enum(ReputationEventType, native_enum=False, length=30), nullable=False
    )
    contract_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("contracts.id"), nullable=True
    )
    score_delta: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    agent = relationship("Agent", back_populates="reputation_events")
