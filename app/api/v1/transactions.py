import uuid
import logging
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.transaction import Transaction
from app.schemas.transaction import TransactionCreate, TransactionOut
from app.services.classifier import classify_transaction
from app.core.exceptions import NotFoundError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.post("", response_model=TransactionOut, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    payload: TransactionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    classification = await classify_transaction(
        amount=payload.amount,
        currency=payload.currency,
        transaction_type=payload.transaction_type,
        narration=payload.narration,
        bank_name=payload.bank_name,
        bank_reference=payload.bank_reference,
        transaction_date=payload.transaction_date,
    )

    transaction = Transaction(
        user_id=current_user.id,
        amount=payload.amount,
        currency=payload.currency,
        transaction_type=payload.transaction_type,
        narration=payload.narration,
        bank_name=payload.bank_name,
        bank_reference=payload.bank_reference,
        transaction_date=payload.transaction_date,
        **classification
    )
    db.add(transaction)
    await db.flush()
    await db.refresh(transaction)
    return transaction


@router.get("", response_model=list[TransactionOut])
async def get_transactions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Transaction)
        .where(Transaction.user_id == current_user.id)
        .order_by(Transaction.transaction_date.desc())
    )
    return result.scalars().all()


@router.get("/{transaction_id}", response_model=TransactionOut)
async def get_transaction(
    transaction_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Transaction).where(
            Transaction.id == transaction_id,
            Transaction.user_id == current_user.id
        )
    )
    transaction = result.scalar_one_or_none()
    if not transaction:
        raise NotFoundError("Transaction")
    return transaction