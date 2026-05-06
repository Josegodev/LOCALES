# Inventario de archivos

> Alcance: `/home/jose-gonzalez-oliva/LOCALES`. Excluye `.venv`, `.git`, `node_modules`, `__pycache__` y `docs_map`.

## Resumen
- Archivos relevantes inventariados: 67
- Modulos Python del proyecto: 34
- Binarios pesados excluidos del arbol detallado: 3
- SQLite detectados: 9
- Endpoints FastAPI detectados: 20

## Arbol relevante
```text
.env  (103 B, sin extension)
DB/.vscode/tasks.json  (530 B, JSON)
DB/README.md  (10.2 KB, Markdown)
DB/Terminal 1 monitorización.txt  (171 B, Texto)
DB/api_server.py  (8.6 KB, Python)
DB/approve_memory.py  (949 B, Python)
DB/archivo.txt  (358 B, Texto)
DB/chat_once.py  (3.4 KB, Python)
DB/chunks/api.py  (1.6 KB, Python)
DB/chunks/archivo.txt  (358 B, Texto)
DB/chunks/document_context.py  (3.0 KB, Python)
DB/chunks/documents.sqlite  (1.0 MB, SQLite)
DB/chunks/identity_nucleo_jose.md  (738 B, Markdown)
DB/chunks/ingest_all_pdfs.py  (3.0 KB, Python)
DB/chunks/ingest_pdf_markdown.py  (3.8 KB, Python)
DB/chunks/lmstudio_client.py  (1.1 KB, Python)
DB/chunks/run_document_rag.py  (1.9 KB, Python)
DB/chunks/run_ingest_pipeline.py  (3.6 KB, Python)
DB/chunks/search_docs.py  (2.0 KB, Python)
DB/chunks/start rag.txt  (101 B, Texto)
DB/config.json  (155 B, JSON)
DB/db_store.py  (17.7 KB, Python)
DB/documents.sqlite  (0 B, SQLite)
DB/lmstudio_client.py  (2.2 KB, Python)
DB/profiles/lmstudio_granite32_8b_temp00/memory.sqlite  (36.0 KB, SQLite)
DB/profiles/lmstudio_granite32_8b_temp00/raw.sqlite  (60.0 KB, SQLite)
DB/profiles/lmstudio_qwen35_9b_q4km_temp02/memory.sqlite  (36.0 KB, SQLite)
DB/profiles/lmstudio_qwen35_9b_q4km_temp02/raw.sqlite  (136.0 KB, SQLite)
DB/profiles/lmstudio_qwen35_9b_q4km_temp07/memory.sqlite  (36.0 KB, SQLite)
DB/profiles/lmstudio_qwen35_9b_q4km_temp07/raw.sqlite  (100.0 KB, SQLite)
DB/prune.py  (538 B, Python)
DB/python3 chat once py.txt  (99 B, Texto)
DB/registry.sqlite  (32.0 KB, SQLite)
DB/schemas/memory.sql  (861 B, SQL)
DB/schemas/raw.sql  (1.9 KB, SQL)
DB/schemas/registry.sql  (1.0 KB, SQL)
DB/setup_profile.py  (1.7 KB, Python)
DB/slugs.txt  (85 B, Texto)
DB/test_validator.py  (0 B, Python)
DB/validator.py  (614 B, Python)
TELEGRAM_DOCS/desde_fastapi.md  (37 B, Markdown)
TELEGRAM_DOCS/prueba.md  (51 B, Markdown)
TELEGRAM_DOCS/prueba2.md  (33 B, Markdown)
TELEGRAM_DOCS/prueba_telegram.md  (50 B, Markdown)
app/__init__.py  (0 B, Python)
app/bot_service.py  (79 B, Python)
app/config.py  (540 B, Python)
app/document_writer.py  (1.8 KB, Python)
app/lmstudio_client.py  (3.3 KB, Python)
app/main.py  (2.5 KB, Python)
app/rag_store.py  (1003 B, Python)
app/schemas.py  (1008 B, Python)
app/telegram_client.py  (352 B, Python)
archivo.txt  (111 B, Texto)
ingest_nucleo_md.py  (2.5 KB, Python)
llm_lab/README.md  (3.7 KB, Markdown)
llm_lab/__init__.py  (38 B, Python)
llm_lab/api.py  (12.6 KB, Python)
llm_lab/artifacts/.gitkeep  (1 B, sin extension)
llm_lab/continue_server.py  (1.4 KB, Python)
llm_lab/eval/eval_cases.json  (1.6 KB, JSON)
llm_lab/model_adapter.py  (11.1 KB, Python)
llm_lab/rag/README.md  (561 B, Markdown)
llm_lab/requirements.txt  (46 B, Texto)
llm_lab/schemas.py  (1.5 KB, Python)
llm_lab/validator.py  (2.5 KB, Python)
run_telegram.py  (4.5 KB, Python)
```

## Binarios pesados excluidos del detalle
- `DB/chunks/pdf/CVjgo.pdf` (127.8 KB)
- `DB/chunks/pdf/MEMORIA 27.12.2021.pdf` (1.8 MB)
- `DB/chunks/pdf/guia_programadores_junior_2026_mouredevpro.pdf` (1.4 MB)

## Lenguajes detectados
- JSON: 3
- Markdown: 8
- PDF/binario: 3
- Python: 34
- SQL: 3
- SQLite: 9
- Texto: 8
- sin extension: 2

## Puntos de entrada
### FastAPI
- `app.get('/health')` -> `DB/api_server.py:128` funcion `health`
- `app.get('/profiles')` -> `DB/api_server.py:138` funcion `get_profiles`
- `app.post('/profiles')` -> `DB/api_server.py:145` funcion `create_profile`
- `app.get('/profiles/{slug}')` -> `DB/api_server.py:186` funcion `get_profile`
- `app.get('/profiles/{slug}/stats')` -> `DB/api_server.py:195` funcion `get_profile_stats`
- `app.get('/profiles/{slug}/memory')` -> `DB/api_server.py:207` funcion `get_profile_memory`
- `app.post('/profiles/{slug}/memory/approve')` -> `DB/api_server.py:225` funcion `approve_profile_memory`
- `app.post('/chat')` -> `DB/api_server.py:248` funcion `chat`
- `app.post('/profiles/{slug}/prune')` -> `DB/api_server.py:339` funcion `prune_profile`
- `app.post('/profiles/{slug}/memory/enforce-limit')` -> `DB/api_server.py:353` funcion `enforce_profile_memory_limit`
- `app.get('/health')` -> `DB/chunks/api.py:36` funcion `health`
- `app.post('/document-chat', response_model=DocumentChatResponse)` -> `DB/chunks/api.py:41` funcion `document_chat`
- `app.get('/health')` -> `app/main.py:15` funcion `health`
- `app.post('/documents', response_model=DocumentCreateResponse)` -> `app/main.py:20` funcion `create_document_endpoint`
- `app.post('/chat', response_model=ChatResponse)` -> `app/main.py:46` funcion `chat`
- `app.post('/rag/query')` -> `llm_lab/api.py:28` funcion `rag_query`
- `app.post('/model/proposal')` -> `llm_lab/api.py:53` funcion `model_proposal`
- `app.post('/model/answer')` -> `llm_lab/api.py:61` funcion `model_answer`
- `app.post('/eval/run')` -> `llm_lab/api.py:69` funcion `eval_run`
- `app.post('/v1/chat/completions')` -> `llm_lab/continue_server.py:25` funcion `chat_completions`

### Scripts ejecutables
- `DB/approve_memory.py`
- `DB/chat_once.py`
- `DB/chunks/ingest_all_pdfs.py`
- `DB/chunks/ingest_pdf_markdown.py`
- `DB/chunks/run_document_rag.py`
- `DB/chunks/run_ingest_pipeline.py`
- `DB/chunks/search_docs.py`
- `DB/prune.py`
- `DB/setup_profile.py`
- `ingest_nucleo_md.py`
- `run_telegram.py`

## Dependencias declaradas
- `llm_lab/requirements.txt` (46 B)

## Dockerfiles
- No se detectan Dockerfiles.

## SQLite / DBs
- `DB/chunks/documents.sqlite` (1.0 MB)
  - Tablas: chunks, documents
  - Filas `chunks`: 261
  - Filas `documents`: 66
- `DB/documents.sqlite` (0 B)
  - Estado: EMPTY_OR_MISSING
- `DB/profiles/lmstudio_granite32_8b_temp00/memory.sqlite` (36.0 KB)
  - Tablas: memory_items, schema_meta
  - Filas `memory_items`: 1
  - Filas `schema_meta`: 1
- `DB/profiles/lmstudio_granite32_8b_temp00/raw.sqlite` (60.0 KB)
  - Tablas: raw_outputs, raw_prompts, schema_meta
  - Filas `raw_outputs`: 8
  - Filas `raw_prompts`: 8
  - Filas `schema_meta`: 1
- `DB/profiles/lmstudio_qwen35_9b_q4km_temp02/memory.sqlite` (36.0 KB)
  - Tablas: memory_items, schema_meta
  - Filas `memory_items`: 4
  - Filas `schema_meta`: 1
- `DB/profiles/lmstudio_qwen35_9b_q4km_temp02/raw.sqlite` (136.0 KB)
  - Tablas: raw_outputs, raw_prompts, schema_meta
  - Filas `raw_outputs`: 9
  - Filas `raw_prompts`: 9
  - Filas `schema_meta`: 1
- `DB/profiles/lmstudio_qwen35_9b_q4km_temp07/memory.sqlite` (36.0 KB)
  - Tablas: memory_items, schema_meta
  - Filas `memory_items`: 0
  - Filas `schema_meta`: 1
- `DB/profiles/lmstudio_qwen35_9b_q4km_temp07/raw.sqlite` (100.0 KB)
  - Tablas: raw_outputs, raw_prompts, schema_meta
  - Filas `raw_outputs`: 7
  - Filas `raw_prompts`: 7
  - Filas `schema_meta`: 1
- `DB/registry.sqlite` (32.0 KB)
  - Tablas: model_profiles, schema_meta
  - Filas `model_profiles`: 3
  - Filas `schema_meta`: 1

## APIs
- `DB/api_server.py`: `app.get('/health')`
- `DB/api_server.py`: `app.get('/profiles')`
- `DB/api_server.py`: `app.post('/profiles')`
- `DB/api_server.py`: `app.get('/profiles/{slug}')`
- `DB/api_server.py`: `app.get('/profiles/{slug}/stats')`
- `DB/api_server.py`: `app.get('/profiles/{slug}/memory')`
- `DB/api_server.py`: `app.post('/profiles/{slug}/memory/approve')`
- `DB/api_server.py`: `app.post('/chat')`
- `DB/api_server.py`: `app.post('/profiles/{slug}/prune')`
- `DB/api_server.py`: `app.post('/profiles/{slug}/memory/enforce-limit')`
- `DB/chunks/api.py`: `app.get('/health')`
- `DB/chunks/api.py`: `app.post('/document-chat', response_model=DocumentChatResponse)`
- `app/main.py`: `app.get('/health')`
- `app/main.py`: `app.post('/documents', response_model=DocumentCreateResponse)`
- `app/main.py`: `app.post('/chat', response_model=ChatResponse)`
- `llm_lab/api.py`: `app.post('/rag/query')`
- `llm_lab/api.py`: `app.post('/model/proposal')`
- `llm_lab/api.py`: `app.post('/model/answer')`
- `llm_lab/api.py`: `app.post('/eval/run')`
- `llm_lab/continue_server.py`: `app.post('/v1/chat/completions')`

## Configuraciones
- `.env`: claves detectadas ['TELEGRAM_BOT_TOKEN', 'TELEGRAM_ALLOWED_CHAT_IDS']; valores no documentados por seguridad.
- `DB/.vscode/tasks.json` (JSON, 530 B)
- `DB/config.json` (JSON, 155 B)
- `DB/schemas/memory.sql` (SQL, 861 B)
- `DB/schemas/raw.sql` (SQL, 1.9 KB)
- `DB/schemas/registry.sql` (SQL, 1.0 KB)
- `llm_lab/eval/eval_cases.json` (JSON, 1.6 KB)
