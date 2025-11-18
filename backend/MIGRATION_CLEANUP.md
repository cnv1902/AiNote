# Files cũ có thể xóa sau khi migrate

Sau khi kiểm tra và đảm bảo ứng dụng chạy tốt với cấu trúc mới, bạn có thể xóa các files cũ sau:

## Files cần xóa:

```
app/config.py           -> đã migrate sang app/core/config.py
app/db.py               -> đã migrate sang app/core/database.py  
app/security.py         -> đã migrate sang app/core/security.py
app/fts.py              -> đã migrate sang app/core/fts.py
app/utils.py            -> đã migrate sang app/core/utils.py
app/deps.py             -> đã migrate sang app/api/dependencies.py
app/s3_client.py        -> đã migrate sang app/services/storage.py
app/storage_client.py   -> đã migrate sang app/services/storage.py
app/image_utils.py      -> đã migrate sang app/services/image.py
app/ocr_utils.py        -> đã migrate sang app/services/ocr.py
app/llm_utils.py        -> đã migrate sang app/services/llm.py
app/routers/            -> đã migrate sang app/api/v1/
```

## Lệnh để xóa (PowerShell):

```powershell
# Di chuyển vào thư mục backend
cd d:\Workspace\AiNote\backend\app

# Xóa các files cũ
Remove-Item config.py
Remove-Item db.py
Remove-Item security.py
Remove-Item fts.py
Remove-Item utils.py
Remove-Item deps.py
Remove-Item s3_client.py
Remove-Item storage_client.py
Remove-Item image_utils.py
Remove-Item ocr_utils.py
Remove-Item llm_utils.py

# Xóa thư mục routers cũ
Remove-Item -Recurse -Force routers/
```

## ⚠️ Lưu ý quan trọng:

1. **Backup trước khi xóa**: Đảm bảo bạn đã backup hoặc commit code vào git
2. **Test kỹ**: Chạy và test ứng dụng trước khi xóa files cũ
3. **Kiểm tra imports**: Đảm bảo không còn file nào import từ các modules cũ

## Kiểm tra trước khi xóa:

```powershell
# Test server
uvicorn app.main:app --reload

# Test endpoints
# - POST /api/auth/register
# - POST /api/auth/login
# - GET /api/notes/
# - POST /api/notes/
# - POST /api/notes/upload-image
```

Nếu tất cả đều hoạt động tốt, bạn có thể an tâm xóa các files cũ!
