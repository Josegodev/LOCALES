# Mapa de dependencias Python

## Imports internos por modulo
### `DB/api_server.py`
- linea 7: `from db_store import approve_memory`
- linea 7: `from db_store import create_model_profile`
- linea 7: `from db_store import ensure_profile_exists`
- linea 7: `from db_store import enforce_memory_limit`
- linea 7: `from db_store import get_memory_context`
- linea 7: `from db_store import list_model_profiles`
- linea 7: `from db_store import memory_stats`
- linea 7: `from db_store import prune_raw`
- linea 7: `from db_store import raw_stats`
- linea 7: `from db_store import save_exchange`
- linea 20: `from lmstudio_client import extract_message_content`
- linea 20: `from lmstudio_client import load_config`
- linea 20: `from lmstudio_client import send_chat_completion`
### `DB/approve_memory.py`
- linea 4: `from db_store import approve_memory`
### `DB/chat_once.py`
- linea 5: `from db_store import ensure_profile_exists`
- linea 5: `from db_store import get_memory_context`
- linea 5: `from db_store import save_exchange`
- linea 10: `from lmstudio_client import extract_message_content`
- linea 10: `from lmstudio_client import load_config`
- linea 10: `from lmstudio_client import send_chat_completion`
### `DB/chunks/api.py`
- linea 8: `from document_context import build_document_prompt`
- linea 9: `from lmstudio_client import ask_lmstudio`
### `DB/chunks/run_document_rag.py`
- linea 5: `from document_context import build_document_prompt`
- linea 6: `from lmstudio_client import ask_lmstudio`
### `DB/chunks/run_ingest_pipeline.py`
- linea 9: `from document_context import build_document_prompt`
- linea 10: `from search_docs import search_chunks`
### `DB/prune.py`
- linea 2: `from db_store import prune_raw`
- linea 2: `from db_store import raw_stats`
- linea 2: `from db_store import memory_stats`
### `DB/setup_profile.py`
- linea 2: `from db_store import create_model_profile`
### `app/lmstudio_client.py`
- linea 6: `from app.config import settings`
### `app/main.py`
- linea 2: `from DB.chunks.document_context import build_document_prompt`
- linea 3: `from app.config import settings`
- linea 4: `from app.schemas import ChatRequest`
- linea 4: `from app.schemas import ChatResponse`
- linea 5: `from app.lmstudio_client import ask_lmstudio`
- linea 5: `from app.lmstudio_client import LLMError`
- linea 7: `from app.schemas import DocumentCreateRequest`
- linea 7: `from app.schemas import DocumentCreateResponse`
- linea 8: `from app.document_writer import create_document`
- linea 8: `from app.document_writer import DocumentWriteError`
### `llm_lab/api.py`
- linea 15: `from .model_adapter import ModelAdapter`
- linea 16: `from .validator import validate_answer_output`
- linea 16: `from .validator import validate_proposal_output`
### `llm_lab/validator.py`
- linea 12: `from .schemas import JSONDict`
- linea 12: `from .schemas import ValidationResult`
- linea 12: `from .schemas import answer_fallback`
- linea 12: `from .schemas import proposal_fallback`
### `run_telegram.py`
- linea 3: `from app.config import settings`

## Dependencias externas observadas
- `__future__`: `DB/chunks/api.py`, `DB/chunks/document_context.py`, `DB/chunks/ingest_all_pdfs.py`, `DB/chunks/ingest_pdf_markdown.py`, `DB/chunks/lmstudio_client.py`, `DB/chunks/run_document_rag.py`, `DB/chunks/run_ingest_pipeline.py`, `DB/chunks/search_docs.py`, `llm_lab/api.py`, `llm_lab/continue_server.py`, `llm_lab/model_adapter.py`, `llm_lab/schemas.py`, `llm_lab/validator.py`
- `fastapi`: `DB/api_server.py`, `DB/chunks/api.py`, `app/main.py`, `llm_lab/api.py`, `llm_lab/continue_server.py`
- `from pydantic import BaseModel, ValidationError, ConfigDict`: `DB/validator.py`
- `pydantic`: `DB/api_server.py`, `DB/chunks/api.py`, `app/schemas.py`, `llm_lab/continue_server.py`
- `pydantic_settings`: `app/config.py`
- `pymupdf4llm`: `DB/chunks/ingest_pdf_markdown.py`
- `requests`: `DB/chunks/lmstudio_client.py`, `app/lmstudio_client.py`, `app/telegram_client.py`, `run_telegram.py`
- `traceback`: `app/lmstudio_client.py`

## Imports ambiguos
### `DB/api_server.py`
- Linea 7: import bare `db_store`; acopla el modulo al cwd/directorio `DB`.
- Linea 7: import bare `db_store`; acopla el modulo al cwd/directorio `DB`.
- Linea 7: import bare `db_store`; acopla el modulo al cwd/directorio `DB`.
- Linea 7: import bare `db_store`; acopla el modulo al cwd/directorio `DB`.
- Linea 7: import bare `db_store`; acopla el modulo al cwd/directorio `DB`.
- Linea 7: import bare `db_store`; acopla el modulo al cwd/directorio `DB`.
- Linea 7: import bare `db_store`; acopla el modulo al cwd/directorio `DB`.
- Linea 7: import bare `db_store`; acopla el modulo al cwd/directorio `DB`.
- Linea 7: import bare `db_store`; acopla el modulo al cwd/directorio `DB`.
- Linea 7: import bare `db_store`; acopla el modulo al cwd/directorio `DB`.
- Linea 20: import bare `lmstudio_client`; AMBIGUO si se ejecuta desde otro cwd porque hay nombres repetidos en el repo.
- Linea 20: import bare `lmstudio_client`; AMBIGUO si se ejecuta desde otro cwd porque hay nombres repetidos en el repo.
- Linea 20: import bare `lmstudio_client`; AMBIGUO si se ejecuta desde otro cwd porque hay nombres repetidos en el repo.
### `DB/approve_memory.py`
- Linea 4: import bare `db_store`; acopla el modulo al cwd/directorio `DB`.
### `DB/chat_once.py`
- Linea 5: import bare `db_store`; acopla el modulo al cwd/directorio `DB`.
- Linea 5: import bare `db_store`; acopla el modulo al cwd/directorio `DB`.
- Linea 5: import bare `db_store`; acopla el modulo al cwd/directorio `DB`.
- Linea 10: import bare `lmstudio_client`; AMBIGUO si se ejecuta desde otro cwd porque hay nombres repetidos en el repo.
- Linea 10: import bare `lmstudio_client`; AMBIGUO si se ejecuta desde otro cwd porque hay nombres repetidos en el repo.
- Linea 10: import bare `lmstudio_client`; AMBIGUO si se ejecuta desde otro cwd porque hay nombres repetidos en el repo.
### `DB/chunks/api.py`
- Linea 8: import bare `document_context`; acopla al directorio `DB/chunks`.
- Linea 9: import bare `lmstudio_client`; AMBIGUO si se ejecuta desde otro cwd porque hay nombres repetidos en el repo.
### `DB/chunks/run_document_rag.py`
- Linea 5: import bare `document_context`; acopla al directorio `DB/chunks`.
- Linea 6: import bare `lmstudio_client`; AMBIGUO si se ejecuta desde otro cwd porque hay nombres repetidos en el repo.
### `DB/chunks/run_ingest_pipeline.py`
- Linea 9: import bare `document_context`; acopla al directorio `DB/chunks`.
### `DB/prune.py`
- Linea 2: import bare `db_store`; acopla el modulo al cwd/directorio `DB`.
- Linea 2: import bare `db_store`; acopla el modulo al cwd/directorio `DB`.
- Linea 2: import bare `db_store`; acopla el modulo al cwd/directorio `DB`.
### `DB/setup_profile.py`
- Linea 2: import bare `db_store`; acopla el modulo al cwd/directorio `DB`.
### `llm_lab/api.py`
- Linea 16: import bare `validator`; AMBIGUO si se ejecuta desde otro cwd porque hay nombres repetidos en el repo.
- Linea 16: import bare `validator`; AMBIGUO si se ejecuta desde otro cwd porque hay nombres repetidos en el repo.
### `llm_lab/validator.py`
- Linea 12: import bare `schemas`; AMBIGUO si se ejecuta desde otro cwd porque hay nombres repetidos en el repo.
- Linea 12: import bare `schemas`; AMBIGUO si se ejecuta desde otro cwd porque hay nombres repetidos en el repo.
- Linea 12: import bare `schemas`; AMBIGUO si se ejecuta desde otro cwd porque hay nombres repetidos en el repo.
- Linea 12: import bare `schemas`; AMBIGUO si se ejecuta desde otro cwd porque hay nombres repetidos en el repo.
