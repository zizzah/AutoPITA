# AutoPITA — Execution Plan
> Phased implementation guide. Each phase has small, testable, independently verifiable steps.  
> Rule: Never move to the next step until the current step is tested and working.

---

## How to Use This Document

Each step follows this format:
- **What:** What you are building
- **Why:** Why it exists and what it connects to
- **Files touched:** Exactly which files change
- **Done when:** The specific test that proves it works
- **Estimated time:** Realistic solo developer estimate

Total phases: 6  
Total steps: ~40  
Recommended order: Sequential — each phase depends on the previous.

---

## Current Status

```
Phase 0 — Foundation         ████████████ COMPLETE
Phase 1 — Auth               ░░░░░░░░░░░░ NOT STARTED
Phase 2 — Transactions       ░░░░░░░░░░░░ NOT STARTED
Phase 3 — Tax Engine         ░░░░░░░░░░░░ NOT STARTED
Phase 4 — RAG / Chat         ░░░░░░░░░░░░ NOT STARTED
Phase 5 — Filing Engine      ░░░░░░░░░░░░ NOT STARTED
Phase 6 — Demo Integration   ░░░░░░░░░░░░ NOT STARTED
```

---

## Phase 0 — Foundation (COMPLETE)

Everything in this phase is already done.

| Step | What | Status |
|---|---|---|
| 0.1 | Project folder structure created | ✅ Done |
| 0.2 | Virtual environment + all packages installed | ✅ Done |
| 0.3 | `config.py` with pydantic-settings | ✅ Done |
| 0.4 | `db/session.py` with Neon SSL connection | ✅ Done |
| 0.5 | `dependencies.py` with `get_db` | ✅ Done |
| 0.6 | `main.py` with lifespan + health endpoint | ✅ Done |
| 0.7 | All four SQLAlchemy models | ✅ Done |
| 0.8 | Alembic init + first migration run | ✅ Done |
| 0.9 | `/health` returns 200 with DB connected | ✅ Done |

---

## Phase 1 — Authentication

**Goal:** A user can register, log in, and receive a JWT token. Every subsequent API call is authenticated.

**Packages needed:**
```bash
pip install python-jose[cryptography] passlib[bcrypt]
```

---

### Step 1.1 — Custom Exception Handlers
**What:** Create base exception classes and register FastAPI error handlers.  
**Why:** Every phase needs consistent error responses. Build this first so all future code uses it.  
**Files:** `app/core/exceptions.py`, `app/main.py`

`app/core/exceptions.py`:
```python
from fastapi import Request
from fastapi.responses import JSONResponse


class AutoPITAException(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class NotFoundError(AutoPITAException):
    def __init__(self, resource: str):
        super().__init__(f"{resource} not found", status_code=404)


class UnauthorizedError(AutoPITAException):
    def __init__(self, message: str = "Unauthorized"):
        super().__init__(message, status_code=401)


class ConflictError(AutoPITAException):
    def __init__(self, message: str):
        super().__init__(message, status_code=409)


class ValidationError(AutoPITAException):
    def __init__(self, message: str):
        super().__init__(message, status_code=422)


async def autopita_exception_handler(request: Request, exc: AutoPITAException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.message, "status_code": exc.status_code}
    )
```

Register in `app/main.py`:
```python
from app.core.exceptions import AutoPITAException, autopita_exception_handler
app.add_exception_handler(AutoPITAException, autopita_exception_handler)
```

**Done when:** `/health` still returns 200. No errors on startup.

---

### Step 1.2 — Auth Schemas
**What:** Pydantic schemas for register, login, and token responses.  
**Why:** Schemas define the API contract — what the client sends and what they get back. Separate from DB models.  
**Files:** `app/schemas/auth.py`

```python
from pydantic import BaseModel, EmailStr


class RegisterRequest(BaseModel):
    email: EmailStr
    full_name: str
    password: str
    phone: str | None = None
    state_of_residence: str = "Lagos"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: str
    email: str
    full_name: str
    payer_id: str | None
    state_of_residence: str

    model_config = {"from_attributes": True}
```

**Done when:** Python imports the file without errors.

---

### Step 1.3 — Auth Service
**What:** Password hashing and JWT creation/verification logic.  
**Why:** All auth logic lives in the service layer — never in routes.  
**Files:** `app/services/auth_service.py`, `app/config.py` (add JWT settings)

Add to `.env`:
```
JWT_SECRET_KEY=your-jwt-secret-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

Add to `app/config.py`:
```python
jwt_secret_key: str
jwt_algorithm: str = "HS256"
access_token_expire_minutes: int = 30
```

`app/services/auth_service.py`:
```python
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User
from app.config import get_settings
from app.core.exceptions import UnauthorizedError, ConflictError

settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    payload = {"sub": user_id, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> str:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        user_id = payload.get("sub")
        if not user_id:
            raise UnauthorizedError("Invalid token")
        return user_id
    except JWTError:
        raise UnauthorizedError("Invalid or expired token")


async def register_user(db: AsyncSession, email: str, full_name: str,
                         password: str, phone: str | None,
                         state_of_residence: str) -> User:
    result = await db.execute(select(User).where(User.email == email))
    if result.scalar_one_or_none():
        raise ConflictError("Email already registered")

    user = User(
        email=email,
        full_name=full_name,
        hashed_password=hash_password(password),
        phone=phone,
        state_of_residence=state_of_residence
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User:
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(password, user.hashed_password):
        raise UnauthorizedError("Invalid email or password")
    return user
```

**Done when:** No import errors. Unit-testable without HTTP.

---

### Step 1.4 — Auth Dependency
**What:** `get_current_user` dependency that validates JWT on every protected route.  
**Why:** FastAPI dependency injection — attach to any route that needs authentication.  
**Files:** `app/dependencies.py`

Add to `app/dependencies.py`:
```python
from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User
from app.services.auth_service import decode_token
from app.core.exceptions import UnauthorizedError

bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    user_id = decode_token(credentials.credentials)
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise UnauthorizedError("User not found or inactive")
    return user
```

**Done when:** No import errors.

---

### Step 1.5 — Auth Routes
**What:** POST /register, POST /login, GET /me endpoints.  
**Why:** Expose auth service through HTTP.  
**Files:** `app/api/v1/auth.py`, `app/api/v1/router.py`, `app/main.py`

`app/api/v1/auth.py`:
```python
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies import get_db, get_current_user
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse, UserOut
from app.services.auth_service import register_user, authenticate_user, create_access_token
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserOut, status_code=201)
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)):
    user = await register_user(
        db,
        email=payload.email,
        full_name=payload.full_name,
        password=payload.password,
        phone=payload.phone,
        state_of_residence=payload.state_of_residence
    )
    return user


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = await authenticate_user(db, payload.email, payload.password)
    token = create_access_token(str(user.id))
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserOut)
async def me(current_user: User = Depends(get_current_user)):
    return current_user
```

`app/api/v1/router.py`:
```python
from fastapi import APIRouter
from app.api.v1 import auth

router = APIRouter(prefix="/api/v1")
router.include_router(auth.router)
```

Update `app/main.py` to include the router:
```python
from app.api.v1.router import router as api_router
app.include_router(api_router)
```

**Done when:**
- `POST /api/v1/auth/register` with valid body returns 201 with user object
- `POST /api/v1/auth/login` returns JWT token
- `GET /api/v1/auth/me` with Bearer token returns user profile
- `GET /api/v1/auth/me` without token returns 401
- Duplicate email registration returns 409

Test in `/docs` Swagger UI — all three endpoints visible and working.

---

## Phase 2 — Transaction Ingestion

**Goal:** Transactions can be ingested manually and via bulk upload. Unclassified transactions are classified by the AI.

---

### Step 2.1 — Transaction Schemas
**What:** Pydantic schemas for creating and returning transactions.  
**Files:** `app/schemas/transaction.py`

```python
from pydantic import BaseModel
from decimal import Decimal
from datetime import datetime
from app.models.transaction import TransactionType, TaxCategory


class TransactionCreate(BaseModel):
    amount: Decimal
    transaction_type: TransactionType
    narration: str
    bank_name: str
    bank_reference: str | None = None
    transaction_date: datetime


class TransactionOut(BaseModel):
    id: str
    amount: Decimal
    currency: str
    transaction_type: TransactionType
    narration: str
    bank_name: str
    transaction_date: datetime
    tax_category: TaxCategory
    income_type: str | None
    ai_confidence: Decimal | None
    ai_reasoning: str | None
    is_manually_reviewed: bool

    model_config = {"from_attributes": True}


class TransactionBulkCreate(BaseModel):
    transactions: list[TransactionCreate]


class ManualCategoryUpdate(BaseModel):
    tax_category: TaxCategory
    income_type: str | None = None
```

**Done when:** Clean import, no errors.

---

### Step 2.2 — AI Classifier Service
**What:** Send transaction narration to Groq, get back JSON classification.  
**Why:** Core AI feature of the product.  
**Files:** `app/services/classifier.py`

```python
import json
from groq import AsyncGroq
from app.config import get_settings
from app.models.transaction import TaxCategory

settings = get_settings()
groq_client = AsyncGroq(api_key=settings.groq_api_key)

SYSTEM_PROMPT = """You are a Nigerian tax classification expert under the Nigeria Tax Act 2025.
Classify bank transactions into tax categories.
Always respond with valid JSON only. No explanation text outside the JSON.

Categories:
- taxable_income: earned income subject to personal income tax
- exempt_income: income excluded under NTA 2025
- deductible_expense: allowable relief or deduction
- non_deductible_expense: personal spending with no tax effect
- unclassified: genuinely ambiguous, cannot determine with confidence

Income types (use when category is taxable_income or exempt_income):
salary, commission, trade_income, allowance, pension, annuity,
gratuities, foreign_income, dividend, interest, rent, other
"""


async def classify_transaction(
    amount: float,
    transaction_type: str,
    narration: str,
    bank_name: str
) -> dict:
    user_prompt = f"""Classify this Nigerian bank transaction:

Amount: ₦{amount:,.2f} ({transaction_type.upper()})
Narration: {narration}
Bank: {bank_name}

Return JSON only:
{{
  "tax_category": "<category>",
  "income_type": "<type or null>",
  "confidence": <0.0 to 1.0>,
  "reasoning": "<one sentence explanation>"
}}"""

    response = await groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.1,  # low temperature — we want deterministic classification
        max_tokens=200
    )

    raw = response.choices[0].message.content.strip()

    # Strip markdown fences if model adds them
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    result = json.loads(raw)

    # Validate category is a known value
    valid_categories = [c.value for c in TaxCategory]
    if result.get("tax_category") not in valid_categories:
        result["tax_category"] = "unclassified"
        result["confidence"] = 0.0

    return result
```

**Done when:** Call `classify_transaction(150000, "credit", "UPWORK PAYMENT USD", "GTBank")` in a test script and get back valid JSON.

---

### Step 2.3 — Transaction Routes
**What:** REST endpoints to ingest, list, and classify transactions.  
**Files:** `app/api/v1/transactions.py`, `app/api/v1/router.py`

Key endpoints:
```python
POST   /api/v1/transactions/          # single ingest
POST   /api/v1/transactions/bulk      # bulk ingest
GET    /api/v1/transactions/          # paginated list
PATCH  /api/v1/transactions/{id}      # manual category override
POST   /api/v1/transactions/classify  # trigger AI on all unclassified
```

**Done when:**
- Ingest 5 sample transactions via POST
- `GET /api/v1/transactions/` returns them paginated
- `POST /api/v1/transactions/classify` runs AI and updates categories
- Verify classifications in Neon dashboard

---

### Step 2.4 — Mock Bank Data Loader
**What:** A script that loads 20 realistic Nigerian bank transactions into the DB for testing.  
**Why:** You need data to test tax computation and filing. Don't wait for Mono integration.  
**Files:** `scripts/seed_transactions.py`

Sample transactions to include:
```python
[
    {"narration": "SALARY PAYROLL MARCH", "amount": 450000, "type": "credit"},
    {"narration": "UPWORK PAYMENT USD 500", "amount": 750000, "type": "credit"},
    {"narration": "TRANSFER FROM JOHN DOE", "amount": 200000, "type": "credit"},
    {"narration": "PENSION CONTRIBUTION MARCH", "amount": 36000, "type": "debit"},
    {"narration": "NHIS MONTHLY DEDUCTION", "amount": 5000, "type": "debit"},
    {"narration": "UBER EATS PAYMENT", "amount": 8500, "type": "debit"},
    {"narration": "AIRTIME PURCHASE MTN", "amount": 2000, "type": "debit"},
    {"narration": "DIVIDEND PAYMENT DANGOTE", "amount": 50000, "type": "credit"},
    {"narration": "RENT INCOME FROM TENANT", "amount": 300000, "type": "credit"},
    {"narration": "ATM WITHDRAWAL IKEJA", "amount": 50000, "type": "debit"},
    # ... 10 more across different months
]
```

**Done when:** Script runs, 20 transactions in DB, all classified by AI.

---

## Phase 3 — Tax Computation Engine

**Goal:** Given a user's classified transactions for a tax year, compute their full LIRS tax return.

---

### Step 3.1 — Tax Engine Service
**What:** Pure Python computation logic implementing NTA 2025 tax bands and reliefs.  
**Why:** This is the core tax logic. No AI involved — deterministic computation.  
**Files:** `app/services/tax_engine.py`

Key functions:
```python
def compute_tax_liability(chargeable_income: Decimal) -> Decimal:
    """Apply NTA 2025 progressive tax bands"""

def compute_reliefs(pension: Decimal, nhis: Decimal,
                    life_assurance: Decimal) -> Decimal:
    """Sum all applicable reliefs"""

async def compute_tax_return(
    db: AsyncSession,
    user_id: str,
    tax_year: int
) -> TaxReturn:
    """
    Full pipeline:
    1. Aggregate classified transactions by income_type
    2. Compute gross_income
    3. Apply reliefs
    4. Compute chargeable_income
    5. Apply tax bands → tax_liability
    6. Save TaxReturn to DB
    """
```

**Done when:**
- `compute_tax_liability(Decimal("2400000"))` returns correct amount
- `POST /api/v1/tax/compute/2025` returns full tax return with all fields populated
- Verify numbers manually against LIRS computation rules

---

### Step 3.2 — Tax Schemas
**What:** Response schemas for tax return and summary.  
**Files:** `app/schemas/tax.py`

```python
class TaxBandResult(BaseModel):
    band: str
    rate: float
    taxable_amount: Decimal
    tax_amount: Decimal

class TaxReturnOut(BaseModel):
    id: str
    tax_year: int
    status: str
    salary: Decimal
    trade_income: Decimal
    # ... all income fields
    gross_income: Decimal
    total_reliefs: Decimal
    chargeable_income: Decimal
    tax_liability: Decimal
    tax_payable: Decimal
    bands: list[TaxBandResult]

    model_config = {"from_attributes": True}
```

**Done when:** `GET /api/v1/tax/returns/{id}` returns fully populated return with band breakdown.

---

### Step 3.3 — Monthly Summary Endpoint
**What:** Show month-by-month income and running tax liability for the dashboard.  
**Files:** `app/api/v1/tax.py`

```
GET /api/v1/tax/summary/2025

Response:
{
  "tax_year": 2025,
  "months": [
    {"month": "January", "income": 450000, "tax_ytd": 0},
    {"month": "February", "income": 900000, "tax_ytd": 15000},
    ...
  ],
  "total_income": 5400000,
  "projected_liability": 720000
}
```

**Done when:** Endpoint returns correct monthly breakdown matching the seeded transactions.

---

## Phase 4 — RAG Tax Law Q&A

**Goal:** User can ask questions about Nigerian tax law and get accurate, cited answers.

---

### Step 4.1 — Document Ingestion
**What:** Load NTA 2025 PDF into ChromaDB vector store.  
**Files:** `app/services/rag_service.py`, `scripts/ingest_documents.py`

```python
# scripts/ingest_documents.py — run once
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import chromadb

loader = PyPDFLoader("docs/NTA_2025.pdf")
pages = loader.load()

splitter = RecursiveCharacterTextSplitter(chunk_size=512, chunk_overlap=50)
chunks = splitter.split_documents(pages)

# Store in ChromaDB
client = chromadb.PersistentClient(path=".chroma")
collection = client.get_or_create_collection("nigerian_tax_law")
# ... add chunks with embeddings
```

**Done when:** ChromaDB `.chroma/` directory created, documents ingested. Query returns relevant chunks.

---

### Step 4.2 — RAG Query Service
**What:** Given a question, retrieve relevant law chunks and generate a grounded answer.  
**Files:** `app/services/rag_service.py`

```python
async def ask_tax_question(question: str) -> dict:
    """
    1. Embed question
    2. Query ChromaDB for top 5 relevant chunks
    3. Build context from chunks
    4. Ask Groq LLM: answer the question using only this context
    5. Return answer + source references
    """
```

**Done when:** "Is Upwork income taxable in Nigeria?" returns a grounded answer citing the NTA 2025.

---

### Step 4.3 — Chat Endpoint
**What:** POST /api/v1/chat/ask endpoint.  
**Files:** `app/api/v1/chat.py`, `app/api/v1/router.py`

**Done when:** Hit endpoint from Swagger UI with a tax question, get back a cited answer.

---

## Phase 5 — Filing Engine

**Goal:** Playwright automation fills the LIRS eTax form from computed tax return data and stops before submission for user confirmation.

> ⚠️ This is the highest-risk phase. Test every step manually before automating.

---

### Step 5.1 — Filing Schema
**What:** Request and response schemas for filing operations.  
**Files:** `app/schemas/filing.py`

```python
class FilingRequest(BaseModel):
    tax_return_id: str
    lirs_username: str
    lirs_password: str   # Never stored — used for session only

class FilingStatusOut(BaseModel):
    id: str
    status: str
    lirs_reference: str | None
    screenshot_path: str | None
    error_message: str | None
    filed_at: str | None

    model_config = {"from_attributes": True}
```

**Done when:** Clean import.

---

### Step 5.2 — LIRS Login Automation
**What:** Playwright logs into etax.lirs.net with user credentials.  
**Why:** First and most critical step — if login fails nothing else works.  
**Files:** `app/services/filing_engine.py`

```python
from playwright.async_api import async_playwright

async def login_lirs(page, username: str, password: str) -> bool:
    """
    Navigate to etax.lirs.net
    Fill username and password
    Click login
    Verify logged in by checking for dashboard element
    Return True if successful
    """
```

**Done when:** Running the function opens a browser, logs in, and returns True. Test with your own LIRS credentials manually first.

---

### Step 5.3 — Income Form Filler
**What:** Playwright fills Tab 1 (Statement of Income) from TaxReturn data.  
**Files:** `app/services/filing_engine.py`

```python
async def fill_income_tab(page, tax_return: TaxReturn) -> None:
    """
    Navigate to returns page
    Select correct year
    Fill all income fields:
      salary, commission, trade_income, allowance,
      pension, annuity, gratuities, foreign_income,
      dividend, interest, rent, other_income
    Click NEXT
    """
```

Field selectors to use (from screenshots):
```python
# Each field is an input with placeholder matching the label
await page.fill('input[placeholder*="Salary"]', str(tax_return.salary))
# ... etc for each field
```

**Done when:** Running against a test account fills all fields correctly and advances to Tab 2.

---

### Step 5.4 — Accommodation Form Filler
**What:** Playwright fills Tab 2 (Accommodation Disclosure).  
**Files:** `app/services/filing_engine.py`

**Done when:** Tab 2 filled correctly, advances to Tab 3.

---

### Step 5.5 — Skip to Reliefs + Screenshot
**What:** Navigate through Tabs 3 and 4 (Support Staff, Assets — empty for most users), reach Tab 5, take screenshot, stop.  
**Files:** `app/services/filing_engine.py`

```python
async def take_prefiling_screenshot(page, filing_id: str) -> str:
    """
    Take full page screenshot
    Save to screenshots/{filing_id}.png
    Return file path
    """
    path = f"screenshots/{filing_id}.png"
    await page.screenshot(path=path, full_page=True)
    return path
```

**Done when:** Screenshot saved showing completed form before submission.

---

### Step 5.6 — Full Filing Pipeline
**What:** Orchestrate the complete flow as a FastAPI background task.  
**Files:** `app/services/filing_engine.py`, `app/api/v1/filing.py`

```python
# Filing states flow:
# PENDING → IN_PROGRESS → AWAITING_CONFIRMATION
#                                    ↓ (user confirms via API)
#                               SUBMITTED → CONFIRMED

async def run_filing(filing_id: str, tax_return: TaxReturn,
                     lirs_username: str, lirs_password: str):
    """Background task — runs Playwright end to end"""
    # 1. Update status to IN_PROGRESS
    # 2. Login
    # 3. Fill Tab 1
    # 4. Fill Tab 2
    # 5. Navigate Tabs 3, 4
    # 6. Screenshot
    # 7. Update status to AWAITING_CONFIRMATION
    # On any exception: status → FAILED, store error_message
```

Routes:
```python
POST /api/v1/filing/initiate        # starts background task
GET  /api/v1/filing/{id}/status     # poll status
POST /api/v1/filing/{id}/confirm    # user confirms → final submit
GET  /api/v1/filing/{id}/screenshot # serve screenshot image
```

**Done when:**
- POST /initiate starts the background task
- Polling /status shows progression from PENDING → IN_PROGRESS → AWAITING_CONFIRMATION
- Screenshot accessible via API
- POST /confirm triggers final submission

---

## Phase 6 — Demo Integration

**Goal:** End-to-end demo flow working. Impressive enough to show the product owner.

---

### Step 6.1 — End-to-End Test Script
**What:** A single Python script that runs the complete flow.  
**Files:** `scripts/demo_flow.py`

```
1. Register test user
2. Ingest 12 months of mock transactions
3. Trigger AI classification
4. Compute 2025 tax return
5. Show tax liability breakdown
6. Ask RAG: "What reliefs can I claim?"
7. Initiate filing
8. Poll until AWAITING_CONFIRMATION
9. Print screenshot path
```

**Done when:** Script runs clean end-to-end, produces screenshot of completed LIRS form.

---

### Step 6.2 — Health Endpoint Enhancement
**What:** Expand /health to show system status.  
**Files:** `app/main.py`

```json
{
  "status": "ok",
  "app": "AutoPITA",
  "environment": "development",
  "database": "connected",
  "groq": "connected",
  "chromadb": "ready",
  "playwright": "ready"
}
```

**Done when:** All four service checks return status.

---

### Step 6.3 — Deploy to Render
**What:** Deploy the backend to Render.  
**Files:** `render.yaml` or Render dashboard config

Environment variables to set on Render:
```
APP_NAME=AutoPITA
ENVIRONMENT=production
DEBUG=False
DATABASE_URL=<neon connection string>
GROQ_API_KEY=<key>
JWT_SECRET_KEY=<key>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

Render build command:
```bash
pip install -r requirements.txt && playwright install chromium
```

Start command:
```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

**Done when:** `/health` returns 200 from the Render URL.

---

## Development Rules

1. **One step at a time.** Never start Step N+1 until Step N passes its "Done when" test.
2. **Test in Swagger UI.** Every endpoint must be tested manually in `/docs` before moving on.
3. **Never put logic in routes.** Routes call services. Services contain logic.
4. **Every DB change goes through Alembic.** Never alter tables manually.
5. **Commit after every working step.** Use git. Message: `feat: step X.X - description`
6. **Never store credentials.** LIRS username/password is session-only, never persisted.
7. **Environment variables only.** No hardcoded secrets, URLs, or API keys anywhere in code.

---

## Git Commit Convention

```
feat: step 1.1 - custom exception handlers
feat: step 1.2 - auth schemas
feat: step 1.3 - auth service with JWT
feat: step 2.1 - transaction schemas
feat: step 2.2 - AI classifier service
...
fix: classifier strips markdown fences from Groq response
refactor: move tax band logic to separate function
```

---

## Questions to Answer Before Each Phase

Before starting Phase 2: Have you tested all Phase 1 auth endpoints in Swagger?  
Before starting Phase 3: Do you have at least 20 classified transactions in the DB?  
Before starting Phase 4: Have you downloaded NTA 2025 PDF into the `/docs` folder?  
Before starting Phase 5: Have you manually completed a filing on etax.lirs.net yourself to verify the form flow?  
Before starting Phase 6: Does every endpoint from Phases 1–5 return correct responses?

---

*Last updated: Phase 0 complete. Next: Phase 1, Step 1.1*
