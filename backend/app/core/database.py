"""
Quản lý kết nối và session cơ sở dữ liệu.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

from .config import settings


# Tạo database engine
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

# Tạo session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Tạo declarative base cho models
Base = declarative_base()


def get_db() -> Session:
    """
    Hàm dependency để lấy database session.
    Yields một session và đảm bảo nó được đóng sau khi sử dụng.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
