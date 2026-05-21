from pydantic import BaseModel
from decimal import Decimal
from typing import Optional


class TaxComputeResponse(BaseModel):
    tax_year: int
    income_breakdown: dict
    gross_income: Decimal
    pension_deduction: Decimal
    additional_deductions: Decimal
    rent_relief: Decimal
    total_reliefs: Decimal
    chargeable_income: Decimal
    tax_liability: Decimal
    paye_tax_paid: Decimal
    tax_payable: Decimal
    tax_band_breakdown: list[dict]
    transaction_breakdown: list[dict]
    deduction_breakdown: list[dict]
    total_income_transactions: int
    total_deduction_transactions: int
    nil_return: bool = False