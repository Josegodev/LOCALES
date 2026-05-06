# Registro de riesgos

## CRITICO

- `DB/validator.py` no compila: `IndentationError` en linea 13 detectado por `py_compile`.
- Contratos `/chat` duplicados e incompatibles: `app/main.py` usa `message`; `DB/api_server.py` usa `slug/prompt`.
- `run_telegram.py` contiene `ask_backend()` con `slug/prompt` contra `app/main.py`; no se usa en flujo principal, pero es drift activo.
- `run_telegram.py` define `handle_doc_command` dos veces; la segunda definicion pisa la primera.
- `app/schemas.py` define `DocumentCreateRequest` dos veces; la segunda definicion pisa la primera.
- `app/main.py` devuelve campos extra `retrieval_status` y `chunks` en `ChatResponse`, pero el schema no los declara.
- `app/rag_store.py` usa ruta relativa `chunks/document_chunks.sqlite`, distinta de `DB/chunks/documents.sqlite`; su runtime depende del cwd.

## INFORMATIVO

- Varias APIs FastAPI pueden competir conceptualmente por el rol de gateway (`app/main.py`, `DB/api_server.py`, `DB/chunks/api.py`, `llm_lab/api.py`).
- Hay tres clientes LM Studio con contratos y defaults distintos.
- Observabilidad por `print` no esta normalizada y no hay correlacion por request id en `app/`.
- `telegram_allowed_chat_ids` existe en config, pero no se observa enforcement en `run_telegram.py`.
- `DB/documents.sqlite` existe con tamano 0; AMBIGUO si es artefacto abandonado o placeholder.

## AMBIGUO / NO_VERIFICADO

- No hay manifiesto que indique cual API se despliega como servicio principal.
- No se verifica runtime de Uvicorn ni comandos exactos de arranque en raiz.
- No se verifica version exacta de Pydantic/FastAPI usada fuera del entorno `.venv` activo.
