"""
OCR service for extracting text from images.
"""
import base64
from typing import Optional, Tuple
import httpx

from app.core.config import settings


class OCRService:
    """Service for OCR text extraction from images."""
    
    @staticmethod
    def encode_image(image_data: bytes) -> str:
        """Encode image data to base64."""
        return base64.b64encode(image_data).decode('utf-8')

    @staticmethod
    async def extract_text(
        image_data: bytes, 
        lang: str = 'vie+eng'
    ) -> Tuple[Optional[str], Optional[float]]:
        """
        Extract text from image using Ollama vision model.
        
        Args:
            image_data: Binary image data
            lang: Language code (not used with Ollama but kept for compatibility)
            
        Returns:
            Tuple of (extracted_text, confidence_score)
        """
        try:
            if not settings.API_EXTRACT_TEXT or not settings.MODEL_EXTRACT_TEXT:
                print("⚠ OCR not configured - missing API_EXTRACT_TEXT or MODEL_EXTRACT_TEXT")
                return None, None

            image_base64 = OCRService.encode_image(image_data)
            endpoint = f"{settings.API_EXTRACT_TEXT}/api/generate"

            payload = {
                "model": settings.MODEL_EXTRACT_TEXT,
                "prompt": (
                    "You are an OCR engine. Extract ALL visible text from the image "
                    "EXACTLY as it appears. Preserve punctuation, Vietnamese accents, "
                    "line breaks, and spacing. Do NOT translate, summarize, or explain. "
                    "Return ONLY the raw extracted text."
                ),
                "images": [image_base64],
                "stream": False
            }

            print(f"ℹ Sending OCR request to {endpoint} using model={settings.MODEL_EXTRACT_TEXT}")

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(endpoint, json=payload)

                if response.status_code != 200:
                    print(f"❌ Ollama error {response.status_code}: {response.text}")
                    return None, None

                data = response.json()
                text = data.get("response", "").strip()

                if not text:
                    return None, None

                return text, 85.0

        except httpx.TimeoutException:
            print("❌ OCR timeout – check if Ollama is running")
            return None, None
        except httpx.ConnectError:
            print(f"❌ Cannot connect to {endpoint} – run: ollama serve")
            return None, None
        except Exception as e:
            print(f"❌ OCR error: {str(e)}")
            return None, None


# Singleton instance
ocr_service = OCRService()
