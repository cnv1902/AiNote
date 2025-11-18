"""
Các thao tác CRUD cho model File và các model liên quan.
"""
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session

from app.models import File, ImageMetadata, OcrText, ExtractedEntity


def create_file(
    db: Session,
    user_id: UUID,
    note_id: UUID | None,
    storage_key: str,
    url: str | None = None,
    filename: str | None = None,
    mime_type: str | None = None,
    size_bytes: int | None = None,
) -> File:
    """Tạo bản ghi file mới."""
    file = File(
        user_id=user_id,
        note_id=note_id,
        storage_key=storage_key,
        url=url,
        filename=filename,
        mime_type=mime_type,
        size_bytes=size_bytes,
    )
    db.add(file)
    db.flush()
    return file


def create_image_metadata(
    db: Session,
    file_id: UUID,
    metadata: dict,
) -> ImageMetadata:
    """Tạo bản ghi siêu dữ liệu hình ảnh."""
    image_metadata = ImageMetadata(
        file_id=file_id,
        camera_make=metadata.get('camera_make'),
        camera_model=metadata.get('camera_model'),
        datetime_original=metadata.get('datetime_original'),
        gps_latitude=metadata.get('gps_latitude'),
        gps_longitude=metadata.get('gps_longitude'),
        width=metadata.get('width'),
        height=metadata.get('height'),
        orientation=metadata.get('orientation'),
        extra=metadata.get('extra') if metadata.get('extra') else None,
    )
    db.add(image_metadata)
    db.flush()
    return image_metadata


def create_ocr_text(
    db: Session,
    file_id: UUID,
    user_id: UUID,
    text: str | None,
    confidence: float | None = None,
) -> OcrText:
    """Tạo bản ghi văn bản OCR."""
    ocr_record = OcrText(
        file_id=file_id,
        user_id=user_id,
        text=text,
        ocr_confidence=confidence,
    )
    db.add(ocr_record)
    db.flush()
    return ocr_record


def create_extracted_entity(
    db: Session,
    user_id: UUID,
    entity_type: str,
    data: dict,
    file_id: UUID | None = None,
    note_id: UUID | None = None,
    confidence: float | None = None,
) -> ExtractedEntity:
    """Tạo bản ghi thực thể đã trích xuất."""
    entity = ExtractedEntity(
        file_id=file_id,
        note_id=note_id,
        user_id=user_id,
        entity_type=entity_type,
        data=data,
        confidence=confidence,
    )
    db.add(entity)
    db.flush()
    return entity
