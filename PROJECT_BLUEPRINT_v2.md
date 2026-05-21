# AutoPITA — Project Blueprint
> AI-Powered Personal Income Tax Automation for Nigeria  
> Version: 2.1 | Status: In Development | Target: LIRS eTax (Lagos State)

---

## Changelog: v1.0 → v2.0

| Area | Change |
|---|---|
| Filing Engine | Added portal health monitor, manual fallback path, resilience strategy |
| Bank Integration | Updated Mono risk note post-Flutterwave acquisition; promoted CSV fallback to required |
| AI Classifier | Added edge-case income types; tightened confidence thresholds; defined review escalation |
| Tax Engine | Added full NTA 2025 bands; added foreign income, crypto, DTT, PAYE reconciliation edge cases |
| Security / Compliance | Replaced NDPR with NDPA 2023 (governing law); added NDPC registration, DPO, DPIA requirements |
| Architecture | Added LLM fallback provider; added portal monitor service; added data retention policy |
| Folder Structure | Added `portal_monitor.py`, `manual_filing.py`, `compliance.py` |
| API | Added portal health endpoint; added manual filing initiation endpoint |
| Legal | Added liability disclaimer framework and user consent requirements |
| Architectural Decisions | Added Decision 6 (filing resilience), Decision 7 (LLM fallback), Decision 8 (NDPA compliance) |

## Changelog: v2.0 → v2.1

| Area | Change |
|---|---|
| Filing Engine | Added WAT filing window (02:00–04:00) to portal resilience spec |
| AI Classifier | Tightened low-confidence floor from 0.70 to 0.75 (third-party review consensus) |
| Pre-Launch Checklist | Added Section 16 — structured go/no-go checklist before first paying user |

---

## 1. Product Overview

### What AutoPITA Does
AutoPITA is a backend system that connects to a user's Nigerian bank accounts, uses AI to classify every transaction as taxable or non-taxable, computes their personal income tax liability under the Nigeria Tax Act 2025, and assists with the filing of their annual return on the Lagos State Internal Revenue Service (LIRS) eTax portal — with minimal user input.

> **Legal Position:** AutoPITA is a tax compliance assistance tool. It does not provide legal tax advice. Every return filed through this system is the user's own legal declaration under the Nigeria Tax Administration Act 2025. Users must confirm all figures before any submission is initiated.

### Target User
- Freelancers and self-employed individuals in Nigeria
- Professionals with multiple income streams (salary + side income)
- Gig workers (Upwork, Fiverr, Toptal, local platforms)
- Remote workers earning foreign income (USD/GBP/EUR) taxable in Nigeria
- Crypto traders with NTA 2025 taxable digital asset gains
- Small business owners filing as individuals
- Anyone currently filing on etax.lirs.net manually

### Core Value Proposition
| Today (Manual) | With AutoPITA |
|---|---|
| User manually reviews 12 months of transactions | AI classifies every transaction automatically |
| User guesses which income is taxable | RAG system applies NTA 2025 rules accurately |
| User fills LIRS form fields manually | System pre-fills every field from computed data |
| User spends 2–4 hours filing | User reviews and confirms in under 5 minutes |
| User doesn't know about rent relief under NTA 2025 | System identifies and applies all eligible reliefs |
| User unaware of DTT credits on foreign income | System flags double-taxation treaty credits |

---

## 2. System Architecture

### High-Level Architecture
```
┌────────────────────────────────────────────────────────────────────┐
│                          AUTOPITA SYSTEM                            │
│                                                                      │
│  ┌──────────┐    ┌──────────────┐    ┌──────────────────┐          │
│  │   React  │───▶│  FastAPI     │───▶│   PostgreSQL     │          │
│  │ Frontend │    │  Backend     │    │   (Neon)         │          │
│  └──────────┘    └──────┬───────┘    └──────────────────┘          │
│                         │                                            │
│          ┌──────────────┼──────────────┐                            │
│          ▼              ▼              ▼                             │
│  ┌──────────────┐ ┌──────────┐ ┌────────────────┐                  │
│  │ Bank Aggreg. │ │  LLM     │ │   ChromaDB     │                  │
│  │ (Mono/CSV)   │ │ (Primary │ │  Vector Store  │                  │
│  └──────────────┘ │ +Fallback│ └────────────────┘                  │
│                   └──────────┘        │                             │
│                              ┌────────▼───────────┐                 │
│                              │  NTA 2025 + LIRS   │                 │
│                              │  Document Corpus   │                 │
│                              └────────────────────┘                 │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                    FILING LAYER                               │  │
│  │                                                               │  │
│  │  ┌─────────────────────┐    ┌──────────────────────────────┐ │  │
│  │  │  Playwright Engine  │    │  Manual Filing Fallback       │ │  │
│  │  │  (primary path)     │    │  (pre-filled form for user)   │ │  │
│  │  └─────────────────────┘    └──────────────────────────────┘ │  │
│  │                                                               │  │
│  │  ┌─────────────────────────────────────────────────────────┐ │  │
│  │  │  Portal Health Monitor (runs daily, alerts on breakage) │ │  │
│  │  └─────────────────────────────────────────────────────────┘ │  │
│  └──────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────┘
```

### Layer Responsibilities

| Layer | Technology | Responsibility |
|---|---|---|
| API Routes | FastAPI | HTTP handling, input validation, response shaping |
| Services | Python | All business logic — classification, computation, filing |
| Models | SQLAlchemy | Database schema definition only |
| Schemas | Pydantic | Request/response contracts |
| Database | PostgreSQL (Neon) | Persistent storage |
| AI Classification | Groq (primary) + Anthropic Claude (fallback) | Transaction tax category classification |
| Tax Knowledge | ChromaDB + RAG | NTA 2025 law retrieval and Q&A |
| Filing (primary) | Playwright | Browser automation on etax.lirs.net |
| Filing (fallback) | Manual pre-fill UI | User-driven submission when Playwright unavailable |
| Portal Monitor | Playwright + cron | Daily health check against live LIRS portal |
| Bank Data | Mono API (primary) + Manual CSV/PDF | Transaction ingestion from Nigerian banks |

---

## 3. Project Folder Structure

```
autopita/
├── app/
│   ├── __init__.py
│   ├── main.py                     # FastAPI app + lifespan
│   ├── config.py                   # Pydantic settings — single source of truth
│   ├── dependencies.py             # get_db and shared FastAPI dependencies
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── router.py           # Registers all v1 routes
│   │       ├── auth.py             # Register, login, JWT
│   │       ├── transactions.py     # Ingest, list, classify transactions
│   │       ├── tax.py              # Compute tax return, get summary
│   │       ├── filing.py           # Initiate and track LIRS filing
│   │       ├── chat.py             # RAG Q&A on Nigerian tax law
│   │       └── health.py           # App, DB, and portal health checks  ← NEW
│   │
│   ├── models/
│   │   ├── __init__.py             # Exports all models
│   │   ├── base.py                 # DeclarativeBase + TimestampMixin
│   │   ├── user.py                 # User model
│   │   ├── transaction.py          # Transaction + enums
│   │   ├── tax_return.py           # TaxReturn + ReturnStatus enum
│   │   └── filing.py               # Filing + FilingStatus enum
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── auth.py                 # RegisterRequest, LoginRequest, TokenResponse
│   │   ├── transaction.py          # TransactionCreate, TransactionOut
│   │   ├── tax.py                  # TaxReturnOut, TaxSummary, TaxBand
│   │   └── filing.py               # FilingRequest, FilingStatusOut, ManualFilingOut  ← UPDATED
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── auth_service.py         # Password hashing, JWT creation/verification
│   │   ├── classifier.py           # AI transaction classification (primary + fallback LLM)  ← UPDATED
│   │   ├── tax_engine.py           # NTA 2025 tax computation logic
│   │   ├── rag_service.py          # ChromaDB ingestion + RAG query
│   │   ├── filing_engine.py        # Playwright LIRS eTax automation
│   │   ├── manual_filing.py        # Manual fallback: pre-filled form generation  ← NEW
│   │   └── portal_monitor.py       # Daily health check against etax.lirs.net     ← NEW
│   │
│   ├── compliance/                                                                  ← NEW
│   │   ├── __init__.py
│   │   ├── audit.py                # Audit trail logging for all data access
│   │   ├── consent.py              # User consent record management
│   │   └── retention.py            # Data retention policy enforcement
│   │
│   ├── db/
│   │   ├── __init__.py
│   │   └── session.py              # Async engine + AsyncSessionLocal
│   │
│   └── core/
│       ├── __init__.py
│       └── exceptions.py           # Custom exceptions + FastAPI handlers
│
├── alembic/                        # DB migrations — never edit manually
│   └── versions/
├── tests/
│   ├── test_classifier.py
│   ├── test_tax_engine.py
│   ├── test_filing.py
│   └── test_portal_monitor.py      # ← NEW
├── docs/
│   ├── NTA_2025.pdf                # Nigeria Tax Act 2025 (primary source)
│   ├── NTAA_2025.pdf               # Nigeria Tax Administration Act 2025  ← NEW
│   ├── PITA_amended.pdf            # Personal Income Tax Act (historical reference)
│   └── LIRS_guidelines.pdf         # LIRS practice notes and circulars
├── .env
├── .env.example
├── .gitignore
├── requirements.txt
├── PROJECT_BLUEPRINT.md
└── EXECUTION_PLAN.md
```

---

## 4. Database Schema

### Users Table
```
users
├── id                  UUID, PK
├── email               VARCHAR(255), UNIQUE, NOT NULL, INDEXED
├── full_name           VARCHAR(255), NOT NULL
├── payer_id            VARCHAR(50), UNIQUE, NULLABLE  ← LIRS Payer ID e.g. N-4849436
├── nin                 VARCHAR(20), NULLABLE  ← NIN now mandatory TIN under NTA 2025  ← NEW
├── phone               VARCHAR(20), NULLABLE
├── state_of_residence  VARCHAR(50), DEFAULT 'Lagos'
├── is_active           BOOLEAN, DEFAULT TRUE
├── hashed_password     VARCHAR(255), NOT NULL
├── ndpa_consent_given  BOOLEAN, DEFAULT FALSE  ← NDPA 2023 explicit consent  ← NEW
├── ndpa_consent_at     TIMESTAMPTZ, NULLABLE   ← Timestamp of consent         ← NEW
├── data_deletion_requested_at TIMESTAMPTZ, NULLABLE  ← Right to erasure       ← NEW
├── created_at          TIMESTAMPTZ
└── updated_at          TIMESTAMPTZ
```

### Transactions Table
```
transactions
├── id                  UUID, PK
├── user_id             UUID, FK → users.id, INDEXED
├── amount              NUMERIC(15,2), NOT NULL
├── currency            VARCHAR(3), DEFAULT 'NGN'
├── foreign_amount      NUMERIC(15,2), NULLABLE  ← Original amount before conversion  ← NEW
├── exchange_rate       NUMERIC(15,6), NULLABLE  ← CBN rate used for conversion        ← NEW
├── transaction_type    ENUM(credit, debit), NOT NULL
├── narration           VARCHAR(500), NOT NULL
├── bank_name           VARCHAR(100), NOT NULL
├── bank_reference      VARCHAR(100), NULLABLE
├── transaction_date    TIMESTAMPTZ, NOT NULL
├── tax_category        ENUM(taxable_income, exempt_income,
│                            deductible_expense, non_deductible_expense,
│                            unclassified), DEFAULT 'unclassified'
├── income_type         VARCHAR(50), NULLABLE
│                       ← salary | trade_income | dividend | interest |
│                          rent_income | foreign_income | digital_asset_gain |
│                          gratuity | annuity | commission | other_income
├── ai_confidence       NUMERIC(5,4), NULLABLE  ← 0.0000 to 1.0000
├── ai_reasoning        VARCHAR(500), NULLABLE
├── ai_provider         VARCHAR(50), NULLABLE   ← 'groq' | 'anthropic'  ← NEW
├── requires_dtt_review BOOLEAN, DEFAULT FALSE  ← Flag for double-tax treaty cases  ← NEW
├── is_manually_reviewed BOOLEAN, DEFAULT FALSE
├── created_at          TIMESTAMPTZ
└── updated_at          TIMESTAMPTZ
```

### Tax Returns Table
```
tax_returns
├── id                  UUID, PK
├── user_id             UUID, FK → users.id, INDEXED
├── tax_year            INTEGER, NOT NULL
├── status              ENUM(draft, computed, pending_review,
│                            approved, filed, failed)
│
│   ── Income Fields (maps to LIRS form exactly) ──
├── salary              NUMERIC(15,2), DEFAULT 0
├── allowance           NUMERIC(15,2), DEFAULT 0
├── commission          NUMERIC(15,2), DEFAULT 0
├── trade_income        NUMERIC(15,2), DEFAULT 0
├── pension             NUMERIC(15,2), DEFAULT 0
├── annuity             NUMERIC(15,2), DEFAULT 0
├── gratuities          NUMERIC(15,2), DEFAULT 0
├── foreign_income      NUMERIC(15,2), DEFAULT 0
├── digital_asset_gains NUMERIC(15,2), DEFAULT 0  ← NTA 2025 taxable  ← NEW
├── dividend            NUMERIC(15,2), DEFAULT 0
├── interest            NUMERIC(15,2), DEFAULT 0
├── rent_income         NUMERIC(15,2), DEFAULT 0
├── other_income        NUMERIC(15,2), DEFAULT 0
│
│   ── Computed Values ──
├── gross_income        NUMERIC(15,2), DEFAULT 0
├── total_reliefs       NUMERIC(15,2), DEFAULT 0
├── chargeable_income   NUMERIC(15,2), DEFAULT 0
├── tax_liability       NUMERIC(15,2), DEFAULT 0
├── tax_paid            NUMERIC(15,2), DEFAULT 0  ← PAYE already deducted by employer
├── foreign_tax_credit  NUMERIC(15,2), DEFAULT 0  ← DTT credit for tax paid abroad  ← NEW
├── tax_payable         NUMERIC(15,2), DEFAULT 0
├── unclassified_txn_count INTEGER, DEFAULT 0     ← Blocks filing if > 0  ← NEW
│
│   ── Accommodation (Tab 2 of LIRS form) ──
├── accommodation_address    VARCHAR(500), NULLABLE
├── accommodation_type       VARCHAR(100), NULLABLE
├── ownership_type           VARCHAR(100), NULLABLE
├── owner_name               VARCHAR(255), NULLABLE
├── owner_payer_id           VARCHAR(50), NULLABLE
├── owner_address            VARCHAR(500), NULLABLE
├── rent_paid                NUMERIC(15,2), DEFAULT 0
├── rent_paid_by_employer    NUMERIC(15,2), DEFAULT 0
│
├── created_at          TIMESTAMPTZ
└── updated_at          TIMESTAMPTZ
```

### Filings Table
```
filings
├── id                  UUID, PK
├── tax_return_id       UUID, FK → tax_returns.id
├── status              ENUM(pending, in_progress, awaiting_confirmation,
│                            submitted, confirmed, failed, portal_unavailable)  ← UPDATED
├── filing_mode         ENUM(automated, manual_fallback)  ← NEW
├── portal_url          VARCHAR(255), DEFAULT 'https://etax.lirs.net'
├── lirs_reference      VARCHAR(100), NULLABLE  ← Return Ref ID from LIRS
├── filed_at            TIMESTAMPTZ, NULLABLE
├── error_message       TEXT, NULLABLE
├── error_code          VARCHAR(50), NULLABLE   ← SELECTOR_BROKEN | CAPTCHA | TIMEOUT | PORTAL_DOWN  ← NEW
├── screenshot_path     VARCHAR(500), NULLABLE
├── audit_log           JSONB, NOT NULL, DEFAULT '[]'  ← JSONB for queryable audit trail  ← UPDATED
├── created_at          TIMESTAMPTZ
└── updated_at          TIMESTAMPTZ
```

### Portal Health Log Table ← NEW
```
portal_health_logs
├── id                  UUID, PK
├── checked_at          TIMESTAMPTZ, NOT NULL
├── portal_reachable    BOOLEAN, NOT NULL
├── login_functional    BOOLEAN, NOT NULL
├── returns_tab_functional BOOLEAN, NOT NULL
├── tab1_selectors_valid   BOOLEAN, NOT NULL
├── error_detail        TEXT, NULLABLE
└── created_at          TIMESTAMPTZ
```

### Consent Records Table ← NEW
```
consent_records
├── id                  UUID, PK
├── user_id             UUID, FK → users.id
├── consent_type        VARCHAR(50)  ← 'data_processing' | 'bank_access' | 'filing_auth'
├── consent_given       BOOLEAN, NOT NULL
├── ip_address          VARCHAR(45), NULLABLE
├── user_agent          TEXT, NULLABLE
├── consented_at        TIMESTAMPTZ, NOT NULL
└── created_at          TIMESTAMPTZ
```

---

## 5. API Endpoints

### Authentication
```
POST   /api/v1/auth/register         Create new user account + record NDPA consent
POST   /api/v1/auth/login            Login, returns JWT token
GET    /api/v1/auth/me               Get current user profile
DELETE /api/v1/auth/me               Request data deletion (NDPA right to erasure)  ← NEW
```

### Transactions
```
POST   /api/v1/transactions/          Ingest single transaction (manual)
POST   /api/v1/transactions/bulk      Bulk ingest from bank/CSV
GET    /api/v1/transactions/          List user transactions (paginated)
GET    /api/v1/transactions/{id}      Get single transaction
PATCH  /api/v1/transactions/{id}      Manually update tax category
POST   /api/v1/transactions/classify  Trigger AI classification on unclassified
GET    /api/v1/transactions/flagged   List transactions requiring review (DTT, low-confidence)  ← NEW
```

### Tax
```
POST   /api/v1/tax/compute/{year}     Compute tax return from classified transactions
GET    /api/v1/tax/returns            List all user tax returns
GET    /api/v1/tax/returns/{id}       Get specific tax return detail
GET    /api/v1/tax/summary/{year}     Monthly income breakdown + YTD liability
PATCH  /api/v1/tax/returns/{id}       Update return fields before filing
GET    /api/v1/tax/returns/{id}/warnings   Get computation warnings (unclassified, DTT, etc.)  ← NEW
```

### Filing
```
POST   /api/v1/filing/initiate              Start Playwright filing for a tax return
GET    /api/v1/filing/{id}/status           Poll filing status
POST   /api/v1/filing/{id}/confirm          User confirms — trigger final submission
GET    /api/v1/filing/{id}/screenshot       Get pre-submission screenshot
GET    /api/v1/filing/history               List all filing attempts
POST   /api/v1/filing/initiate-manual       Initiate manual fallback filing  ← NEW
GET    /api/v1/filing/{id}/prefill-data     Get pre-filled form data for manual mode  ← NEW
```

### Chat (RAG)
```
POST   /api/v1/chat/ask               Ask a question about Nigerian tax law
GET    /api/v1/chat/history           Get conversation history
```

### Health
```
GET    /health                         App + DB health check
GET    /health/portal                  Current LIRS portal health status  ← NEW
GET    /health/portal/history          Last 30 days of portal health logs  ← NEW
```

---

## 6. AI Classification System

### How It Works
Every bank transaction narration is sent to the primary LLM (Groq LLaMA 3.3-70B) with a structured prompt. If Groq is unavailable or returns a non-JSON response, the request falls back to Anthropic Claude. The model returns a JSON classification.

### LLM Provider Strategy
```
Primary:  Groq (LLaMA 3.3-70B) — fast inference, cost-effective
Fallback: Anthropic Claude (claude-haiku) — invoked automatically on Groq timeout or error

Fallback trigger conditions:
- Groq API returns HTTP 5xx
- Groq response is not valid JSON after 2 retries
- Groq response time exceeds 10 seconds

The provider used is stored in transactions.ai_provider for audit and debugging.
```

### Transaction Categories
| Category | Description | Example Narration |
|---|---|---|
| `taxable_income` | Earned income subject to NTA 2025 | "UPWORK PAYMENT", "SALARY PAYROLL", "TRANSFER FROM CLIENT" |
| `exempt_income` | Income excluded under NTA 2025 | "PENSION WITHDRAWAL", "INSURANCE PAYOUT" |
| `deductible_expense` | Allowable deduction under NTA | "NHIS CONTRIBUTION", "PENSION CONTRIBUTION" |
| `non_deductible_expense` | Personal spending, no tax effect | "UBER EATS", "AIRTIME PURCHASE", "ATM WITHDRAWAL" |
| `unclassified` | Ambiguous — requires human review | Anything below confidence threshold or flagged for DTT |

### Edge-Case Income Types the Classifier Must Handle ← NEW
| Income Type | Notes |
|---|---|
| `digital_asset_gain` | Crypto trades, NFT sales — NTA 2025 taxable; valuation in NGN at CBN rate on transaction date |
| `foreign_income` | Upwork/Fiverr/PayPal inflows — taxable if user is a Nigerian tax resident; flag for DTT credit review if origin country has a treaty with Nigeria |
| `gratuity` | Terminal benefits — taxable under NTA 2025 (exemption threshold raised to ₦50M) |
| `paye_reconciliation` | Credit for PAYE already deducted by employer — reduces tax_payable, not additional income |
| `nil_return_candidate` | Income below ₦800,000 after reliefs — still requires filing, computation shows zero payable |

### Classifier Prompt Structure
```
System: You are a Nigerian tax classification expert operating under the Nigeria Tax Act 2025.
        Classify bank transactions accurately.
        Nigerian narrations may be abbreviated, use Pidgin, or reference local merchants.
        For foreign currency inflows, flag requires_dtt_review if the source country
        has a double-taxation treaty with Nigeria (e.g. UK, South Africa, Pakistan, Netherlands).
        Always return valid JSON only. No prose, no markdown.

User:   Classify this transaction:
        Amount: ₦150,000 (CREDIT)
        Narration: "PAYMENT FROM JOHN DOE CONSULTING"
        Bank: GTBank
        Date: 2025-03-15
        User's state of residence: Lagos

        Return JSON:
        {
          "tax_category": "taxable_income",
          "income_type": "trade_income",
          "confidence": 0.89,
          "reasoning": "Payment from named individual for consulting services — trade income under NTA 2025 Section 4",
          "requires_dtt_review": false
        }
```

### Confidence Thresholds and Escalation
```
>= 0.85  → Auto-classified, stored, no review needed
0.75–0.84 → Classified, flagged for optional user review
< 0.75   → Marked unclassified, user MUST review before tax computation proceeds

Blocking rule: A tax return with unclassified_txn_count > 0 cannot advance
to status = approved or trigger a filing. The user must manually resolve
all unclassified transactions first.

DTT flag: Any transaction with requires_dtt_review = true is surfaced
on the flagged transactions endpoint regardless of confidence score.
The user must confirm or override the DTT credit claim.
```

---

## 7. Tax Computation Engine (NTA 2025)

### Tax Bands — Nigeria Tax Act 2025 (Effective January 1, 2026)
```
Annual Chargeable Income     Rate
──────────────────────────────────
₦0 – ₦800,000               0%   (exempt threshold)
₦800,001 – ₦3,000,000       15%
₦3,000,001 – ₦12,000,000    18%
₦12,000,001 – ₦25,000,000   21%
₦25,000,001 – ₦50,000,000   23%
Above ₦50,000,000            25%
```
> ⚠️ These bands are sourced from the signed NTA 2025 text and corroborated by KPMG Nigeria, Baker Tilly Nigeria, and PwC Nigeria analysis as of January 2026. Verify against the official NTA gazette before any production deployment.

### Reliefs Available Under NTA 2025 ← UPDATED
```
1. Rent relief
   → 20% of annual rent paid, capped at ₦500,000
   → Requires: accommodation address, rental amount, tenancy period
   → Not available to homeowners
   → CRA has been ABOLISHED — do not apply old PITA CRA rules

2. Pension contribution (statutory)
   → 8% of gross income (employee contribution)
   → Requires: RSA account number, Pension Fund Admin name

3. NHIS contribution
   → Actual amount contributed, evidenced

4. Life assurance premium
   → Actual premium paid, evidenced

5. Foreign tax credit (DTT)  ← NEW
   → For income earned in a treaty country where tax was already paid
   → Nigeria has DTTs with: UK, South Africa, Pakistan, Netherlands,
     Romania, Slovakia, China, Belgium, France, Canada, Czech Republic,
     Philippines, South Korea, Spain, Sweden
   → Credit capped at Nigerian tax that would otherwise apply to that income
   → Requires: proof of foreign tax payment, country of income origin
```

### Computation Steps ← UPDATED
```
1. Sum all classified taxable_income transactions by income_type
   → salary, trade_income, dividend, interest, foreign_income,
      digital_asset_gains, gratuities, commission, annuity, etc.

2. Calculate gross_income
   → sum of all income categories

3. Apply reliefs in order
   → pension contribution (8% of gross, if evidenced)
   → NHIS contribution (if evidenced)
   → life assurance premium (if evidenced)
   → rent relief: min(rent_paid × 0.20, 500000) — NTA 2025 replaces CRA

4. chargeable_income = gross_income - total_reliefs

5. Apply progressive tax bands to chargeable_income
   → tax_liability (use marginal rate logic — not flat rate on total)

6. tax_payable = tax_liability - tax_paid - foreign_tax_credit
   → tax_paid = PAYE already deducted by employer
   → foreign_tax_credit = DTT credit confirmed by user review

7. Edge case: nil return
   → if chargeable_income <= 0 after reliefs: tax_payable = 0
   → filing is still legally required under NTAA 2025 Section 13
```

### Edge Cases the Engine Must Handle ← NEW
```
Foreign income (CBN rate conversion)
  → foreign_amount × exchange_rate_on_transaction_date = NGN amount
  → Use CBN official rate, not black market rate
  → exchange_rate stored per transaction for audit trail

Digital asset gains
  → Net gain = disposal proceeds - cost basis (both in NGN at CBN rate)
  → Losses may offset gains within the same tax year

Gratuities
  → Taxable under NTA 2025
  → Exemption threshold raised from ₦10M to ₦50M for loss-of-employment compensation
  → Amounts above ₦50M are taxable at standard progressive rates

PAYE reconciliation
  → If user has salaried employment: PAYE deducted by employer reduces tax_payable
  → Employer-filed P9/payslips are the source of truth — user must upload or confirm

Nil return
  → chargeable_income <= ₦800,000 after reliefs → tax_payable = 0
  → Still requires annual filing under NTAA 2025 Section 13
  → AutoPITA should pre-fill and assist with nil return, not block the user
```

---

## 8. LIRS eTax Filing Automation

### Portal Details
- **URL:** https://etax.lirs.net
- **Filing URL:** https://etax.lirs.net/user/returns
- **Primary Technology:** Playwright (Python) with Chromium
- **Fallback Technology:** Manual pre-fill UI (see Section 8.3)

### Form Structure (Fully Mapped)
The LIRS annual return form has 5 tabs:

**Tab 1 — Statement of Income**
Fields: Salary, Commission, Trade Income, Allowance, Pension, Annuity,
Gratuities, Foreign Income, Dividend, Interest, Rent, Other Income(s)
Plus: Document upload section

**Tab 2 — Mandatory Disclosure of Accommodation**
Fields: Address, Accommodation Type, Ownership Type (dropdown),
Owner Name, Owner Payer ID, Owner Address,
Rent Paid, Rent Paid By Employer, Date Started, Date End

**Tab 3 — Support Staff**
Dynamic: ADD STAFF button → entries per staff member

**Tab 4 — Assets**
Dynamic: ADD ASSET button → entries per asset

**Tab 5 — Other Disclosure for Reliefs**
Modal fields:
- A) Life Assurance: Yes/No radio
- B) NHIS: Yes/No radio
- C) NPS Statutory: RSA Account, Pension Fund Admin,
     Total Contribution, RSA Statement upload (file)
- D) NPS Voluntary: Yes/No radio

**Submission Flow:**
```
Login → Select Year → Tab 1 → NEXT → Tab 2 → NEXT →
Tab 3 → NEXT → Tab 4 → NEXT → Tab 5 → ADD RELIEF →
[STOP — show user screenshot] → User confirms → SUBMIT
```

### Filing States ← UPDATED
```
PENDING → IN_PROGRESS → AWAITING_CONFIRMATION → SUBMITTED → CONFIRMED
                                                           ↘ FAILED
        ↘ PORTAL_UNAVAILABLE → [notify user + offer manual fallback]
```

### Safety Rules (Non-Negotiable)
1. Never auto-submit without explicit user confirmation
2. Always take a screenshot before confirmation step
3. Store full audit log of every Playwright action in JSONB
4. On any portal error, set status to FAILED with structured error_code
5. Never store LIRS credentials in plaintext — session-scoped memory only
6. **NEW:** If portal_health_logs shows portal unhealthy → do not initiate new filing sessions; immediately offer manual fallback
7. **NEW:** A tax return with unclassified_txn_count > 0 cannot initiate filing

### 8.3 Portal Health Monitor ← NEW

The portal health monitor is a Playwright script that runs on a daily cron (00:30 WAT) against the live LIRS portal using a dedicated test account with a zero-income return. It does not submit anything.

**Filing session scheduling:**
```
All Playwright filing sessions are queued and executed between 02:00–04:00 WAT.
Reason: LIRS portal load is lowest during these hours. During March 28–April 14
(peak filing season), portal congestion and timeouts increase significantly
in business hours. Off-peak scheduling reduces failure rate and improves
screenshot quality for the user confirmation step.

Sessions initiated by users outside this window are queued and
the user is notified: "Your filing is scheduled for tonight at 02:00 WAT."
Users who cannot wait can use the manual fallback path immediately.
```

**What it checks:**
```
1. Portal reachable (HTTP 200 on etax.lirs.net)
2. Login form fields present (email, password selectors)
3. Login succeeds with test credentials
4. "Returns" tab navigable
5. Tab 1 fields present and fillable (salary, trade_income selectors)
6. File upload field present on Tab 1
7. Tab navigation (NEXT button) functional
```

**On failure:**
```
- Log failure to portal_health_logs with error_detail
- Set a system-wide flag: PORTAL_FUNCTIONAL = False
- Send alert to the engineering team (email/Slack webhook)
- All subsequent /filing/initiate calls return 503 with:
  { "error": "portal_unavailable", "fallback_available": true }
- Users are directed to /filing/initiate-manual
```

**Selector version pinning:**
- All Playwright selectors are defined in a single config file: `app/services/filing_selectors.py`
- When the monitor detects a broken selector, it logs which specific selector failed
- This isolates portal changes to a single fix location, not scattered across the codebase

### 8.4 Manual Filing Fallback ← NEW

When `PORTAL_FUNCTIONAL = False` or when the user chooses manual mode:

1. The system generates a structured summary from the computed tax return:
   - All income fields, computed totals, reliefs claimed
   - Step-by-step instructions for each LIRS form tab
   - Exact values to enter per field

2. The frontend presents this as a guided form assistant: "Enter this value in the Salary field on Tab 1."

3. The user navigates the LIRS portal themselves; AutoPITA serves as a reference panel.

4. Once the user confirms they have submitted, the filing record is updated with `filing_mode = manual_fallback` and `status = submitted`.

This guarantees the product delivers its core value — accurate tax computation and data preparation — even when the automation layer is broken.

---

## 9. RAG System (Tax Law Q&A)

### Document Corpus
```
docs/
├── NTA_2025.pdf          Nigeria Tax Act 2025 (primary source)
├── NTAA_2025.pdf         Nigeria Tax Administration Act 2025  ← NEW
├── PITA_amended.pdf      Personal Income Tax Act (historical reference)
└── LIRS_guidelines.pdf   LIRS practice notes and circulars
```

> **Why NTAA_2025.pdf is added:** The NTAA governs filing procedures, penalties, deadlines, and the Best of Judgment assessment process. Users frequently ask about penalties for late filing (₦100,000 for the first month, ₦50,000 per subsequent month under NTAA Section 101) and what happens if they don't file. The RAG system must answer these accurately.

### RAG Pipeline
```
1. Load PDFs → LangChain document loaders
2. Chunk into 512-token segments with 50-token overlap
3. Embed with sentence-transformers (or Groq embeddings)
4. Store in ChromaDB (local vector store)
5. At query time:
   → embed user question
   → retrieve top 5 relevant chunks
   → pass chunks + question to Groq LLM
   → return answer with source citations (document + section number)
```

### Example Queries It Must Handle
- "Is my Upwork income taxable in Nigeria?"
- "What reliefs can I claim under NTA 2025?"
- "What is the tax rate on dividend income?"
- "Do I need to file a nil return if I earned below ₦800,000?"
- "What is the penalty for late filing?"
- "I paid tax in the UK on my freelance income — can I claim a credit in Nigeria?" ← NEW
- "Are my crypto gains taxable under NTA 2025?" ← NEW
- "My employer already deducts PAYE — do I still need to file?" ← NEW

---

## 10. Bank Integration

### Provider Strategy
- **Primary:** Mono API (read-only transaction access)
- **Required fallback:** Manual CSV/PDF bank statement upload — must be built and tested before launch, not treated as future work
- **Architecture:** Abstract `BankProvider` base class — swap providers without touching business logic

> **Mono Ownership Risk Note:** Mono was acquired by Flutterwave in early 2026. While Mono continues to operate independently, its API pricing and terms are ultimately controlled by Flutterwave. If Flutterwave restricts access or raises prices, the Manual CSV fallback becomes the primary data path. The abstraction layer is not optional — it is the insurance policy against this dependency.

### Bank Abstraction Layer
```python
class BankProvider:
    async def connect_account(user_id: str, auth_code: str) -> AccountInfo
    async def fetch_transactions(account_id: str, from_date: date, to_date: date) -> list[Transaction]
    async def fetch_balance(account_id: str) -> Balance
    async def refresh_account(account_id: str) -> None

class MonoProvider(BankProvider): ...
class ManualUploadProvider(BankProvider): ...  # CSV and PDF bank statement parsing
```

### Normalized Transaction Schema
All transactions — regardless of source — are stored in the same format:
```python
{
    "amount": Decimal,            # NGN amount (converted if foreign currency)
    "currency": "NGN",
    "foreign_amount": Decimal | None,  # Original amount if foreign currency  ← NEW
    "exchange_rate": Decimal | None,   # CBN rate used at transaction date     ← NEW
    "transaction_type": "credit" | "debit",
    "narration": str,
    "bank_name": str,
    "bank_reference": str | None,
    "transaction_date": datetime
}
```

### Manual Upload Handling ← NEW
For users who cannot or will not connect via Mono:

```
Supported formats:
  - CSV: GTBank, Access, Zenith, First Bank, UBA, Fidelity statement exports
  - PDF: Standard Nigerian bank statement format (text-extractable)

Parser responsibilities:
  - Detect and normalize narration fields (bank-specific column names vary)
  - Convert foreign currency transactions using CBN rate on transaction date
  - Deduplicate against existing transactions by bank_reference

This path must be fully functional at launch. It is not optional.
```

---

## 11. Security and Compliance Requirements

### Security
| Requirement | Implementation |
|---|---|
| Password storage | bcrypt hashing via passlib |
| API authentication | JWT Bearer tokens (python-jose) |
| Token expiry | Access: 30min, Refresh: 7 days |
| LIRS credentials | Session-scoped memory only, never written to disk or database |
| Bank tokens | Encrypted at rest using Fernet (cryptography library) |
| Rate limiting | slowapi middleware |
| CORS | Configured per environment |
| Audit trail | All sensitive data access logged to audit table with user_id, action, timestamp |

### NDPA 2023 Compliance ← UPDATED (replaces "NDPR compliance")

> The governing data protection law in Nigeria is the **Nigeria Data Protection Act 2023 (NDPA)**, not the NDPR 2019. The NDPR was superseded on September 19, 2025, when the General Application and Implementation Directive (GAID) took effect. All references to "NDPR compliance" in v1.0 of this blueprint are replaced by NDPA compliance obligations.

AutoPITA processes highly sensitive personal financial data: bank transaction records, salary information, tax filings, and LIRS credentials. This places it in the highest-risk category under NDPA.

**Required compliance actions before launch:**

| Obligation | Requirement | Status |
|---|---|---|
| NDPC Registration | Register as a data controller of major importance (processes financial data of potentially 2,000+ users) | Must complete before launch |
| Data Protection Impact Assessment (DPIA) | Required before processing sensitive financial data at scale | Must complete before launch |
| Data Protection Officer (DPO) | Appoint a DPO once active user count approaches 2,000 | Plan for first 6 months |
| Privacy Policy | Publish a clear policy in plain language covering data use, retention, sharing | Must complete before launch |
| Explicit Consent | Obtain and record explicit consent from each user at registration for: (a) bank data access, (b) tax computation processing, (c) LIRS filing on their behalf | Captured in consent_records table |
| Breach Notification | Notify NDPC within 72 hours of any breach that risks user rights | Incident response procedure required |
| Annual Audit Report | Submit annual NDPC compliance audit if processing 2,000+ data subjects | Required once at scale |
| Data Retention | Define and enforce retention periods per data category | See Section 11.1 |
| Right to Erasure | Users can request account + data deletion; must be processed within 30 days | DELETE /api/v1/auth/me endpoint |

### 11.1 Data Retention Policy ← NEW
```
Transaction data:           7 years from tax year end (Nigerian tax statute of limitations)
Tax return records:         7 years from filing date
Filing audit logs:          7 years from filing date
Bank connection tokens:     Deleted on user account disconnect or deletion
LIRS session credentials:   Never persisted — session-scoped only
Portal health logs:         90 days rolling
User account data:          Until deletion requested + 30-day grace period
```

---

## 12. Technology Stack

### Backend
| Package | Version | Purpose |
|---|---|---|
| fastapi | latest | Web framework |
| uvicorn | latest | ASGI server |
| sqlalchemy | 2.x | ORM (async) |
| asyncpg | latest | PostgreSQL async driver |
| alembic | latest | Database migrations |
| pydantic-settings | latest | Configuration management |
| groq | latest | Primary LLM API client |
| anthropic | latest | Fallback LLM API client ← NEW |
| langchain | latest | RAG pipeline |
| langchain-groq | latest | Groq LangChain integration |
| chromadb | latest | Vector store |
| playwright | latest | Browser automation |
| python-jose | latest | JWT |
| passlib | latest | Password hashing |
| bcrypt | latest | Hashing algorithm |
| cryptography | latest | Fernet encryption for bank tokens ← NEW |
| apscheduler | latest | Cron job for portal health monitor ← NEW |

### Infrastructure
| Service | Purpose |
|---|---|
| Neon | PostgreSQL database (cloud) |
| Render | Backend deployment |
| Groq | Primary LLM inference |
| Anthropic Claude | Fallback LLM inference ← NEW |
| ChromaDB | Local vector store (no external service) |

---

## 13. Key Architectural Decisions

**Decision 1: RAG over Fine-tuning**
We use RAG instead of fine-tuning an LLM on Nigerian tax law. Reason: Nigerian tax law changes annually (Finance Act). RAG lets us update the knowledge base by swapping documents — no retraining required.

**Decision 2: State-level portal first (LIRS)**
We automate LIRS eTax (Lagos) only for MVP. Lagos has the largest individual taxpayer base in Nigeria. Other states follow the same LIRS pattern — expansion is mechanical work, not architectural rethinking.

**Decision 3: Stop-before-submit filing**
The Playwright automation fills all form fields but always stops before final submission, showing the user a screenshot for confirmation. This protects against AI classification errors, portal glitches, and liability exposure.

**Decision 4: Mono for bank data (with abstraction)**
Mono is the primary Nigerian open banking aggregator. Following its acquisition by Flutterwave in early 2026, we treat Mono as a vendor with acquisition-level dependency risk. The `BankProvider` abstraction is mandatory, and the `ManualUploadProvider` must be fully functional at launch.

**Decision 5: Async everywhere**
All database calls, HTTP calls, and AI API calls are async. The filing engine runs as a background task — it never blocks an HTTP request.

**Decision 6: Portal resilience over portal dependency ← NEW**
The LIRS eTax portal is a government web application outside our control. It will change without notice. Our filing layer is therefore designed with two modes: automated (Playwright) and manual fallback (pre-fill assistant). A daily health monitor gates the automated path. The product's core value — accurate tax computation — is independent of whether the Playwright layer is working.

**Decision 7: LLM fallback for classification ← NEW**
Groq provides fast, cost-effective inference for transaction classification. However, a single-provider dependency on a startup-tier LLM service is not acceptable for a financial compliance product. Anthropic Claude (claude-haiku) is the fallback, invoked automatically on Groq failure. The fallback is transparent to the user.

**Decision 8: NDPA 2023 compliance is a launch prerequisite, not a post-launch task ← NEW**
AutoPITA processes bank transaction data, salary records, tax returns, and government portal credentials. This is the highest-sensitivity category of personal financial data under Nigerian law. NDPC registration, a DPIA, and a published Privacy Policy are required before any paying users onboard. Treating these as "we'll handle compliance later" is not acceptable — the NDPC has demonstrated willingness to impose nine-figure fines.

---

## 14. Tax Professional Sign-Off Requirement ← NEW

Before the tax computation engine is used by real users, the following must be reviewed and approved in writing by a qualified Nigerian tax professional (ICAN or CITN-certified):

- The full tax band computation logic in `tax_engine.py`
- The rent relief calculation (20% capped at ₦500,000, replacement for CRA)
- The PAYE reconciliation logic
- The foreign income and DTT credit handling
- The digital asset gains computation
- The nil return flow
- The gratuity exemption threshold (₦50M under NTA 2025)

This review must be dated, documented, and repeated whenever the Finance Act or NTA is amended. The product's legal disclaimer must accurately reflect its assistance role — it does not provide tax advice and is not a substitute for a qualified tax consultant in ambiguous or complex cases.

---

## 15. What This Is NOT (Scope Boundaries)

- Not a B2B product — corporate income tax, VAT, WHT are out of scope
- Not a multi-state product at MVP — Lagos LIRS only
- Not a payment product — we compute and file, we do not initiate tax payments
- Not a real-time product — bank sync runs on schedule, not instant
- Not a replacement for a tax professional — high-ambiguity cases (DTT, significant foreign income, disputed transactions) must be referred
- Not a legal tax advisory service — all computations are assistance tools; the user's confirmed submission is their own legal declaration under NTAA 2025

---

## 16. Pre-Launch Checklist (Go/No-Go Before First Paying User) ← NEW

No paying users should onboard until every item below is checked. This checklist consolidates the legal, technical, and product requirements identified across all engineering reviews.

### Legal & Compliance
- [ ] NDPC registration as a data controller of major importance completed
- [ ] Data Protection Impact Assessment (DPIA) completed and documented
- [ ] Privacy Policy published in plain language (covers data use, retention, third-party sharing)
- [ ] Terms of Service published — must include explicit "AI-assisted, not legal advice" disclaimer
- [ ] User consent flow implemented: explicit consent recorded at registration for bank access, tax computation, and LIRS filing
- [ ] Incident response procedure written: breach notification path to NDPC within 72 hours

### Tax Engine
- [ ] Full computation logic reviewed and approved in writing by a qualified Nigerian tax professional (ICAN or CITN-certified)
- [ ] Rent relief calculation validated (20% of annual rent, capped at ₦500,000; CRA not applied)
- [ ] PAYE reconciliation logic validated
- [ ] DTT credit handling validated for all 15 treaty countries
- [ ] Digital asset gains computation validated
- [ ] Nil return flow validated (zero payable but filing still required)
- [ ] Gratuity exemption threshold validated (₦50M under NTA 2025)

### AI Classifier
- [ ] Confidence threshold confirmed at 0.75 (below this → unclassified, user must review)
- [ ] Blocking rule enforced: filing cannot proceed with any unclassified transactions
- [ ] LLM fallback (Anthropic Claude) tested and working
- [ ] Nigerian narration edge cases tested: abbreviated text, Pidgin, local merchant names

### Filing Engine
- [ ] Portal health monitor live and running daily at 00:30 WAT
- [ ] Alert pipeline tested: engineering team notified within 5 minutes of portal failure
- [ ] Manual fallback path fully functional and user-tested
- [ ] WAT filing window (02:00–04:00) scheduler implemented and tested
- [ ] Filing selectors centralized in `filing_selectors.py`
- [ ] Stop-before-submit confirmed: no path exists to auto-submit without explicit user confirmation
- [ ] LIRS test account registered for health monitor use (zero-income, never submits)

### Bank Integration
- [ ] ManualUploadProvider (CSV + PDF) fully functional for all major Nigerian banks
- [ ] Mono integration tested end-to-end
- [ ] Bank token encryption (Fernet) tested

### Infrastructure
- [ ] Environment variables validated: no secrets in codebase
- [ ] Rate limiting confirmed active on all public endpoints
- [ ] CORS locked to production domain only
- [ ] Database backups configured on Neon
- [ ] Render deployment with health check endpoint confirmed

---

*Document maintained by the development team. Update when architectural decisions change.*  
*Version 2.1 — Updated May 2026. Changes from prior versions are marked ← NEW or ← UPDATED throughout.*
