import json
from typing import Any
from datetime import timedelta

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://user:password@db:5432/moodbrief_db"
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_MODEL: str = "google/gemini-2.5-flash"
    OPENROUTER_TEXT_MODEL: str = "google/gemini-2.5-flash"
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    OPENROUTER_REFERER: str = "https://moodbrief.app"
    OPENROUTER_TITLE: str = "MoodBrief"

    # Fallback chains. Tried in order if the primary model fails.
    # Comma-separated in env, e.g. "openai/gpt-4o-mini,anthropic/claude-haiku-4.5"
    OPENROUTER_VISION_MODELS: list[str] = [
        "openai/gpt-4o-mini",
        "anthropic/claude-haiku-4.5",
        "meta-llama/llama-3.2-11b-vision-instruct",
    ]
    OPENROUTER_TEXT_MODELS: list[str] = [
        "anthropic/claude-haiku-4.5",
        "openai/gpt-4o-mini",
        "deepseek/deepseek-v3.2",
    ]
    
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # JWT Settings
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Any) -> list[str] | str:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            if isinstance(v, str):
                try:
                    return json.loads(v)
                except json.JSONDecodeError:
                    return v
            return v
        return v

    @field_validator("OPENROUTER_VISION_MODELS", "OPENROUTER_TEXT_MODELS", mode="before")
    @classmethod
    def _parse_model_list(cls, v: Any) -> list[str]:
        if v is None or v == "":
            return []
        if isinstance(v, list):
            return [s for s in (str(x).strip() for x in v) if s]
        if isinstance(v, str):
            s = v.strip()
            if s.startswith("["):
                try:
                    parsed = json.loads(s)
                    return [str(x).strip() for x in parsed if str(x).strip()]
                except json.JSONDecodeError:
                    pass
            return [item.strip() for item in s.split(",") if item.strip()]
        return []

    def vision_model_chain(self) -> list[str]:
        chain: list[str] = []
        if self.OPENROUTER_MODEL:
            chain.append(self.OPENROUTER_MODEL)
        for m in self.OPENROUTER_VISION_MODELS:
            if m and m not in chain:
                chain.append(m)
        return chain

    def text_model_chain(self) -> list[str]:
        chain: list[str] = []
        if self.OPENROUTER_TEXT_MODEL:
            chain.append(self.OPENROUTER_TEXT_MODEL)
        for m in self.OPENROUTER_TEXT_MODELS:
            if m and m not in chain:
                chain.append(m)
        return chain

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()

