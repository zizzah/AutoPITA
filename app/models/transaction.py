import uuid
from decimal import Decimal
from datetime import datetime
from sqlalchemy import String, Numeric, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum
from app.models.base import Base, TimestampMixin


class TransactionType(str, enum.Enum):
    CREDIT = "credit"
    DEBIT = "debit"


class TaxCategory(str, enum.Enum):
    TAXABLE_INCOME = "taxable_income"
    EXEMPT_INCOME = "exempt_income"
    DEDUCTIBLE_EXPENSE = "deductible_expense"
    NON_DEDUCTIBLE_EXPENSE = "non_deductible_expense"
    UNCLASSIFIED = "unclassified"


class Transaction(Base, TimestampMixin):
    __tablename__ = "transactions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)

    # Raw bank data
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="NGN", nullable=False)
    transaction_type: Mapped[TransactionType] = mapped_column(SAEnum(TransactionType), nullable=False)
    narration: Mapped[str] = mapped_column(String(500), nullable=False)
    bank_name: Mapped[str] = mapped_column(String(100), nullable=False)
    bank_reference: Mapped[str | None] = mapped_column(String(100), nullable=True)
    transaction_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # AI classification output
    tax_category: Mapped[TaxCategory] = mapped_column(
        SAEnum(TaxCategory),
        default=TaxCategory.UNCLASSIFIED,
        nullable=False
    )
    income_type: Mapped[str | None] = mapped_column(String(50), nullable=True)  # salary, trade, dividend etc
    ai_confidence: Mapped[Decimal | None] = mapped_column(Numeric(5, 4), nullable=True)
    ai_reasoning: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_manually_reviewed: Mapped[bool] = mapped_column(default=False, nullable=False)

    # Relationship
    user: Mapped["User"] = relationship(back_populates="transactions")  # type: ignore