import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy import JSON as PG_JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class RateType(str, enum.Enum):
    fixed = "fixed"
    hourly = "hourly"
    per_deliverable = "per_deliverable"


class ListingAvailability(str, enum.Enum):
    available = "available"
    busy = "busy"
    unavailable = "unavailable"


class ServiceListing(Base):
    __tablename__ = "service_listings"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    provider_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("agents.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    capabilities: Mapped[list] = mapped_column(PG_JSON, nullable=False)
    rate_type: Mapped[RateType] = mapped_column(
        Enum(RateType, native_enum=False, length=20), nullable=False
    )
    rate_range_min: Mapped[float] = mapped_column(Float, nullable=False)
    rate_range_max: Mapped[float] = mapped_column(Float, nullable=False)
    availability: Mapped[ListingAvailability] = mapped_column(
        Enum(ListingAvailability, native_enum=False, length=20),
        default=ListingAvailability.available,
    )
    response_time_hours: Mapped[int] = mapped_column(Integer, default=24)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    provider = relationship("Agent", back_populates="service_listings")
