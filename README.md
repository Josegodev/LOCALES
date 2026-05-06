# LOCALES

Runtime local para interacción Telegram → FastAPI → herramientas controladas, con generación opcional mediante LLM local.

El sistema está diseñado para mantener la ejecución bajo contratos explícitos, permisos, sandbox filesystem y trazabilidad por `request_id`.

## Arquitectura

```text
Telegram Bot
    ↓
Command Parser
    ↓
Permission Layer
    ↓
Optional LLM Generation
    ↓
Pydantic Contracts
    ↓
FastAPI /documents
    ↓
Sandbox Document Writer
    ↓
Filesystem

Comandos Telegram
/doc

Crea un documento Markdown con contenido escrito por el usuario.

/doc prueba.md
Contenido del documento.

Flujo:

Telegram → parser → permisos → CreateDocumentRequest → /documents → writer
/doc_ai

Crea un documento Markdown con contenido generado por un LLM local.

/doc_ai resumen.md
Explica en 5 líneas qué es un sandbox.

Flujo:

Telegram → parser → permisos → LLM → validación salida → /documents → writer

El LLM solo genera contenido. No decide filename, ruta, permisos ni escritura.

Contratos principales
CreateDocumentRequest

Campos obligatorios:

request_id
filename
content
overwrite = false
user_id
chat_id

Restricciones:

filename obligatorio.
Solo extensión .md.
No rutas absolutas.
No ...
No / ni \.
Máximo 120 caracteres.
content no vacío.
content máximo 100000 caracteres.
overwrite solo puede ser false.
Campos extra rechazados.
Seguridad defensiva

Medidas implementadas:

Allowlist de usuarios Telegram.
Deny-by-default si no hay usuarios permitidos.
Sandbox filesystem.
Rechazo de path traversal.
Rechazo de sobrescritura.
request_id extremo a extremo.
Logs estructurados.
Separación entre generación LLM y escritura.
Tests de contrato, permisos y rechazos.
Variables de entorno

Crear .env local. No subirlo a Git.

TELEGRAM_BOT_TOKEN=...
TELEGRAM_ALLOWED_USER_IDS=123456789

TELEGRAM_DOCS_DIR=./TELEGRAM_DOCS

LMSTUDIO_BASE_URL=http://127.0.0.1:1234
LMSTUDIO_MODEL=granite-3.2-8b
LLM_TIMEOUT_SECONDS=60
LLM_MAX_OUTPUT_CHARS=50000
Arranque local

Terminal 1:

cd ~/LOCALES
source .venv/bin/activate
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

Terminal 2:

cd ~/LOCALES
source .venv/bin/activate
python run_telegram.py

LM Studio debe estar levantado en modo servidor OpenAI-compatible si se usa /doc_ai.

Validación

Compilar módulos principales:

.venv/bin/python -m py_compile app/config.py app/schemas.py app/main.py app/document_writer.py app/llm_client.py run_telegram.py

Ejecutar tests:

.venv/bin/python -m unittest discover -s tests
Límites actuales

Este proyecto no debe considerarse aún un agente autónomo.

No implementado todavía:

Tool calling autónomo por LLM.
Planner.
Ejecución shell.
Memoria persistente.
RAG integrado en /doc_ai.
Rate limiting.
Aislamiento fuerte por usuario Linux/systemd.
Multiusuario avanzado.
Principio de diseño

El LLM no es autoridad operacional.

Puede generar texto, pero las acciones pasan por:

contrato → permisos → sandbox → writer

Esto evita que un fallo de inferencia implique compromiso del filesystem.