from pydantic_settings import BaseSettings, SettingsConfigDict



class Settings(BaseSettings):
    backend_url: str = "http://127.0.0.1:8000"
    lmstudio_base_url: str = "http://127.0.0.1:1234"
    lmstudio_timeout_seconds: float = 60.0
    lmstudio_model: str = "ibm/granite-3.2-8b"
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "granite4.1:8b"
    ollama_timeout_seconds: float = 45.0
    llm_timeout_seconds: float = 60.0
    llm_max_output_chars: int = 50_000
    default_model: str = "ibm/granite-3.2-8b"

    max_prompt_chars: int = 4000
    max_tokens: int = 512
    temperature: float = 0.2

    telegram_bot_token: str | None = None
    telegram_allowed_chat_ids: str | None = None
    telegram_allowed_user_ids: str | None = None
    telegram_trace_include_text: bool = False
    repo_analyzer_enabled: bool = False
    repo_analyzer_path: str = ""
    repo_analyzer_model: str = "granite4.1:8b"
    repo_analyzer_temperature: float = 0.2
    openai_api_key: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    def lmstudio_v1_base_url(self) -> str:
        base_url = self.lmstudio_base_url.rstrip("/")
        if base_url.endswith("/v1"):
            return base_url
        return f"{base_url}/v1"

    def backend_base_url(self) -> str:
        return self.backend_url.rstrip("/")

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

    def effective_ollama_model(self) -> str:
        return self.ollama_model

    def effective_ollama_timeout_seconds(self) -> float:
        return self.ollama_timeout_seconds


settings = Settings()
BACKEND_URL = settings.backend_base_url()
