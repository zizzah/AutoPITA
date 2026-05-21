import json
import logging
from decimal import Decimal
from datetime import datetime
from groq import AsyncGroq
from app.models.transaction import TransactionType, TaxCategory
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

client = AsyncGroq(api_key=settings.GROQ_API_KEY)


async def classify_transaction(
    amount: Decimal,
    currency: str,
    transaction_type: TransactionType,
    narration: str,
    bank_name: str,
    bank_reference: str | None,
    transaction_date: datetime,
) -> dict:
    prompt = f"""You are a Nigerian tax expert. Classify this bank transaction under the Nigeria Tax Act 2025.

Transaction:
- Amount: {currency} {amount}
- Type: {transaction_type.value}
- Narration: {narration}
- Bank: {bank_name}
- Reference: {bank_reference or 'N/A'}
- Date: {transaction_date.date()}

Tax categories:
- taxable_income: salary, allowance, commission, dividends, rent received, trade income
- exempt_income: gratuities, NHIS reimbursements, foreign income under DTT
- deductible_expense: pension contributions, NHIS payments, rent paid, life assurance premiums
- non_deductible_expense: fines, personal expenses, entertainment
- unclassified: cannot determine from available data

Income type must be exactly one of: salary, trade_income, dividend, interest, rent_income, freelance, pension
Use underscores, never spaces. Use null if not applicable.

Return ONLY a JSON object, no markdown, no explanation:
{{
  "tax_category": "one of the five categories above",
  "income_type": "one of the valid income types or null",
  "ai_confidence": 0.00,
  "ai_reasoning": "one sentence explanation"
}}"""
    response = await client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": "You are a Nigerian tax classification engine. Return only valid JSON. No preamble. No markdown."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.1,
        max_tokens=256,
    )

    response_text = response.choices[0].message.content
    if not response_text:
        raise ValueError("Groq returned empty response")

    # Strip markdown fences if model ignores instructions
    text = response_text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    text = text.strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        logger.error(f"Groq returned invalid JSON: {text[:300]}")
        raise ValueError("Groq did not return valid JSON")

    # Validate and coerce types
    confidence = Decimal(str(data.get("ai_confidence", 0)))

    try:
        tax_category = TaxCategory(data.get("tax_category", "unclassified"))
    except ValueError:
        tax_category = TaxCategory.UNCLASSIFIED
        confidence = Decimal("0.0")

    return {
        "tax_category": tax_category,
        "income_type": data.get("income_type"),
        "ai_confidence": confidence,
        "ai_reasoning": data.get("ai_reasoning"),
        "is_manually_reviewed": confidence < Decimal("0.75"),
    }