from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://user:password@db:5432/moodbrief_db"
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_MODEL: str = "google/gemini-2.5-flash"
    OPENROUTER_TEXT_MODEL: str = "google/gemma-3-27b-it:free"
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    class Config:
        env_file = ".env"


settings = Settings()
