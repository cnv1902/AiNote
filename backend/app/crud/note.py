"""
CRUD operations for Note model.
"""
from uuid import UUID
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select

from app.models import Note, File as FileModel


def get_note_by_id(db: Session, note_id: UUID, user_id: UUID) -> Note | None:
    """Get note by ID for a specific user."""
    return db.execute(
        select(Note)
        .options(selectinload(Note.files).selectinload(FileModel.image_metadata))
        .where(Note.id == note_id, Note.user_id == user_id)
    ).scalar_one_or_none()


def get_user_notes(
    db: Session, 
    user_id: UUID, 
    include_archived: bool = False,
    limit: int = 100,
    offset: int = 0
) -> list[Note]:
    """Get all notes for a user."""
    query = select(Note).options(
        selectinload(Note.files).selectinload(FileModel.image_metadata)
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
    """Create a new note."""
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
    """Update an existing note."""
    if title is not None:
        note.title = title
    if content is not None:
        note.content = content
    db.add(note)
    return note


def archive_note(db: Session, note: Note) -> Note:
    """Archive a note."""
    note.is_archived = True
    db.add(note)
    return note


def delete_note(db: Session, note: Note) -> None:
    """Delete a note."""
    db.delete(note)
