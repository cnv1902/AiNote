"""
LLM service for entity extraction and intelligent text processing.
"""
import json
from typing import Optional
from urllib.parse import urlparse
import httpx

from app.core.config import settings


ENTITY_EXTRACTION_PROMPT = (
    "You are an AI assistant that extracts structured information from user notes or documents.\n\n"
    "1. Determine the type of document. Possible types: receipt, invoice, id_card, meeting_note, general_note.\n"
    "2. Extract the main fields relevant to that type. Return as JSON with keys:\n"
    "   - entity_type\n"
    "   - data (structured content according to entity_type)\n\n"
    "Text:\n\"\"\"\n{note_text}\n\"\"\"\n\n"
    "Return ONLY a JSON object."
)


class LLMService:
    """Service for LLM-based entity extraction and text analysis."""
    
    @staticmethod
    def _get_base_url() -> str:
        """Get the base URL for the LLM API."""
        api_url = settings.API_CHAT or "http://localhost:11434"
        try:
            parsed = urlparse(api_url)
            if parsed.scheme and parsed.netloc:
                return f"{parsed.scheme}://{parsed.netloc}"
            else:
                return api_url.split('/api')[0].split('/v1')[0].rstrip('/')
        except Exception:
            return "http://localhost:11434"

    @staticmethod
    async def extract_entities(note_text: str) -> Optional[dict]:
        """
        Extract structured entities from text using LLM.
        
        Args:
            note_text: The text to analyze
            
        Returns:
            Dictionary containing entity_type and structured data, or None if failed
        """
        if not note_text or not note_text.strip():
            return None

        if not settings.API_CHAT or not settings.MODEL_CHAT:
            print("⚠ Entity extraction not configured - missing API_CHAT or MODEL_CHAT")
            return None

        base_url = LLMService._get_base_url()
        model_name = settings.MODEL_CHAT
        
        prompt = ENTITY_EXTRACTION_PROMPT.format(note_text=note_text.strip())
        payload = {
            "model": model_name,
            "prompt": prompt,
            "stream": False,
        }

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                endpoint = f"{base_url}/api/generate"
                print(f"ℹ Entity extraction request to {endpoint} model={model_name}")
                
                resp = await client.post(
                    endpoint, 
                    json=payload, 
                    headers={"Content-Type": "application/json"}
                )
                
                if resp.status_code != 200:
                    print(f"❌ Chat API error {resp.status_code}: {resp.text}")
                    return None
                
                data = resp.json()
                raw = data.get("response", "").strip()
                
                if not raw:
                    return None
                
                # Try to parse JSON response
                try:
                    return json.loads(raw)
                except Exception:
                    # Attempt to extract JSON from response
                    start = raw.find('{')
                    end = raw.rfind('}')
                    if start != -1 and end != -1 and end > start:
                        try:
                            return json.loads(raw[start:end+1])
                        except Exception:
                            pass
                    print("⚠ Failed to parse JSON from model response")
                    return None
                    
        except httpx.TimeoutException:
            print("❌ Chat API timeout - ensure Ollama is running")
        except httpx.ConnectError:
            print(f"❌ Cannot connect to Chat API at {base_url}")
        except Exception as e:
            print(f"❌ Unexpected error during entity extraction: {e}")
        
        return None


# Singleton instance
llm_service = LLMService()
