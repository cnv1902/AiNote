"""
Dịch vụ OCR để trích xuất văn bản từ hình ảnh.
"""
import base64
from typing import Optional, Tuple
import httpx

from app.core.config import settings
from app.core.llm_providers import LLMProvider, APIClient, get_provider_and_config


class OCRService:
    """Dịch vụ trích xuất văn bản OCR từ hình ảnh."""
    
    @staticmethod
    def encode_image(image_data: bytes) -> str:
        """Mã hóa dữ liệu hình ảnh sang base64."""
        return base64.b64encode(image_data).decode('utf-8')

    @staticmethod
    async def extract_text(
        image_data: bytes, 
        lang: str = 'vie+eng'
    ) -> Tuple[Optional[str], Optional[float]]:
        """
        Trích xuất văn bản từ hình ảnh bằng model vision.
        
        Args:
            image_data: Dữ liệu hình ảnh nhị phân
            lang: Mã ngôn ngữ (không được sử dụng với một số provider nhưng giữ lại để tương thích)
            
        Returns:
            Tuple của (extracted_text, confidence_score)
        """
        try:
            image_base64 = OCRService.encode_image(image_data)
            
            ocr_prompt = (
                "Bạn là một công cụ OCR. Trích xuất TẤT CẢ văn bản có thể nhìn thấy từ hình ảnh "
                "CHÍNH XÁC như nó xuất hiện. Giữ nguyên dấu câu, dấu tiếng Việt, "
                "ngắt dòng và khoảng trắng. KHÔNG dịch, tóm tắt hoặc giải thích. "
                "Chỉ trả về văn bản thô đã trích xuất."
            )
            
            provider, config = get_provider_and_config(settings.API_EXTRACT_NAME, is_chat=False)
            
            print(f"ℹ Đang gửi yêu cầu OCR với provider={settings.API_EXTRACT_NAME or 'LOCAL'}")
            
            text = None
            
            if provider == LLMProvider.LOCAL:
                if not config.get("base_url") or not config.get("model"):
                    print("⚠ OCR chưa được cấu hình - thiếu API_EXTRACT_TEXT hoặc MODEL_EXTRACT_TEXT")
                    return None, None
                
                text = await APIClient.call_ollama(
                    base_url=config["base_url"],
                    model=config["model"],
                    prompt=ocr_prompt,
                    image_base64=image_base64
                )
            
            elif provider == LLMProvider.GPT:
                if not config.get("api_key"):
                    print("⚠ Thiếu OPENAI_API_KEY")
                    return None, None
                
                text = await APIClient.call_openai(
                    api_key=config["api_key"],
                    model=config.get("model", "gpt-4o-mini"),
                    prompt=ocr_prompt,
                    image_base64=image_base64
                )
            
            elif provider == LLMProvider.GEMINI:
                if not config.get("api_key"):
                    print("⚠ Thiếu GEMINI_API_KEY")
                    return None, None
                
                text = await APIClient.call_gemini(
                    api_key=config["api_key"],
                    model=config.get("model", "gemini-1.5-flash"),
                    prompt=ocr_prompt,
                    image_base64=image_base64
                )
            
            elif provider == LLMProvider.CLAUDE:
                if not config.get("api_key"):
                    print("⚠ Thiếu ANTHROPIC_API_KEY")
                    return None, None
                
                text = await APIClient.call_claude(
                    api_key=config["api_key"],
                    model=config.get("model", "claude-3-5-sonnet-20241022"),
                    prompt=ocr_prompt,
                    image_base64=image_base64
                )
            
            else:
                print(f"⚠ Provider {provider} không hỗ trợ OCR/Vision")
                return None, None
            
            if not text:
                return None, None
            
            return text, 85.0

        except Exception as e:
            print(f"❌ Lỗi OCR: {str(e)}")
            return None, None


# Instance singleton
ocr_service = OCRService()
