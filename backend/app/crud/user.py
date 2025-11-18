"""
Các thao tác CRUD cho model User.
"""
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models import User
from app.schemas import UserCreate
from app.core.security import hash_password


def get_user_by_id(db: Session, user_id: UUID) -> User | None:
    """Lấy người dùng theo ID."""
    return db.get(User, user_id)


def get_user_by_email(db: Session, email: str) -> User | None:
    """Lấy người dùng theo email."""
    return db.execute(
        select(User).where(User.email == email)
    ).scalar_one_or_none()


def get_user_by_email_or_username(db: Session, identifier: str) -> User | None:
    """Lấy người dùng theo email hoặc username."""
    return db.execute(
        select(User).where(
            (User.email == identifier) | (User.username == identifier)
        )
    ).scalar_one_or_none()


def create_user(db: Session, user_in: UserCreate) -> User:
    """Tạo người dùng mới."""
    user = User(
        email=user_in.email,
        username=user_in.username,
        password_hash=hash_password(user_in.password),
    )
    db.add(user)
    db.flush()
    return user


def update_user_password(db: Session, user: User, new_password_hash: str) -> User:
    """Cập nhật mật khẩu người dùng."""
    user.password_hash = new_password_hash
    db.add(user)
    return user
