from pydantic import BaseModel, EmailStr, Field, field_validator
import uuid


class RegisterRequest(BaseModel):
    email: EmailStr = Field(
        ...,
        description="User email address",
        examples=["user@example.com"]
    )
    full_name: str = Field(
        ...,
        min_length=2,
        max_length=255,
        description="User full name"
    )
    password: str = Field(
        ...,
        min_length=8,
        description="User password"
    )
    phone: str | None = Field(
        default=None,
        description="Nigerian phone number"
    )
    state_of_residence: str = Field(
        default="Lagos",
        description="State of residence — determines which portal to file on"
    )

    @field_validator("email")
    @classmethod
    def normalise_email(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Email cannot be empty")
        return v.strip().lower()

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Full name cannot be empty")
        return v.strip().title()

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Password cannot be empty")
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
        v = v.strip()
        # Accept 080xxxxxxxx, 090xxxxxxxx, +2348xxxxxxxx
        import re
        if not re.match(r"^(\+234|0)[789][01]\d{8}$", v):
            raise ValueError("Enter a valid Nigerian phone number e.g. 08012345678")
        return v


class LoginRequest(BaseModel):
    email: EmailStr = Field(
        ...,
        description="User email address",
        examples=["user@example.com"]
    )
    password: str = Field(
        ...,
        min_length=1,
        description="User password"
    )

    @field_validator("email")
    @classmethod
    def normalise_email(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Email cannot be empty")
        return v.strip().lower()

    @field_validator("password")
    @classmethod
    def validate_password_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Password cannot be empty")
        return v


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