# Setup Script cho AI Note Backend (RAG Architecture)

## Bước 1: Cài đặt Python dependencies

```bash
cd backend
pip install -r requirements.txt
```

## Bước 2: Cài đặt spaCy models (Optional nhưng khuyến nghị)

### Option 1: Vietnamese model (recommended)
```bash
python -m spacy download vi_core_news_lg
```

### Option 2: Multilingual model (fallback)
```bash
python -m spacy download xx_ent_wiki_sm
```

**Lưu ý:** Nếu không cài spaCy models, hệ thống vẫn hoạt động nhưng:
- NER embedding sẽ không khả dụng
- Hệ thống tự động fallback sang API embedding
- Tốn thêm API cost cho các văn bản ngắn

## Bước 3: Cấu hình file .env

Sao chép file example và điền thông tin:

```bash
cp .env.example .env
```

Chỉnh sửa `.env`:

```env
# Database (bắt buộc)
DATABASE_URL=postgresql://user:pass@host:port/dbname

# S3 Storage (bắt buộc cho image upload)
S3_ACCESS_KEY_ID=your_key
S3_SECRET_ACCESS_KEY=your_secret
S3_ENDPOINT_URL=https://your-bucket.supabase.co/storage/v1/s3
S3_BUCKET_NAME=AiNote

# LLM Configuration (chọn providers)

# Option 1: Sử dụng Ollama local (miễn phí)
API_EXTRACT_NAME=
API_CHAT_NAME=
API_EXTRACT_EMBEDDING=
API_EXTRACT_TEXT=http://localhost:11434
API_CHAT=http://localhost:11434
MODEL_EXTRACT_TEXT=qwen2.5vl:3b
MODEL_CHAT=llama3.1:8b

# Option 2: Sử dụng OpenAI GPT
API_EXTRACT_NAME=GPT
API_CHAT_NAME=GPT
API_EXTRACT_EMBEDDING=GPT
MODEL_EXTRACT_TEXT=gpt-4o-mini
MODEL_CHAT=gpt-4o-mini
MODEL_EXTRACT_EMBEDDING=text-embedding-3-small
OPENAI_API_KEY=sk-your-key-here

# Option 3: Sử dụng Google Gemini
API_EXTRACT_NAME=GEMINI
API_CHAT_NAME=GEMINI
API_EXTRACT_EMBEDDING=GEMINI
MODEL_EXTRACT_TEXT=gemini-1.5-flash
MODEL_CHAT=gemini-1.5-flash
MODEL_EXTRACT_EMBEDDING=text-embedding-004
GEMINI_API_KEY=your-key-here

# Option 4: Mix providers (recommended)
API_EXTRACT_NAME=GEMINI          # Gemini cho OCR
API_CHAT_NAME=GPT                # GPT cho chat quality
API_EXTRACT_EMBEDDING=GPT        # GPT cho embedding quality
MODEL_EXTRACT_TEXT=gemini-1.5-flash
MODEL_CHAT=gpt-4o-mini
MODEL_EXTRACT_EMBEDDING=text-embedding-3-small
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=AIza...
```

## Bước 4: Setup Database

### Tạo database và chạy migrations

```bash
# Nếu dùng Alembic
alembic upgrade head

# Hoặc tạo tables thủ công
python -c "from app.core.database import Base, engine; Base.metadata.create_all(bind=engine)"
```

### Setup FTS triggers

```python
from app.core.database import engine
from app.core.fts import install_note_items_fts
from app.core.config import settings

with engine.connect() as conn:
    install_note_items_fts(conn, settings.FTS_CONFIG)
    conn.commit()
```

## Bước 5: Chạy server

### Development mode
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production mode
```bash
uvicorn app.main:app --workers 4 --host 0.0.0.0 --port 8000
```

## Bước 6: Test hệ thống

### Test health check
```bash
curl http://localhost:8000/health
```

### Test với authentication

1. Register user:
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "username": "testuser",
    "password": "testpass123"
  }'
```

2. Login:
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpass123"
  }'
```

3. Create note:
```bash
TOKEN="your_access_token_here"

curl -X POST http://localhost:8000/api/notes/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Note",
    "content": "This is a test note with some content"
  }'
```

4. Upload image:
```bash
curl -X POST http://localhost:8000/api/notes/upload-image \
  -H "Authorization: Bearer $TOKEN" \
  -F "image=@path/to/image.jpg" \
  -F "title=My Image Note"
```

5. Ask question (RAG):
```bash
curl -X POST http://localhost:8000/api/notes/ask \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What notes do I have about meetings?"
  }'
```

## Troubleshooting

### spaCy model không tìm thấy
```bash
# Kiểm tra models đã cài
python -m spacy info

# Cài lại model
python -m spacy download vi_core_news_lg --force
```

### Import errors
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Database connection errors
- Kiểm tra DATABASE_URL trong .env
- Kiểm tra database đã được tạo
- Kiểm tra network/firewall

### S3/Storage errors
- Kiểm tra S3 credentials
- Kiểm tra bucket permissions
- Kiểm tra endpoint URL

### API provider errors
- Kiểm tra API keys
- Kiểm tra provider names (GPT, GEMINI, etc.)
- Kiểm tra model names
- Check API quotas/limits

### Embedding không hoạt động
- Kiểm tra spaCy models đã cài
- Kiểm tra API_EXTRACT_EMBEDDING config
- System sẽ fallback về keyword-based nếu cả 2 fail

## Monitoring

### Check logs
```bash
# Xem logs realtime
tail -f logs/app.log

# Search for errors
grep ERROR logs/app.log
```

### Check database
```sql
-- Count notes
SELECT COUNT(*) FROM note_items;

-- Check embeddings
SELECT COUNT(*) FROM note_items WHERE embedding IS NOT NULL;

-- Check entities
SELECT COUNT(*) FROM note_items WHERE entities IS NOT NULL;

-- Check FTS
SELECT COUNT(*) FROM note_items WHERE tsv_content IS NOT NULL;
```

## Performance Optimization

### 1. Database Indexes
```sql
-- Ensure indexes exist
CREATE INDEX IF NOT EXISTS idx_note_items_user_active 
  ON note_items(user_id, is_archived);

CREATE INDEX IF NOT EXISTS idx_note_items_tsv_content 
  ON note_items USING GIN(tsv_content);

CREATE INDEX IF NOT EXISTS idx_note_items_embedding 
  ON note_items USING GIN(embedding jsonb_path_ops);
```

### 2. Connection Pool
Trong .env hoặc config:
```python
# SQLAlchemy pool settings
SQLALCHEMY_POOL_SIZE=20
SQLALCHEMY_MAX_OVERFLOW=40
```

### 3. Caching
Implement Redis caching cho:
- Embeddings (cache theo content hash)
- Frequent queries
- User sessions

## Deployment Checklist

- [ ] Database migrations chạy thành công
- [ ] FTS triggers đã được cài đặt
- [ ] Indexes đã được tạo
- [ ] S3 storage hoạt động
- [ ] API providers configured (or Ollama running)
- [ ] spaCy models installed (optional)
- [ ] Environment variables đã set
- [ ] SSL certificates (production)
- [ ] Firewall rules
- [ ] Monitoring tools
- [ ] Backup strategy
- [ ] Log rotation

## Next Steps

1. Đọc [RAG_README.md](./RAG_README.md) để hiểu architecture
2. Test tất cả endpoints
3. Monitor performance
4. Optimize weights trong retrieval strategy
5. Fine-tune embedding strategy based on usage
6. Implement caching layer nếu cần
7. Set up monitoring và alerting

---

**Happy coding! 🚀**
