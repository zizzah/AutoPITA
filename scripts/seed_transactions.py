import asyncio
import httpx
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000/api/v1"
EMAIL = "netopconfiguration@gmail.com"
PASSWORD = "Golden@1"

TRANSACTIONS = [
    # Taxable income
    {"amount": "450000.00", "currency": "NGN", "transaction_type": "credit",
     "narration": "SALARY JANUARY 2023 - STERLING BANK", "bank_name": "Sterling Bank",
     "bank_reference": "STB202601001", "transaction_date": "2023-01-31T00:00:00Z"},
      {"amount": "450000.00", "currency": "NGN", "transaction_type": "credit",
     "narration": "SALARY JANUARY 2023 - STERLING BANK", "bank_name": "Sterling Bank",
     "bank_reference": "STB202601001", "transaction_date": "2023-01-31T00:00:00Z"},
      {"amount": "450000.00", "currency": "NGN", "transaction_type": "credit",
     "narration": "SALARY JANUARY 2023 - STERLING BANK", "bank_name": "Sterling Bank",
     "bank_reference": "STB202601001", "transaction_date": "2023-01-31T00:00:00Z"},
      {"amount": "450000.00", "currency": "NGN", "transaction_type": "credit",
     "narration": "SALARY JANUARY 2023 - STERLING BANK", "bank_name": "Sterling Bank",
     "bank_reference": "STB202601001", "transaction_date": "2023-01-31T00:00:00Z"},
      {"amount": "450000.00", "currency": "NGN", "transaction_type": "credit",
     "narration": "SALARY JANUARY 2023 - STERLING BANK", "bank_name": "Sterling Bank",
     "bank_reference": "STB202601001", "transaction_date": "2023-01-31T00:00:00Z"}, {"amount": "450000.00", "currency": "NGN", "transaction_type": "credit",
     "narration": "SALARY JANUARY 2023 - STERLING BANK", "bank_name": "Sterling Bank",
     "bank_reference": "STB202601001", "transaction_date": "2023-01-31T00:00:00Z"}, {"amount": "450000.00", "currency": "NGN", "transaction_type": "credit",
     "narration": "SALARY JANUARY 2023 - STERLING BANK", "bank_name": "Sterling Bank",
     "bank_reference": "STB202601001", "transaction_date": "2023-01-31T00:00:00Z"}, {"amount": "450000.00", "currency": "NGN", "transaction_type": "credit",
     "narration": "SALARY JANUARY 2023 - STERLING BANK", "bank_name": "Sterling Bank",
     "bank_reference": "STB202601001", "transaction_date": "2023-01-31T00:00:00Z"}, {"amount": "450000.00", "currency": "NGN", "transaction_type": "credit",
     "narration": "SALARY JANUARY 2023 - STERLING BANK", "bank_name": "Sterling Bank",
     "bank_reference": "STB202601001", "transaction_date": "2023-01-31T00:00:00Z"}, {"amount": "450000.00", "currency": "NGN", "transaction_type": "credit",
     "narration": "SALARY JANUARY 2₀₂₃ - STERLING BANK", "bank_name": "Sterling Bank",
     "bank_reference": "STB202601001", "transaction_date": "2023-01-31T00:00:00Z"}, {"amount": "450000.00", "currency": "NGN", "transaction_type": "credit",
     "narration": "SALARY JANUARY 2023 - STERLING BANK", "bank_name": "Sterling Bank",
     "bank_reference": "STB202601001", "transaction_date": "2023-01-31T00:00:00Z"},
    # ... 19 more
]

async def main():
    async with httpx.AsyncClient() as client:
        # login
        r = await client.post(f"{BASE_URL}/auth/login", json={"email": EMAIL, "password": PASSWORD})
        token = r.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        for tx in TRANSACTIONS:
            r = await client.post(f"{BASE_URL}/transactions", json=tx, headers=headers, timeout=30)
            data = r.json()
            print(f"{data['narration'][:40]} → {data['tax_category']} ({data['ai_confidence']})")

asyncio.run(main())