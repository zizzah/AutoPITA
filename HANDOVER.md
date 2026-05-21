# AutoPITA — Developer Handover Document v2
> Complete project state as of May 18, 2026
> Purpose: Enable any developer or AI agent to continue immediately without context loss

---

## 1. What This Project Is

AutoPITA is an AI-powered personal income tax automation backend for Nigeria.
It connects to Nigerian bank accounts, classifies transactions using AI, computes
tax liability under the Nigeria Tax Act 2025, and automates filing on the LIRS
eTax portal (etax.lirs.net) using Playwright browser automation.

**Demo deadline: May 23, 2026 — presentation to Kelechi Ibe (co-founder, TaxStreem) for potential purchase.**

---

## 2. Developer Profile

- Name: Chuks (David)
- Level: Intermediate Python developer, learning FastAPI
- Stack familiarity: FastAPI, SQLAlchemy, PostgreSQL, Groq, Render
- OS: Windows (PowerShell — use Windows commands, not bash)
- Goal: Become a world-class fullstack engineer

---

## 3. Project Location

```
C:\Users\DAVID\autopita\
```

### Activating the environment (Windows PowerShell)
```powershell
cd C:\Users\DAVID\autopita
venv\Scripts\activate
uvicorn app.main:app --reload
```

---

## 4. Environment (.env)

```env
APP_NAME=AutoPITA
ENVIRONMENT=development
DEBUG=True
DATABASE_URL=postgresql+asyncpg://<user>:<password>@<neon-host>/autopita
GROQ_API_KEY=<groq_key>
SECRET_KEY=<secret>
JWT_SECRET_KEY=<jwt_secret>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

All values already set. Do not regenerate.

### Database
- Provider: Neon (cloud PostgreSQL)
- SSL: Required — handled via ssl.create_default_context() in session.py
- All 4 tables migrated and exist: users, transactions, tax_returns, filings

---

## 5. What Is Built and Working

```
Phase 0 — Foundation              COMPLETE
Phase 1 — Auth                    COMPLETE
Phase 2 — Transactions + AI       COMPLETE
Phase 3 — Tax Engine              COMPLETE
Phase 4 — RAG / Chat              NOT STARTED (blocked on NTA 2025 PDF)
Phase 5 — Playwright Filing       NOT STARTED
Phase 6 — Demo + Render Deploy    NOT STARTED
```

### Completed endpoints (all tested and working):

```
GET  /health
POST /api/v1/auth/register        → 201 + UserOut
POST /api/v1/auth/login           → TokenResponse (JWT)
GET  /api/v1/auth/me              → UserOut (Bearer required)
POST /api/v1/transactions         → 201 + TransactionOut (Groq classifies first)
GET  /api/v1/transactions         → list[TransactionOut]
GET  /api/v1/transactions/{id}    → TransactionOut
GET  /api/v1/tax/compute          → TaxComputeResponse (query params: year, annual_rent_paid, paye_tax_paid)
```

---

## 6. Complete File Contents (Current State)

### app/config.py
```python
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = "AutoPITA"
    environment: str = "development"
    debug: bool = True
    database_url: str
    groq_api_key: str
    secret_key: str
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

### app/db/session.py
```python
import ssl
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.config import get_settings

settings = get_settings()
ssl_context = ssl.create_default_context()

engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=300,
    connect_args={"ssl": ssl_context}
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)
```

### app/dependencies.py
```python
from typing import AsyncGenerator
from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.models.user import User
from app.services.auth_service import decode_token
from app.core.exceptions import UnauthorizedError


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


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

### app/core/exceptions.py
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

### app/main.py
```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from sqlalchemy import text
from app.config import get_settings
from app.db.session import engine
from app.core.exceptions import AutoPITAException, autopita_exception_handler
from app.api.v1.router import router as api_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
    print("✅ Database connection successful")
    yield
    await engine.dispose()
    print("🛑 Database connection closed")


app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    lifespan=lifespan
)

app.add_exception_handler(AutoPITAException, autopita_exception_handler)
app.include_router(api_router)


@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "app": settings.app_name,
        "environment": settings.environment
    }
```

### app/models/base.py
```python
from datetime import datetime, timezone
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import DateTime


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )
```

### app/models/user.py
```python
import uuid
from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    payer_id: Mapped[str | None] = mapped_column(String(50), unique=True, nullable=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    state_of_residence: Mapped[str] = mapped_column(String(50), default="Lagos", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    transactions: Mapped[list["Transaction"]] = relationship(back_populates="user")
    tax_returns: Mapped[list["TaxReturn"]] = relationship(back_populates="user")
```

### app/models/transaction.py
```python
import uuid
from decimal import Decimal
from datetime import datetime
from sqlalchemy import String, Numeric, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum
from app.models.base import Base, TimestampMixin


class TransactionType(str, enum.Enum):
    CREDIT = "credit"
    DEBIT = "debit"


class TaxCategory(str, enum.Enum):
    TAXABLE_INCOME = "taxable_income"
    EXEMPT_INCOME = "exempt_income"
    DEDUCTIBLE_EXPENSE = "deductible_expense"
    NON_DEDUCTIBLE_EXPENSE = "non_deductible_expense"
    UNCLASSIFIED = "unclassified"


class Transaction(Base, TimestampMixin):
    __tablename__ = "transactions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="NGN", nullable=False)
    transaction_type: Mapped[TransactionType] = mapped_column(SAEnum(TransactionType), nullable=False)
    narration: Mapped[str] = mapped_column(String(500), nullable=False)
    bank_name: Mapped[str] = mapped_column(String(100), nullable=False)
    bank_reference: Mapped[str | None] = mapped_column(String(100), nullable=True)
    transaction_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    tax_category: Mapped[TaxCategory] = mapped_column(
        SAEnum(TaxCategory), default=TaxCategory.UNCLASSIFIED, nullable=False
    )
    income_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    ai_confidence: Mapped[Decimal | None] = mapped_column(Numeric(5, 4), nullable=True)
    ai_reasoning: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_manually_reviewed: Mapped[bool] = mapped_column(default=False, nullable=False)

    user: Mapped["User"] = relationship(back_populates="transactions")
```

### app/schemas/auth.py
```python
from pydantic import BaseModel, EmailStr, Field, field_validator
import uuid


class RegisterRequest(BaseModel):
    email: EmailStr = Field(..., description="User email address")
    full_name: str = Field(..., min_length=2, max_length=255)
    password: str = Field(..., min_length=8)
    phone: str | None = Field(default=None)
    state_of_residence: str = Field(default="Lagos")

    @field_validator("email")
    @classmethod
    def normalise_email(cls, v: str) -> str:
        return v.strip().lower()

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, v: str) -> str:
        return v.strip().title()

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one number")
        if not any(c in "!@#$%^&*()_+-=[]{}|;':\",./<>?" for c in v):
            raise ValueError("Password must contain at least one special character")
        return v

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str | None) -> str | None:
        if v is None:
            return v
        import re
        v = v.strip()
        if not re.match(r"^(\+234|0)[789][01]\d{8}$", v):
            raise ValueError("Enter a valid Nigerian phone number e.g. 08012345678")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1)

    @field_validator("email")
    @classmethod
    def normalise_email(cls, v: str) -> str:
        return v.strip().lower()


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    payer_id: str | None
    state_of_residence: str

    model_config = {"from_attributes": True}
```

### app/schemas/transaction.py
```python
import uuid
from pydantic import BaseModel, Field
from typing import Optional
from decimal import Decimal
from datetime import datetime
from app.models.transaction import TransactionType, TaxCategory


class TransactionBase(BaseModel):
    amount: Decimal
    currency: str = "NGN"
    transaction_type: TransactionType
    narration: str = Field(..., min_length=2, max_length=500)
    bank_name: str = Field(..., min_length=2, max_length=100)
    bank_reference: Optional[str] = Field(default=None, max_length=100)
    transaction_date: datetime


class TransactionCreate(TransactionBase):
    pass


class TransactionOut(TransactionBase):
    id: uuid.UUID
    user_id: uuid.UUID
    tax_category: TaxCategory
    income_type: Optional[str] = None
    ai_confidence: Optional[Decimal] = None
    ai_reasoning: Optional[str] = None
    is_manually_reviewed: bool = False
    created_at: datetime

    model_config = {"from_attributes": True}
```

### app/schemas/tax.py
```python
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
```

### app/services/auth_service.py
```python
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
import bcrypt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User
from app.config import get_settings
from app.core.exceptions import UnauthorizedError, ConflictError

settings = get_settings()


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def create_access_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    payload = {"sub": user_id, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> str:
    try:
        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
        user_id = payload.get("sub")
        if not user_id:
            raise UnauthorizedError("Invalid token")
        return user_id
    except JWTError:
        raise UnauthorizedError("Invalid or expired token")


async def register_user(
    db: AsyncSession,
    email: str,
    full_name: str,
    password: str,
    phone: str | None,
    state_of_residence: str
) -> User:
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
    await db.flush()
    await db.refresh(user)
    return user


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User:
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(password, user.hashed_password):
        raise UnauthorizedError("Invalid email or password")
    return user
```

### app/services/classifier.py
```python
import json
import logging
from decimal import Decimal
from datetime import datetime
from groq import AsyncGroq
from app.models.transaction import TransactionType, TaxCategory
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

client = AsyncGroq(api_key=settings.groq_api_key)


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
            {"role": "user", "content": prompt}
        ],
        temperature=0.1,
        max_tokens=256,
    )

    response_text = response.choices[0].message.content
    if not response_text:
        raise ValueError("Groq returned empty response")

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
```

### app/services/tax_engine.py
```python
from decimal import Decimal
from typing import Any
from sqlalchemy import extract, select
from sqlalchemy.ext.asyncio import AsyncSession
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


def calculate_rent_relief(annual_rent_paid: Decimal) -> Decimal:
    if annual_rent_paid <= ZERO:
        return ZERO
    return min(annual_rent_paid * Decimal("0.20"), Decimal("500000"))


def calculate_progressive_tax(chargeable_income: Decimal) -> dict:
    remaining = chargeable_income
    total_tax = ZERO
    bands = []

    for band_size, rate, label in BANDS:
        if remaining <= ZERO:
            break
        taxable = remaining if band_size is None else min(remaining, band_size)
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


async def compute_tax(
    *,
    current_user: User,
    db: AsyncSession,
    tax_year: int,
    annual_rent_paid: Decimal = ZERO,
    paye_tax_paid: Decimal = ZERO,
) -> dict[str, Any]:

    result = await db.execute(
        select(Transaction).where(
            Transaction.user_id == current_user.id,
            extract("year", Transaction.transaction_date) == tax_year,
            Transaction.tax_category == "taxable_income",
            Transaction.transaction_type == "credit",
        )
    )
    income_transactions = result.scalars().all()

    # Nil return — must still file
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

    deduction_result = await db.execute(
        select(Transaction).where(
            Transaction.user_id == current_user.id,
            extract("year", Transaction.transaction_date) == tax_year,
            Transaction.tax_category == "deductible_expense",
        )
    )
    deduction_transactions = deduction_result.scalars().all()

    salary_income = freelance_income = dividend_income = ZERO
    interest_income = rent_income = other_income = ZERO
    transaction_breakdown = []

    for tx in income_transactions:
        amount = Decimal(tx.amount)
        transaction_breakdown.append({
            "transaction_id": str(tx.id),
            "amount": str(amount),
            "income_type": tx.income_type,
            "narration": tx.narration,
            "ai_confidence": float(tx.ai_confidence) if tx.ai_confidence else None,
            "manually_reviewed": tx.is_manually_reviewed,
        })

        if tx.income_type == "salary":
            salary_income += amount
        elif tx.income_type in ["trade_income", "trade income", "freelance", "consulting", "gigs"]:
            freelance_income += amount
        elif tx.income_type == "dividend":
            dividend_income += amount
        elif tx.income_type == "interest":
            interest_income += amount
        elif tx.income_type == "rent_income":
            rent_income += amount
        else:
            other_income += amount

    gross_income = salary_income + freelance_income + dividend_income + interest_income + rent_income + other_income
    pension_deduction = gross_income * Decimal("0.08")

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

    rent_relief = calculate_rent_relief(annual_rent_paid)
    total_reliefs = pension_deduction + additional_deductions + rent_relief
    chargeable_income = max(gross_income - total_reliefs, ZERO)

    tax_result = calculate_progressive_tax(chargeable_income)
    tax_liability = tax_result["total_tax"]
    tax_payable = max(tax_liability - paye_tax_paid, ZERO)

    return {
        "tax_year": tax_year,
        "income_breakdown": {
            "salary_income": str(salary_income),
            "freelance_income": str(freelance_income),
            "dividend_income": str(dividend_income),
            "interest_income": str(interest_income),
            "rent_income": str(rent_income),
            "other_income": str(other_income),
        },
        "gross_income": str(gross_income),
        "pension_deduction": str(pension_deduction),
        "additional_deductions": str(additional_deductions),
        "rent_relief": str(rent_relief),
        "total_reliefs": str(total_reliefs),
        "chargeable_income": str(chargeable_income),
        "tax_liability": str(tax_liability),
        "paye_tax_paid": str(paye_tax_paid),
        "tax_payable": str(tax_payable),
        "tax_band_breakdown": tax_result["bands"],
        "transaction_breakdown": transaction_breakdown,
        "deduction_breakdown": deduction_breakdown,
        "total_income_transactions": len(income_transactions),
        "total_deduction_transactions": len(deduction_transactions),
        "nil_return": False,
    }
```

### app/api/v1/auth.py
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

### app/api/v1/transactions.py
```python
import uuid
import logging
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.transaction import Transaction
from app.schemas.transaction import TransactionCreate, TransactionOut
from app.services.classifier import classify_transaction
from app.core.exceptions import NotFoundError

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.post("", response_model=TransactionOut, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    payload: TransactionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    classification = await classify_transaction(
        amount=payload.amount,
        currency=payload.currency,
        transaction_type=payload.transaction_type,
        narration=payload.narration,
        bank_name=payload.bank_name,
        bank_reference=payload.bank_reference,
        transaction_date=payload.transaction_date,
    )
    transaction = Transaction(
        user_id=current_user.id,
        amount=payload.amount,
        currency=payload.currency,
        transaction_type=payload.transaction_type,
        narration=payload.narration,
        bank_name=payload.bank_name,
        bank_reference=payload.bank_reference,
        transaction_date=payload.transaction_date,
        **classification
    )
    db.add(transaction)
    await db.flush()
    await db.refresh(transaction)
    return transaction


@router.get("", response_model=list[TransactionOut])
async def get_transactions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Transaction)
        .where(Transaction.user_id == current_user.id)
        .order_by(Transaction.transaction_date.desc())
    )
    return result.scalars().all()


@router.get("/{transaction_id}", response_model=TransactionOut)
async def get_transaction(
    transaction_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Transaction).where(
            Transaction.id == transaction_id,
            Transaction.user_id == current_user.id
        )
    )
    transaction = result.scalar_one_or_none()
    if not transaction:
        raise NotFoundError("Transaction")
    return transaction
```

### app/api/v1/tax.py
```python
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
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await compute_tax(
        current_user=current_user,
        db=db,
        tax_year=year,
        annual_rent_paid=annual_rent_paid,
        paye_tax_paid=paye_tax_paid,
    )
    return result
```

### app/api/v1/router.py
```python
from fastapi import APIRouter
from app.api.v1 import auth, transactions, tax

router = APIRouter(prefix="/api/v1")
router.include_router(auth.router)
router.include_router(transactions.router)
router.include_router(tax.router)
```

---

## 7. Installed Packages

```
fastapi, uvicorn[standard], sqlalchemy, asyncpg, alembic,
pydantic-settings, python-dotenv, groq, chromadb, langchain,
langchain-groq, langchain-community, playwright, psycopg2-binary,
python-jose[cryptography], bcrypt
```

NOTE: passlib was replaced with bcrypt directly due to Python 3.12 incompatibility.
Playwright chromium browser is installed.

---

## 8. Architecture Rules (Never Break These)

1. No business logic in routes — routes call services, services contain logic
2. No direct DB calls from routes — always use Depends(get_db)
3. No hardcoded secrets — everything from .env via get_settings()
4. Every DB schema change goes through Alembic — never alter tables manually
5. All DB calls are async — no sync SQLAlchemy in this project
6. LIRS credentials are session-only — never persist to DB or logs
7. Never auto-submit a tax filing — always stop for user confirmation first
8. AI confidence below 0.75 — flag for human review (is_manually_reviewed=True)
9. get_db owns transaction lifecycle — services use flush(), never commit()

---

## 9. Known Issues / Technical Debt

- Old transactions in DB have `income_type = "trade income"` (with space) instead of `"trade_income"`. Tax engine handles this via string matching fallback. Fix: delete old test transactions and re-seed.
- No DELETE endpoint for transactions (not needed for demo)
- No pagination on GET /transactions (add before production)
- passlib removed, bcrypt used directly — update any documentation that references passlib

---

## 10. Immediate Next Steps (Continue From Here)

### Priority order for May 23 demo:

```
[ ] Step 2.4 — scripts/seed_transactions.py (20 realistic Nigerian transactions)
[ ] Phase 4  — RAG / ChromaDB / chat endpoint
[ ] Phase 5  — Playwright filing engine
[ ] Phase 6  — Deploy to Render
```

---

### Step 2.4 — Seed Script

Create `scripts/seed_transactions.py`. Use `httpx` (async HTTP).

The script must:
1. Register a fresh demo user OR login with existing credentials
2. POST 20 transactions covering ALL tax categories
3. Print classification result for each one
4. Transactions must span 6 months (Jan-June 2026) with realistic Nigerian narrations
5. Include: 4x monthly salary, 3x freelance/Upwork, 1x dividend, rent payments, pension, DSTV, Shoprite, Uber, one ambiguous transaction that gets flagged

```python
import asyncio
import httpx
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000/api/v1"
EMAIL = "demo@autopita.ng"
PASSWORD = "DemoPass@2026"

TRANSACTIONS = [
    # Taxable income
    {"amount": "450000.00", "currency": "NGN", "transaction_type": "credit",
     "narration": "SALARY JANUARY 2026 - STERLING BANK", "bank_name": "Sterling Bank",
     "bank_reference": "STB202601001", "transaction_date": "2026-01-31T00:00:00Z"},
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
```

---

### Phase 4 — RAG

**BLOCKER: Need NTA 2025 PDF.** Search:
- firs.gov.ng
- lirs.net
- "Nigeria Tax Act 2025 PDF KPMG"
- nigerialaw.org or lawyard.ng

Once PDF is obtained, save to `docs/NTA_2025.pdf` then:

**`scripts/ingest_documents.py`:**
```python
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_groq import ChatGroq
from langchain_community.embeddings import HuggingFaceEmbeddings

loader = PyPDFLoader("docs/NTA_2025.pdf")
docs = loader.load()
splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
chunks = splitter.split_documents(docs)
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
vectorstore = Chroma.from_documents(chunks, embeddings, persist_directory="chroma_db")
vectorstore.persist()
print(f"Ingested {len(chunks)} chunks")
```

**`app/services/rag_service.py`:** query the vectorstore, pass context to Groq, return answer.

**`app/api/v1/chat.py`:** `POST /api/v1/chat` with `{"question": "..."}` → `{"answer": "..."}`.

---

### Phase 5 — Playwright Filing Engine

Portal: https://etax.lirs.net/user/returns

**`app/services/filing_engine.py`** must:
1. Launch Playwright (async)
2. Login with user's LIRS credentials (NEVER save to DB)
3. Navigate to new return, select tax year
4. Fill Tab 1 income fields from tax computation result
5. Fill Tab 2 accommodation fields
6. Skip Tab 3 (Support Staff) and Tab 4 (Assets)
7. Reach Tab 5 (Reliefs), take screenshot
8. STOP — return screenshot path to user for confirmation
9. Only submit after explicit user confirmation

Tab 1 fields: Salary, Commission, Trade Income, Allowance, Pension, Annuity, Gratuities, Foreign Income, Dividend, Interest, Rent, Other Income

Tab 2 fields: Address, Accommodation Type, Ownership Type (dropdown), Owner Name, Owner Payer ID, Owner Address, Rent Paid, Rent Paid By Employer, Date Started, Date End

```python
from playwright.async_api import async_playwright

async def run_filing(
    lirs_username: str,
    lirs_password: str,
    tax_data: dict,
    tax_year: int
) -> dict:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # visible for demo
        page = await browser.new_page()
        await page.goto("https://etax.lirs.net")
        # login, navigate, fill fields...
        screenshot = await page.screenshot(path="filing_preview.png")
        await browser.close()
        return {"status": "pending_confirmation", "screenshot": "filing_preview.png"}
```

**`app/api/v1/filing.py`:** `POST /api/v1/filing/run` — triggers as FastAPI BackgroundTask.

---

### Phase 6 — Render Deployment

1. Create `render.yaml`:
```yaml
services:
  - type: web
    name: autopita
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: DATABASE_URL
        sync: false
      - key: GROQ_API_KEY
        sync: false
      - key: JWT_SECRET_KEY
        sync: false
      - key: SECRET_KEY
        sync: false
```

2. Create `requirements.txt` from venv:
```powershell
pip freeze > requirements.txt
```

3. Push to GitHub, connect to Render, set env vars in Render dashboard.

4. Test live URL before demo.

---

## 11. LIRS Portal Knowledge (Critical for Phase 5)

Portal URL: https://etax.lirs.net/user/returns

Filing flow: Login → Year select → Tab1 → NEXT → Tab2 → NEXT →
Tab3 → NEXT → Tab4 → NEXT → Tab5 → ADD RELIEF →
STOP (screenshot) → user confirms → Submit

---

## 12. Tax Law Reference (NTA 2025)

Tax bands (effective January 1, 2026):
```
₦0 - ₦800,000           0%
₦800,001 - ₦3,000,000   15%
₦3M - ₦12M              18%
₦12M - ₦25M             21%
₦25M - ₦50M             23%
Above ₦50M              25%
```

CRA IS REMOVED. Do not implement it.

Reliefs:
- Rent Relief: 20% of annual rent paid, capped at ₦500,000
- Pension: 8% of gross income (statutory)
- NHIS: actual contribution (evidenced)
- Life Assurance: actual premium (evidenced)

Key edge cases:
- Nil returns for income <= ₦800,000 (must still file)
- PAYE reconciliation for salaried + side income earners
- Crypto/stock = Capital Gains (not regular income)
- Foreign income may be partially exempt under DTTs

---

## 13. Key Product Decisions

- RAG over fine-tuning (Finance Act changes annually)
- Lagos LIRS only at MVP
- Stop-before-submit on all filings
- Mono as primary bank aggregator (acquired by Flutterwave Jan 2026)
- Manual CSV/PDF upload is first-class feature
- Off-peak filing queue: 02:00-04:00 WAT
- Confidence threshold 0.75: below = flag for human review
- Daily portal health monitor with manual fallback PDF path

---

## 14. Mentor Instructions

Chuks is learning FastAPI while building this. Hold high standards:
- Push back when logic belongs in routes instead of services
- Flag any sync code in async context
- Flag hardcoded values that should be in config
- Flag missing error handling
- Do not let him skip "done when" tests

He uses Windows PowerShell. All terminal commands must be PowerShell-compatible.
No bash line continuations. Use single-line pip installs.

Communication: direct, no flattery, explain the why, challenge him to think
before giving answers on conceptual questions.