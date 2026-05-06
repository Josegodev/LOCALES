# Flujo: Telegram -> FastAPI /chat -> LM Studio

```text
Telegram Bot API
  -> run_telegram.py:get_updates()
  -> handle_message()
  -> ask_fastapi(text)
  -> POST http://127.0.0.1:8000/chat {"message": text}
  -> app/main.py:chat()
  -> DB.chunks.document_context.build_document_prompt()
  -> app.lmstudio_client.ask_lmstudio()
  -> LM Studio /v1/chat/completions
  -> ChatResponse.answer
  -> send_message()
```

## Contratos

- Entrada Telegram: `message.text` string.
- Entrada `/chat`: `ChatRequest.message` obligatorio, 1..4000 chars.
- RAG: `build_document_prompt()` devuelve `status`, `prompt`, `chunks`.
- LLM: `choices[0].message.content` debe ser string no vacio.

## Riesgos

- Si no hay evidencia, no se llama a LM Studio.
- Si LM Studio devuelve `content` vacio, `app/lmstudio_client.py` levanta `LLMError(EMPTY_RESPONSE)` y FastAPI responde 502.
- `ask_backend()` no participa en este flujo, pero contiene contrato incompatible.
