# AutoPITA — Project Blueprint
> AI-Powered Personal Income Tax Automation for Nigeria
> Version: 2.0 | Status: In Development | Last Updated: May 2026
> Target: LIRS eTax Portal (Lagos State) — MVP

---

## Executive Summary

AutoPITA is an AI-powered backend system that connects to a Nigerian individual's bank accounts, automatically classifies every transaction under the Nigeria Tax Act 2025, computes their personal income tax liability, and automates the filing of their annual return on the LIRS eTax portal — requiring under 5 minutes of user input per year.

**Market Timing:** The NTA 2025, signed June 2025 and effective January 1, 2026, is the largest tax reform in Nigeria in 25 years. It created a compliance event — millions of self-employed Nigerians who never filed before are now legally mandated to do so. LIRS no longer accepts manual submissions. Electronic filing on etax.lirs.net is the only legal path.

**The Opportunity:** Nigeria has approximately 17.5 million gig and freelance workers. The government is actively enforcing compliance, with penalties ranging from N50,000 to N1,000,000 for non-filing. There is no consumer-grade product that automates personal income tax filing end-to-end in Nigeria today.

---

## 1. Product Overview

### What AutoPITA Does

```
Bank Accounts --> AI Classification --> Tax Computation --> LIRS Filing
     |                  |                    |                  |
 Mono API /        Groq LLaMA 3.3       NTA 2025 Rules     Playwright
 CSV Upload        + RAG System         Engine             Automation
```

The system operates in five stages:

1. Ingest — Connect bank accounts via Mono API or upload bank statements (PDF/CSV)
2. Classify — AI categorises every transaction: taxable income, exempt income, deductible expense, or non-deductible
3. Compute — Tax engine applies NTA 2025 bands and reliefs to produce exact tax liability
4. Review — User sees pre-filled return, monthly breakdown, and tax liability summary
5. File — Playwright automation fills the LIRS eTax form; user confirms and submits

### Target Users

- Freelancers and remote workers — Upwork, Fiverr, foreign client transfers
- Self-employed professionals — consultants, lawyers, doctors, creatives
- Multiple-income earners — salary + side business + investments
- Gig economy workers — Bolt drivers, food delivery, marketplace sellers
- Anyone earning above N800,000 annually who must now file under NTA 2025

### Core Value Proposition

| Without AutoPITA | With AutoPITA |
|---|---|
| 2-4 hours manually reviewing 12 months of transactions | AI classifies all transactions in seconds |
| Guessing which income is taxable | RAG system applies NTA 2025 rules accurately |
| Manually filling LIRS form fields | Every field pre-filled from computed data |
| Risk of errors attracting N100,000+ penalties | Reviewed computation before any submission |
| Fear of the process — most people simply don't file | Guided, simple, 5-minute confirmation flow |

---

## 2. Market Context

### Why Now — The NTA 2025 Compliance Event

- New N800,000 exempt threshold — individuals earning above this must file. Those below must still file a nil return to remain compliant for bank loans, visa applications, and government contracts.
- CRA eliminated — the old Consolidated Relief Allowance (21% of gross income) is gone. The replacement is a rent relief of 20% of annual rent paid, capped at N500,000. Most Nigerians do not know this has changed.
- Progressive bands restructured — new rates differ significantly from the old structure. Self-computation is now harder.
- Capital Gains Tax aligned with income rates — crypto P2P, stock platform withdrawals, and asset sales are now high-scrutiny areas.
- Enforcement escalating — LIRS is using internationally sourced platform data (Google, Facebook) for system validation. Non-compliance is no longer invisible.

### Competitive Landscape

| Product | Target | Tax Type | Filing Automation |
|---|---|---|---|
| TaxStreem | Businesses | VAT, WHT, CIT | Yes |
| Manual accountants | Anyone | All | Manual only |
| LIRS eTax portal | Anyone | Personal | Manual only |
| AutoPITA | Individuals | Personal income | Automated |

No product currently automates personal income tax filing end-to-end for Nigerian individuals. That is the gap AutoPITA fills.

---

## 3. System Architecture

### High-Level Architecture

```
+------------------------------------------------------------------+
|                        AUTOPITA SYSTEM                           |
|                                                                  |
|  +----------+    +---------------+    +---------------------+   |
|  |  React   |--->|   FastAPI     |--->|  PostgreSQL (Neon)  |   |
|  | Frontend |    |   Backend     |    |  Persistent Storage |   |
|  +----------+    +------+--------+    +---------------------+   |
|                         |                                        |
|          +--------------+--------------+                         |
|          v              v              v                         |
|  +--------------+ +----------+ +----------------+               |
|  |  Bank Layer  | |  Groq    | |   ChromaDB     |               |
|  | Mono / CSV   | | LLaMA3.3 | |  Vector Store  |               |
|  +--------------+ +----------+ +-------+--------+               |
|                                        |                         |
|                             +----------v---------+              |
|                             | NTA 2025 Document  |              |
|                             | Corpus (RAG)       |              |
|                             +--------------------+              |
|                                                                  |
|  +------------------------------------------------------------+  |
|  |           Playwright Filing Engine                         |  |
|  |  etax.lirs.net --> Form Fill --> Screenshot --> Confirm    |  |
|  |  + Daily Health Monitor + Queue & Retry (02:00 WAT)       |  |
|  +------------------------------------------------------------+  |
+------------------------------------------------------------------+
```

### Layer Responsibilities

| Layer | Technology | Responsibility |
|---|---|---|
| API Routes | FastAPI | HTTP handling, input validation, response shaping |
| Services | Python | All business logic — no logic in routes ever |
| Models | SQLAlchemy 2.x async | Database schema definition only |
| Schemas | Pydantic v2 | Request/response API contracts |
| Database | PostgreSQL via Neon | Persistent storage, fully managed cloud |
| AI Classification | Groq LLaMA 3.3-70B | Transaction tax category classification |
| Tax Knowledge | ChromaDB + RAG | NTA 2025 law retrieval and Q&A |
| Filing | Playwright + Chromium | Browser automation on etax.lirs.net |
| Bank Data | Mono API + CSV/PDF fallback | Transaction ingestion |

---

## 4. Project Folder Structure

```
autopita/
├── app/
│   ├── main.py                     # FastAPI app entry point + lifespan
│   ├── config.py                   # Pydantic settings — single config source
│   ├── dependencies.py             # get_db, get_current_user dependencies
│   │
│   ├── api/v1/
│   │   ├── router.py               # Aggregates all v1 routes
│   │   ├── auth.py                 # Register, login, JWT
│   │   ├── transactions.py         # Ingest, list, classify transactions
│   │   ├── tax.py                  # Compute return, monthly summary
│   │   ├── filing.py               # Initiate, track, confirm LIRS filing
│   │   └── chat.py                 # RAG Q&A on Nigerian tax law
│   │
│   ├── models/
│   │   ├── base.py                 # DeclarativeBase + TimestampMixin
│   │   ├── user.py                 # User model
│   │   ├── transaction.py          # Transaction + TaxCategory enum
│   │   ├── tax_return.py           # TaxReturn + ReturnStatus enum
│   │   └── filing.py               # Filing + FilingStatus enum
│   │
│   ├── schemas/
│   │   ├── auth.py                 # RegisterRequest, LoginRequest, TokenResponse
│   │   ├── transaction.py          # TransactionCreate, TransactionOut
│   │   ├── tax.py                  # TaxReturnOut, TaxSummary, TaxBandResult
│   │   └── filing.py               # FilingRequest, FilingStatusOut
│   │
│   ├── services/
│   │   ├── auth_service.py         # Password hashing, JWT creation/verification
│   │   ├── classifier.py           # AI classification via Groq
│   │   ├── tax_engine.py           # NTA 2025 computation — pure deterministic logic
│   │   ├── rag_service.py          # ChromaDB ingestion + RAG query
│   │   └── filing_engine.py        # Playwright automation + health monitor
│   │
│   ├── db/session.py               # Async engine + AsyncSessionLocal (Neon SSL)
│   └── core/exceptions.py          # Custom exceptions + FastAPI error handlers
│
├── alembic/versions/               # DB migrations — never edit manually
├── tests/
├── docs/
│   ├── NTA_2025.pdf                # Nigeria Tax Act 2025 — primary RAG source
│   ├── PITA_amended.pdf            # Legacy reference
│   └── LIRS_guidelines.pdf         # LIRS practice notes
├── scripts/
│   ├── seed_transactions.py        # Load mock data for testing
│   ├── ingest_documents.py         # Build ChromaDB vector store
│   └── demo_flow.py                # End-to-end demo script
├── screenshots/                    # Pre-submission filing screenshots
├── .env
├── requirements.txt
├── PROJECT_BLUEPRINT.md
└── EXECUTION_PLAN.md
```

---

## 5. Database Schema

### Users Table
```
users
├── id                   UUID, PK
├── email                VARCHAR(255), UNIQUE, NOT NULL, INDEXED
├── full_name            VARCHAR(255), NOT NULL
├── payer_id             VARCHAR(50), UNIQUE, NULLABLE     -- LIRS Payer ID e.g. N-4849436
├── phone                VARCHAR(20), NULLABLE
├── state_of_residence   VARCHAR(50), DEFAULT 'Lagos'
├── is_active            BOOLEAN, DEFAULT TRUE
├── hashed_password      VARCHAR(255), NOT NULL
├── created_at           TIMESTAMPTZ
└── updated_at           TIMESTAMPTZ
```

### Transactions Table
```
transactions
├── id                    UUID, PK
├── user_id               UUID, FK -> users.id, INDEXED
├── amount                NUMERIC(15,2), NOT NULL
├── currency              VARCHAR(3), DEFAULT 'NGN'
├── transaction_type      ENUM(credit, debit), NOT NULL
├── narration             VARCHAR(500), NOT NULL
├── bank_name             VARCHAR(100), NOT NULL
├── bank_reference        VARCHAR(100), NULLABLE
├── transaction_date      TIMESTAMPTZ, NOT NULL
│
│   -- AI Classification Output --
├── tax_category          ENUM(taxable_income, exempt_income,
│                              deductible_expense, non_deductible_expense,
│                              unclassified), DEFAULT 'unclassified'
├── income_type           VARCHAR(50), NULLABLE    -- salary/trade/dividend/rent etc
├── ai_confidence         NUMERIC(5,4), NULLABLE   -- 0.0000 to 1.0000
├── ai_reasoning          VARCHAR(500), NULLABLE   -- one sentence explanation
├── needs_review          BOOLEAN, DEFAULT FALSE   -- TRUE when confidence < 0.75
├── is_manually_reviewed  BOOLEAN, DEFAULT FALSE
│
├── created_at            TIMESTAMPTZ
└── updated_at            TIMESTAMPTZ
```

### Tax Returns Table
```
tax_returns
├── id                    UUID, PK
├── user_id               UUID, FK -> users.id, INDEXED
├── tax_year              INTEGER, NOT NULL
├── status                ENUM(draft, computed, pending_review, approved, filed, failed)
│
│   -- Income Fields (maps to LIRS eTax form exactly) --
├── salary                NUMERIC(15,2), DEFAULT 0
├── allowance             NUMERIC(15,2), DEFAULT 0
├── commission            NUMERIC(15,2), DEFAULT 0
├── trade_income          NUMERIC(15,2), DEFAULT 0
├── pension               NUMERIC(15,2), DEFAULT 0
├── annuity               NUMERIC(15,2), DEFAULT 0
├── gratuities            NUMERIC(15,2), DEFAULT 0
├── foreign_income        NUMERIC(15,2), DEFAULT 0
├── dividend              NUMERIC(15,2), DEFAULT 0
├── interest              NUMERIC(15,2), DEFAULT 0
├── rent_income           NUMERIC(15,2), DEFAULT 0
├── other_income          NUMERIC(15,2), DEFAULT 0
│
│   -- NTA 2025 Reliefs (CRA removed -- see Section 8) --
├── pension_relief        NUMERIC(15,2), DEFAULT 0   -- 8% of gross (statutory)
├── nhis_relief           NUMERIC(15,2), DEFAULT 0   -- actual contribution
├── life_assurance_relief NUMERIC(15,2), DEFAULT 0   -- if evidenced
├── rent_relief           NUMERIC(15,2), DEFAULT 0   -- 20% of rent, max N500,000
│
│   -- Computed Values --
├── gross_income          NUMERIC(15,2), DEFAULT 0
├── total_reliefs         NUMERIC(15,2), DEFAULT 0
├── chargeable_income     NUMERIC(15,2), DEFAULT 0
├── tax_liability         NUMERIC(15,2), DEFAULT 0
├── tax_paid              NUMERIC(15,2), DEFAULT 0   -- PAYE already deducted
├── tax_payable           NUMERIC(15,2), DEFAULT 0   -- final amount owed
│
│   -- Accommodation (Tab 2 of LIRS form) --
├── accommodation_address      VARCHAR(500), NULLABLE
├── accommodation_type         VARCHAR(100), NULLABLE
├── ownership_type             VARCHAR(100), NULLABLE
├── owner_name                 VARCHAR(255), NULLABLE
├── owner_payer_id             VARCHAR(50), NULLABLE
├── owner_address              VARCHAR(500), NULLABLE
├── rent_paid                  NUMERIC(15,2), DEFAULT 0
├── rent_paid_by_employer      NUMERIC(15,2), DEFAULT 0
│
├── created_at            TIMESTAMPTZ
└── updated_at            TIMESTAMPTZ
```

### Filings Table
```
filings
├── id                UUID, PK
├── tax_return_id     UUID, FK -> tax_returns.id
├── status            ENUM(pending, in_progress, awaiting_confirmation,
│                          submitted, confirmed, failed)
├── portal_url        VARCHAR(255), DEFAULT 'https://etax.lirs.net'
├── lirs_reference    VARCHAR(100), NULLABLE    -- Return Ref ID from LIRS
├── filed_at          TIMESTAMPTZ, NULLABLE
├── error_message     TEXT, NULLABLE
├── screenshot_path   VARCHAR(500), NULLABLE
├── audit_log         TEXT, NULLABLE
├── retry_count       INTEGER, DEFAULT 0
├── scheduled_at      TIMESTAMPTZ, NULLABLE     -- for off-peak queue
├── created_at        TIMESTAMPTZ
└── updated_at        TIMESTAMPTZ
```

---

## 6. API Endpoints

### Authentication
```
POST   /api/v1/auth/register         Create new user account
POST   /api/v1/auth/login            Login, returns JWT token
GET    /api/v1/auth/me               Get current user profile
```

### Transactions
```
POST   /api/v1/transactions/          Ingest single transaction
POST   /api/v1/transactions/bulk      Bulk ingest from bank or CSV
GET    /api/v1/transactions/          List user transactions (paginated)
GET    /api/v1/transactions/{id}      Get single transaction detail
PATCH  /api/v1/transactions/{id}      Manually override tax category
GET    /api/v1/transactions/review    List transactions needing human review
POST   /api/v1/transactions/classify  Trigger AI classification on unclassified
```

### Tax
```
POST   /api/v1/tax/compute/{year}     Compute tax return from classified transactions
GET    /api/v1/tax/returns            List all user tax returns
GET    /api/v1/tax/returns/{id}       Get full return with band breakdown
GET    /api/v1/tax/summary/{year}     Monthly income + running tax liability
PATCH  /api/v1/tax/returns/{id}       Update return fields before filing
```

### Filing
```
POST   /api/v1/filing/initiate        Start Playwright filing (background task)
GET    /api/v1/filing/{id}/status     Poll filing status
POST   /api/v1/filing/{id}/confirm    User confirms — trigger LIRS submission
GET    /api/v1/filing/{id}/screenshot Serve pre-submission screenshot
GET    /api/v1/filing/history         All filing attempts with status
```

### Chat (RAG)
```
POST   /api/v1/chat/ask               Ask question about Nigerian tax law
GET    /api/v1/chat/history           Conversation history
```

### System
```
GET    /health                         Full system health check
GET    /api/v1/filing/portal-status   LIRS portal health monitor result
```

---

## 7. AI Classification System

### Confidence Threshold Policy

| Score | Action |
|---|---|
| >= 0.85 | Auto-classified, stored, no review needed |
| 0.75 - 0.84 | Classified, flagged as optional review |
| < 0.75 | Marked unclassified, needs_review = TRUE, user must confirm |

This threshold is non-negotiable. A misclassified N500,000 credit could produce a N75,000 tax error.

### Transaction Categories

| Category | Example Nigerian Narrations |
|---|---|
| taxable_income | "UPWORK PAYMENT USD 500", "SALARY PAYROLL MARCH", "TRF FROM CLIENT" |
| exempt_income | "PENSION WITHDRAWAL STANBIC", "INSURANCE CLAIM PAYOUT" |
| deductible_expense | "NHIS MONTHLY DEDUCTION", "PENSION CONTRIBUTION RSA" |
| non_deductible_expense | "UBER EATS", "AIRTIME MTN", "POS SHOPRITE" |
| unclassified | "TRF", "FROM JOHN", "TRANSFER", any score below 0.75 |

### The Nigerian Narration Problem

Nigerian bank narrations are often abbreviated and context-free. "TRF", "FROM CHUKS", "POS" — the same N500,000 credit could be salary, a loan, family support, or business income. The classifier mitigates this with:

- Recurring pattern detection — same sender monthly suggests salary
- Amount clustering — regular same-amount credits indicate payroll
- User correction learning — reviewed transactions inform future similar ones
- Hard confidence floor — ambiguous narrations always route to human review

---

## 8. Tax Computation Engine (NTA 2025)

### Tax Bands — Effective January 1, 2026

```
Annual Chargeable Income        Rate
------------------------------------
N0 – N800,000                    0%   (exempt threshold)
N800,001 – N3,000,000           15%
N3,000,001 – N12,000,000        18%
N12,000,001 – N25,000,000       21%
N25,000,001 – N50,000,000       23%
Above N50,000,000                25%
```

WARNING: Engine must be reviewed by a qualified Nigerian tax professional before
production launch. Specifically: foreign income DTTs, crypto gains, gratuities,
PAYE reconciliation, and nil-return edge cases.

### CRITICAL: The CRA Has Been Removed

The old Consolidated Relief Allowance (20% of gross + N200,000) NO LONGER EXISTS under NTA 2025.

New relief system:

| Relief | Calculation | Cap |
|---|---|---|
| Rent Relief | 20% of annual rent paid | N500,000 maximum |
| Pension Statutory | 8% of gross income | None |
| NHIS | Actual contribution | Must be evidenced |
| Life Assurance | Actual premium paid | Must be evidenced |
| NHF | Actual contribution | Must be evidenced |

Homeowners receive NO personal relief beyond the N800,000 exempt threshold.
The system must surface this clearly — most users will not expect it.

### Computation Steps

```
1. Sum classified transactions by income_type
   salary + commission + trade_income + allowance + pension
   + annuity + gratuities + foreign_income + dividend
   + interest + rent_income + other_income = gross_income

2. Apply NTA 2025 reliefs
   pension_relief = gross_income x 8%
   rent_relief    = MIN(annual_rent_paid x 20%, 500000)
   nhis_relief    = actual (if evidenced)
   life_assurance = actual (if evidenced)
   total_reliefs  = sum of above

3. chargeable_income = gross_income - total_reliefs

4. Apply progressive tax bands -> tax_liability

5. tax_payable = tax_liability - tax_paid (PAYE already deducted)
```

### Edge Cases

- Foreign income with DTT — partial exemption may apply; flag for human review
- Crypto P2P / stock app withdrawals — Capital Gains under NTA 2025; classify separately
- Gratuities — taxable under specific conditions; not automatically exempt
- Nil returns — users earning <= N800,000 still must file; engine generates valid nil return
- PAYE reconciliation — salaried users with side income must deduct PAYE already paid

---

## 9. LIRS eTax Filing Automation

### Portal Details
- URL: https://etax.lirs.net/user/returns
- Technology: Playwright (Python) with Chromium
- Authentication: User's own LIRS credentials — session-only, never stored

### Complete Form Map (Verified Against Live Portal)

Tab 1 — Statement of Income
  Salary | Commission | Trade Income | Allowance | Pension | Annuity
  Gratuities | Foreign Income | Dividend | Interest | Rent | Other Income
  + Document upload section

Tab 2 — Mandatory Disclosure of Accommodation
  Address | Accommodation Type | Ownership Type (dropdown)
  Owner Name | Owner Payer ID | Owner Address
  Rent Paid | Rent Paid By Employer | Date Started | Date End

Tab 3 — Support Staff (dynamic ADD STAFF — skip if empty)

Tab 4 — Assets (dynamic ADD ASSET — skip if empty)

Tab 5 — Other Disclosure for Reliefs
  A) Life Assurance: Yes/No
  B) NHIS: Yes/No
  C) NPS Statutory: RSA Account + Pension Fund Admin + Total Contribution + RSA Statement file
  D) NPS Voluntary: Yes/No

### Submission Flow

```
Login -> Select Year -> Tab 1 -> NEXT -> Tab 2 -> NEXT ->
Tab 3 -> NEXT -> Tab 4 -> NEXT -> Tab 5 -> ADD RELIEF ->
[STOP — Take full-page screenshot]
            |
   Status: AWAITING_CONFIRMATION
            |
   User reviews screenshot -> confirms via API
            |
   Playwright: Submit -> Status: SUBMITTED
            |
   Store LIRS Return Ref ID -> Status: CONFIRMED
```

### Filing States

```
PENDING -> IN_PROGRESS -> AWAITING_CONFIRMATION -> SUBMITTED -> CONFIRMED
                                                             -> FAILED (retryable)
```

### Resilience Architecture

The LIRS portal has a documented history of crashing during peak filing season
(March 28-31) and making UI changes without notice. Three resilience layers:

Layer 1 — Daily Health Monitor
  Runs at 06:00 WAT. Verifies login page loads and critical selectors exist.
  Sends alert if any check fails. Result stored in portal_health_log.

Layer 2 — Queue and Retry with Off-Peak Scheduling
  Filings queued and executed 02:00-04:00 WAT (lowest portal load).
  On failure: exponential backoff, maximum 3 retries.
  On max retries: status FAILED, user notified immediately.

Layer 3 — Manual Fallback Path
  If automation fails: system generates pre-filled PDF of all computed values.
  User downloads and submits manually on etax.lirs.net.
  Filing record updated with manual_submission = TRUE.
  Users are never left with no path forward.

### Safety Rules (Non-Negotiable)

1. Never auto-submit without explicit user confirmation via API call
2. Always screenshot the completed form before the confirmation step
3. Full audit log of every Playwright action stored in filings.audit_log
4. LIRS credentials are session-only — never written to database or logs
5. On any error: status FAILED, error_message stored, user notified
6. On portal selector failure: trigger health monitor alert immediately

---

## 10. RAG System — Nigerian Tax Law Q&A

### Document Corpus

```
docs/
├── NTA_2025.pdf          Nigeria Tax Act 2025 — signed June 2025 (PRIMARY SOURCE)
├── PITA_amended.pdf      Personal Income Tax Act — historical reference only
└── LIRS_guidelines.pdf   LIRS practice notes and circulars
```

### Why RAG, Not Fine-tuning

Fine-tuning costs significant compute, goes stale after every Finance Act amendment,
and requires retraining annually. RAG gives equivalent grounding at near-zero cost.
When the law changes, you replace one PDF. No retraining required.

### RAG Pipeline

```
Build (once):
PDF -> LangChain loader -> Chunk (512 tokens, 50 overlap)
-> Embed -> ChromaDB persistent collection "nigerian_tax_law"

Query (per question):
Embed question -> Retrieve top 5 chunks -> Pass to Groq LLM
-> "Answer using only the provided context. Cite section numbers."
-> Return answer + source citations
```

### Example Queries the System Handles

- "Is my Upwork income taxable in Nigeria?"
- "The CRA I claimed last year — does it still apply under NTA 2025?"
- "I earned N650,000 this year. Do I still need to file?"
- "How is crypto P2P income taxed?"
- "What is the penalty for filing late?"
- "What rent relief can I claim and what documents do I need?"

---

## 11. Bank Integration

### Provider Strategy

- Primary: Mono API — read-only access, transaction history, webhooks
- Fallback: Manual PDF/CSV bank statement upload — built at MVP, not deferred
- Architecture: Abstract BankProvider interface — swap providers without touching business logic

NOTE on Mono: Mono was acquired by Flutterwave in January 2026. AutoPITA's bank
abstraction layer means any provider change requires only a new implementation class.
Zero impact on classification or tax logic.

### Bank Abstraction Layer

```python
class BankProvider:
    async def connect_account(user_id, auth_code) -> AccountInfo
    async def fetch_transactions(account_id, from_date, to_date) -> list[RawTransaction]
    async def fetch_balance(account_id) -> Balance
    async def refresh_account(account_id) -> None

class MonoProvider(BankProvider): ...         # Primary
class StitchProvider(BankProvider): ...       # Alternative
class ManualUploadProvider(BankProvider): ... # PDF/CSV — built at MVP
```

### Manual Upload as First-Class Feature

Nigerian users have documented wariness about bank account linking due to fraud concerns.
The CSV/PDF path is fully functional at launch. Both paths feed identical data into
the same classification engine.

---

## 12. Security Requirements

| Requirement | Implementation |
|---|---|
| Password storage | bcrypt via passlib |
| API authentication | JWT Bearer tokens via python-jose |
| Access token expiry | 30 minutes |
| Refresh token expiry | 7 days |
| LIRS credentials | Session-only — never persisted or logged |
| Bank tokens | Encrypted at rest |
| Data access | Full audit trail with user_id + timestamp |
| Rate limiting | slowapi middleware on all endpoints |
| CORS | Environment-specific allowed origins |

---

## 13. Legal and Compliance Requirements

### Nigeria Data Protection Act 2023 (NDPA)

AutoPITA processes bank transaction data, tax records, salary information, and
government portal credentials. This is the highest-sensitivity category of personal
data. Legal requirements before accepting paying users:

| Requirement | Status |
|---|---|
| Register as Data Controller with NDPC | Pre-launch required |
| Data Protection Impact Assessment (DPIA) | Pre-launch required |
| Data Protection Officer (DPO) appointment | Required at 2,000+ data subjects |
| Annual compliance audit submission to NDPC | Ongoing |
| Breach notification within 72 hours | Operational requirement |
| Data retention policy documented | Pre-launch required |

NOTE: The governing law is NDPA 2023, not the older NDPR. The NDPC has demonstrated
serious enforcement — fines include N766M against Multichoice and $220M against Meta.

### Liability Framework

AutoPITA is an AI-assisted compliance tool, not a licensed tax advisory service:

- Every confirmed return is the USER'S OWN legal declaration to LIRS
- "AI-assisted, not legal tax advice" must appear on every computation screen
- Explicit user confirmation required before any filing action
- Tax computation engine must be reviewed by a qualified Nigerian tax professional
  before production launch

### Penalty Reference (NTA 2025 Section 101)

Incorrect returns: N100,000 base penalty + N50,000 per month the error persists.
This context must be shown to users — it explains why accuracy matters.

---

## 14. Technology Stack

| Package | Purpose |
|---|---|
| fastapi | Web framework — async, OpenAPI docs auto-generated |
| uvicorn | ASGI server |
| sqlalchemy 2.x | Async ORM |
| asyncpg | PostgreSQL async driver |
| alembic | Database migrations |
| pydantic-settings | Config management via .env |
| groq | LLM API client (LLaMA 3.3-70B) |
| langchain + langchain-groq | RAG pipeline |
| chromadb | Local vector store |
| playwright | Browser automation |
| python-jose[cryptography] | JWT |
| passlib[bcrypt] | Password hashing |

| Infrastructure | Purpose |
|---|---|
| Neon | PostgreSQL managed cloud |
| Render | Backend deployment |
| Groq | LLM inference (free tier available) |
| ChromaDB | Vector store (runs locally) |

---

## 15. Key Architectural Decisions

Decision 1 — RAG over Fine-tuning
Tax law changes annually. RAG updates by swapping a PDF. Fine-tuning requires
expensive compute and goes stale after every Finance Act.

Decision 2 — Lagos LIRS only at MVP
Largest concentration of target users. Adding other states post-MVP is mechanical,
not architectural.

Decision 3 — Stop-before-submit
Non-negotiable. User confirms every filing. Protects against AI errors, portal
glitches, and legal liability.

Decision 4 — Bank abstraction layer
Mono's acquisition by Flutterwave is a real vendor risk. The abstraction layer means
any provider change requires only a new class — not a rewrite.

Decision 5 — Async everywhere
All DB, HTTP, and AI calls are async. Filing runs as a background task. A 2-minute
Playwright session never blocks an HTTP response.

Decision 6 — Off-peak filing queue
Filings scheduled at 02:00-04:00 WAT. Avoids March deadline portal crash window.
Users get reliable confirmation before deadlines.

Decision 7 — Manual upload as first-class feature
Nigerian users distrust bank linking. Full PDF/CSV path means we don't lose users
at onboarding. Both paths feed the same classification engine.

Decision 8 — Confidence threshold at 0.75
Below 0.75, transactions are flagged for human review. The system never silently
accepts ambiguous classifications on a financial compliance product.

---

## 16. Scope Boundaries

- Not B2B — corporate tax, VAT, WHT are out of scope
- Not multi-state at MVP — Lagos LIRS only
- Not a payment product — we file, we do not initiate tax payments
- Not real-time — bank sync runs on schedule, not instant
- Not a tax advisory service — AI-assisted tool, not licensed consultant
- Not fully autonomous — user confirmation required before every submission

---

## 17. Roadmap

### MVP (Current Build)
- [ ] Authentication — register, login, JWT
- [ ] Transaction ingestion — manual + CSV upload
- [ ] AI classification with confidence thresholds and review queue
- [ ] NTA 2025 tax computation engine
- [ ] LIRS eTax filing automation (Lagos)
- [ ] RAG Q&A on Nigerian tax law
- [ ] Filing queue with off-peak scheduling
- [ ] Portal health monitor with manual fallback

### Phase 2 — Post-MVP
- [ ] Mono API live bank connection
- [ ] PDF bank statement OCR parsing
- [ ] Multi-state portal support (FCT, Rivers, Ogun)
- [ ] Recurring income detection and pattern learning
- [ ] Quarterly tax estimate notifications
- [ ] Accountant collaboration mode

### Phase 3 — Scale
- [ ] LIRS Certified Software Provider application
- [ ] Direct API integration if LIRS opens partner access
- [ ] Financial intelligence dashboard
- [ ] Embedded tax product for payroll providers and platforms

---

## 18. External Review Summary (May 2026)

Three independent technical reviews reached the following consensus:

| Area | Assessment |
|---|---|
| Market need | Strong — NTA 2025 creates immediate compliance demand |
| Technical architecture | Sound — async, abstracted, correctly layered |
| RAG decision | Correct — fine-tuning would be expensive and go stale |
| Filing automation | Viable with resilience layer added |
| Nigerian narration quality | Risk acknowledged — confidence threshold mitigates |
| CRA removal | Addressed — rent relief correctly implemented |
| NDPA compliance | Pre-launch legal requirement — noted |
| MVP scope | Focused and correctly prioritised |

Overall verdict: Technically sound. Market timing exceptional. Execution blueprint ready.

---

Version 2.0 — Updated following multi-source technical review (May 2026)
Previous version: 1.0 (initial draft)
Next review: After MVP Phase 1 completion
