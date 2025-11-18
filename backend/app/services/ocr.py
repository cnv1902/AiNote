"""
Dịch vụ OCR để trích xuất văn bản từ hình ảnh.
"""
import base64
from typing import Optional, Tuple
import httpx

from app.core.config import settings


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
        Trích xuất văn bản từ hình ảnh bằng model vision Ollama.
        
        Args:
            image_data: Dữ liệu hình ảnh nhị phân
            lang: Mã ngôn ngữ (không được sử dụng với Ollama nhưng giữ lại để tương thích)
            
        Returns:
            Tuple của (extracted_text, confidence_score)
        """
        try:
            if not settings.API_EXTRACT_TEXT or not settings.MODEL_EXTRACT_TEXT:
                print("⚠ OCR chưa được cấu hình - thiếu API_EXTRACT_TEXT hoặc MODEL_EXTRACT_TEXT")
                return None, None

            image_base64 = OCRService.encode_image(image_data)
            endpoint = f"{settings.API_EXTRACT_TEXT}/api/generate"

            payload = {
                "model": settings.MODEL_EXTRACT_TEXT,
                "prompt": (
                    "Bạn là một công cụ OCR. Trích xuất TẤT CẢ văn bản có thể nhìn thấy từ hình ảnh "
                    "CHÍNH XÁC như nó xuất hiện. Giữ nguyên dấu câu, dấu tiếng Việt, "
                    "ngắt dòng và khoảng trắng. KHÔNG dịch, tóm tắt hoặc giải thích. "
                    "Chỉ trả về văn bản thô đã trích xuất."
                ),
                "images": [image_base64],
                "stream": False
            }

            print(f"ℹ Đang gửi yêu cầu OCR đến {endpoint} sử dụng model={settings.MODEL_EXTRACT_TEXT}")

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(endpoint, json=payload)

                if response.status_code != 200:
                    print(f"❌ Lỗi Ollama {response.status_code}: {response.text}")
                    return None, None

                data = response.json()
                text = data.get("response", "").strip()

                if not text:
                    return None, None

                return text, 85.0

        except httpx.TimeoutException:
            print("❌ OCR hết thời gian chờ – kiểm tra xem Ollama có đang chạy không")
            return None, None
        except httpx.ConnectError:
            print(f"❌ Không thể kết nối đến {endpoint} – chạy: ollama serve")
            return None, None
        except Exception as e:
            print(f"❌ Lỗi OCR: {str(e)}")
            return None, None


# Instance singleton
ocr_service = OCRService()
