from __future__ import annotations

from app.chat.dependencies import ChatDependencies
from app import chat_runtime as chat_runtime_module
from app.schemas import ChatRequest, ChatResponse


class ChatService:
    def __init__(self, dependencies: ChatDependencies) -> None:
        self.dependencies = dependencies

    def run_chat_request(
        self,
        request: ChatRequest,
        *,
        persist_trace: bool = True,
    ) -> ChatResponse:
        return chat_runtime_module.run_chat_request(
            request,
            persist_trace=persist_trace,
            dependencies=self.dependencies,
        )
