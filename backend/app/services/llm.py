"""
Dịch vụ LLM để trích xuất thực thể và xử lý văn bản thông minh.
"""
import json
from typing import Optional
from urllib.parse import urlparse
import httpx

from app.core.config import settings

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
    def _get_base_url() -> str:
        """Lấy URL cơ sở cho API LLM."""
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

        if not settings.API_CHAT or not settings.MODEL_CHAT:
            print("⚠ Trích xuất thực thể chưa được cấu hình - thiếu API_CHAT hoặc MODEL_CHAT")
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
                print(f"ℹ Yêu cầu trích xuất thực thể đến {endpoint} model={model_name}")
                
                resp = await client.post(
                    endpoint, 
                    json=payload, 
                    headers={"Content-Type": "application/json"}
                )
                
                if resp.status_code != 200:
                    print(f"❌ Lỗi Chat API {resp.status_code}: {resp.text}")
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
                    print("⚠ Không thể phân tích JSON từ phản hồi của model")
                    return None
                    
        except httpx.TimeoutException:
            print("❌ Chat API hết thời gian chờ - đảm bảo Ollama đang chạy")
        except httpx.ConnectError:
            print(f"❌ Không thể kết nối đến Chat API tại {base_url}")
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

        if not settings.API_CHAT or not settings.MODEL_CHAT:
            print("⚠ Q&A chưa được cấu hình - thiếu API_CHAT hoặc MODEL_CHAT")
            return None

        base_url = LLMService._get_base_url()
        model_name = settings.MODEL_CHAT
        
        prompt = QA_ANSWER_PROMPT.format(context=context, question=question)
        payload = {
            "model": model_name,
            "prompt": prompt,
            "stream": False,
        }

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                endpoint = f"{base_url}/api/generate"
                print(f"ℹ Yêu cầu trả lời câu hỏi đến {endpoint} model={model_name}")

                resp = await client.post(
                    endpoint, 
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                
                if resp.status_code != 200:
                    print(f"❌ Lỗi Chat API {resp.status_code}: {resp.text}")
                    return None
                
                data = resp.json()
                answer = data.get("response", "").strip()
                
                if answer:
                    print(f"✓ Đã nhận câu trả lời ({len(answer)} ký tự)")
                    return answer
                
                return None
                    
        except httpx.TimeoutException:
            print("❌ Chat API hết thời gian chờ - đảm bảo Ollama đang chạy")
        except httpx.ConnectError:
            print(f"❌ Không thể kết nối đến Chat API tại {base_url}")
        except Exception as e:
            print(f"❌ Lỗi không mong muốn khi trả lời câu hỏi: {e}")
        
        return None


# Instance singleton
llm_service = LLMService()
