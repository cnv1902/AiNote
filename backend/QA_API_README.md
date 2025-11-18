# Smart Q&A API Documentation

## Tổng quan

API trả lời câu hỏi (Q&A) sử dụng Smart Retrieval với nhiều chiến lược tìm kiếm để tìm ghi chú liên quan và trả lời câu hỏi của người dùng bằng LLM.

## Endpoint

### POST `/api/notes/ask`

Trả lời câu hỏi dựa trên ghi chú của người dùng.

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "question": "Hôm nay tôi có cuộc họp nào không?"
}
```

**Response:**
```json
{
  "question": "Hôm nay tôi có cuộc họp nào không?",
  "answer": "Có, bạn có cuộc họp dự án lúc 14:00 với team Marketing...",
  "relevant_notes": [
    {
      "id": "uuid",
      "user_id": "uuid",
      "title": "Lịch làm việc tuần này",
      "content": "14:00 - Họp dự án với team Marketing",
      "is_archived": false,
      "created_at": "2025-11-18T10:00:00Z",
      "updated_at": "2025-11-18T10:00:00Z",
      "files": []
    }
  ],
  "query_type": "keyword",
  "confidence": 85.5
}
```

**Note:** Endpoint này tự động lưu lịch sử chat vào database.

### GET `/api/notes/chat-history`

Lấy lịch sử chat Q&A của người dùng.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `limit` (optional, default: 50): Số lượng bản ghi tối đa
- `offset` (optional, default: 0): Vị trí bắt đầu

**Response:**
```json
[
  {
    "id": "uuid",
    "user_id": "uuid",
    "question": "Hôm nay tôi có cuộc họp nào không?",
    "context": {
      "query_type": "keyword",
      "relevant_note_ids": ["uuid1", "uuid2"],
      "scores": [0.85, 0.72]
    },
    "response": {
      "answer": "Có, bạn có cuộc họp dự án lúc 14:00...",
      "confidence": 85.5,
      "note_count": 2
    },
    "created_at": "2025-11-18T10:00:00Z"
  }
]
```

### GET `/api/notes/chat-history/{qa_id}`

Lấy chi tiết một bản ghi chat cụ thể.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:** Giống như một item trong array của endpoint trên.

### DELETE `/api/notes/chat-history/{qa_id}`

Xóa một bản ghi lịch sử chat.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:** 204 No Content

## Kiến trúc Smart Retrieval

### 1. Query Analysis
API phân tích câu hỏi để xác định chiến lược tìm kiếm phù hợp:

- **keyword**: Câu hỏi ngắn với từ khóa cụ thể (họp, deadline, mua, gọi...)
- **semantic**: Câu hỏi dài, trừu tượng (chuẩn bị gì, nên làm gì...)
- **structured**: Có thực thể rõ ràng (ngày, tháng, địa điểm, người...)
- **hybrid**: Kết hợp nhiều loại

### 2. Multi-Strategy Retrieval

API chạy song song 3 phương pháp tìm kiếm:

#### a) Full-Text Search (FTS)
- Sử dụng PostgreSQL `tsvector` và `tsquery`
- Tìm kiếm nhanh dựa trên từ khóa
- Tính điểm với `ts_rank`

#### b) Vector/Semantic Search
- Tìm kiếm dựa trên ý nghĩa và ngữ cảnh
- So khớp từ trong câu hỏi với nội dung ghi chú
- Tính điểm similarity

#### c) Entity-based Search
- Tìm kiếm dựa trên extracted entities
- Khớp entity type và entity data
- Phù hợp cho câu hỏi có cấu trúc

### 3. Weighted Fusion

Kết quả từ 3 phương pháp được kết hợp với trọng số khác nhau tùy theo query type:

| Query Type | FTS Weight | Vector Weight | Entity Weight |
|------------|------------|---------------|---------------|
| keyword    | 0.6        | 0.3           | 0.1           |
| semantic   | 0.2        | 0.6           | 0.2           |
| structured | 0.3        | 0.2           | 0.5           |
| hybrid     | 0.4        | 0.4           | 0.2           |

### 4. Reranking

Kết quả cuối cùng được rerank dựa trên:
- Điểm từ weighted fusion
- Title matching (boost 1.2x)
- Freshness (ghi chú mới trong 7 ngày, boost 1.1x)

### 5. LLM Answer Generation

Context từ top 3 ghi chú được gửi đến LLM để tạo câu trả lời tự nhiên.

## Cấu hình

Trong file `.env`:

```env
API_CHAT=http://localhost:11434
MODEL_CHAT=llama3.1:8b
```

## Ví dụ sử dụng

### Python
```python
import requests

url = "http://localhost:8000/api/notes/ask"
headers = {
    "Authorization": "Bearer your_access_token",
    "Content-Type": "application/json"
}
data = {
    "question": "Tôi cần mua gì ở siêu thị?"
}

response = requests.post(url, json=data, headers=headers)
result = response.json()

print(f"Câu trả lời: {result['answer']}")
print(f"Loại câu hỏi: {result['query_type']}")
print(f"Độ tin cậy: {result['confidence']}%")
```

### cURL
```bash
curl -X POST http://localhost:8000/api/notes/ask \
  -H "Authorization: Bearer your_access_token" \
  -H "Content-Type: application/json" \
  -d '{"question": "Deadline dự án ABC là khi nào?"}'
```

### JavaScript/TypeScript
```typescript
// Đặt câu hỏi
const response = await fetch('http://localhost:8000/api/notes/ask', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${accessToken}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    question: 'Hôm nay tôi có việc gì cần làm?'
  })
});

const result = await response.json();
console.log(result.answer);

// Lấy lịch sử chat
const historyResponse = await fetch('http://localhost:8000/api/notes/chat-history', {
  headers: {
    'Authorization': `Bearer ${accessToken}`
  }
});

const history = await historyResponse.json();
console.log(`Có ${history.length} câu hỏi trong lịch sử`);

// Xóa một bản ghi lịch sử
await fetch(`http://localhost:8000/api/notes/chat-history/${qaId}`, {
  method: 'DELETE',
  headers: {
    'Authorization': `Bearer ${accessToken}`
  }
});
```

## Error Handling

### 400 Bad Request
```json
{
  "detail": "Câu hỏi không được để trống"
}
```

### 401 Unauthorized
```json
{
  "detail": "Không thể xác thực thông tin đăng nhập"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Không thể trả lời câu hỏi: <error message>"
}
```

## Performance Tips

1. **Câu hỏi rõ ràng**: Đặt câu hỏi cụ thể, rõ ràng để có kết quả tốt hơn
2. **Từ khóa quan trọng**: Dùng từ khóa có trong ghi chú của bạn
3. **Context**: Model hiểu tốt hơn khi có context đầy đủ trong ghi chú
4. **Ollama running**: Đảm bảo Ollama đang chạy và model đã được pull

## Testing

```bash
# Đảm bảo Ollama đang chạy
ollama serve

# Pull model nếu chưa có
ollama pull llama3.1:8b

# Chạy backend
cd backend
uvicorn app.main:app --reload

# Test endpoint
curl -X POST http://localhost:8000/api/notes/ask \
  -H "Authorization: Bearer your_token" \
  -H "Content-Type: application/json" \
  -d '{"question": "test question"}'
```
