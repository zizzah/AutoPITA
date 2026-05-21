# app/services/tax_engine.py

from decimal import Decimal
from typing import Any

from sqlalchemy import extract, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.transaction import Transaction
from app.models.user import User


ZERO = Decimal("0.00")

BANDS = [
        (Decimal("800000"),   Decimal("0.00"), "₦0 - ₦800,000"),
        (Decimal("2200000"),  Decimal("0.15"), "₦800,001 - ₦3,000,000"),
        (Decimal("9000000"),  Decimal("0.18"), "₦3,000,001 - ₦12,000,000"),
        (Decimal("13000000"), Decimal("0.21"), "₦12,000,001 - ₦25,000,000"),
        (Decimal("25000000"), Decimal("0.23"), "₦25,000,001 - ₦50,000,000"),
        (None,                Decimal("0.25"), "Above ₦50,000,000"),
    ]

# =========================================================
# MAIN TAX ENGINE
# =========================================================
async def compute_tax(
    *,
    current_user: User,
    db: AsyncSession,
    tax_year: int,
    annual_rent_paid: Decimal = ZERO,
    paye_tax_paid: Decimal = ZERO,
    pension_paid: Decimal = ZERO,

) -> dict[str, Any]:

    # -----------------------------------------------------
    # FETCH RELEVANT TRANSACTIONS
    # -----------------------------------------------------
    result = await db.execute(
        select(Transaction).where(
            Transaction.user_id == current_user.id,

            # only selected year
            extract(
                "year",
                Transaction.transaction_date
            ) == tax_year,

            # taxable income only
            Transaction.tax_category == "taxable_income",

            # income inflow only
            Transaction.transaction_type == "credit",
        )
    )

    income_transactions = result.scalars().all()

    if not income_transactions:
        return {
            "tax_year": tax_year,
            "income_breakdown": {},
            "gross_income": "0.00",
            "pension_deduction": "0.00",
            "additional_deductions": "0.00",
            "rent_relief": "0.00",
            "total_reliefs": "0.00",
            "chargeable_income": "0.00",
            "tax_liability": "0.00",
            "paye_tax_paid": str(paye_tax_paid),
            "tax_payable": "0.00",
            "tax_band_breakdown": [],
            "transaction_breakdown": [],
            "deduction_breakdown": [],
            "total_income_transactions": 0,
            "total_deduction_transactions": 0,
            "nil_return": True,
        }

    # -----------------------------------------------------
    # FETCH DEDUCTIBLE TRANSACTIONS
    # -----------------------------------------------------
    deduction_result = await db.execute(
        select(Transaction).where(
            Transaction.user_id == current_user.id,

            extract(
                "year",
                Transaction.transaction_date
            ) == tax_year,

            Transaction.tax_category
            == "deductible_expense",
            Transaction.transaction_type == "debit",
        )
    )

    deduction_transactions = (
        deduction_result.scalars().all()
    )

    # -----------------------------------------------------
    # INCOME BUCKETS
    # -----------------------------------------------------
    salary_income = ZERO
    freelance_income = ZERO
    dividend_income = ZERO
    interest_income = ZERO
    rent_income = ZERO
    other_income = ZERO

    transaction_breakdown = []

    # -----------------------------------------------------
    # PROCESS INCOME TRANSACTIONS
    # -----------------------------------------------------
    for tx in income_transactions:

        amount = Decimal(tx.amount)

        transaction_breakdown.append({
            "transaction_id": str(tx.id),
            "amount": str(amount),
            "income_type": tx.income_type,
            "narration": tx.narration,
            "ai_confidence": (
                float(tx.ai_confidence)
                if tx.ai_confidence
                else None
            ),
            "manually_reviewed":
                tx.is_manually_reviewed,
        })

        # salary
        if tx.income_type == "salary":
            salary_income += amount

        # freelance / trade
        elif tx.income_type in [
            "trade_income",
            "trade income",
            "freelance",
            "consulting",
            "gigs",
        ]:
            freelance_income += amount

        # dividend
        elif tx.income_type == "dividend":
            dividend_income += amount

        # interest
        elif tx.income_type == "interest":
            interest_income += amount

        # rent
        elif tx.income_type == "rent_income":
            rent_income += amount

        else:
            other_income += amount

    # -----------------------------------------------------
    # GROSS INCOME
    # -----------------------------------------------------
    gross_income = (
        salary_income
        + freelance_income
        + dividend_income
        + interest_income
        + rent_income
        + other_income
    )

    # -----------------------------------------------------
    # PENSION DEDUCTION
    # 8% statutory
    # -----------------------------------------------------
    pension_deduction = pension_paid

    # -----------------------------------------------------
    # OTHER DEDUCTIBLE EXPENSES
    # -----------------------------------------------------
    additional_deductions = ZERO

    deduction_breakdown = []

    for tx in deduction_transactions:

        amount = Decimal(tx.amount)

        additional_deductions += amount

        deduction_breakdown.append({
            "transaction_id": str(tx.id),
            "amount": str(amount),
            "narration": tx.narration,
        })

    # -----------------------------------------------------
    # RENT RELIEF
    # MVP ASSUMPTION:
    # lower of:
    # 20% of rent paid
    # OR ₦500k cap
    # -----------------------------------------------------
    rent_relief = calculate_rent_relief(
        annual_rent_paid
    )

    # -----------------------------------------------------
    # TOTAL RELIEFS
    # -----------------------------------------------------
    total_reliefs = (
        pension_deduction
        + additional_deductions
        + rent_relief
    )

    # -----------------------------------------------------
    # CHARGEABLE INCOME
    # -----------------------------------------------------
    chargeable_income = (
        gross_income - total_reliefs
    )

    if chargeable_income < ZERO:
        chargeable_income = ZERO

    # -----------------------------------------------------
    # PROGRESSIVE TAX
    # -----------------------------------------------------
    tax_result = calculate_progressive_tax(
        chargeable_income
    )

    tax_liability = tax_result["total_tax"]

    # -----------------------------------------------------
    # FINAL TAX PAYABLE
    # -----------------------------------------------------
    tax_payable = (
        tax_liability - paye_tax_paid
    )

    if tax_payable < ZERO:
        tax_payable = ZERO

    # -----------------------------------------------------
    # RESPONSE
    # -----------------------------------------------------
    return {

        # metadata
        "tax_year": tax_year,

        # income breakdown
        "income_breakdown": {
            "salary_income":
                str(salary_income),

            "freelance_income":
                str(freelance_income),

            "dividend_income":
                str(dividend_income),

            "interest_income":
                str(interest_income),

            "rent_income":
                str(rent_income),

            "other_income":
                str(other_income),
        },

        # totals
        "gross_income":
            str(gross_income),

        "pension_deduction":
            str(pension_deduction),

        "additional_deductions":
            str(additional_deductions),

        "rent_relief":
            str(rent_relief),

        "total_reliefs":
            str(total_reliefs),

        "chargeable_income":
            str(chargeable_income),

        "tax_liability":
            str(tax_liability),

        "paye_tax_paid":
            str(paye_tax_paid),

        "tax_payable":
            str(tax_payable),

        # explainability
        "tax_band_breakdown":
            tax_result["bands"],

        "transaction_breakdown":
            transaction_breakdown,

        "deduction_breakdown":
            deduction_breakdown,

        # audit
        "total_income_transactions":
            len(income_transactions),

        "total_deduction_transactions":
            len(deduction_transactions),
        "nil_return": False

    }


# =========================================================
# RENT RELIEF
# =========================================================
def calculate_rent_relief(
    annual_rent_paid: Decimal
) -> Decimal:

    if annual_rent_paid <= ZERO:
        return ZERO

    relief = (
        annual_rent_paid
        * Decimal("0.20")
    )

    max_relief = Decimal("500000")

    return min(
        relief,
        max_relief,
    )


# =========================================================
# PROGRESSIVE TAX ENGINE
# =========================================================
def calculate_progressive_tax(
    chargeable_income: Decimal,
) -> dict:



    remaining = chargeable_income
    total_tax = ZERO
    bands = []

    for band_size, rate, label in BANDS:
        if remaining <= ZERO:
            break

        if band_size is None:
            taxable = remaining
        else:
            taxable = min(remaining, band_size)

        tax = taxable * rate
        total_tax += tax

        bands.append({
            "band": label,
            "rate": f"{int(rate * 100)}%",
            "taxable_amount": str(taxable),
            "tax": str(tax),
        })

        remaining -= taxable

    return {"total_tax": total_tax, "bands": bands}