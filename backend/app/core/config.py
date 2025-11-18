"""
Module cấu hình ứng dụng.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Cài đặt ứng dụng được tải từ các biến môi trường."""
    
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8", 
        case_sensitive=False
    )

    # Cài đặt ứng dụng
    APP_ENV: str = "dev"
    API_PREFIX: str = "/api"
    HOST: str = "127.0.0.1"
    PORT: int = 8000

    # Cơ sở dữ liệu
    DATABASE_URL: str

    # Xác thực JWT
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRES_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRES_DAYS: int = 14

    # Tìm kiếm toàn văn
    FTS_CONFIG: str = "simple"

    # Supabase (tùy chọn)
    SUPABASE_URL: str | None = None
    SUPABASE_ANON_KEY: str | None = None

    # Lưu trữ S3
    S3_ACCESS_KEY_ID: str
    S3_SECRET_ACCESS_KEY: str
    S3_ENDPOINT_URL: str
    S3_BUCKET_NAME: str = "AiNote"
    S3_REGION: str = "ap-south-1"

    # API LLM
    API_EXTRACT_NAME: str = ""  # GPT, GEMINI, GROCK, DEEPSEEK, CLAUDE hoặc để trống cho local
    API_EXTRACT_TEXT: str | None = None
    MODEL_EXTRACT_TEXT: str | None = None
    API_CHAT_NAME: str = ""  # GPT, GEMINI, GROCK, DEEPSEEK, CLAUDE hoặc để trống cho local
    API_CHAT: str | None = None
    MODEL_CHAT: str | None = None
    
    # API Keys cho các providers
    OPENAI_API_KEY: str | None = None
    GEMINI_API_KEY: str | None = None
    GROCK_API_KEY: str | None = None
    DEEPSEEK_API_KEY: str | None = None
    ANTHROPIC_API_KEY: str | None = None


settings = Settings()
