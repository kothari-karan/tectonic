import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ProposalStatus(str, enum.Enum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"
    withdrawn = "withdrawn"


class Proposal(Base):
    __tablename__ = "proposals"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    bounty_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("bounties.id"), nullable=False
    )
    solver_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("agents.id"), nullable=False
    )
    status: Mapped[ProposalStatus] = mapped_column(
        Enum(ProposalStatus, native_enum=False, length=20), default=ProposalStatus.pending
    )
    proposed_price: Mapped[float] = mapped_column(Float, nullable=False)
    proposed_deadline: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    approach_summary: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    bounty = relationship("Bounty", back_populates="proposals")
    solver = relationship("Agent", back_populates="proposals")
    negotiations = relationship("Negotiation", back_populates="proposal")

    __table_args__ = ()
