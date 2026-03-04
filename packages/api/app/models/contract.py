import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, Float, ForeignKey, String
from sqlalchemy import JSON as PG_JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ContractStatus(str, enum.Enum):
    pending_funding = "pending_funding"
    funded = "funded"
    in_progress = "in_progress"
    delivered = "delivered"
    verified = "verified"
    settled = "settled"
    disputed = "disputed"
    resolved = "resolved"


class Contract(Base):
    __tablename__ = "contracts"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    engagement_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("engagements.id"), nullable=False
    )
    negotiation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("negotiations.id"), nullable=False
    )
    requester_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("agents.id"), nullable=False
    )
    provider_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("agents.id"), nullable=False
    )
    status: Mapped[ContractStatus] = mapped_column(
        Enum(ContractStatus, native_enum=False, length=20),
        default=ContractStatus.pending_funding,
    )
    agreed_terms: Mapped[dict] = mapped_column(PG_JSON, nullable=False)
    terms_hash: Mapped[str] = mapped_column(String(66), nullable=False)
    escrow_contract_address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    funding_tx_hash: Mapped[str | None] = mapped_column(String(66), nullable=True)
    release_tx_hash: Mapped[str | None] = mapped_column(String(66), nullable=True)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
