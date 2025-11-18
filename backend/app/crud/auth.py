"""
Các thao tác CRUD cho token xác thực.
"""
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models import AuthRefreshToken


def create_refresh_token(
    db: Session,
    user_id: UUID,
    token_hash: str,
    expires_at: datetime,
) -> AuthRefreshToken:
    """Tạo bản ghi refresh token mới."""
    token = AuthRefreshToken(
        user_id=user_id,
        token_hash=token_hash,
        expires_at=expires_at,
    )
    db.add(token)
    db.flush()
    return token


def get_valid_refresh_token(
    db: Session,
    token_hash: str,
) -> AuthRefreshToken | None:
    """Lấy refresh token hợp lệ (chưa bị thu hồi) theo hash của nó."""
    return db.execute(
        select(AuthRefreshToken)
        .where(
            AuthRefreshToken.token_hash == token_hash,
            AuthRefreshToken.revoked_at.is_(None),
        )
    ).scalar_one_or_none()


def revoke_refresh_token(
    db: Session,
    token: AuthRefreshToken,
) -> AuthRefreshToken:
    """Thu hồi refresh token."""
    token.revoked_at = datetime.now(timezone.utc)
    db.add(token)
    return token
