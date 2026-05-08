import requests

from app.adapters.ollama_client import (
    SYSTEM_PROMPT,
    OllamaClientError,
    ask_chat as _ask_chat,
    generate_markdown as _generate_markdown,
)
from app.config import settings

LLMClientError = OllamaClientError
CHAT_SYSTEM_PROMPT = (
    "Te llamas 5060Ti eres el bot del llm lab de Jose Gonzalez Oliva, "
    "tu función es responder a las preguntas de forma clara y concisa. "
    "Si no sabes la respuesta, di que no lo sabes."
)


def generate_markdown(prompt: str, request_id: str) -> str:
    return _generate_markdown(
        prompt,
        request_id,
        requests_module=requests,
        settings_obj=settings,
    )


def ask_chat(
    message: str,
    *,
    model: str | None = None,
    max_tokens: int | None = None,
    temperature: float | None = None,
) -> dict:
    return _ask_chat(
        message,
        model=model,
        temperature=temperature,
        num_predict=max_tokens,
        system_prompt=CHAT_SYSTEM_PROMPT,
        requests_module=requests,
        settings_obj=settings,
    )
