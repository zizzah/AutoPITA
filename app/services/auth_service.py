from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
import bcrypt #type:ignore
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
    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm
    )


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
    # No commit here — get_db owns the transaction lifecycle
    await db.flush()   # assigns DB-generated values (id, created_at) without committing
    await db.refresh(user)
    return user


async def authenticate_user(
    db: AsyncSession,
    email: str,
    password: str
) -> User:
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(password, user.hashed_password):
        raise UnauthorizedError("Invalid email or password")
    return user