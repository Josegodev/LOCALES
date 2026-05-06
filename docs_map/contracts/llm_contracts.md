# Contratos LLM

## App productiva `app/lmstudio_client.py`

Payload enviado a LM Studio:

```json
{
  "model": "settings.default_model o request.model",
  "messages": [
    {"role": "system", "content": "..."},
    {"role": "user", "content": "prompt RAG"}
  ],
  "temperature": "settings.temperature o request.temperature",
  "max_tokens": "settings.max_tokens o request.max_tokens"
}
```

Respuesta aceptada:

```text
choices[0].message.content debe existir, ser string y no estar vacio.
```

Errores cerrados: `LMSTUDIO_UNAVAILABLE`, `TIMEOUT`, `HTTP_ERROR`, `LMSTUDIO_HTTP_ERROR`, `INVALID_RESPONSE`, `EMPTY_RESPONSE`.

## DB/perfiles `DB/lmstudio_client.py`

Payload construido por `DB/api_server.py` o `DB/chat_once.py` incluye `model`, `messages`, parametros del perfil y `stream=false`.

Respuesta aceptada: `choices[0].message.content` textual no vacio.

## llm_lab

`llm_lab/model_adapter.py` admite proveedores `mock`, `ollama`, `lmstudio` por variables de entorno. Todo raw output pasa por `llm_lab/validator.py`.

Contratos validados:

- Propuesta: `suggested_action: str`, `arguments: dict`, `confidence: 0..1`, `meta` con `needs_clarification` y `justification`.
- Respuesta: `answer: str`, `confidence: 0..1`, `meta` valido.

## Riesgos

- CRITICO: los tres clientes LM Studio no comparten un unico contrato ni mismos defaults.
- CRITICO: `DB/chunks/lmstudio_client.py` mantiene `DEFAULT_MODEL="local-model"`.
- INFORMATIVO: `app/lmstudio_client.py` imprime payload y body completo; util para debug, pero puede exponer prompts en logs.
