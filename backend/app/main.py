"""
Điểm vào chính của ứng dụng FastAPI.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
import time
import random

from app.core.config import settings
from app.core.database import Base, engine
from app.core.fts import install_notes_fts, install_ocr_fts
from app.api.v1.auth import router as auth_router
from app.api.v1.notes import router as notes_router


def init_database_safely():
    """
    Khởi tạo cơ sở dữ liệu an toàn với lock để tránh xung đột giữa các worker.
    Sử dụng PostgreSQL advisory locks để đảm bảo chỉ một worker khởi tạo cơ sở dữ liệu.
    """
    max_retries = 3
    wait_time = 2  # giây
    
    for attempt in range(max_retries):
        try:
            with engine.begin() as conn:
                # Thử lấy advisory lock
                lock_result = conn.execute(
                    text("SELECT pg_try_advisory_lock(123456) as acquired")
                )
                acquired = lock_result.scalar()
                
                if not acquired:
                    if attempt < max_retries - 1:
                        time.sleep(wait_time + random.uniform(0, 1))
                    continue
                
                try:
                    # Kiểm tra xem các bảng đã tồn tại chưa
                    table_exists = conn.execute(
                        text(
                            "SELECT EXISTS (SELECT FROM information_schema.tables "
                            "WHERE table_name = 'notes')"
                        )
                    ).scalar()
                    
                    if not table_exists:
                        print("🔄 Đang tạo các bảng cơ sở dữ liệu...")
                        Base.metadata.create_all(bind=engine)
                        install_notes_fts(conn, settings.FTS_CONFIG)
                        install_ocr_fts(conn, settings.FTS_CONFIG)
                        print("✅ Khởi tạo cơ sở dữ liệu thành công")
                    else:
                        print("✅ Cơ sở dữ liệu đã được khởi tạo")
                finally:
                    # Giải phóng advisory lock
                    conn.execute(text("SELECT pg_advisory_unlock(123456)"))
                break
                
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(wait_time)
            else:
                print(f"⚠️ Không thể khởi tạo cơ sở dữ liệu sau {max_retries} lần thử")
                print(f"Lỗi: {str(e)}")


def create_app() -> FastAPI:
    """Tạo và cấu hình ứng dụng FastAPI."""
    app = FastAPI(
        title="AiNote API",
        version="1.0.0",
        description="Ứng dụng ghi chú hỗ trợ AI với OCR và trích xuất thực thể",
    )

    # Cấu hình CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Cấu hình phù hợp cho production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Bao gồm routers
    app.include_router(auth_router, prefix=settings.API_PREFIX)
    app.include_router(notes_router, prefix=settings.API_PREFIX)

    @app.on_event("startup")
    def on_startup():
        """Khởi tạo cơ sở dữ liệu khi ứng dụng khởi động."""
        init_database_safely()

    @app.get("/")
    def root():
        """Endpoint gốc."""
        return {
            "message": "Chào mừng đến với AiNote API",
            "version": "1.0.0",
            "docs": "/docs"
        }

    @app.get("/health")
    def health_check():
        """Endpoint kiểm tra sức khỏe."""
        return {"status": "healthy"}

    return app


# Tạo instance ứng dụng
app = create_app()