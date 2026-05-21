import uuid
from decimal import Decimal
from sqlalchemy import String, Numeric, Integer, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum
from app.models.base import Base, TimestampMixin


class ReturnStatus(str, enum.Enum):
    DRAFT = "draft"
    COMPUTED = "computed"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    FILED = "filed"
    FAILED = "failed"


class TaxReturn(Base, TimestampMixin):
    __tablename__ = "tax_returns"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    tax_year: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[ReturnStatus] = mapped_column(SAEnum(ReturnStatus), default=ReturnStatus.DRAFT)

    # Income breakdown — maps directly to LIRS form fields
    salary: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    allowance: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    commission: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    trade_income: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    pension: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    annuity: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    gratuities: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    foreign_income: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    dividend: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    interest: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    rent_income: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    other_income: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)

    # Computed values
    gross_income: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    total_reliefs: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    chargeable_income: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    tax_liability: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    tax_paid: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    tax_payable: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)

    # Accommodation
    accommodation_address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    accommodation_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    ownership_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    owner_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    owner_payer_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    owner_address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    rent_paid: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    rent_paid_by_employer: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="tax_returns")  # type: ignore
    filings: Mapped[list["Filing"]] = relationship(back_populates="tax_return")  # type: ignore