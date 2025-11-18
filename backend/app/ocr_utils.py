import httpx
from PIL import Image
from io import BytesIO
from typing import Optional, Tuple
import base64
import json

from .config import settings
from urllib.parse import urlparse


def encode_image_to_base64(image_data: bytes) -> str:
    return base64.b64encode(image_data).decode('utf-8')


async def extract_text_from_image(image_data: bytes, lang: str = 'vie+eng') -> Tuple[Optional[str], Optional[float]]:
    try:

        image_base64 = encode_image_to_base64(image_data)

        base_url = settings.API_EXTRACT_TEXT
        endpoint = f"{base_url}/api/generate"

        model = settings.MODEL_EXTRACT_TEXT
        payload = {
            "model": model,
            "prompt": "You are an OCR engine. Extract ALL visible text from the image EXACTLY as it appears. Preserve punctuation, Vietnamese accents, line breaks, and spacing. Do NOT translate, summarize, or explain. Return ONLY the raw extracted text.",
            "images": [image_base64],
            "stream": False
            }


        print(f"ℹ Sending OCR request to Ollama at {endpoint} using model={model}")

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
        print("❌ OCR timeout – kiểm tra Ollama đang chạy")
        return None, None

    except httpx.ConnectError:
        print(f"❌ Không thể kết nối {endpoint} – chạy: ollama serve")
        return None, None

    except Exception as e:
        print(f"❌ Lỗi OCR: {str(e)}")
        return None, None



def is_text_present(image_data: bytes, lang: str = 'vie+eng', min_confidence: float = 30.0) -> bool:
    import asyncio
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    text, confidence = loop.run_until_complete(extract_text_from_image(image_data, lang))
    
    if text and confidence and confidence >= min_confidence:
        return True
    return False


def preprocess_image_for_ocr(image_data: bytes) -> bytes:
    try:
        image = Image.open(BytesIO(image_data))
        
        if image.mode not in ('RGB', 'L'):
            image = image.convert('RGB')
        
        output = BytesIO()
        image.save(output, format='PNG')
        return output.getvalue()
        
    except Exception as e:
        print(f"Có lỗi trong quá trình xử lý ảnh: {str(e)}")
        return image_data  
