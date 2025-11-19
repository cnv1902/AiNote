"""
Các endpoint quản lý entity types - Phân loại và lọc ghi chú theo loại.
"""
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import User
from app.schemas import NoteOut, EntityTypeInfo
from app.api.dependencies import get_current_user
from app.crud.note import get_notes_by_entity_type, get_all_entity_types


router = APIRouter(prefix="/entity-types", tags=["entity-types"])


@router.get("/", response_model=List[str])
def list_entity_types(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Liệt kê tất cả entity types có trong notes của người dùng.
    
    Returns:
        Danh sách các entity type duy nhất (work_tasks, shopping_list, etc.)
    """
    entity_types = get_all_entity_types(db, user.id)
    return entity_types


@router.get("/{entity_type}/notes", response_model=List[NoteOut])
def get_notes_by_type(
    entity_type: str,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Lấy tất cả ghi chú theo entity type cụ thể.
    
    Args:
        entity_type: Loại entity (work_tasks, personal_tasks, shopping_list, etc.)
        limit: Số lượng notes tối đa (default: 100)
        offset: Vị trí bắt đầu (default: 0)
    
    Returns:
        Danh sách notes có entity_type khớp
    
    Example:
        GET /api/v1/entity-types/work_tasks/notes
        GET /api/v1/entity-types/shopping_list/notes?limit=20
    """
    notes = get_notes_by_entity_type(
        db=db,
        user_id=user.id,
        entity_type=entity_type,
        limit=limit,
        offset=offset
    )
    return notes


@router.get("/stats", response_model=List[EntityTypeInfo])
def get_entity_type_stats(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Lấy thống kê số lượng notes theo từng entity type.
    
    Returns:
        Danh sách entity types với số lượng notes tương ứng
    
    Example Response:
        [
            {"entity_type": "work_tasks", "count": 15},
            {"entity_type": "shopping_list", "count": 8},
            {"entity_type": "personal_tasks", "count": 23}
        ]
    """
    from sqlalchemy import select, func
    from app.models import NoteItem
    
    result = db.execute(
        select(
            NoteItem.entity_type,
            func.count(NoteItem.id).label('count')
        )
        .where(
            NoteItem.user_id == user.id,
            NoteItem.entity_type.isnot(None),
            NoteItem.is_archived == False
        )
        .group_by(NoteItem.entity_type)
        .order_by(func.count(NoteItem.id).desc())
    )
    
    stats = []
    for row in result.fetchall():
        stats.append({
            "entity_type": row[0],
            "count": row[1]
        })
    
    return stats
