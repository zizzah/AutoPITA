"""
TaxFlow NG — Full Endpoint Test Suite
======================================
Tests every endpoint on the hosted Render backend.

Usage:
    python test_all_endpoints.py

Requirements:
    pip install requests
"""

import requests
import json
import sys
import time
from datetime import date, timedelta
from typing import Optional

# ── Config ────────────────────────────────────────────────────────────────────
BASE_URL = "http://127.0.0.1:8000/api/v1"

# Test credentials — change if you already have an account on the hosted server
TEST_EMAIL    = f"netopconfiguration@gmail.com"
TEST_PASSWORD = "Golden@1"

# Colours for terminal output
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
BLUE   = "\033[94m"
RESET  = "\033[0m"
BOLD   = "\033[1m"

# ── State shared between tests ────────────────────────────────────────────────
state: dict = {
    "token":        None,
    "transaction_id":  None,
}

passed = 0
failed = 0
skipped = 0


# ── Helpers ───────────────────────────────────────────────────────────────────

def headers() -> dict:
    return {"Authorization": f"Bearer {state['token']}", "Content-Type": "application/json"}


def p(label: str, ok: bool, detail: str = ""):
    global passed, failed
    if ok:
        passed += 1
        print(f"  {GREEN}✓{RESET} {label}")
    else:
        failed += 1
        print(f"  {RED}✗{RESET} {label}  {RED}{detail}{RESET}")


def section(title: str):
    print(f"\n{BOLD}{BLUE}── {title} {'─' * (55 - len(title))}{RESET}")


def skip(label: str, reason: str = ""):
    global skipped
    skipped += 1
    print(f"  {YELLOW}○{RESET} {label}  {YELLOW}(skipped: {reason}){RESET}")


def post(path, payload=None, auth=True):
    h = headers() if auth else {"Content-Type": "application/json"}
    r = requests.post(f"{BASE_URL}{path}", json=payload, headers=h, timeout=30)
    return r


def get(path, params=None, auth=True):
    h = headers() if auth else {}
    r = requests.get(f"{BASE_URL}{path}", params=params, headers=h, timeout=30)
    return r


def patch(path, payload, auth=True):
    h = headers() if auth else {"Content-Type": "application/json"}
    r = requests.patch(f"{BASE_URL}{path}", json=payload, headers=h, timeout=30)
    return r


def delete(path, auth=True):
    h = headers() if auth else {}
    r = requests.delete(f"{BASE_URL}{path}", headers=h, timeout=30)
    return r


# ══════════════════════════════════════════════════════════════════════════════
# 1. SYSTEM HEALTH
# ══════════════════════════════════════════════════════════════════════════════

def test_system():
    section("System Health")


    r = requests.get(BASE_URL.replace("/api/v1", "/health"), timeout=15)
    p("GET /health  (health check)", r.status_code == 200,
      f"status={r.status_code}")



# ══════════════════════════════════════════════════════════════════════════════
# 2. AUTH
# ══════════════════════════════════════════════════════════════════════════════

def test_auth():
    section("Authentication")

    # Register
    r = post("/auth/register", {
        "email":            TEST_EMAIL,
        "full_name": "chukwudi okolo",
        "password":         TEST_PASSWORD,
        "phone": "08012345678",
        "state_of_residence": "Lagos"


    }, auth=False)
    p("POST /auth/register", r.status_code == 201, f"{r.status_code} {r.text[:100]}")

    # Login
    r = post("/auth/login", {
        "email":    TEST_EMAIL,
        "password": TEST_PASSWORD,
    }, auth=False)
    ok = r.status_code == 200 and "access_token" in r.json()
    p("POST /auth/login", ok, f"{r.status_code} {r.text[:100]}")
    if ok:
        state["token"] = r.json()["access_token"]







# ══════════════════════════════════════════════════════════════════════════════
# 4. Transaction
# ══════════════════════════════════════════════════════════════════════════════

def test_transaction():
    section("transactions")
    if not state["token"]:
        skip("all  tests", "no token"); return

    r = post("/transactions",{
    "amount": "150000.00",
    "currency": "NGN",
    "transaction_type": "credit",
    "narration": "SALARY PAYMENT - APRIL 2026 - ZENITH BANK",
    "bank_name": "Zenith Bank",
    "bank_reference": "ZB20260401123456",
    "transaction_date": "2026-04-30T00:00:00Z"
    })
    p("POST /transactions", r.status_code == 201, f"{r.status_code} {r.text[:120]}")
    if r.status_code == 201:
        state["transaction_id"] = r.json()["id"]

    r = post("/transactions", {
        "amount": "12000000.00",
        "currency": "NGN",
        "transaction_type": "credit",
        "narration": "app dev gig  - ZENITH BANK",
        "bank_name": "Zenith Bank",
        "bank_reference": "ZB20260401123456",
        "transaction_date": "2026-04-30T00:00:00Z"
        })
    p("POST /transactions", r.status_code == 201, f"{r.status_code} {r.text[:120]}")
    if r.status_code == 201:
        state["transaction_id"] = r.json()["id"]

    r = post("/transactions", {
        "amount": "150000.00",
        "currency": "NGN",
        "transaction_type": "debit",
        "narration": "rent for   2026 - ZENITH BANK",
        "bank_name": "Zenith Bank",
        "bank_reference": "ZB20260401123456",
        "transaction_date": "2026-04-30T00:00:00Z"
        })
    p("POST /transactions", r.status_code == 201, f"{r.status_code} {r.text[:120]}")
    if r.status_code == 201:
        state["transaction_id"] = r.json()["id"]


    r = post("/transactions", {
        "amount": "5000000.00",
        "currency": "NGN",
        "transaction_type": "credit",
        "narration": "upwork payment   2026 - PALMPAY ",
        "bank_name": "Zenith Bank",
        "bank_reference": "ZB20260401123456",
        "transaction_date": "2026-04-30T00:00:00Z"
        })
    p("POST /transactions", r.status_code == 201, f"{r.status_code} {r.text[:120]}")
    if r.status_code == 201:
        state["transaction_id"] = r.json()["id"]

    r = post("/transactions", {
        "amount": "50000.00",
        "currency": "NGN",
        "transaction_type": "debit",
        "narration": "insurance for   2026 - ZENITH BANK",
        "bank_name": "Zenith Bank",
        "bank_reference": "ZB20260401123456",
        "transaction_date": "2026-04-30T00:00:00Z"
        })
    p("POST /transactions", r.status_code == 201, f"{r.status_code} {r.text[:120]}")
    if r.status_code == 201:
        state["transaction_id"] = r.json()["id"]

    r = post("/transactions", {
        "amount": "50000.00",
        "currency": "NGN",
        "transaction_type": "debit",
        "narration": "grocery for   2026 - opay",
        "bank_name": "Zenith Bank",
        "bank_reference": "ZB20260401123456",
        "transaction_date": "2026-04-30T00:00:00Z"
        })
    p("POST /transactions", r.status_code == 201, f"{r.status_code} {r.text[:120]}")
    if r.status_code == 201:
        state["transaction_id"] = r.json()["id"]


# ══════════════════════════════════════════════════════════════════════════════
# 5. CUSTOMERS
# ══════════════════════════════════════════════════════════════════════════════


def test_cleanup():
    section("Cleanup (soft deletes)")
    if not state["token"]:
        return

    if state["transaction_id"]:
        r = delete(f"/transaction/{state['transaction_id']}")
        p("DELETE /transactions/{id}", r.status_code == 204)

# ══════════════════════════════════════════════════════════════════════════════

def main():
    print(f"\n{BOLD}{'═' * 60}{RESET}")
    print(f"{BOLD}  TaxFlow NG — Full API Test Suite{RESET}")
    print(f"  Target: {BASE_URL}")
    print(f"{BOLD}{'═' * 60}{RESET}")

    test_system()   
    test_auth()
    test_transaction()
    test_cleanup()

    total = passed + failed + skipped
    print(f"\n{BOLD}{'═' * 60}{RESET}")
    print(f"{BOLD}  Results: {total} tests{RESET}")
    print(f"  {GREEN}{passed} passed{RESET}  "
          f"{RED}{failed} failed{RESET}  "
          f"{YELLOW}{skipped} skipped{RESET}")
    print(f"{BOLD}{'═' * 60}{RESET}\n")

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()