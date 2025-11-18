import json
from typing import Optional, Tuple
from urllib.parse import urlparse

import httpx

from .config import settings

PROMPT_TEMPLATE = (
    "You are an AI assistant that extracts structured information from user notes or documents.\n\n"
    "1. Determine the type of document. Possible types: receipt, invoice, id_card, meeting_note, general_note.\n"
    "2. Extract the main fields relevant to that type. Return as JSON with keys:\n"
    "   - entity_type\n   - data (structured content according to entity_type)\n\n"
    "Text:\n\"\"\"\n{note_text}\n\"\"\"\n\nReturn ONLY a JSON object."
)


async def extract_entities(note_text: str) -> Optional[dict]:
    if not note_text or not note_text.strip():
        return None

    api_url = settings.API_CHAT or "http://localhost:11434"
    model_name = settings.MODEL_CHAT or "llama3.1:8b"
    try:
        parsed = urlparse(api_url)
        if parsed.scheme and parsed.netloc:
            base_url = f"{parsed.scheme}://{parsed.netloc}"
        else:
            base_url = api_url.split('/api')[0].split('/v1')[0].rstrip('/')
    except Exception:
        base_url = "http://localhost:11434"

    prompt = PROMPT_TEMPLATE.format(note_text=note_text.strip())
    payload = {
        "model": model_name,
        "prompt": prompt,
        "stream": False,
    }

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            endpoint = f"{base_url}/api/generate"
            print(f"ℹ Entity extraction request to {endpoint} model={model_name}")
            resp = await client.post(endpoint, json=payload, headers={"Content-Type": "application/json"})
            if resp.status_code != 200:
                print(f"❌ Chat API error {resp.status_code}: {resp.text}")
                return None
            data = resp.json()
            raw = data.get("response", "").strip()
            if not raw:
                return None
            try:
                return json.loads(raw)
            except Exception:
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
        print(f"❌ Cannot connect to Chat API at {api_url}")
    except Exception as e:
        print(f"❌ Unexpected error during entity extraction: {e}")
    return None
