from fastapi import APIRouter

from app.api.runtime_bridge import main_module
from app.schemas import (
    CONVERSATION_WINDOW_DEFAULT,
    CONVERSATION_WINDOW_MAX,
    CONVERSATION_WINDOW_MIN,
    ChatModelListResponse,
    ChatOptionsResponse,
    TEMPERATURE_DEFAULT,
    TEMPERATURE_MAX,
    TEMPERATURE_MIN,
    TEMPERATURE_STEP,
    TOP_K_DEFAULT,
    TOP_K_MAX,
    TOP_K_MIN,
    TOP_K_STEP,
    TOP_P_DEFAULT,
    TOP_P_MAX,
    TOP_P_MIN,
    TOP_P_STEP,
)

router = APIRouter()


@router.get("/api/models/chat", response_model=ChatModelListResponse)
def chat_models() -> dict:
    return {"status": "ok", "items": main_module().list_chat_models()}


@router.get("/api/chat/options", response_model=ChatOptionsResponse)
def chat_options() -> dict:
    temperature_options = {
        "default": TEMPERATURE_DEFAULT,
        "min": TEMPERATURE_MIN,
        "max": TEMPERATURE_MAX,
        "presets": [
            {"value": 0.0, "label": "Deterministic"},
            {"value": TEMPERATURE_DEFAULT, "label": "Technical default"},
            {"value": 0.7, "label": "Balanced"},
            {"value": 1.0, "label": "Exploratory"},
        ],
    }
    return {
        "status": "ok",
        "temperature": temperature_options,
        "conversation": {
            "default": CONVERSATION_WINDOW_DEFAULT,
            "min": CONVERSATION_WINDOW_MIN,
            "max": CONVERSATION_WINDOW_MAX,
            "presets": [
                {"value": 0, "label": "Sin memoria"},
                {"value": 2, "label": "1 turno"},
                {"value": 4, "label": "2 turnos"},
                {"value": 8, "label": "4 turnos"},
            ],
        },
        "generation": {
            "temperature": {
                **temperature_options,
                "step": TEMPERATURE_STEP,
            },
            "top_p": {
                "default": TOP_P_DEFAULT,
                "min": TOP_P_MIN,
                "max": TOP_P_MAX,
                "step": TOP_P_STEP,
            },
            "top_k": {
                "default": TOP_K_DEFAULT,
                "min": TOP_K_MIN,
                "max": TOP_K_MAX,
                "step": TOP_K_STEP,
            },
        },
    }
