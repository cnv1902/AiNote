"""
Các endpoint xác thực.
"""
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import (
    hash_password, 
    verify_password, 
    create_access_token, 
    create_refresh_token,
    decode_token,
    pwd_context
)
from app.crud.user import (
    get_user_by_email,
    get_user_by_email_or_username,
    create_user,
    update_user_password,
)
from app.crud.auth import (
    create_refresh_token as create_refresh_token_record,
    get_valid_refresh_token,
    revoke_refresh_token,
)
from app.schemas import UserCreate, UserOut, TokenPair, TokenRefreshIn
from app.api.dependencies import get_current_user
from app.models import User
from app.core.utils import hash_text_sha256


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(data: UserCreate, db: Session = Depends(get_db)):
    """Đăng ký người dùng mới."""
    existing = get_user_by_email(db, data.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email đã được đăng ký"
        )
    
    try:
        user = create_user(db, data)
        db.commit()
        db.refresh(user)
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/login", response_model=TokenPair)
def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Đăng nhập bằng email/username và mật khẩu."""
    user = get_user_by_email_or_username(db, form.username)
    
    if not user or not verify_password(form.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Thông tin đăng nhập không hợp lệ"
        )
    
    # Cập nhật hash mật khẩu nếu cần
    if pwd_context.needs_update(user.password_hash):
        update_user_password(db, user, hash_password(form.password))

    # Tạo tokens
    access = create_access_token(str(user.id))
    refresh, exp = create_refresh_token(str(user.id))
    
    # Lưu refresh token
    create_refresh_token_record(
        db,
        user_id=user.id,
        token_hash=hash_text_sha256(refresh),
        expires_at=exp,
    )
    
    db.commit()

    return TokenPair(access_token=access, refresh_token=refresh)


@router.post("/refresh", response_model=TokenPair)
def refresh_token(data: TokenRefreshIn, db: Session = Depends(get_db)):
    """Làm mới access token bằng refresh token."""
    hashed = hash_text_sha256(data.refresh_token)
    token_row = get_valid_refresh_token(db, hashed)
    
    if not token_row:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Mã thông báo làm mới không hợp lệ"
        )

    # Giải mã và xác thực token
    try:
        payload = decode_token(data.refresh_token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Mã thông báo làm mới không hợp lệ"
        )
    
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Loại mã thông báo không hợp lệ"
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tải trọng mã thông báo không hợp lệ"
        )

    user = db.get(User, uuid.UUID(user_id))
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Người dùng không hoạt động"
        )

    # Kiểm tra thời hạn
    if datetime.now(timezone.utc) >= token_row.expires_at:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Mã thông báo đã hết hạn"
        )

    # Tạo tokens mới
    access = create_access_token(user_id)
    new_refresh, exp = create_refresh_token(user_id)
    
    # Thu hồi token cũ và tạo token mới
    revoke_refresh_token(db, token_row)
    create_refresh_token_record(
        db,
        user_id=user.id,
        token_hash=hash_text_sha256(new_refresh),
        expires_at=exp,
    )
    
    db.commit()

    return TokenPair(access_token=access, refresh_token=new_refresh)


@router.get("/me", response_model=UserOut)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Lấy thông tin người dùng hiện tại."""
    return current_user
