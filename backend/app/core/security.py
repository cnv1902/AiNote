"""
Tiện ích bảo mật cho xác thực và phân quyền.
"""
from datetime import datetime, timedelta, timezone
from jose import jwt
from passlib.context import CryptContext

from .config import settings

# Thiết lập context mã hóa mật khẩu - hỗ trợ cả bcrypt_sha256 và bcrypt (cũ)
pwd_context = CryptContext(
    schemes=["bcrypt_sha256", "bcrypt"],
    deprecated=["bcrypt"],  # Đánh dấu bcrypt là cũ, sẽ tự động chuyển sang bcrypt_sha256 khi đăng nhập
)

def hash_password(password: str) -> str:
    """
    Mã hóa mật khẩu bằng bcrypt_sha256.
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Kiểm tra mật khẩu với mã hóa đã lưu.
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(subject: str) -> str:
    """
    Tạo access token JWT.
    """
    expires = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRES_MINUTES)
    payload = {
        "sub": subject,
        "exp": expires,
        "type": "access",
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(subject: str) -> tuple[str, datetime]:
    """
    Tạo refresh token JWT. Trả về (token, thời gian hết hạn).
    """
    expires = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRES_DAYS)
    payload = {
        "sub": subject,
        "exp": expires,
        "type": "refresh",
    }
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return token, expires


def decode_token(token: str) -> dict:
    """
    Giải mã và kiểm tra tính hợp lệ của JWT token.
    """
    return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
