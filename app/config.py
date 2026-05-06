from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    lmstudio_base_url: str = "http://127.0.0.1:1234"
    lmstudio_timeout_seconds: float = 60.0
    lmstudio_model: str = "ibm/granite-3.2-8b"
    llm_timeout_seconds: float = 60.0
    llm_max_output_chars: int = 50_000
    default_model: str = "ibm/granite-3.2-8b"

    max_prompt_chars: int = 4000
    max_tokens: int = 512
    temperature: float = 0.2

    telegram_bot_token: str | None = None
    telegram_allowed_chat_ids: str | None = None
    telegram_allowed_user_ids: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="forbid",
    )

    def lmstudio_v1_base_url(self) -> str:
        base_url = self.lmstudio_base_url.rstrip("/")
        if base_url.endswith("/v1"):
            return base_url
        return f"{base_url}/v1"


settings = Settings()
