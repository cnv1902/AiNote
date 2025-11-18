"""
Các thao tác CRUD cho model QARequest (lịch sử chat).
"""
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import List

from app.models import QARequest


def create_qa_request(
    db: Session,
    user_id: UUID,
    question: str,
    context: dict | None = None,
    response: dict | None = None
) -> QARequest:
    """Tạo bản ghi lịch sử Q&A mới."""
    qa_request = QARequest(
        user_id=user_id,
        question=question,
        context=context,
        response=response
    )
    db.add(qa_request)
    db.flush()
    return qa_request

def get_user_qa_history(
    db: Session,
    user_id: UUID,
    limit: int = 50,
    offset: int = 0
) -> List[QARequest]:
    """Lấy lịch sử Q&A của người dùng."""
    query = (
        select(QARequest)
        .where(QARequest.user_id == user_id)
        .order_by(QARequest.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return db.execute(query).scalars().all()


def get_qa_request_by_id(
    db: Session,
    qa_id: UUID,
    user_id: UUID
) -> QARequest | None:
    """Lấy một bản ghi Q&A cụ thể."""
    return db.execute(
        select(QARequest)
        .where(QARequest.id == qa_id, QARequest.user_id == user_id)
    ).scalar_one_or_none()

def delete_qa_request(db: Session, qa_request: QARequest) -> None:
    """Xóa bản ghi Q&A."""
    db.delete(qa_request)
