"""
Các thao tác CRUD cho model Note.
"""
from uuid import UUID
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select

from app.models import Note, File as FileModel, OcrText


def get_note_by_id(db: Session, note_id: UUID, user_id: UUID) -> Note | None:
    """Lấy ghi chú theo ID cho một người dùng cụ thể."""
    return db.execute(
        select(Note)
        .options(
            selectinload(Note.files).selectinload(FileModel.image_metadata),
            selectinload(Note.files).selectinload(FileModel.ocr_texts)
        )
        .where(Note.id == note_id, Note.user_id == user_id)
    ).scalar_one_or_none()


def get_user_notes(
    db: Session, 
    user_id: UUID, 
    include_archived: bool = False,
    limit: int = 100,
    offset: int = 0
) -> list[Note]:
    """Lấy tất cả ghi chú của một người dùng."""
    query = select(Note).options(
        selectinload(Note.files).selectinload(FileModel.image_metadata),
        selectinload(Note.files).selectinload(FileModel.ocr_texts)
    ).where(Note.user_id == user_id)
    
    if not include_archived:
        query = query.where(Note.is_archived == False)
    
    query = query.order_by(Note.created_at.desc()).limit(limit).offset(offset)
    
    return db.execute(query).scalars().all()


def create_note(
    db: Session, 
    user_id: UUID, 
    title: str | None = None, 
    content: str | None = None
) -> Note:
    """Tạo ghi chú mới."""
    note = Note(user_id=user_id, title=title, content=content)
    db.add(note)
    db.flush()
    return note


def update_note(
    db: Session, 
    note: Note, 
    title: str | None = None, 
    content: str | None = None
) -> Note:
    """Cập nhật ghi chú hiện có."""
    if title is not None:
        note.title = title
    if content is not None:
        note.content = content
    db.add(note)
    return note


def archive_note(db: Session, note: Note) -> Note:
    """Lưu trữ ghi chú."""
    note.is_archived = True
    db.add(note)
    return note


def delete_note(db: Session, note: Note) -> None:
    """Xóa ghi chú."""
    db.delete(note)
