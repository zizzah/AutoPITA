import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, Enum as SAEnum, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum
from app.models.base import Base, TimestampMixin


class FilingStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    AWAITING_CONFIRMATION = "awaiting_confirmation"
    SUBMITTED = "submitted"
    CONFIRMED = "confirmed"
    FAILED = "failed"


class Filing(Base, TimestampMixin):
    __tablename__ = "filings"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tax_return_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tax_returns.id"), nullable=False)
    status: Mapped[FilingStatus] = mapped_column(SAEnum(FilingStatus), default=FilingStatus.PENDING)
    portal_url: Mapped[str] = mapped_column(String(255), default="https://etax.lirs.net")
    lirs_reference: Mapped[str | None] = mapped_column(String(100), nullable=True)
    filed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    screenshot_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    audit_log: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationship
    tax_return: Mapped["TaxReturn"] = relationship(back_populates="filings")  # type: ignore