from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Bank Files Harmonizer API"
    environment: str = "development"
    api_prefix: str = "/api"
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])
    ras_classification_rules_path: str = (
        "../docs/reference/ras-classification-rules.csv"
    )
    rag_embedding_provider: str = "deterministic"
    rag_embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    llm_provider_chain: str = "internal:controlled-response"
    llm_default_timeout_seconds: float = 30.0
    llm_max_output_tokens: int = 1200
    excel_agent_allowed_root_path: str = "../docs"
    agent_max_answer_characters: int = 4_000

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
