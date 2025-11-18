"""
Pydantic schemas for request/response validation.
"""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


# User
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


# Auth
class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenRefreshIn(BaseModel):
    refresh_token: str


# Notes
class NoteCreate(BaseModel):
    title: str | None = None
    content: str | None = None


class NoteUpdate(BaseModel):
    title: str | None = None
    content: str | None = None


class NoteImageUpload(BaseModel):
    title: str | None = None
    # content will be set to image URL after upload


class ImageMetadataOut(BaseModel):
    file_id: UUID
    camera_make: str | None
    camera_model: str | None
    datetime_original: datetime | None
    gps_latitude: float | None
    gps_longitude: float | None
    width: int | None
    height: int | None
    orientation: int | None
    extra: dict | None
    created_at: datetime

    class Config:
        from_attributes = True


class OcrTextOut(BaseModel):
    id: UUID
    file_id: UUID
    user_id: UUID
    text: str | None
    ocr_confidence: float | None
    created_at: datetime

    class Config:
        from_attributes = True


class FileOut(BaseModel):
    id: UUID
    user_id: UUID
    note_id: UUID | None
    storage_key: str
    url: str | None
    filename: str | None
    mime_type: str | None
    size_bytes: int | None
    created_at: datetime
    image_metadata: ImageMetadataOut | None = None

    class Config:
        from_attributes = True


class NoteOut(BaseModel):
    id: UUID
    user_id: UUID
    title: str | None
    content: str | None
    is_archived: bool
    created_at: datetime
    updated_at: datetime
    files: list[FileOut] = []

    class Config:
        from_attributes = True