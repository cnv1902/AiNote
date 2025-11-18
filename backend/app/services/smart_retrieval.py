"""
Dịch vụ Smart Retrieval cho tìm kiếm ghi chú thông minh.
"""
import uuid
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text, func, or_
import asyncio

from app.models import Note, OcrText, ExtractedEntity


class SmartRetrieval:
    """Dịch vụ retrieval thông minh - kết hợp nhiều phương pháp tìm kiếm."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def retrieve_relevant_notes(
        self, 
        question: str, 
        user_id: uuid.UUID,
        limit: int = 10
    ) -> List[Tuple[Note, float]]:
        """
        Retrieval thông minh - kết hợp nhiều phương pháp.
        
        Args:
            question: Câu hỏi của người dùng
            user_id: ID người dùng
            limit: Số lượng kết quả tối đa
            
        Returns:
            Danh sách tuple (Note, score) được sắp xếp theo độ liên quan
        """
        # Phân tích loại câu hỏi
        query_type = self.analyze_query_type(question)
        
        # Khởi chạy retrieval song song
        fts_results, vector_results, entity_results = await asyncio.gather(
            self.fts_retrieval(question, user_id, limit),
            self.vector_retrieval(question, user_id, limit),
            self.entity_retrieval(question, user_id, limit)
        )
        
        # Fusion và reranking theo loại câu hỏi
        if query_type == "keyword":
            weighted_results = self.weighted_fusion(
                fts_results, 0.6,
                vector_results, 0.3, 
                entity_results, 0.1
            )
        elif query_type == "semantic":
            weighted_results = self.weighted_fusion(
                vector_results, 0.6,
                fts_results, 0.2,
                entity_results, 0.2
            )
        elif query_type == "structured":
            weighted_results = self.weighted_fusion(
                entity_results, 0.5,
                fts_results, 0.3,
                vector_results, 0.2
            )
        else:  # hybrid
            weighted_results = self.weighted_fusion(
                fts_results, 0.4,
                vector_results, 0.4,
                entity_results, 0.2
            )
        
        # Rerank và giới hạn kết quả
        final_results = self.rerank(weighted_results, question, limit)
        return final_results
    
    def analyze_query_type(self, question: str) -> str:
        """
        Phân loại câu hỏi để chọn chiến lược retrieval.
        
        Returns:
            "keyword", "semantic", "structured", hoặc "hybrid"
        """
        question_lower = question.lower()
        words = question.split()
        
        # Structured: có thực thể/thuộc tính cụ thể - ưu tiên cao nhất
        structured_indicators = [
            'lúc', 'vào', 'ngày', 'tháng', 'của', 'ở đâu', 
            'bao nhiêu', 'số điện thoại', 'số', 'giá', 'địa chỉ',
            'email', 'website', 'sdt', 'phone', 'giờ', 'thời gian'
        ]
        if any(pattern in question_lower for pattern in structured_indicators):
            return "structured"
        
        # Keyword-based: có tên riêng hoặc từ khóa cụ thể
        keyword_indicators = ['họp', 'deadline', 'mua', 'gọi', 'gặp', 'làm', 'đi', 'về']
        # Kiểm tra tên riêng (chữ hoa) hoặc từ khóa cụ thể
        has_proper_noun = any(word[0].isupper() for word in question.split() if len(word) > 1)
        has_keyword = any(word in question_lower for word in keyword_indicators)
        
        if (len(words) <= 6 and (has_proper_noun or has_keyword)) or has_proper_noun:
            return "keyword"
        
        # Semantic: mô tả dài, abstract
        semantic_indicators = [
            'chuẩn bị gì', 'nên làm gì', 'kế hoạch', 'ý tưởng', 
            'làm thế nào', 'tại sao', 'như thế nào', 'có nên', 'có thể'
        ]
        if len(words) > 8 or any(phrase in question_lower for phrase in semantic_indicators):
            return "semantic"
        
        return "hybrid"
    
    async def fts_retrieval(
        self, 
        question: str, 
        user_id: uuid.UUID,
        limit: int = 10
    ) -> List[Tuple[Note, float]]:
        """
        Tìm kiếm Full-Text Search sử dụng PostgreSQL tsvector.
        
        Returns:
            Danh sách tuple (Note, ts_rank_score)
        """
        try:
            # Chuẩn bị query từ câu hỏi - loại bỏ stop words
            words = question.lower().split()
            stop_words = {'của', 'là', 'có', 'và', 'trong', 'với', 'được', 'này', 'đó', 'các', 'cho', 'về'}
            meaningful_words = [w for w in words if w not in stop_words and len(w) > 1]
            
            if not meaningful_words:
                meaningful_words = words  # Fallback nếu tất cả là stop words
            
            # Tạo query với OR operator để linh hoạt hơn
            search_query = ' | '.join(meaningful_words)
            
            # Tìm kiếm trong notes
            query = text("""
                SELECT id, user_id, title, content, is_archived, created_at, updated_at,
                       ts_rank(content_tsv, to_tsquery('simple', :query)) as rank
                FROM notes
                WHERE user_id = :user_id 
                    AND is_archived = false
                    AND content_tsv @@ to_tsquery('simple', :query)
                ORDER BY rank DESC
                LIMIT :limit
            """)
            
            result = self.db.execute(
                query, 
                {"query": search_query, "user_id": user_id, "limit": limit}
            )
            
            notes_with_scores = []
            for row in result:
                note = self.db.get(Note, row.id)
                if note:
                    notes_with_scores.append((note, float(row.rank)))
            
            # Nếu không tìm thấy kết quả với FTS, thử tìm kiếm đơn giản với LIKE
            if not notes_with_scores:
                fallback_query = text("""
                    SELECT id, user_id, title, content, is_archived, created_at, updated_at,
                           1.0 as rank
                    FROM notes
                    WHERE user_id = :user_id 
                        AND is_archived = false
                        AND (
                            LOWER(title) LIKE :pattern
                            OR LOWER(content) LIKE :pattern
                        )
                    ORDER BY updated_at DESC
                    LIMIT :limit
                """)
                
                # Tìm kiếm với từ quan trọng nhất
                important_words = [w for w in meaningful_words if len(w) > 3]
                if important_words:
                    pattern = f"%{important_words[0]}%"
                    result = self.db.execute(
                        fallback_query,
                        {"user_id": user_id, "pattern": pattern, "limit": limit}
                    )
                    
                    for row in result:
                        note = self.db.get(Note, row.id)
                        if note:
                            notes_with_scores.append((note, 0.5))
            
            # Tìm kiếm trong OCR text nếu vẫn không có kết quả
            if not notes_with_scores:
                ocr_query = text("""
                    SELECT DISTINCT n.id, n.user_id, n.title, n.content, n.is_archived, 
                           n.created_at, n.updated_at,
                           ts_rank(o.text_tsv, to_tsquery('simple', :query)) as rank
                    FROM notes n
                    JOIN files f ON f.note_id = n.id
                    JOIN ocr_texts o ON o.file_id = f.id
                    WHERE n.user_id = :user_id 
                        AND n.is_archived = false
                        AND o.text_tsv @@ to_tsquery('simple', :query)
                    ORDER BY rank DESC
                    LIMIT :limit
                """)
                
                result = self.db.execute(
                    ocr_query,
                    {"query": search_query, "user_id": user_id, "limit": limit}
                )
                
                for row in result:
                    note = self.db.get(Note, row.id)
                    if note:
                        notes_with_scores.append((note, float(row.rank)))
            
            return notes_with_scores
            
        except Exception as e:
            print(f"FTS retrieval error: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    async def vector_retrieval(
        self, 
        question: str, 
        user_id: uuid.UUID,
        limit: int = 10
    ) -> List[Tuple[Note, float]]:
        """
        Tìm kiếm semantic dựa trên similarity (simplified version).
        Tìm kiếm trong cả notes và OCR text.
        
        Returns:
            Danh sách tuple (Note, similarity_score)
        """
        try:
            # Simplified: tìm kiếm theo nội dung chứa các từ trong câu hỏi
            question_lower = question.lower()
            question_words = question_lower.split()
            
            # Loại bỏ stop words
            stop_words = {'của', 'là', 'có', 'và', 'trong', 'với', 'được', 'này', 'đó', 'các'}
            meaningful_words = [w for w in question_words if w not in stop_words and len(w) > 1]
            
            if not meaningful_words:
                meaningful_words = question_words
            
            notes = self.db.query(Note).filter(
                Note.user_id == user_id,
                Note.is_archived == False
            ).all()
            
            notes_with_scores = []
            for note in notes:
                # Kết hợp title, content và OCR text
                search_text = f"{note.title or ''} {note.content or ''}".lower()
                
                # Thêm OCR text từ files
                if note.files:
                    for file in note.files:
                        if hasattr(file, 'ocr_texts'):
                            for ocr in file.ocr_texts:
                                if ocr.text:
                                    search_text += f" {ocr.text.lower()}"
                
                # Tính điểm dựa trên số từ khớp và vị trí
                score = 0.0
                matched_words = 0
                
                for word in meaningful_words:
                    if word in search_text:
                        matched_words += 1
                        # Bonus nếu từ xuất hiện trong title
                        if note.title and word in note.title.lower():
                            score += 0.3
                        else:
                            score += 0.2
                
                if matched_words > 0:
                    # Normalize score theo số từ trong câu hỏi
                    base_score = matched_words / len(meaningful_words)
                    score = (score + base_score) / 2
                    
                    # Bonus cho exact phrase match
                    if question_lower in search_text:
                        score *= 1.5
                    
                    notes_with_scores.append((note, score))
            
            # Sắp xếp theo điểm
            notes_with_scores.sort(key=lambda x: x[1], reverse=True)
            return notes_with_scores[:limit]
            
        except Exception as e:
            print(f"Vector retrieval error: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    async def entity_retrieval(
        self, 
        question: str, 
        user_id: uuid.UUID,
        limit: int = 10
    ) -> List[Tuple[Note, float]]:
        """
        Tìm kiếm dựa trên extracted entities.
        
        Returns:
            Danh sách tuple (Note, relevance_score)
        """
        try:
            question_lower = question.lower()
            
            # Tìm entities liên quan
            entities = self.db.query(ExtractedEntity).filter(
                ExtractedEntity.user_id == user_id
            ).all()
            
            note_scores: Dict[uuid.UUID, float] = {}
            
            for entity in entities:
                if not entity.data:
                    continue
                
                # Tính điểm dựa trên entity_type và data
                entity_type = entity.entity_type.lower()
                
                # Chuyển đổi entity data thành chuỗi để tìm kiếm
                import json
                if isinstance(entity.data, dict):
                    entity_data_str = json.dumps(entity.data, ensure_ascii=False).lower()
                else:
                    entity_data_str = str(entity.data).lower()
                
                score = 0.0
                
                # Khớp entity type với câu hỏi
                if entity_type in question_lower:
                    score += 0.3
                
                # Khớp nội dung entity data với câu hỏi
                question_words = set(question_lower.split())
                
                # Loại bỏ stop words
                stop_words = {'của', 'là', 'có', 'và', 'trong', 'với', 'được', 'này', 'đó', 'các'}
                question_words = question_words - stop_words
                
                # Tính điểm dựa trên số từ khớp
                matches = 0
                for word in question_words:
                    if len(word) > 2 and word in entity_data_str:
                        matches += 1
                        # Bonus cho từ khóa quan trọng
                        if word in ['điện', 'thoại', 'số', 'địa', 'chỉ', 'email', 'tên', 'giá']:
                            matches += 0.5
                
                if matches > 0:
                    score += min(0.7 * (matches / len(question_words)), 0.7)
                
                # Bonus nếu entity chứa số điện thoại và câu hỏi hỏi về số điện thoại
                if 'điện thoại' in question_lower or 'sdt' in question_lower or 'phone' in question_lower:
                    if 'phone' in entity_data_str or any(char.isdigit() for char in entity_data_str):
                        score += 0.4
                
                # Bonus cho entity có nhiều thông tin
                if isinstance(entity.data, dict) and len(entity.data) > 3:
                    score += 0.1
                
                if score > 0 and entity.note_id:
                    if entity.note_id in note_scores:
                        note_scores[entity.note_id] = max(note_scores[entity.note_id], score)
                    else:
                        note_scores[entity.note_id] = score
            
            # Chuyển đổi sang list notes với scores
            notes_with_scores = []
            for note_id, score in sorted(note_scores.items(), key=lambda x: x[1], reverse=True)[:limit]:
                note = self.db.get(Note, note_id)
                if note and not note.is_archived:
                    notes_with_scores.append((note, score))
            
            return notes_with_scores
            
        except Exception as e:
            print(f"Entity retrieval error: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def weighted_fusion(
        self,
        results1: List[Tuple[Note, float]], weight1: float,
        results2: List[Tuple[Note, float]], weight2: float,
        results3: List[Tuple[Note, float]], weight3: float
    ) -> Dict[uuid.UUID, Tuple[Note, float]]:
        """
        Kết hợp kết quả từ nhiều phương pháp retrieval với trọng số.
        
        Returns:
            Dictionary mapping note_id -> (Note, combined_score)
        """
        combined: Dict[uuid.UUID, Tuple[Note, float]] = {}
        
        # Cộng điểm từ method 1
        for note, score in results1:
            combined[note.id] = (note, score * weight1)
        
        # Cộng điểm từ method 2
        for note, score in results2:
            if note.id in combined:
                existing_note, existing_score = combined[note.id]
                combined[note.id] = (existing_note, existing_score + score * weight2)
            else:
                combined[note.id] = (note, score * weight2)
        
        # Cộng điểm từ method 3
        for note, score in results3:
            if note.id in combined:
                existing_note, existing_score = combined[note.id]
                combined[note.id] = (existing_note, existing_score + score * weight3)
            else:
                combined[note.id] = (note, score * weight3)
        
        return combined
    
    def rerank(
        self, 
        weighted_results: Dict[uuid.UUID, Tuple[Note, float]], 
        question: str,
        limit: int = 10
    ) -> List[Tuple[Note, float]]:
        """
        Rerank kết quả cuối cùng dựa trên độ liên quan.
        
        Returns:
            Danh sách tuple (Note, final_score) được sắp xếp
        """
        # Chuyển đổi dict thành list và sort
        results = list(weighted_results.values())
        results.sort(key=lambda x: x[1], reverse=True)
        
        # Boost điểm cho ghi chú mới hơn
        question_lower = question.lower()
        reranked = []
        
        for note, score in results[:limit * 2]:  # Xem xét nhiều hơn limit để rerank
            # Boost score nếu title khớp với câu hỏi
            if note.title and any(word in note.title.lower() for word in question_lower.split()):
                score *= 1.2
            
            # Boost score cho ghi chú mới (trong 7 ngày gần đây)
            from datetime import datetime, timezone, timedelta
            if (datetime.now(timezone.utc) - note.updated_at) < timedelta(days=7):
                score *= 1.1
            
            reranked.append((note, score))
        
        # Sort lại và giới hạn
        reranked.sort(key=lambda x: x[1], reverse=True)
        return reranked[:limit]
