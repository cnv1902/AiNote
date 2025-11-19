"""
Dịch vụ Embedding cho RAG - Ưu tiên NER, fallback sang API providers.
"""
from typing import Optional, List
import json
import httpx
import spacy
from app.core.config import settings
from app.core.llm_providers import LLMProvider, get_provider_and_config


class EmbeddingService:
    """Dịch vụ tạo embedding cho văn bản - ưu tiên NER cho nội dung ngắn."""
    
    # Ngưỡng độ dài văn bản để quyết định dùng NER hay API
    NER_TEXT_LENGTH_THRESHOLD = 500  # ký tự
    
    def __init__(self):
        """Khởi tạo service."""
        self.nlp = None
        self._load_spacy_model()
    
    def _load_spacy_model(self):
        """Tải spaCy model cho NER (tiếng Việt hoặc multilingual)."""
        try:
            # Thử tải model tiếng Việt trước
            try:
                self.nlp = spacy.load("vi_core_news_lg")
                print("✓ Đã tải spaCy model: vi_core_news_lg")
            except OSError:
                # Fallback sang model multilingual
                try:
                    self.nlp = spacy.load("xx_ent_wiki_sm")
                    print("✓ Đã tải spaCy model: xx_ent_wiki_sm")
                except OSError:
                    print("⚠ Không tìm thấy spaCy model - NER sẽ không khả dụng")
                    print("  Cài đặt: python -m spacy download vi_core_news_lg")
                    self.nlp = None
        except Exception as e:
            print(f"⚠ Lỗi khi tải spaCy model: {e}")
            self.nlp = None
    
    def extract_ner_features(self, text: str) -> dict:
        """
        Trích xuất đặc trưng NER từ văn bản.
        
        Args:
            text: Văn bản cần phân tích
            
        Returns:
            Dictionary chứa các entities và từ khóa quan trọng
        """
        if not self.nlp or not text:
            return {}
        
        try:
            doc = self.nlp(text[:10000])  # Giới hạn độ dài để tránh quá tải
            
            features = {
                "entities": {},
                "keywords": [],
                "pos_tags": {},
                "noun_chunks": []
            }
            
            # Trích xuất named entities
            for ent in doc.ents:
                entity_type = ent.label_
                entity_text = ent.text.strip()
                
                if entity_type not in features["entities"]:
                    features["entities"][entity_type] = []
                
                if entity_text not in features["entities"][entity_type]:
                    features["entities"][entity_type].append(entity_text)
            
            # Trích xuất noun chunks (cụm danh từ) - không hỗ trợ cho một số ngôn ngữ
            try:
                for chunk in doc.noun_chunks:
                    chunk_text = chunk.text.strip()
                    if len(chunk_text) > 2 and chunk_text not in features["noun_chunks"]:
                        features["noun_chunks"].append(chunk_text)
            except NotImplementedError:
                # noun_chunks không được hỗ trợ cho ngôn ngữ này (như tiếng Việt)
                pass
            
            # Trích xuất từ khóa (danh từ riêng, danh từ quan trọng)
            for token in doc:
                # Lọc stop words và punctuation
                if token.is_stop or token.is_punct or len(token.text) < 2:
                    continue
                
                # Thu thập từ quan trọng (NOUN, PROPN, NUM)
                if token.pos_ in ["NOUN", "PROPN", "NUM", "VERB"]:
                    lemma = token.lemma_.lower()
                    if lemma not in features["keywords"]:
                        features["keywords"].append(lemma)
                
                # Đếm POS tags
                if token.pos_ not in features["pos_tags"]:
                    features["pos_tags"][token.pos_] = 0
                features["pos_tags"][token.pos_] += 1
            
            # Giới hạn số lượng features
            features["keywords"] = features["keywords"][:50]
            features["noun_chunks"] = features["noun_chunks"][:30]
            
            return features
            
        except Exception as e:
            print(f"⚠ Lỗi khi trích xuất NER features: {e}")
            return {}
    
    def create_ner_embedding(self, text: str) -> Optional[dict]:
        """
        Tạo embedding dựa trên NER features (cho văn bản ngắn).
        
        Args:
            text: Văn bản cần embedding
            
        Returns:
            Dictionary chứa embedding features hoặc None
        """
        features = self.extract_ner_features(text)
        
        if not features or not features.get("keywords"):
            return None
        
        # Tạo embedding representation dựa trên features
        embedding = {
            "type": "ner_features",
            "entities": features["entities"],
            "keywords": features["keywords"][:20],  # Top 20 keywords
            "noun_chunks": features["noun_chunks"][:15],  # Top 15 noun chunks
            "text_length": len(text),
            "entity_count": sum(len(v) for v in features["entities"].values()),
            "metadata": {
                "pos_distribution": features["pos_tags"]
            }
        }
        
        return embedding
    
    async def create_api_embedding(self, text: str) -> Optional[List[float]]:
        """
        Tạo embedding vector sử dụng API provider.
        
        Args:
            text: Văn bản cần embedding
            
        Returns:
            List các số thực (embedding vector) hoặc None
        """
        if not text or not text.strip():
            return None
        
        # Hỗ trợ cả API_EXTRACT_EMBEDDING_NAME (mới) và API_EXTRACT_EMBEDDING (cũ)
        provider_name = getattr(settings, "API_EXTRACT_EMBEDDING_NAME", "") or  ""
        provider, config = get_provider_and_config(provider_name, is_chat=False)
        
        # Ghi đè model cho embedding
        model_extract_embedding = getattr(settings, "MODEL_EXTRACT_EMBEDDING", None)
        if model_extract_embedding:
            config["model"] = model_extract_embedding
        
        try:
            if provider == LLMProvider.LOCAL:
                # Ollama không có embedding endpoint chuẩn
                print("⚠ Ollama local không hỗ trợ embedding API")
                return None
            
            elif provider == LLMProvider.GPT:
                if not config.get("api_key"):
                    print("⚠ Thiếu OPENAI_API_KEY")
                    return None
                
                return await self._call_openai_embedding(
                    api_key=config["api_key"],
                    model=config.get("model", "text-embedding-3-small"),
                    text=text
                )
            
            elif provider == LLMProvider.GEMINI:
                if not config.get("api_key"):
                    print("⚠ Thiếu GEMINI_API_KEY")
                    return None
                
                return await self._call_gemini_embedding(
                    api_key=config["api_key"],
                    model=config.get("model", "models/text-embedding-004"),
                    text=text
                )
            
            elif provider == LLMProvider.DEEPSEEK:
                # DeepSeek có thể không hỗ trợ embedding
                print("⚠ DeepSeek chưa hỗ trợ embedding API")
                return None
            
            else:
                print(f"⚠ Provider {provider} không hỗ trợ embedding")
                return None
                
        except Exception as e:
            print(f"❌ Lỗi khi tạo API embedding: {e}")
            return None
    
    async def _call_openai_embedding(
        self,
        api_key: str,
        model: str,
        text: str
    ) -> Optional[List[float]]:
        """Gọi OpenAI Embedding API."""
        try:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": model,
                "input": text[:8000],  # Giới hạn độ dài
                "encoding_format": "float"
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    "https://api.openai.com/v1/embeddings",
                    headers=headers,
                    json=payload
                )
                
                if resp.status_code != 200:
                    print(f"❌ Lỗi OpenAI Embedding API {resp.status_code}: {resp.text}")
                    return None
                
                data = resp.json()
                embedding = data.get("data", [{}])[0].get("embedding")
                
                if embedding and isinstance(embedding, list):
                    print(f"✓ Đã tạo OpenAI embedding (dim={len(embedding)})")
                    return embedding
                
                return None
                
        except Exception as e:
            print(f"❌ Lỗi OpenAI embedding: {e}")
            return None
    
    async def _call_gemini_embedding(
        self,
        api_key: str,
        model: str,
        text: str
    ) -> Optional[List[float]]:
        """Gọi Google Gemini Embedding API."""
        try:
            # Gemini embedding API format
            if not model.startswith("models/"):
                model = f"models/{model}"
            
            url = f"https://generativelanguage.googleapis.com/v1beta/{model}:embedContent?key={api_key}"
            
            payload = {
                "content": {
                    "parts": [{
                        "text": text[:10000]  # Giới hạn độ dài
                    }]
                }
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(url, json=payload)
                
                if resp.status_code != 200:
                    print(f"❌ Lỗi Gemini Embedding API {resp.status_code}: {resp.text}")
                    return None
                
                data = resp.json()
                embedding = data.get("embedding", {}).get("values")
                
                if embedding and isinstance(embedding, list):
                    print(f"✓ Đã tạo Gemini embedding (dim={len(embedding)})")
                    return embedding
                
                return None
                
        except Exception as e:
            print(f"❌ Lỗi Gemini embedding: {e}")
            return None
    
    async def create_embedding(self, text: str) -> Optional[dict]:
        """
        Tạo embedding cho văn bản - tự động chọn phương pháp phù hợp.
        
        Chiến lược:
        - Nếu văn bản ngắn (< 500 ký tự) và có NER: dùng NER features
        - Nếu văn bản dài hoặc NER không khả dụng: dùng API embedding
        
        Args:
            text: Văn bản cần embedding
            
        Returns:
            Dictionary chứa embedding (NER features hoặc vector)
        """
        if not text or not text.strip():
            return None
        
        text = text.strip()
        text_length = len(text)
        
        # Quyết định phương pháp embedding
        use_ner = (
            text_length < self.NER_TEXT_LENGTH_THRESHOLD 
            and self.nlp is not None
        )
        
        if use_ner:
            print(f"ℹ Sử dụng NER embedding (text_length={text_length})")
            ner_embedding = self.create_ner_embedding(text)
            
            if ner_embedding and ner_embedding.get("keywords"):
                return ner_embedding
            
            # Fallback sang API nếu NER không đủ chất lượng
            print("⚠ NER embedding không đủ chất lượng, fallback sang API")
        
        # Sử dụng API embedding
        print(f"ℹ Sử dụng API embedding (text_length={text_length})")
        vector = await self.create_api_embedding(text)
        
        if vector:
            return {
                "type": "api_vector",
                "vector": vector,
                "dimension": len(vector),
                "text_length": text_length
            }
        
        # Fallback cuối cùng: tạo embedding đơn giản dựa trên keywords
        print("⚠ API embedding thất bại, sử dụng keyword fallback")
        return self._create_keyword_embedding(text)
    
    def _create_keyword_embedding(self, text: str) -> dict:
        """
        Tạo embedding đơn giản dựa trên từ khóa (fallback cuối cùng).
        
        Args:
            text: Văn bản cần embedding
            
        Returns:
            Dictionary chứa keywords và metadata
        """
        # Tách từ và lọc
        words = text.lower().split()
        stop_words = {
            'của', 'là', 'có', 'và', 'trong', 'với', 'được', 'này', 'đó', 
            'các', 'cho', 'về', 'từ', 'đến', 'một', 'không', 'như', 'để'
        }
        
        keywords = []
        for word in words:
            # Lọc stop words và từ ngắn
            if word not in stop_words and len(word) > 2:
                if word not in keywords:
                    keywords.append(word)
        
        return {
            "type": "keyword_fallback",
            "keywords": keywords[:30],  # Top 30 keywords
            "text_length": len(text),
            "word_count": len(words)
        }
    
    def calculate_similarity(
        self, 
        embedding1: dict, 
        embedding2: dict
    ) -> float:
        """
        Tính độ tương đồng giữa 2 embeddings.
        
        Args:
            embedding1: Embedding thứ nhất
            embedding2: Embedding thứ hai
            
        Returns:
            Điểm similarity (0.0 - 1.0)
        """
        type1 = embedding1.get("type")
        type2 = embedding2.get("type")
        
        # Cả 2 đều là API vector
        if type1 == "api_vector" and type2 == "api_vector":
            return self._cosine_similarity(
                embedding1.get("vector", []),
                embedding2.get("vector", [])
            )
        
        # Cả 2 đều là NER features hoặc keywords
        if type1 in ["ner_features", "keyword_fallback"] and \
           type2 in ["ner_features", "keyword_fallback"]:
            return self._keyword_similarity(
                embedding1.get("keywords", []),
                embedding2.get("keywords", [])
            )
        
        # Mixed types: tính similarity dựa trên keywords
        keywords1 = embedding1.get("keywords", [])
        keywords2 = embedding2.get("keywords", [])
        
        return self._keyword_similarity(keywords1, keywords2)
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Tính cosine similarity giữa 2 vectors."""
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0
        
        try:
            import numpy as np
            vec1_np = np.array(vec1)
            vec2_np = np.array(vec2)
            
            dot_product = np.dot(vec1_np, vec2_np)
            norm1 = np.linalg.norm(vec1_np)
            norm2 = np.linalg.norm(vec2_np)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            return float(dot_product / (norm1 * norm2))
            
        except Exception as e:
            print(f"⚠ Lỗi cosine similarity: {e}")
            return 0.0
    
    def _keyword_similarity(self, keywords1: List[str], keywords2: List[str]) -> float:
        """Tính similarity dựa trên keyword overlap."""
        if not keywords1 or not keywords2:
            return 0.0
        
        set1 = set(keywords1)
        set2 = set(keywords2)
        
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        
        if union == 0:
            return 0.0
        
        # Jaccard similarity
        return intersection / union


# Singleton instance
embedding_service = EmbeddingService()
