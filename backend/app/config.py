from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)

    APP_ENV: str = "dev"
    API_PREFIX: str = "/api"
    HOST: str = "127.0.0.1"
    PORT: int = 8000

    DATABASE_URL: str

    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRES_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRES_DAYS: int = 14

    FTS_CONFIG: str = "simple"

    SUPABASE_URL: str | None = None
    SUPABASE_ANON_KEY: str | None = None

    S3_ACCESS_KEY_ID: str
    S3_SECRET_ACCESS_KEY: str
    S3_ENDPOINT_URL: str
    S3_BUCKET_NAME: str = "AiNote"
    S3_REGION: str = "ap-south-1"

    API_EXTRACT_TEXT: str | None = None
    MODEL_EXTRACT_TEXT: str | None = None
    API_CHAT: str | None = None
    MODEL_CHAT: str | None = None

settings = Settings()