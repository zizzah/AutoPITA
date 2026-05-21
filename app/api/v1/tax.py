from email.policy import default
from fastapi import APIRouter, Depends, Query
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_current_user
from app.models.user import User
from app.services.tax_engine import compute_tax
from app.schemas.tax import TaxComputeResponse

router = APIRouter(prefix="/tax", tags=["Tax"])


@router.get("/compute", response_model=TaxComputeResponse)
async def compute_user_tax(
    year: int = Query(..., description="Tax year e.g. 2026"),
    annual_rent_paid: Decimal = Query(default=Decimal("0.00")),
    paye_tax_paid: Decimal = Query(default=Decimal("0.00")),
    pension_paid : Decimal=Query(default=Decimal("0.00")),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await compute_tax(
        current_user=current_user,
        db=db,
        tax_year=year,
        annual_rent_paid=annual_rent_paid,
        paye_tax_paid=paye_tax_paid,
        pension_paid=pension_paid
    )
    return result