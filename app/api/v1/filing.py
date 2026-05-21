from fastapi import APIRouter, Depends, BackgroundTasks
from pydantic import BaseModel
from app.dependencies import get_current_user
from app.models.user import User
from app.services.filing_engine import run_filing
from app.services.tax_engine import compute_tax
from app.db.session import AsyncSessionLocal
from decimal import Decimal


router = APIRouter(prefix="/filing", tags=["Filing"])


class FilingRequest(BaseModel):
    lirs_payer_id: str
    lirs_password: str
    tax_year: int
    accommodation: dict


class FilingResponse(BaseModel):
    status: str
    message: str
    screenshot: str | None = None


@router.post("/run", response_model=FilingResponse)
async def run_tax_filing(
    payload: FilingRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Triggers the Playwright filing automation.
    Fills the LIRS form up to Tab 5 and stops for user confirmation.
    LIRS credentials are never stored — used only for this session.
    """

    async with AsyncSessionLocal() as db:
        tax_data = await compute_tax(
            current_user=current_user,
            db=db,
            tax_year=payload.tax_year,
            annual_rent_paid=Decimal(
                str(payload.accommodation.get("rent_paid", "0"))
            ),
        )

    result = await run_filing(
        lirs_username=payload.lirs_payer_id,
        lirs_password=payload.lirs_password,
        tax_data=tax_data,
        tax_year=payload.tax_year,
        accommodation=payload.accommodation,
    )

    return result