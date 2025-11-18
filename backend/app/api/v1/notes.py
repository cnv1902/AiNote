"""
Các endpoint ghi chú.
"""
import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import User
from app.schemas import NoteCreate, NoteUpdate, NoteOut, QuestionIn, AnswerOut, QAHistoryOut
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
from app.crud.qa import (
    create_qa_request,
    get_user_qa_history,
    get_qa_request_by_id,
    delete_qa_request,
)
from app.services.storage import storage_service
from app.services.image import image_service
from app.services.ocr import ocr_service
from app.services.llm import llm_service
from app.services.smart_retrieval import SmartRetrieval


router = APIRouter(prefix="/notes", tags=["notes"])


@router.post("/", response_model=NoteOut, status_code=status.HTTP_201_CREATED)
async def create_note(
    payload: NoteCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Tạo ghi chú mới."""
    note = crud_create_note(db, user.id, payload.title, payload.content)
    
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
                print(f"✓ Đã lưu thực thể trích xuất cho ghi chú loại={entity_type}")
        except Exception as e:
            print(f"⚠ Không thể trích xuất thực thể: {e}")

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
    """Tạo ghi chú với hình ảnh đã tải lên."""
    if not image.content_type or not image.content_type.startswith('image/'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Chỉ chấp nhận tệp hình ảnh hợp lệ."
        )
    
    try:
        image_data = await image.read()
        
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
        
        note = crud_create_note(
            db,
            user_id=user.id,
            title=title or "Ghi chú hình ảnh",
            content=None
        )
        
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
        
        try:
            exif_data = image_service.extract_exif_data(image_data)
            if exif_data:
                metadata = image_service.parse_metadata(exif_data)
                create_image_metadata(db, file_record.id, metadata)
        except Exception as e:
            print(f"Cảnh báo: Không thể trích xuất siêu dữ liệu EXIF: {str(e)}")
        
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
                print(f"OCR đã trích xuất {len(ocr_text)} ký tự")
                
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
                        print(f"✓ Đã lưu thực thể trích xuất loại={entity_type}")
                except Exception as e:
                    print(f"⚠ Không thể trích xuất thực thể: {e}")
        except Exception as e:
            print(f"Cảnh báo: Không thể trích xuất văn bản qua OCR: {str(e)}")
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
    """Liệt kê tất cả ghi chú của người dùng hiện tại."""
    notes = get_user_notes(db, user.id, include_archived=False)
    return notes


@router.get("/{note_id}", response_model=NoteOut)
def get_note(
    note_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Lấy một ghi chú cụ thể theo ID."""
    note = get_note_by_id(db, note_id, user.id)
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy ghi chú"
        )
    return note


@router.put("/{note_id}", response_model=NoteOut)
def update_note(
    note_id: uuid.UUID,
    payload: NoteUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Cập nhật ghi chú."""
    note = get_note_by_id(db, note_id, user.id)
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy ghi chú"
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
    """Xóa ghi chú."""
    note = get_note_by_id(db, note_id, user.id)
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy ghi chú"
        )
    
    # Xóa các file liên quan từ kho lưu trữ
    if note.files:
        for file in note.files:
            try:
                storage_service.delete_image_by_key(file.storage_key)
            except Exception as e:
                print(f"Không thể xóa hình ảnh từ kho lưu trữ: {str(e)}")
    
    crud_delete_note(db, note)
    db.commit()
    return None


@router.post("/ask", response_model=AnswerOut)
async def ask_question(
    payload: QuestionIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Trả lời câu hỏi của người dùng dựa trên ghi chú của họ.
    Sử dụng smart retrieval để tìm ghi chú liên quan và LLM để tạo câu trả lời.
    """
    question = payload.question.strip()
    
    if not question:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Câu hỏi không được để trống"
        )
    
    try:
        retrieval = SmartRetrieval(db)
        
        query_type = retrieval.analyze_query_type(question)
        
        relevant_notes_with_scores = await retrieval.retrieve_relevant_notes(
            question=question,
            user_id=user.id,
            limit=5
        )
        
        if not relevant_notes_with_scores:
            return AnswerOut(
                question=question,
                answer="Xin lỗi, tôi không tìm thấy ghi chú nào liên quan đến câu hỏi của bạn.",
                relevant_notes=[],
                query_type=query_type,
                confidence=0.0
            )
        
        context_parts = []
        for i, (note, score) in enumerate(relevant_notes_with_scores[:3], 1):
            note_text = f"**Ghi chú {i}**"
            if note.title:
                note_text += f"\nTiêu đề: {note.title}"
            if note.content:
                note_text += f"\nNội dung: {note.content}"
            
            for file in note.files:
                if hasattr(file, 'ocr_texts') and file.ocr_texts:
                    for ocr in file.ocr_texts:
                        if ocr.text:
                            note_text += f"\nVăn bản từ hình ảnh: {ocr.text}"
            
            context_parts.append(note_text)
        context = "\n\n---\n\n".join(context_parts)
        answer = await llm_service.answer_question(question, context)
        if not answer:
            answer = "Xin lỗi, tôi không thể tạo câu trả lời cho câu hỏi của bạn lúc này."

        max_score = relevant_notes_with_scores[0][1] if relevant_notes_with_scores else 0
        confidence = min(max_score * 100, 100.0) if max_score > 0 else 50.0
        relevant_notes = [note for note, _ in relevant_notes_with_scores]
        
        # Lưu lịch sử chat
        try:
            qa_context = {
                "query_type": query_type,
                "relevant_note_ids": [str(note.id) for note in relevant_notes],
                "scores": [float(score) for _, score in relevant_notes_with_scores]
            }
            qa_response = {
                "answer": answer,
                "confidence": confidence,
                "note_count": len(relevant_notes)
            }
            create_qa_request(
                db,
                user_id=user.id,
                question=question,
                context=qa_context,
                response=qa_response
            )
            db.commit()
        except Exception as e:
            print(f"⚠ Không thể lưu lịch sử Q&A: {e}")
            # Không raise lỗi, tiếp tục trả về kết quả
        
        return AnswerOut(
            question=question,
            answer=answer,
            relevant_notes=relevant_notes,
            query_type=query_type,
            confidence=confidence
        )
        
    except Exception as e:
        print(f"❌ Lỗi khi trả lời câu hỏi: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Không thể trả lời câu hỏi: {str(e)}"
        )


@router.get("/chat-history", response_model=List[QAHistoryOut])
def get_chat_history(
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Lấy lịch sử chat Q&A của người dùng."""
    history = get_user_qa_history(db, user.id, limit=limit, offset=offset)
    return history


@router.get("/chat-history/{qa_id}", response_model=QAHistoryOut)
def get_chat_detail(
    qa_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Lấy chi tiết một bản ghi chat."""
    qa_request = get_qa_request_by_id(db, qa_id, user.id)
    if not qa_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy lịch sử chat"
        )
    return qa_request


@router.delete("/chat-history/{qa_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_chat_history(
    qa_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Xóa một bản ghi lịch sử chat."""
    qa_request = get_qa_request_by_id(db, qa_id, user.id)
    if not qa_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy lịch sử chat"
        )
    delete_qa_request(db, qa_request)
    db.commit()
    return None
