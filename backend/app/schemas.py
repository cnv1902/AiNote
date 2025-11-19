"""
Các schema Pydantic để xác thực request/response.
"""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


# Người dùng
class UserBase(BaseModel):
    email: EmailStr
    username: str | None = None


class UserCreate(UserBase):
    password: str = Field(min_length=6, max_length=1024)


class UserOut(UserBase):
    id: UUID
    is_active: bool
    is_verified: bool
    avatar_url: str | None = None
    role: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Xác thực
class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenRefreshIn(BaseModel):
    refresh_token: str


# Ghi chú
class NoteCreate(BaseModel):
    title: str | None = None
    content_text: str | None = None


class NoteUpdate(BaseModel):
    title: str | None = None
    content_text: str | None = None


class NoteOut(BaseModel):
    id: UUID
    user_id: UUID
    title: str | None
    content_text: str | None
    ocr_text: str | None
    raw_image_url: str | None
    image_metadata: dict | None
    semantic_summary: str | None
    entity_type: str | None
    entities: dict | None
    is_archived: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Q&A
class QuestionIn(BaseModel):
    question: str = Field(min_length=1, max_length=1000)


class AnswerOut(BaseModel):
    question: str
    answer: str
    relevant_notes: list[NoteOut] = []
    query_type: str
    confidence: float | None = None


class QAHistoryOut(BaseModel):
    id: UUID
    user_id: UUID
    question: str
    context: dict | None = None
    response: dict | None = None
    created_at: datetime

    class Config:
        from_attributes = True


# Entity Types
class EntityTypeInfo(BaseModel):
    entity_type: str
    count: int