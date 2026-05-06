from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import Any


app = FastAPI(title="NUCLEO llm_lab Continue Adapter")


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    model: str = "nucleo-lab"
    messages: list[ChatMessage]
    temperature: float | None = None
    max_tokens: int | None = None
    stream: bool = False


@app.post("/v1/chat/completions")
def chat_completions(req: ChatCompletionRequest) -> dict[str, Any]:
    if req.stream:
        return {
            "error": {
                "message": "Streaming not supported by llm_lab adapter",
                "type": "unsupported_feature",
            }
        }

    user_text = "\n".join(
        m.content for m in req.messages if m.role == "user"
    ).strip()

    if not user_text:
        answer = "NO_INPUT"
    else:
        answer = (
            "Respuesta desde llm_lab adapter.\n\n"
            f"Input recibido:\n{user_text}"
        )

    return {
        "id": "chatcmpl-nucleo-lab",
        "object": "chat.completion",
        "model": req.model,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": answer,
                },
                "finish_reason": "stop",
            }
        ],
    }
