"""
Module định nghĩa các provider LLM và logic gọi API.
"""
from enum import Enum
from typing import Optional, Dict, Any
import httpx
from app.core.config import settings


class LLMProvider(str, Enum):
    """Enum định nghĩa các provider LLM được hỗ trợ."""
    LOCAL = ""  # Để trống = sử dụng Ollama local
    GPT = "GPT"
    GEMINI = "GEMINI"
    GROCK = "GROCK"
    DEEPSEEK = "DEEPSEEK"
    CLAUDE = "CLAUDE"


class APIClient:
    """Client tổng quát để gọi các API LLM khác nhau."""
    
    @staticmethod
    async def call_openai(
        api_key: str,
        model: str,
        prompt: str,
        system_message: Optional[str] = None,
        image_base64: Optional[str] = None,
        timeout: float = 120.0
    ) -> Optional[str]:
        """Gọi OpenAI API (GPT)."""
        try:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            messages = []
            if system_message:
                messages.append({"role": "system", "content": system_message})
            
            if image_base64:
                messages.append({
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
                    ]
                })
            else:
                messages.append({"role": "user", "content": prompt})
            
            payload = {
                "model": model or "gpt-4o-mini",
                "messages": messages,
                "temperature": 0.7
            }
            
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers=headers,
                    json=payload
                )
                
                if resp.status_code != 200:
                    print(f"❌ Lỗi OpenAI API {resp.status_code}: {resp.text}")
                    return None
                
                data = resp.json()
                return data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                
        except Exception as e:
            print(f"❌ Lỗi khi gọi OpenAI API: {e}")
            return None
    
    @staticmethod
    async def call_gemini(
        api_key: str,
        model: str,
        prompt: str,
        image_base64: Optional[str] = None,
        timeout: float = 120.0
    ) -> Optional[str]:
        """Gọi Google Gemini API."""
        try:
            model_name = model or "gemini-1.5-flash"
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
            
            contents = []
            if image_base64:
                contents.append({
                    "parts": [
                        {"text": prompt},
                        {"inline_data": {"mime_type": "image/jpeg", "data": image_base64}}
                    ]
                })
            else:
                contents.append({"parts": [{"text": prompt}]})
            
            payload = {"contents": contents}
            
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.post(url, json=payload)
                
                if resp.status_code != 200:
                    print(f"❌ Lỗi Gemini API {resp.status_code}: {resp.text}")
                    return None
                
                data = resp.json()
                candidates = data.get("candidates", [])
                if candidates:
                    return candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "").strip()
                return None
                
        except Exception as e:
            print(f"❌ Lỗi khi gọi Gemini API: {e}")
            return None
    
    @staticmethod
    async def call_grock(
        api_key: str,
        model: str,
        prompt: str,
        system_message: Optional[str] = None,
        timeout: float = 120.0
    ) -> Optional[str]:
        """Gọi Grok API (xAI)."""
        try:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            messages = []
            if system_message:
                messages.append({"role": "system", "content": system_message})
            messages.append({"role": "user", "content": prompt})
            
            payload = {
                "model": model or "grok-beta",
                "messages": messages,
                "temperature": 0.7
            }
            
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.post(
                    "https://api.x.ai/v1/chat/completions",
                    headers=headers,
                    json=payload
                )
                
                if resp.status_code != 200:
                    print(f"❌ Lỗi Grok API {resp.status_code}: {resp.text}")
                    return None
                
                data = resp.json()
                return data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                
        except Exception as e:
            print(f"❌ Lỗi khi gọi Grok API: {e}")
            return None
    
    @staticmethod
    async def call_deepseek(
        api_key: str,
        model: str,
        prompt: str,
        system_message: Optional[str] = None,
        timeout: float = 120.0
    ) -> Optional[str]:
        """Gọi DeepSeek API."""
        try:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            messages = []
            if system_message:
                messages.append({"role": "system", "content": system_message})
            messages.append({"role": "user", "content": prompt})
            
            payload = {
                "model": model or "deepseek-chat",
                "messages": messages,
                "temperature": 0.7
            }
            
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.post(
                    "https://api.deepseek.com/v1/chat/completions",
                    headers=headers,
                    json=payload
                )
                
                if resp.status_code != 200:
                    print(f"❌ Lỗi DeepSeek API {resp.status_code}: {resp.text}")
                    return None
                
                data = resp.json()
                return data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                
        except Exception as e:
            print(f"❌ Lỗi khi gọi DeepSeek API: {e}")
            return None
    
    @staticmethod
    async def call_claude(
        api_key: str,
        model: str,
        prompt: str,
        system_message: Optional[str] = None,
        image_base64: Optional[str] = None,
        timeout: float = 120.0
    ) -> Optional[str]:
        """Gọi Anthropic Claude API."""
        try:
            headers = {
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json"
            }
            
            content = []
            if image_base64:
                content.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/jpeg",
                        "data": image_base64
                    }
                })
            content.append({"type": "text", "text": prompt})
            
            payload = {
                "model": model or "claude-3-5-sonnet-20241022",
                "max_tokens": 4096,
                "messages": [{"role": "user", "content": content}]
            }
            
            if system_message:
                payload["system"] = system_message
            
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers=headers,
                    json=payload
                )
                
                if resp.status_code != 200:
                    print(f"❌ Lỗi Claude API {resp.status_code}: {resp.text}")
                    return None
                
                data = resp.json()
                content_blocks = data.get("content", [])
                if content_blocks:
                    return content_blocks[0].get("text", "").strip()
                return None
                
        except Exception as e:
            print(f"❌ Lỗi khi gọi Claude API: {e}")
            return None
    
    @staticmethod
    async def call_ollama(
        base_url: str,
        model: str,
        prompt: str,
        image_base64: Optional[str] = None,
        timeout: float = 120.0
    ) -> Optional[str]:
        """Gọi Ollama local API."""
        try:
            endpoint = f"{base_url}/api/generate"
            
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": False
            }
            
            if image_base64:
                payload["images"] = [image_base64]
            
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.post(
                    endpoint,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                
                if resp.status_code != 200:
                    print(f"❌ Lỗi Ollama API {resp.status_code}: {resp.text}")
                    return None
                
                data = resp.json()
                return data.get("response", "").strip()
                
        except Exception as e:
            print(f"❌ Lỗi khi gọi Ollama API: {e}")
            return None


def get_provider_and_config(provider_name: str, is_chat: bool = True) -> tuple[LLMProvider, Dict[str, Any]]:
    """
    Lấy provider và cấu hình dựa trên tên provider.
    
    Args:
        provider_name: Tên provider (GPT, GEMINI, GROCK, DEEPSEEK, CLAUDE hoặc trống)
        is_chat: True nếu là chat API, False nếu là extract API
        
    Returns:
        Tuple (provider_enum, config_dict)
    """
    provider_name = (provider_name or "").strip().upper()
    
    # Xác định provider
    if not provider_name:
        provider = LLMProvider.LOCAL
    elif provider_name == "GPT":
        provider = LLMProvider.GPT
    elif provider_name == "GEMINI":
        provider = LLMProvider.GEMINI
    elif provider_name == "GROCK":
        provider = LLMProvider.GROCK
    elif provider_name == "DEEPSEEK":
        provider = LLMProvider.DEEPSEEK
    elif provider_name == "CLAUDE":
        provider = LLMProvider.CLAUDE
    else:
        print(f"⚠ Provider không hợp lệ: {provider_name}, sử dụng LOCAL")
        provider = LLMProvider.LOCAL
    
    # Lấy cấu hình
    config = {}
    
    if provider == LLMProvider.LOCAL:
        config["base_url"] = settings.API_CHAT if is_chat else settings.API_EXTRACT_TEXT
        config["model"] = settings.MODEL_CHAT if is_chat else settings.MODEL_EXTRACT_TEXT
        if not config["base_url"]:
            config["base_url"] = "http://localhost:11434"
    elif provider == LLMProvider.GPT:
        config["api_key"] = settings.OPENAI_API_KEY
        config["model"] = settings.MODEL_CHAT if is_chat else settings.MODEL_EXTRACT_TEXT
    elif provider == LLMProvider.GEMINI:
        config["api_key"] = settings.GEMINI_API_KEY
        config["model"] = settings.MODEL_CHAT if is_chat else settings.MODEL_EXTRACT_TEXT
    elif provider == LLMProvider.GROCK:
        config["api_key"] = settings.GROCK_API_KEY
        config["model"] = settings.MODEL_CHAT if is_chat else settings.MODEL_EXTRACT_TEXT
    elif provider == LLMProvider.DEEPSEEK:
        config["api_key"] = settings.DEEPSEEK_API_KEY
        config["model"] = settings.MODEL_CHAT if is_chat else settings.MODEL_EXTRACT_TEXT
    elif provider == LLMProvider.CLAUDE:
        config["api_key"] = settings.ANTHROPIC_API_KEY
        config["model"] = settings.MODEL_CHAT if is_chat else settings.MODEL_EXTRACT_TEXT
    
    return provider, config
