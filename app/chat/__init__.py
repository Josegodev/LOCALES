from app.chat.dependencies import ChatDependencies

__all__ = ["ChatDependencies", "ChatService"]


def __getattr__(name: str):
    if name == "ChatService":
        from app.chat.service import ChatService

        return ChatService
    raise AttributeError(name)
