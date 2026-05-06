# Arquitectura general

> Lectura estatica. Donde no hay runtime verificado se marca `NO_VERIFICADO` o `AMBIGUO`.

## Componentes principales
- Telegram polling: `run_telegram.py`. Lee updates de Telegram y llama a FastAPI local.
- Gateway FastAPI productivo: `app/main.py`. Expone `/health`, `/documents` y `/chat`.
- RAG documental: `DB/chunks/document_context.py` + `DB/chunks/documents.sqlite`. Busca chunks por terminos y construye prompt con evidencia.
- Cliente LM Studio app: `app/lmstudio_client.py`. POST OpenAI-compatible a `http://127.0.0.1:1234/v1/chat/completions`.
- Document writer: `app/document_writer.py`. Permite crear `.txt`/`.md` en `TELEGRAM_DOCS`.
- DB API experimental: `DB/api_server.py` + `DB/db_store.py`. Gestiona perfiles, raw prompts, outputs y memoria aprobada.
- Chunks lab API: `DB/chunks/api.py`. API separada de document-chat sobre la misma base de chunks.
- llm_lab aislado: `llm_lab/*`. Laboratorio con mocks, proveedores locales, validacion JSON, trazas y eval.

## Flujo productivo observado
```text
Telegram update
  -> run_telegram.py:get_updates()
  -> run_telegram.py:handle_message()
  -> POST http://127.0.0.1:8000/chat {"message": text}
  -> app/main.py:chat(ChatRequest)
  -> DB/chunks/document_context.py:build_document_prompt()
  -> app/lmstudio_client.py:ask_lmstudio()
  -> LM Studio /v1/chat/completions
  -> ChatResponse.answer
  -> Telegram sendMessage
```

## Flujo de documentos desde Telegram
```text
/doc nombre.md + contenido
  -> run_telegram.py:handle_doc_command()
  -> POST /documents
  -> app/main.py:create_document_endpoint()
  -> app/document_writer.py:create_document()
  -> TELEGRAM_DOCS/<nombre>.md
```

## Fronteras del sistema
- Red externa: Telegram Bot API (`https://api.telegram.org`).
- Red local: FastAPI `127.0.0.1:8000`, LM Studio `127.0.0.1:1234`, Ollama opcional `127.0.0.1:11434`.
- Disco local: SQLite en `DB/`, documentos en `TELEGRAM_DOCS`, trazas en `llm_lab/artifacts`.
- Modelos LLM: salidas no deterministas salvo mocks de `llm_lab`.

## Separacion runtime / lab / experimental
- Runtime productivo local: `app/` + `run_telegram.py` + `DB/chunks/document_context.py`.
- Experimental persistencia/perfiles: `DB/api_server.py`, `DB/db_store.py`, scripts `DB/*.py`.
- Laboratorio aislado: `llm_lab/`, con mocks y validacion JSON propia.
- AMBIGUO: no hay un unico manifiesto que declare cual FastAPI debe ser el servicio principal cuando hay varios `/chat`.

## LLM: puntos de intervencion
- `app/lmstudio_client.py`: LM Studio para `/chat` productivo.
- `DB/lmstudio_client.py`: LM Studio para API de perfiles y CLI `DB/chat_once.py`.
- `DB/chunks/lmstudio_client.py`: LM Studio para API documental separada.
- `llm_lab/model_adapter.py`: mock, Ollama o LM Studio segun variables de entorno.

## Determinismo
- Deterministas: validadores puros, formacion de payloads, `safe_slug`, hashing, chunking por texto fijo.
- Parciales: busquedas SQLite dependen del estado de DB; trazas dependen de tiempo/UUID.
- No deterministas: llamadas a Telegram, LM Studio, Ollama, red local y modelos LLM.

## Superficies de riesgo
- Contratos `/chat` duplicados: `app/main.py` usa `message`; `DB/api_server.py` usa `slug/prompt`.
- Imports bare (`lmstudio_client`, `db_store`, `document_context`) dependen del cwd.
- `run_telegram.py` y `app/schemas.py` tienen definiciones duplicadas que se pisan.
- `DB/validator.py` no compila por indentacion.
- Observabilidad heterogenea: `app/lmstudio_client.py` imprime body completo; otros clientes no tienen el mismo nivel.
