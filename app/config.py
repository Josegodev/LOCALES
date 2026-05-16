from pathlib import Path
from typing import Literal

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


REPO_ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = REPO_ROOT / ".env"


class Settings(BaseSettings):
    app_env: str = "local"
    backend_url: str = Field(
        default="http://127.0.0.1:8000",
        validation_alias=AliasChoices("BACKEND_URL", "BACKEND_BASE_URL"),
    )
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = ""
    ollama_timeout_seconds: float = 45.0
    llm_timeout_seconds: float = 60.0

    max_prompt_chars: int = 4000
    max_tokens: int = 512
    temperature: float = 0.2

    openai_api_key: str | None = None
    documents_db_path: str = "DB/chunks/documents.sqlite"
    use_remote_rag: bool = False
    rag_service_url: str = "http://127.0.0.1:9000"
    rag_timeout_seconds: float = 10.0
    rag_top_k: int = 5
    chat_runs_path: str = Field(
        default="CHAT_RUNS",
        validation_alias=AliasChoices("CHAT_RUNS_PATH", "CHAT_TRACE_PATH"),
    )
    operation_timeout_ms: int = Field(default=10000, validation_alias=AliasChoices("OPERATION_TIMEOUT_MS"))
    jose_dev_token: str | None = None
    chat_auth_mode: Literal["local_open", "bearer_required", "disabled"] = "local_open"

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    def backend_base_url(self) -> str:
        return self.backend_url.rstrip("/")

    def rag_service_base_url(self) -> str:
        return self.rag_service_url.rstrip("/")

    def ollama_api_base_url(self) -> str:
        base_url = self.ollama_base_url.rstrip("/")
        if base_url.endswith("/v1"):
            return base_url[:-3]
        return base_url

    def ollama_v1_base_url(self) -> str:
        base_url = self.ollama_api_base_url()
        if base_url.endswith("/v1"):
            return base_url
        return f"{base_url}/v1"

    def effective_ollama_model(self) -> str | None:
        normalized_model = self.ollama_model.strip()
        return normalized_model or None

    def effective_ollama_timeout_seconds(self) -> float:
        return self.ollama_timeout_seconds


settings = Settings()
