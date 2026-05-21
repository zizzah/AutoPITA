import uuid
from pydantic import BaseModel, Field
from typing import Optional
from decimal import Decimal
from datetime import datetime
from app.models.transaction import TransactionType, TaxCategory


class TransactionBase(BaseModel):
    amount: Decimal
    currency: str = "NGN"
    transaction_type: TransactionType
    narration: str = Field(..., min_length=2, max_length=500)
    bank_name: str = Field(..., min_length=2, max_length=100)
    bank_reference: Optional[str] = Field(default=None, max_length=100)
    transaction_date: datetime


class TransactionCreate(TransactionBase):
    pass


class TransactionOut(TransactionBase):
    id: uuid.UUID
    user_id: uuid.UUID
    tax_category: TaxCategory
    income_type: Optional[str] = None
    ai_confidence: Optional[Decimal] = None
    ai_reasoning: Optional[str] = None
    is_manually_reviewed: bool = False
    created_at: datetime

    model_config = {"from_attributes": True}