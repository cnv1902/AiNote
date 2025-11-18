import uuid
from typing import List
import re

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select

from ..db import get_db
from ..models import Note, User, File as FileModel, ImageMetadata, OcrText, ExtractedEntity
from ..schemas import NoteCreate, NoteUpdate, NoteOut
from ..deps import get_current_user
from ..storage_client import s3_client
from ..image_utils import extract_exif_data, parse_image_metadata
from ..ocr_utils import extract_text_from_image
from ..llm_utils import extract_entities

router = APIRouter(prefix="/notes", tags=["notes"])

@router.post("/", response_model=NoteOut)
async def create_note(payload: NoteCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    note = Note(user_id=user.id, title=payload.title, content=payload.content)
    db.add(note)
    db.flush() 
    if payload.content:
        entities_json = await extract_entities(payload.content)
        if entities_json and isinstance(entities_json, dict):
            entity_type = entities_json.get("entity_type") or "general_note"
            data = entities_json.get("data") or {}
            extracted = ExtractedEntity(
                note_id=note.id,
                file_id=None,
                user_id=user.id,
                entity_type=entity_type,
                data=data,
                confidence=None,
            )
            try:
                db.add(extracted)
                print(f"✓ Stored extracted entity for note type={entity_type}")
            except Exception as e:
                print(f"⚠ Failed to persist extracted entities for note: {e}")

    db.commit()
    db.refresh(note)
    return note

@router.post("/upload-image", response_model=NoteOut)
async def create_note_with_image(
    image: UploadFile = File(...),
    title: str = Form(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):

    if not image.content_type or not image.content_type.startswith('image/'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Chắc chắn bạn đã tải lên một tệp hình ảnh hợp lệ."
        )
    
    try:
        image_data = await image.read()
        try:
            image_url, storage_key = s3_client.upload_image(
                file_data=image_data,
                filename=image.filename or "image.jpg",
                content_type=image.content_type
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"S3 upload failed: {str(e)}"
            )
        
        note = Note(
            user_id=user.id,
            title=title or "Ghi chú hình ảnh",
            content=None
        )
        db.add(note)
        db.flush() 
        file_record = FileModel(
            user_id=user.id,
            note_id=note.id,
            storage_key=storage_key,
            url=image_url,
            filename=image.filename,
            mime_type=image.content_type,
            size_bytes=len(image_data)
        )
        db.add(file_record)
        db.flush() 
        try:
            exif_data = extract_exif_data(image_data)
            if exif_data:
                metadata = parse_image_metadata(exif_data)
                image_metadata = ImageMetadata(
                    file_id=file_record.id,
                    camera_make=metadata.get('camera_make'),
                    camera_model=metadata.get('camera_model'),
                    datetime_original=metadata.get('datetime_original'),
                    gps_latitude=metadata.get('gps_latitude'),
                    gps_longitude=metadata.get('gps_longitude'),
                    width=metadata.get('width'),
                    height=metadata.get('height'),
                    orientation=metadata.get('orientation'),
                    extra=metadata.get('extra') if metadata.get('extra') else None
                )
                db.add(image_metadata)
        except Exception as e:
            print(f"Warning: Could not extract EXIF metadata: {str(e)}")
        try:
            ocr_text, ocr_confidence = await extract_text_from_image(image_data, lang='vie+eng')
            if ocr_text:
                ocr_record = OcrText(
                    file_id=file_record.id,
                    user_id=user.id,
                    text=ocr_text,
                    ocr_confidence=ocr_confidence
                )
                db.add(ocr_record)
                print(f"OCR extracted {len(ocr_text)} characters")
                entities_json = await extract_entities(ocr_text)
                if entities_json and isinstance(entities_json, dict):
                    entity_type = entities_json.get("entity_type") or "general_note"
                    data = entities_json.get("data") or {}
                    try:
                        extracted = ExtractedEntity(
                            file_id=file_record.id,
                            note_id=None,
                            user_id=user.id,
                            entity_type=entity_type,
                            data=data,
                            confidence=None,
                        )
                        db.add(extracted)
                        print(f"✓ Stored extracted entity type={entity_type}")
                    except Exception as e:
                        print(f"⚠ Failed to store extracted entity: {e}")
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
            detail=f"Failed to upload image: {str(e)}"
        )


@router.get("/", response_model=List[NoteOut])
def list_notes(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    notes = db.execute(
        select(Note)
        .options(selectinload(Note.files).selectinload(FileModel.image_metadata))
        .where(Note.user_id == user.id, Note.is_archived == False)
        .order_by(Note.created_at.desc())
    ).scalars().all()
    return notes


@router.put("/{note_id}", response_model=NoteOut)
def update_note(note_id: uuid.UUID, payload: NoteUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    note = db.execute(select(Note).where(Note.id == note_id, Note.user_id == user.id)).scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
    if payload.title is not None:
        note.title = payload.title
    if payload.content is not None:
        note.content = payload.content
    db.commit()
    db.refresh(note)
    return note


@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_note(note_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    note = db.execute(select(Note).where(Note.id == note_id, Note.user_id == user.id)).scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
    if note.files:
        for file in note.files:
            try:
                s3_client.delete_image_by_key(file.storage_key)
            except Exception as e:
                print(f"Failed to delete image from S3: {str(e)}")
    db.delete(note)
    db.commit()
    return None