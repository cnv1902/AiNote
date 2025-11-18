import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import User, AuthRefreshToken
from ..schemas import UserCreate, UserOut, TokenPair, TokenRefreshIn
from ..security import hash_password, verify_password, create_access_token, create_refresh_token, pwd_context
from ..utils import hash_text_sha256
from ..deps import get_current_user


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut)
def register(data: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email đã được đăng ký")
    try:
        password_hash = hash_password(data.password)
    except ValueError as e:
        # Normalize backend errors into a 400 instead of 500
        raise HTTPException(status_code=400, detail=str(e))

    user = User(
        email=data.email,
        username=data.username,
        password_hash=password_hash,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenPair)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(
        (User.email == form.username) | (User.username == form.username)
    ).first()
    if not user or not verify_password(form.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Thông tin đăng nhập không hợp lệ")
    if pwd_context.needs_update(user.password_hash):
        user.password_hash = hash_password(form.password)
        db.add(user)

    access = create_access_token(str(user.id))
    refresh, exp = create_refresh_token(str(user.id))
    r = AuthRefreshToken(
        user_id=user.id,
        token_hash=hash_text_sha256(refresh),
        expires_at=exp,
    )
    db.add(r)
    db.commit()

    return TokenPair(access_token=access, refresh_token=refresh)


@router.post("/refresh", response_model=TokenPair)
def refresh_token(data: TokenRefreshIn, db: Session = Depends(get_db)):
    hashed = hash_text_sha256(data.refresh_token)
    token_row = (
        db.query(AuthRefreshToken)
        .filter(AuthRefreshToken.token_hash == hashed, AuthRefreshToken.revoked_at.is_(None))
        .first()
    )
    if not token_row:
        raise HTTPException(status_code=401, detail="Mã thông báo làm mới không hợp lệ")

    from ..security import decode_token
    payload = decode_token(data.refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Loại mã thông báo làm mới không hợp lệ")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Tải trọng mã thông báo làm mới không hợp lệ")

    user = db.get(User, uuid.UUID(user_id))
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Người dùng không hoạt động")

    if datetime.now(timezone.utc) >= token_row.expires_at:
        raise HTTPException(status_code=401, detail="Mã thông báo làm mới đã hết hạn")

    access = create_access_token(user_id)
    token_row.revoked_at = datetime.now(timezone.utc)
    new_refresh, exp = create_refresh_token(user_id)
    db.add(AuthRefreshToken(user_id=user.id, token_hash=hash_text_sha256(new_refresh), expires_at=exp))
    db.commit()

    return TokenPair(access_token=access, refresh_token=new_refresh)

@router.get("/me", response_model=UserOut)
def me(current: User = Depends(get_current_user)):
    return current