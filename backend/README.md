# AiNote Backend - FastAPI Application

## 📁 Cấu trúc dự án

Dự án được tổ chức theo chuẩn FastAPI best practices với kiến trúc modular, phân tách rõ ràng các layer:

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                    # Application entry point
│   ├── models.py                  # SQLAlchemy ORM models
│   ├── schemas.py                 # Pydantic schemas
│   │
│   ├── api/                       # API layer
│   │   ├── __init__.py
│   │   ├── dependencies.py        # Shared dependencies (auth, etc.)
│   │   └── v1/                    # API version 1
│   │       ├── __init__.py
│   │       ├── auth.py            # Authentication endpoints
│   │       └── notes.py           # Notes endpoints
│   │
│   ├── core/                      # Core configurations
│   │   ├── __init__.py
│   │   ├── config.py              # Application settings
│   │   ├── database.py            # Database connection
│   │   ├── security.py            # Security utilities (JWT, hashing)
│   │   ├── fts.py                 # Full-text search setup
│   │   └── utils.py               # Core utilities
│   │
│   ├── crud/                      # Database operations layer
│   │   ├── __init__.py
│   │   ├── user.py                # User CRUD operations
│   │   ├── note.py                # Note CRUD operations
│   │   ├── file.py                # File CRUD operations
│   │   └── auth.py                # Auth token CRUD operations
│   │
│   └── services/                  # Business logic layer
│       ├── __init__.py
│       ├── storage.py             # S3/Storage service
│       ├── image.py               # Image processing service
│       ├── ocr.py                 # OCR service
│       └── llm.py                 # LLM/AI service
│
└── requirements.txt
```

## 🏗️ Kiến trúc phân layer

### 1. **Core Layer** (`app/core/`)
Chứa các cấu hình cốt lõi và utilities:
- `config.py`: Quản lý settings từ environment variables
- `database.py`: Database connection và session management
- `security.py`: JWT authentication, password hashing
- `fts.py`: Full-text search configuration
- `utils.py`: Utility functions

### 2. **Models Layer** (`app/models.py`)
SQLAlchemy ORM models định nghĩa database schema:
- User, AuthRefreshToken
- Note, File, ImageMetadata
- OcrText, ExtractedEntity
- QARequest, AuditLog

### 3. **Schemas Layer** (`app/schemas.py`)
Pydantic models cho validation:
- Request/Response schemas
- Data transfer objects (DTOs)

### 4. **CRUD Layer** (`app/crud/`)
Database operations được tách biệt khỏi business logic:
- `user.py`: User database operations
- `note.py`: Note database operations
- `file.py`: File-related database operations
- `auth.py`: Authentication token operations

### 5. **Services Layer** (`app/services/`)
Business logic và external service integrations:
- `storage.py`: S3-compatible storage (Supabase)
- `image.py`: Image processing, EXIF extraction
- `ocr.py`: Text extraction from images
- `llm.py`: Entity extraction using LLM

### 6. **API Layer** (`app/api/`)
API endpoints với versioning:
- `dependencies.py`: Shared dependencies (authentication)
- `v1/auth.py`: Authentication endpoints
- `v1/notes.py`: Notes management endpoints

## 🔑 Nguyên tắc thiết kế

1. **Separation of Concerns**: Mỗi layer có trách nhiệm rõ ràng
2. **Dependency Injection**: Sử dụng FastAPI's dependency injection
3. **Type Safety**: Sử dụng type hints và Pydantic validation
4. **Modularity**: Code được tổ chức thành modules độc lập
5. **Testability**: Dễ dàng test từng layer riêng biệt

## 🚀 Chạy ứng dụng

### Windows (PowerShell)
```powershell
# Tạo và kích hoạt venv (khuyên dùng)
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Cài đặt dependencies
pip install -r requirements.txt

# Tạo file .env (xem mẫu bên dưới)
Copy-Item -Path .env.example -Destination .env -ErrorAction SilentlyContinue

# Chạy development server (mặc định 8000)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### macOS/Linux (tuỳ chọn tham khảo)
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 📝 Environment Variables

Tạo file `.env` với các biến sau (các biến bắt buộc được đánh dấu Required). Nếu một tính năng không dùng (ví dụ upload ảnh), có thể để trống nhóm biến liên quan nhưng những API gọi đến tính năng đó sẽ không hoạt động.

```env
# Application
APP_ENV=dev
API_PREFIX=/api
HOST=127.0.0.1
PORT=8000

# Database
DATABASE_URL=

# JWT
JWT_SECRET=your-secret-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRES_MINUTES=30
REFRESH_TOKEN_EXPIRES_DAYS=14

# Full-text Search
FTS_CONFIG=simple

# S3 Storage
S3_ACCESS_KEY_ID=your-access-key
S3_SECRET_ACCESS_KEY=your-secret-key
S3_ENDPOINT_URL=https://your-endpoint/storage/v1/s3
S3_BUCKET_NAME=AiNote
S3_REGION=ap-south-1

# Optional: Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key

# LLM Providers (chọn 1 trong các provider bên dưới)
# - Nếu dùng Local (Ollama): để API_*_NAME trống, đặt API_* là base URL và MODEL_* là model name
# - Nếu dùng cloud (GPT/GEMINI/GROCK/DEEPSEEK/CLAUDE): đặt *_NAME theo provider và cung cấp API key tương ứng

# Cấu hình chung
API_EXTRACT_NAME=
API_EXTRACT_TEXT=http://localhost:11434
MODEL_EXTRACT_TEXT=llava:7b
API_CHAT_NAME=
API_CHAT=http://localhost:11434
MODEL_CHAT=llama3.1:8b

# API Keys (tuỳ provider)
OPENAI_API_KEY=
GEMINI_API_KEY=
GROCK_API_KEY=
DEEPSEEK_API_KEY=
ANTHROPIC_API_KEY=
```

Gợi ý nhanh:
- Local OCR + Chat qua Ollama: để trống `API_EXTRACT_NAME` và `API_CHAT_NAME`, đặt `API_EXTRACT_TEXT=http://localhost:11434`, `MODEL_EXTRACT_TEXT=llava:7b`, `API_CHAT=http://localhost:11434`, `MODEL_CHAT=llama3.1:8b`.
- Dùng OpenAI: đặt `API_CHAT_NAME=GPT`, `OPENAI_API_KEY=...`, `MODEL_CHAT=gpt-4o-mini` (hoặc model tương thích). OCR có thể dùng `API_EXTRACT_NAME=GPT` với model multimodal.

## 🔄 Migration từ cấu trúc cũ

### Files đã được tổ chức lại:

| Cũ | Mới |
|-----|-----|
| `app/config.py` | `app/core/config.py` |
| `app/db.py` | `app/core/database.py` |
| `app/security.py` | `app/core/security.py` |
| `app/fts.py` | `app/core/fts.py` |
| `app/utils.py` | `app/core/utils.py` |
| `app/deps.py` | `app/api/dependencies.py` |
| `app/routers/auth.py` | `app/api/v1/auth.py` |
| `app/routers/notes.py` | `app/api/v1/notes.py` |
| `app/s3_client.py` | `app/services/storage.py` |
| `app/storage_client.py` | `app/services/storage.py` |
| `app/image_utils.py` | `app/services/image.py` |
| `app/ocr_utils.py` | `app/services/ocr.py` |
| `app/llm_utils.py` | `app/services/llm.py` |

### Imports cần cập nhật:

```python
# Cũ:
from app.config import settings
from app.db import get_db
from app.security import hash_password

# Mới:
from app.core.config import settings
from app.core.database import get_db
from app.core.security import hash_password
```

## 📚 API Documentation

Sau khi chạy server, truy cập:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🗄️ Database & FTS (PostgreSQL)

- Ứng dụng tự tạo bảng và trigger FTS (Full-Text Search) khi khởi động lần đầu, không cần Alembic cho chạy thử.
- Yêu cầu PostgreSQL với extension `plpgsql` (mặc định đã bật). Biến `FTS_CONFIG` có thể đặt `simple`, `english`, `vietnamese` (tuỳ DB đã cài dict).

## 🧪 Kiểm tra nhanh

```powershell
# Health check
Invoke-WebRequest http://localhost:8000/health | Select-Object -ExpandProperty Content

# Mở docs
Start-Process http://localhost:8000/docs
```

## ✅ Lợi ích của cấu trúc mới

1. **Dễ maintain**: Code được tổ chức logic, dễ tìm và sửa
2. **Scalable**: Dễ dàng thêm features mới mà không làm rối code
3. **Testable**: Mỗi layer có thể test độc lập
4. **Team-friendly**: Nhiều người có thể làm việc cùng lúc ít conflict
5. **Professional**: Follow best practices của FastAPI và Python
