"""
Notes endpoints.
"""
import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import User
from app.schemas import NoteCreate, NoteUpdate, NoteOut
from app.api.dependencies import get_current_user
from app.crud.note import (
    get_note_by_id,
    get_user_notes,
    create_note as crud_create_note,
    update_note as crud_update_note,
    delete_note as crud_delete_note,
)
from app.crud.file import (
    create_file,
    create_image_metadata,
    create_ocr_text,
    create_extracted_entity,
)
from app.services.storage import storage_service
from app.services.image import image_service
from app.services.ocr import ocr_service
from app.services.llm import llm_service


router = APIRouter(prefix="/notes", tags=["notes"])


@router.post("/", response_model=NoteOut, status_code=status.HTTP_201_CREATED)
async def create_note(
    payload: NoteCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Create a new note."""
    note = crud_create_note(db, user.id, payload.title, payload.content)
    
    # Extract entities if content exists
    if payload.content:
        try:
            entities_json = await llm_service.extract_entities(payload.content)
            if entities_json and isinstance(entities_json, dict):
                entity_type = entities_json.get("entity_type") or "general_note"
                data = entities_json.get("data") or {}
                
                create_extracted_entity(
                    db,
                    user_id=user.id,
                    entity_type=entity_type,
                    data=data,
                    note_id=note.id,
                )
                print(f"✓ Stored extracted entity for note type={entity_type}")
        except Exception as e:
            print(f"⚠ Failed to extract entities: {e}")

    db.commit()
    db.refresh(note)
    return note


@router.post("/upload-image", response_model=NoteOut, status_code=status.HTTP_201_CREATED)
async def create_note_with_image(
    image: UploadFile = File(...),
    title: str = Form(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Create a note with an uploaded image."""
    if not image.content_type or not image.content_type.startswith('image/'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Chỉ chấp nhận tệp hình ảnh hợp lệ."
        )
    
    try:
        image_data = await image.read()
        
        # Upload to storage
        try:
            image_url, storage_key = storage_service.upload_image(
                file_data=image_data,
                filename=image.filename or "image.jpg",
                content_type=image.content_type
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Tải lên S3 thất bại: {str(e)}"
            )
        
        # Create note
        note = crud_create_note(
            db,
            user_id=user.id,
            title=title or "Ghi chú hình ảnh",
            content=None
        )
        
        # Create file record
        file_record = create_file(
            db,
            user_id=user.id,
            note_id=note.id,
            storage_key=storage_key,
            url=image_url,
            filename=image.filename,
            mime_type=image.content_type,
            size_bytes=len(image_data)
        )
        
        # Extract and store image metadata
        try:
            exif_data = image_service.extract_exif_data(image_data)
            if exif_data:
                metadata = image_service.parse_metadata(exif_data)
                create_image_metadata(db, file_record.id, metadata)
        except Exception as e:
            print(f"Warning: Could not extract EXIF metadata: {str(e)}")
        
        # Extract text via OCR
        try:
            ocr_text, ocr_confidence = await ocr_service.extract_text(
                image_data, 
                lang='vie+eng'
            )
            
            if ocr_text:
                create_ocr_text(
                    db,
                    file_id=file_record.id,
                    user_id=user.id,
                    text=ocr_text,
                    confidence=ocr_confidence
                )
                print(f"OCR extracted {len(ocr_text)} characters")
                
                # Extract entities from OCR text
                try:
                    entities_json = await llm_service.extract_entities(ocr_text)
                    if entities_json and isinstance(entities_json, dict):
                        entity_type = entities_json.get("entity_type") or "general_note"
                        data = entities_json.get("data") or {}
                        
                        create_extracted_entity(
                            db,
                            user_id=user.id,
                            entity_type=entity_type,
                            data=data,
                            file_id=file_record.id,
                        )
                        print(f"✓ Stored extracted entity type={entity_type}")
                except Exception as e:
                    print(f"⚠ Failed to extract entities: {e}")
        except Exception as e:
            print(f"Warning: Could not extract text via OCR: {str(e)}")
        
        db.commit()
        db.refresh(note)
        return note
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Tải lên hình ảnh thất bại: {str(e)}"
        )


@router.get("/", response_model=List[NoteOut])
def list_notes(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """List all notes for the current user."""
    notes = get_user_notes(db, user.id, include_archived=False)
    return notes


@router.get("/{note_id}", response_model=NoteOut)
def get_note(
    note_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Get a specific note by ID."""
    note = get_note_by_id(db, note_id, user.id)
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found"
        )
    return note


@router.put("/{note_id}", response_model=NoteOut)
def update_note(
    note_id: uuid.UUID,
    payload: NoteUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Update a note."""
    note = get_note_by_id(db, note_id, user.id)
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found"
        )
    
    crud_update_note(db, note, payload.title, payload.content)
    db.commit()
    db.refresh(note)
    return note


@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_note(
    note_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Delete a note."""
    note = get_note_by_id(db, note_id, user.id)
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found"
        )
    
    # Delete associated files from storage
    if note.files:
        for file in note.files:
            try:
                storage_service.delete_image_by_key(file.storage_key)
            except Exception as e:
                print(f"Failed to delete image from storage: {str(e)}")
    
    crud_delete_note(db, note)
    db.commit()
    return None
