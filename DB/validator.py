# validator.py

from pydantic import BaseModel, ValidationError, ConfigDict


class ModelOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action: str
    confidence: float

    def validate_or_fallback(raw_text: str) -> dict:
    try:
        parsed = ModelOutput.model_validate_json(raw_text)
        return {
            "status": "valid",
            "data": parsed.model_dump()
        }
    except ValidationError:
        return {
            "status": "invalid",
            "data": {
                "action": "none",
                "confidence": 0.0
            }
        }
    
    