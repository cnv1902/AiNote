"""
Dịch vụ LLM để trích xuất thực thể và xử lý văn bản thông minh.
"""
import json
from typing import Optional
from urllib.parse import urlparse
import httpx

from app.core.config import settings
from app.core.llm_providers import LLMProvider, APIClient, get_provider_and_config

ENTITY_EXTRACTION_PROMPT = (
    "Bạn là một trợ lý AI trích xuất thông tin có cấu trúc từ ghi chú hoặc tài liệu của người dùng.\n\n"
    "1. Xác định loại tài liệu theo lĩnh vực thực tế. Các loại có thể:\n"
    "   - 'work_tasks': Công việc, dự án, deadline, meeting, báo cáo\n"
    "   - 'personal_tasks': Việc cá nhân, gia đình, nhà cửa, sửa chữa\n"
    "   - 'study_schedule': Học tập, lịch học, bài tập, ôn thi, khóa học\n"
    "   - 'shopping_list': Mua sắm, đồ dùng, thực phẩm, vật tư\n"
    "   - 'health_care': Sức khỏe, thuốc, lịch khám, triệu chứng, thể dục\n"
    "   - 'finance_records': Tài chính, chi tiêu, thu nhập, hóa đơn, ngân sách\n"
    "   - 'social_events': Sự kiện xã hội, sinh nhật, đám cưới, gặp gỡ\n"
    "   - 'travel_plans': Du lịch, booking, lịch trình, địa điểm\n"
    "   - 'business_contacts': Liên hệ công việc, đối tác, khách hàng\n"
    "   - 'personal_contacts': Liên hệ cá nhân, bạn bè, gia đình\n"
    "   - 'ideas_notes': Ý tưởng, sáng tạo, kế hoạch, brainstorm\n"
    "   - 'reminders': Nhắc nhở quan trọng, deadline cấp bách\n"
    "   - 'receipts_bills': Biên lai, hóa đơn, thanh toán dịch vụ\n"
    "   - 'project_plans': Kế hoạch dự án, timeline, phân công\n"
    "   - 'daily_routine': Thói quen hàng ngày, lịch trình cố định\n\n"
    
    "2. Trích xuất các trường chính liên quan đến loại đó. Trả về dưới dạng JSON với các khóa:\n"
    "   - entity_type\n"
    "   - data (nội dung có cấu trúc theo entity_type)\n\n"
    "Văn bản:\n\"\"\"\n{note_text}\n\"\"\"\n\n"
    "Chỉ trả về một đối tượng JSON."
)

QA_ANSWER_PROMPT = (
    "Bạn là trợ lý AI thông minh giúp người dùng tìm thông tin từ ghi chú cá nhân của họ.\n\n"
    "**Nhiệm vụ của bạn:**\n"
    "- Đọc và hiểu câu hỏi của người dùng\n"
    "- Phân tích các ghi chú liên quan được cung cấp\n"
    "- Trả lời câu hỏi một cách chính xác, súc tích và hữu ích\n"
    "- Nếu thông tin không rõ ràng, hãy đưa ra câu trả lời tốt nhất dựa trên context\n"
    "- Trả lời bằng tiếng Việt một cách tự nhiên và thân thiện\n\n"
    "**Ghi chú liên quan:**\n"
    "{context}\n\n"
    "**Câu hỏi:** {question}\n\n"
    "**Câu trả lời:**"
)

class LLMService:
    """Dịch vụ trích xuất thực thể dựa trên LLM và phân tích văn bản."""
    
    @staticmethod
    async def _call_llm_api(
        prompt: str,
        provider_name: str,
        is_chat: bool = True,
        system_message: Optional[str] = None,
        image_base64: Optional[str] = None
    ) -> Optional[str]:
        """
        Gọi LLM API dựa trên provider được cấu hình.
        
        Args:
            prompt: Prompt để gửi
            provider_name: Tên provider (API_CHAT_NAME hoặc API_EXTRACT_NAME)
            is_chat: True nếu là chat API, False nếu là extract API
            system_message: System message (chỉ cho một số provider)
            image_base64: Hình ảnh base64 (cho vision models)
            
        Returns:
            Kết quả từ LLM, hoặc None nếu thất bại
        """
        provider, config = get_provider_and_config(provider_name, is_chat)
        
        if provider == LLMProvider.LOCAL:
            if not config.get("base_url") or not config.get("model"):
                print(f"⚠ Cấu hình LOCAL chưa đầy đủ - thiếu API hoặc MODEL")
                return None
            
            return await APIClient.call_ollama(
                base_url=config["base_url"],
                model=config["model"],
                prompt=prompt,
                image_base64=image_base64
            )
        
        elif provider == LLMProvider.GPT:
            if not config.get("api_key"):
                print("⚠ Thiếu OPENAI_API_KEY")
                return None
            
            return await APIClient.call_openai(
                api_key=config["api_key"],
                model=config.get("model", "gpt-4o-mini"),
                prompt=prompt,
                system_message=system_message,
                image_base64=image_base64
            )
        
        elif provider == LLMProvider.GEMINI:
            if not config.get("api_key"):
                print("⚠ Thiếu GEMINI_API_KEY")
                return None
            
            return await APIClient.call_gemini(
                api_key=config["api_key"],
                model=config.get("model", "gemini-1.5-flash"),
                prompt=prompt,
                image_base64=image_base64
            )
        
        elif provider == LLMProvider.GROCK:
            if not config.get("api_key"):
                print("⚠ Thiếu GROCK_API_KEY")
                return None
            
            # Grok không hỗ trợ vision hiện tại
            if image_base64:
                print("⚠ Grok chưa hỗ trợ xử lý hình ảnh")
                return None
            
            return await APIClient.call_grock(
                api_key=config["api_key"],
                model=config.get("model", "grok-beta"),
                prompt=prompt,
                system_message=system_message
            )
        
        elif provider == LLMProvider.DEEPSEEK:
            if not config.get("api_key"):
                print("⚠ Thiếu DEEPSEEK_API_KEY")
                return None
            
            # DeepSeek không hỗ trợ vision hiện tại
            if image_base64:
                print("⚠ DeepSeek chưa hỗ trợ xử lý hình ảnh")
                return None
            
            return await APIClient.call_deepseek(
                api_key=config["api_key"],
                model=config.get("model", "deepseek-chat"),
                prompt=prompt,
                system_message=system_message
            )
        
        elif provider == LLMProvider.CLAUDE:
            if not config.get("api_key"):
                print("⚠ Thiếu ANTHROPIC_API_KEY")
                return None
            
            return await APIClient.call_claude(
                api_key=config["api_key"],
                model=config.get("model", "claude-3-5-sonnet-20241022"),
                prompt=prompt,
                system_message=system_message,
                image_base64=image_base64
            )
        
        return None
    
    @staticmethod
    def _get_base_url() -> str:
        """Lấy URL cơ sở cho API LLM (deprecated - giữ lại để tương thích)."""
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
        Trích xuất thực thể có cấu trúc từ văn bản bằng LLM.
        Args:
            note_text: Văn bản cần phân tích
        Returns:
            Dictionary chứa entity_type và dữ liệu có cấu trúc, hoặc None nếu thất bại
        """
        if not note_text or not note_text.strip():
            return None

        prompt = ENTITY_EXTRACTION_PROMPT.format(note_text=note_text.strip())
        
        try:
            print(f"ℹ Yêu cầu trích xuất thực thể với provider={settings.API_CHAT_NAME or 'LOCAL'}")
            
            raw = await LLMService._call_llm_api(
                prompt=prompt,
                provider_name=settings.API_CHAT_NAME,
                is_chat=True
            )
            
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
                print("⚠ Không thể phân tích JSON từ phản hồi của model")
                return None
                    
        except Exception as e:
            print(f"❌ Lỗi không mong muốn khi trích xuất thực thể: {e}")
            return None

    @staticmethod
    async def answer_question(question: str, context: str) -> Optional[str]:
        """
        Trả lời câu hỏi dựa trên context từ ghi chú người dùng.
        
        Args:
            question: Câu hỏi của người dùng
            context: Context từ các ghi chú liên quan
            
        Returns:
            Câu trả lời từ LLM, hoặc None nếu thất bại
        """
        if not question or not context:
            return None

        prompt = QA_ANSWER_PROMPT.format(context=context, question=question)
        
        try:
            print(f"ℹ Yêu cầu trả lời câu hỏi với provider={settings.API_CHAT_NAME or 'LOCAL'}")
            
            answer = await LLMService._call_llm_api(
                prompt=prompt,
                provider_name=settings.API_CHAT_NAME,
                is_chat=True
            )
            
            if answer:
                print(f"✓ Đã nhận câu trả lời ({len(answer)} ký tự)")
                return answer
            
            return None
                    
        except Exception as e:
            print(f"❌ Lỗi không mong muốn khi trả lời câu hỏi: {e}")
            return None


# Instance singleton
llm_service = LLMService()
