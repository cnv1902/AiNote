"""
Main FastAPI application entry point.
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
    Initialize database safely with lock to avoid conflicts between workers.
    Uses PostgreSQL advisory locks to ensure only one worker initializes the database.
    """
    max_retries = 3
    wait_time = 2  # seconds
    
    for attempt in range(max_retries):
        try:
            with engine.begin() as conn:
                # Try to acquire advisory lock
                lock_result = conn.execute(
                    text("SELECT pg_try_advisory_lock(123456) as acquired")
                )
                acquired = lock_result.scalar()
                
                if not acquired:
                    if attempt < max_retries - 1:
                        time.sleep(wait_time + random.uniform(0, 1))
                    continue
                
                try:
                    # Check if tables already exist
                    table_exists = conn.execute(
                        text(
                            "SELECT EXISTS (SELECT FROM information_schema.tables "
                            "WHERE table_name = 'notes')"
                        )
                    ).scalar()
                    
                    if not table_exists:
                        print("🔄 Creating database tables...")
                        Base.metadata.create_all(bind=engine)
                        install_notes_fts(conn, settings.FTS_CONFIG)
                        install_ocr_fts(conn, settings.FTS_CONFIG)
                        print("✅ Database initialized successfully")
                    else:
                        print("✅ Database already initialized")
                finally:
                    # Release advisory lock
                    conn.execute(text("SELECT pg_advisory_unlock(123456)"))
                break
                
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(wait_time)
            else:
                print(f"⚠️ Could not initialize database after {max_retries} attempts")
                print(f"Error: {str(e)}")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="AiNote API",
        version="1.0.0",
        description="AI-powered note-taking application with OCR and entity extraction",
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(auth_router, prefix=settings.API_PREFIX)
    app.include_router(notes_router, prefix=settings.API_PREFIX)

    @app.on_event("startup")
    def on_startup():
        """Initialize database on application startup."""
        init_database_safely()

    @app.get("/")
    def root():
        """Root endpoint."""
        return {
            "message": "Welcome to AiNote API",
            "version": "1.0.0",
            "docs": "/docs"
        }

    @app.get("/health")
    def health_check():
        """Health check endpoint."""
        return {"status": "healthy"}

    return app


# Create application instance
app = create_app()