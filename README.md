# AiNote

Ứng dụng ghi chú thông minh hỗ trợ AI: tạo/lưu ghi chú văn bản và hình ảnh, OCR trích xuất chữ từ ảnh, phân tích thực thể từ ghi chú bằng LLM, và hỏi-đáp (Q&A) dựa trên ghi chú cá nhân.

## 🌟 Tính năng chính

- Ghi chú văn bản và hình ảnh, kèm lưu trữ file S3/Supabase.
- OCR (vision) trích xuất văn bản từ hình ảnh.
- Phân tích thực thể tự động từ ghi chú bằng LLM (local hoặc cloud).
- Hỏi-đáp (Q&A) dựa trên ghi chú với smart retrieval + LLM.
- Tìm kiếm toàn văn (PostgreSQL FTS) cho tiêu đề/nội dung/OCR.

## 🏗️ Kiến trúc

- Backend: FastAPI + SQLAlchemy + PostgreSQL FTS.
- Frontend: React + Vite + TypeScript.
- Lưu trữ ảnh: S3-compatible (Supabase Storage).
- LLM: Local (Ollama) hoặc Cloud (OpenAI/Gemini/Claude/...)

Cấu trúc repo:
```
AiNote/
├── backend/      # FastAPI service (API, DB, OCR, LLM)
└── frontend/     # React app (UI)
```

## ✅ Yêu cầu hệ thống

- Python 3.10+
- Node.js 18+
- PostgreSQL 14+ (có `plpgsql`, FTS mặc định hoạt động với `simple` config)
- Tuỳ chọn: Ollama (local LLM) nếu muốn chạy hoàn toàn local cho OCR/Chat
- Tuỳ chọn: Supabase/S3 endpoint nếu cần upload ảnh thật sự

## ⚙️ Chuẩn bị Database

Tạo một database PostgreSQL, ví dụ `ainote`.

```powershell
# Ví dụ tạo DB (tuỳ môi trường của bạn)
# psql -U postgres -c "CREATE DATABASE ainote;"
```

Lưu DSN vào biến `DATABASE_URL` trong `backend/.env` theo dạng:
```
postgresql://<user>:<password>@<host>:<port>/<database>
```

## 🔐 Tạo file cấu hình Backend (.env)

Tạo file `backend/.env` và điền các biến môi trường (xem chi tiết trong `backend/README.md`). Ví dụ cấu hình local sử dụng Ollama:

```
APP_ENV=dev
API_PREFIX=/api
HOST=127.0.0.1
PORT=8000

DATABASE_URL=postgresql://postgres:postgres@localhost:5432/ainote

JWT_SECRET=change-me
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRES_MINUTES=30
REFRESH_TOKEN_EXPIRES_DAYS=14

FTS_CONFIG=simple

# Nếu không dùng upload ảnh, có thể để trống nhưng các API upload sẽ lỗi
S3_ACCESS_KEY_ID=
S3_SECRET_ACCESS_KEY=
S3_ENDPOINT_URL=
S3_BUCKET_NAME=AiNote
S3_REGION=ap-south-1

# OCR/Chat dùng Ollama local
API_EXTRACT_NAME=
API_EXTRACT_TEXT=http://localhost:11434
MODEL_EXTRACT_TEXT=llava:7b
API_CHAT_NAME=
API_CHAT=http://localhost:11434
MODEL_CHAT=llama3.1:8b
```

Dùng OpenAI (ví dụ) cho Chat:
```
API_CHAT_NAME=GPT
OPENAI_API_KEY=sk-...
MODEL_CHAT=gpt-4o-mini
```

## ▶️ Chạy dự án (Windows PowerShell)

1) Backend
```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
# chạy API
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- API Docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

2) Frontend (mở cửa sổ khác)
```powershell
cd frontend
npm install
npm run dev
# mở UI
Start-Process http://localhost:5173
```

Frontend mặc định gọi API tại `http://localhost:8000/api`. Nếu bạn đổi cổng/host backend, cập nhật `src/services/api.ts` tương ứng.

## 🧪 Kiểm tra nhanh luồng sử dụng

- Đăng ký tài khoản và đăng nhập từ UI.
- Tạo ghi chú văn bản.
- Tải ảnh có chữ để thử OCR (cần cấu hình S3/Supabase).
- Hỏi-đáp (Ask) để kiểm tra truy xuất và trả lời từ LLM.

## 🛠️ Khắc phục sự cố thường gặp

- 401 Unauthorized: kiểm tra token trong localStorage, đăng nhập lại; đảm bảo `JWT_SECRET` chính xác ở backend.
- Kết nối DB: kiểm tra `DATABASE_URL` đúng, DB đã khởi động; backend tự tạo bảng/trigger FTS lần đầu.
- Upload ảnh lỗi: cần cấu hình nhóm biến S3 (`S3_*`) + endpoint hợp lệ (Supabase Storage hoặc S3 tương thích).
- LLM không trả lời/OCR rỗng: kiểm tra cấu hình provider và model (`API_*_NAME`, `MODEL_*`, API keys nếu dùng cloud) hoặc Ollama đang chạy.
- CORS/Network Error: backend CORS đã mở rộng; đảm bảo `API_BASE_URL` ở frontend đúng host/port.

## 📚 Tài liệu chi tiết

- Backend: xem `backend/README.md`
- Frontend: xem `frontend/README.md`
