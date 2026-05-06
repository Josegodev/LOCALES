# docs_map INDEX

Documentacion tecnica generada por lectura estatica del repositorio. No modifica codigo existente.

## Navegacion

- [Inventario](inventory/files_inventory.md)
- [Arquitectura](architecture/system_overview.md)
- [Runtime](runtime/runtime_entrypoints.md)
- [Contratos HTTP](contracts/http_contracts.md)
- [Contratos SQLite](contracts/sqlite_contracts.md)
- [Contratos LLM](contracts/llm_contracts.md)
- [Riesgos](risks/risk_register.md)
- [Dependencias Python](dependency_map/python_imports.md)
- [Servicios externos](dependency_map/external_services.md)

## Flujos

- [Telegram a chat](flows/telegram_to_chat.md)
- [Ingesta documental y RAG](flows/document_ingest_rag.md)
- [Perfiles DB y memoria](flows/db_profile_memory.md)
- [llm_lab evaluacion](flows/llm_lab_eval.md)

## Modulos Python

- [`DB/api_server.py`](modules/DB__api_server.md)
- [`DB/approve_memory.py`](modules/DB__approve_memory.md)
- [`DB/chat_once.py`](modules/DB__chat_once.md)
- [`DB/chunks/api.py`](modules/DB__chunks__api.md)
- [`DB/chunks/document_context.py`](modules/DB__chunks__document_context.md)
- [`DB/chunks/ingest_all_pdfs.py`](modules/DB__chunks__ingest_all_pdfs.md)
- [`DB/chunks/ingest_pdf_markdown.py`](modules/DB__chunks__ingest_pdf_markdown.md)
- [`DB/chunks/lmstudio_client.py`](modules/DB__chunks__lmstudio_client.md)
- [`DB/chunks/run_document_rag.py`](modules/DB__chunks__run_document_rag.md)
- [`DB/chunks/run_ingest_pipeline.py`](modules/DB__chunks__run_ingest_pipeline.md)
- [`DB/chunks/search_docs.py`](modules/DB__chunks__search_docs.md)
- [`DB/db_store.py`](modules/DB__db_store.md)
- [`DB/lmstudio_client.py`](modules/DB__lmstudio_client.md)
- [`DB/prune.py`](modules/DB__prune.md)
- [`DB/setup_profile.py`](modules/DB__setup_profile.md)
- [`DB/test_validator.py`](modules/DB__test_validator.md)
- [`DB/validator.py`](modules/DB__validator.md)
- [`app/__init__.py`](modules/app____init__.md)
- [`app/bot_service.py`](modules/app__bot_service.md)
- [`app/config.py`](modules/app__config.md)
- [`app/document_writer.py`](modules/app__document_writer.md)
- [`app/lmstudio_client.py`](modules/app__lmstudio_client.md)
- [`app/main.py`](modules/app__main.md)
- [`app/rag_store.py`](modules/app__rag_store.md)
- [`app/schemas.py`](modules/app__schemas.md)
- [`app/telegram_client.py`](modules/app__telegram_client.md)
- [`ingest_nucleo_md.py`](modules/ingest_nucleo_md.md)
- [`llm_lab/__init__.py`](modules/llm_lab____init__.md)
- [`llm_lab/api.py`](modules/llm_lab__api.md)
- [`llm_lab/continue_server.py`](modules/llm_lab__continue_server.md)
- [`llm_lab/model_adapter.py`](modules/llm_lab__model_adapter.md)
- [`llm_lab/schemas.py`](modules/llm_lab__schemas.md)
- [`llm_lab/validator.py`](modules/llm_lab__validator.md)
- [`run_telegram.py`](modules/run_telegram.md)
