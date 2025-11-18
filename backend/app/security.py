from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from jose import jwt
from passlib.context import CryptContext

from .config import settings


# Use bcrypt_sha256 to safely support passwords >72 bytes.
# Keep bcrypt as a fallback for verifying existing hashes.
# Disable bcrypt's truncate_error so legacy bcrypt hashes won't raise on long inputs.
pwd_context = CryptContext(
    schemes=["bcrypt_sha256", "bcrypt"],
    deprecated="auto",
    bcrypt__truncate_error=False,
)


def hash_password(password: str) -> str:
    return pwd_context.hash(password, scheme="bcrypt_sha256")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        if pwd_context.verify(password, password_hash):
            return True
    except ValueError:
        pass

    try:
        scheme = pwd_context.identify(password_hash)
        if scheme == "bcrypt":
            return pwd_context.verify(password[:72], password_hash)
    except Exception:
        pass
    return False


def create_access_token(subject: str | Any, expires_minutes: Optional[int] = None) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=expires_minutes or settings.ACCESS_TOKEN_EXPIRES_MINUTES
    )
    to_encode = {"sub": str(subject), "exp": expire}
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(subject: str | Any, expires_days: Optional[int] = None) -> tuple[str, datetime]:
    expire = datetime.now(timezone.utc) + timedelta(days=expires_days or settings.REFRESH_TOKEN_EXPIRES_DAYS)
    to_encode = {"sub": str(subject), "type": "refresh", "exp": expire}
    token = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return token, expire


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])