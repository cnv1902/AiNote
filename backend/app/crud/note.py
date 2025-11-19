"""
Các thao tác CRUD cho model NoteItem.
"""
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from typing import List, Optional

from app.models import NoteItem


def get_note_by_id(db: Session, note_id: UUID, user_id: UUID) -> NoteItem | None:
    """Lấy ghi chú theo ID cho một người dùng cụ thể."""
    return db.execute(
        select(NoteItem)
        .where(NoteItem.id == note_id, NoteItem.user_id == user_id)
    ).scalar_one_or_none()


def get_user_notes(
    db: Session, 
    user_id: UUID, 
    include_archived: bool = False,
    limit: int = 100,
    offset: int = 0
) -> List[NoteItem]:
    """Lấy tất cả ghi chú của một người dùng."""
    query = select(NoteItem).where(NoteItem.user_id == user_id)
    
    if not include_archived:
        query = query.where(NoteItem.is_archived == False)
    
    query = query.order_by(NoteItem.created_at.desc()).limit(limit).offset(offset)
    
    return db.execute(query).scalars().all()


def create_note(
    db: Session, 
    user_id: UUID, 
    title: str | None = None, 
    content_text: str | None = None,
    ocr_text: str | None = None,
    raw_image_url: str | None = None,
    image_metadata: dict | None = None,
    semantic_summary: str | None = None,
    entity_type: str | None = None,
    embedding: dict | None = None,
    entities: dict | None = None
) -> NoteItem:
    """Tạo ghi chú mới với đầy đủ thông tin."""
    note = NoteItem(
        user_id=user_id,
        title=title,
        content_text=content_text,
        ocr_text=ocr_text,
        raw_image_url=raw_image_url,
        image_metadata=image_metadata,
        semantic_summary=semantic_summary,
        entity_type=entity_type,
        embedding=embedding,
        entities=entities
    )
    db.add(note)
    db.flush()
    return note


def update_note(
    db: Session, 
    note: NoteItem, 
    title: str | None = None, 
    content_text: str | None = None,
    ocr_text: str | None = None,
    raw_image_url: str | None = None,
    image_metadata: dict | None = None,
    semantic_summary: str | None = None,
    entity_type: str | None = None,
    embedding: dict | None = None,
    entities: dict | None = None
) -> NoteItem:
    """Cập nhật ghi chú hiện có."""
    if title is not None:
        note.title = title
    if content_text is not None:
        note.content_text = content_text
    if ocr_text is not None:
        note.ocr_text = ocr_text
    if raw_image_url is not None:
        note.raw_image_url = raw_image_url
    if image_metadata is not None:
        note.image_metadata = image_metadata
    if semantic_summary is not None:
        note.semantic_summary = semantic_summary
    if entity_type is not None:
        note.entity_type = entity_type
    if embedding is not None:
        note.embedding = embedding
    if entities is not None:
        note.entities = entities
    
    db.add(note)
    return note


def update_note_embedding(
    db: Session,
    note: NoteItem,
    embedding: dict
) -> NoteItem:
    """Cập nhật embedding cho ghi chú."""
    note.embedding = embedding
    db.add(note)
    return note


def update_note_entities(
    db: Session,
    note: NoteItem,
    entities: dict
) -> NoteItem:
    """Cập nhật entities cho ghi chú."""
    note.entities = entities
    db.add(note)
    return note


def update_note_summary(
    db: Session,
    note: NoteItem,
    semantic_summary: str
) -> NoteItem:
    """Cập nhật semantic summary cho ghi chú."""
    note.semantic_summary = semantic_summary
    db.add(note)
    return note


def update_note_entity_type(
    db: Session,
    note: NoteItem,
    entity_type: str
) -> NoteItem:
    """Cập nhật entity type cho ghi chú."""
    note.entity_type = entity_type
    db.add(note)
    return note


def archive_note(db: Session, note: NoteItem) -> NoteItem:
    """Lưu trữ ghi chú."""
    note.is_archived = True
    db.add(note)
    return note


def delete_note(db: Session, note: NoteItem) -> None:
    """Xóa ghi chú."""
    db.delete(note)


def search_notes_by_text(
    db: Session,
    user_id: UUID,
    search_query: str,
    limit: int = 20
) -> List[NoteItem]:
    """Tìm kiếm ghi chú theo văn bản (LIKE search đơn giản)."""
    pattern = f"%{search_query}%"
    query = (
        select(NoteItem)
        .where(
            NoteItem.user_id == user_id,
            NoteItem.is_archived == False,
            (
                NoteItem.title.ilike(pattern) |
                NoteItem.content_text.ilike(pattern) |
                NoteItem.ocr_text.ilike(pattern)
            )
        )
        .order_by(NoteItem.updated_at.desc())
        .limit(limit)
    )
    
    return db.execute(query).scalars().all()


def get_notes_with_embeddings(
    db: Session,
    user_id: UUID,
    limit: Optional[int] = None
) -> List[NoteItem]:
    """Lấy tất cả ghi chú có embedding của user."""
    query = (
        select(NoteItem)
        .where(
            NoteItem.user_id == user_id,
            NoteItem.is_archived == False,
            NoteItem.embedding.isnot(None)
        )
        .order_by(NoteItem.updated_at.desc())
    )
    
    if limit:
        query = query.limit(limit)
    
    return db.execute(query).scalars().all()


def count_user_notes(db: Session, user_id: UUID) -> int:
    """Đếm số lượng ghi chú của user."""
    return db.execute(
        select(func.count(NoteItem.id))
        .where(NoteItem.user_id == user_id, NoteItem.is_archived == False)
    ).scalar() or 0


def get_notes_by_entity_type(
    db: Session,
    user_id: UUID,
    entity_type: str,
    limit: int = 100,
    offset: int = 0
) -> List[NoteItem]:
    """Lấy tất cả ghi chú theo entity_type của một người dùng."""
    query = (
        select(NoteItem)
        .where(
            NoteItem.user_id == user_id,
            NoteItem.entity_type == entity_type,
            NoteItem.is_archived == False
        )
        .order_by(NoteItem.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    
    return db.execute(query).scalars().all()


def get_all_entity_types(db: Session, user_id: UUID) -> List[str]:
    """Lấy danh sách tất cả entity_type duy nhất của user."""
    result = db.execute(
        select(NoteItem.entity_type)
        .where(
            NoteItem.user_id == user_id,
            NoteItem.entity_type.isnot(None),
            NoteItem.is_archived == False
        )
        .distinct()
        .order_by(NoteItem.entity_type)
    )
    
    return [row[0] for row in result.fetchall()]
