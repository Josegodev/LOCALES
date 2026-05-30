from fastapi import APIRouter

from app.api.runtime_bridge import main_module
from app.schemas import (
    ChatModelListResponse,
    ChatOptionsResponse,
    TEMPERATURE_DEFAULT,
    TEMPERATURE_MAX,
    TEMPERATURE_MIN,
)

router = APIRouter()


@router.get("/api/models/chat", response_model=ChatModelListResponse)
def chat_models() -> dict:
    return {"status": "ok", "items": main_module().list_chat_models()}


@router.get("/api/chat/options", response_model=ChatOptionsResponse)
def chat_options() -> dict:
    return {
        "status": "ok",
        "temperature": {
            "default": TEMPERATURE_DEFAULT,
            "min": TEMPERATURE_MIN,
            "max": TEMPERATURE_MAX,
            "presets": [
                {"value": 0.0, "label": "Deterministic"},
                {"value": TEMPERATURE_DEFAULT, "label": "Technical default"},
                {"value": 0.7, "label": "Balanced"},
                {"value": 1.0, "label": "Exploratory"},
            ],
        },
    }
