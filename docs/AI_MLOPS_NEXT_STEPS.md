# AI/MLOps Next Steps Review

## 1. Estado actual entendido
Hoy existe un sistema local con dos caminos principales y varios laboratorios alrededor:

- Runtime principal de chat: `scripts/run_telegram.py` -> `app/services/bot_service.py` -> `app/main.py`.
- API principal FastAPI: `app/main.py` con `/health`, `/documents` y `/chat`.
- Retrieval RAG local sobre SQLite: `DB/chunks/document_context.py` y `DB/chunks/documents.sqlite`.
- Proveedores de modelo: `app/adapters/ollama_client.py` y `app/adapters/openai_client.py`, coordinados por `app/llm_client.py`.
- Trazas JSONL y espejos JSON: `app/observability/telegram_trace.py`, `logs/telegram_runs/`, `evals/runs/`.
- Evals actuales: `scripts/run_chat_evals.py` y `evals/run_telegram_evals.py`.
- Laboratorios separados: `DB/` para memoria/perfiles SQLite y `llm_lab/` para pruebas aisladas.

Incertidumbre controlada:

- No he desplegado servicios externos reales desde este informe; la evidencia sale del código, artefactos y tests.
- No he encontrado `compose.yml` ni `docker-compose.yml`.

## 2. Mapa operacional del sistema
Flujo real del runtime principal:

1. Telegram entra por `scripts/run_telegram.py`.
2. El mensaje se normaliza y enruta en `app/services/bot_service.py`.
3. El bot llama al backend local por HTTP usando `app/adapters/backend_client.py`.
4. FastAPI recibe en `app/main.py` el `POST /chat`.
5. Si `use_rag=true`, se construye contexto con `DB/chunks/document_context.py`.
6. El prompt resultante se envía al proveedor en `app/llm_client.py`.
7. El proveedor real responde desde `app/adapters/ollama_client.py` o `app/adapters/openai_client.py`.
8. La respuesta vuelve a Telegram y se persiste en `logs/telegram_runs/` y `evals/runs/` mediante `app/observability/telegram_trace.py`.
9. Las evals reutilizan el mismo endpoint `/chat` desde `scripts/run_chat_evals.py` y `evals/run_telegram_evals.py`.

Separación actual por zonas:

- Runtime: `app/`, `scripts/run_telegram.py`.
- Evals: `evals/`, `scripts/run_chat_evals.py`.
- Datos locales: `DB/chunks/documents.sqlite`, `DB/profiles/`, `logs/`, `TELEGRAM_DOCS/`.
- Laboratorio: `DB/api_server.py`, `DB/chunks/api.py`, `llm_lab/`.

## 3. Fortalezas actuales
- Hay contratos Pydantic explícitos en `app/schemas.py` y `app/contracts/bot.py`.
- Existe `trace_id` extremo a extremo y logs JSON estructurados en `app/observability/logging.py`.
- El bot persiste trazas útiles para operación real en `logs/telegram_runs/`.
- El RAG ya soporta allowlist por `allowed_source_filenames`, útil para evals controladas.
- Hay tests valiosos de retrieval, trazas, polling y hardening en `tests/`.
- `llm_lab/README.md` define bien un espacio aislado de experimentación y evita mezclarlo con runtime.

## 4. Riesgos técnicos actuales
### CRITICO - Docker actual no representa el runtime real
- Evidencia en repo: `Dockerfile` copia solo `app/`, pero `app/main.py` importa `DB.chunks.document_context`.
- Impacto operacional: la imagen no reproduce el sistema real de `/chat` con RAG y puede fallar al arrancar o quedar incompleta.
- Cómo detectarlo: construir la imagen y arrancarla; revisar si importa `DB/` y si `/chat` funciona con RAG.
- Cambio mínimo recomendado: hacer que la imagen incluya `DB/chunks/`, declarar volumen de datos y documentar variables mínimas antes de hablar de demo portable.

### CRITICO - La suite de tests no está verde
- Evidencia en repo: `.venv/bin/python -m unittest discover -s tests` devuelve `114` tests con `2` fallos en `tests/test_run_telegram_evals.py`.
- Impacto operacional: la capa que debería detectar regresiones ya está desalineada; baja la confianza en cada cambio.
- Cómo detectarlo: ejecutar la suite completa localmente.
- Cambio mínimo recomendado: alinear `evals/run_telegram_evals.py` y `tests/test_run_telegram_evals.py` para dejar la base en verde antes de ampliar evals.

### ALTO - Hay drift entre documentación y runtime real
- Evidencia en repo: `README.md` describe sobre todo `/documents` y LM Studio, pero el flujo vivo usa `/chat`, RAG, Ollama/OpenAI y trazas Telegram.
- Impacto operacional: un operador nuevo arranca componentes equivocados y no reproduce el comportamiento observado.
- Cómo detectarlo: comparar `README.md` con `app/main.py`, `scripts/run_telegram.py` y artefactos en `logs/telegram_runs/`.
- Cambio mínimo recomendado: crear una tabla corta de "entrypoints reales" y marcar qué es runtime y qué es laboratorio.

### ALTO - Hay varias APIs FastAPI y varios "centros" del sistema
- Evidencia en repo: `app/main.py`, `DB/api_server.py`, `DB/chunks/api.py` y `llm_lab/api.py`.
- Impacto operacional: confusión entre prototipo local, laboratorio y runtime principal; esto complica demos, soporte y validación.
- Cómo detectarlo: listar endpoints y comandos de arranque por directorio.
- Cambio mínimo recomendado: documentar una frontera explícita: "runtime principal", "lab RAG", "lab memoria", "llm_lab".

### ALTO - El contrato de telemetría no es uniforme
- Evidencia en repo: `app/observability/telegram_trace.py` mantiene campos legacy planos y además un bloque `ollama`; `app/main.py` devuelve `latency_ms=0` en no-evidence; trazas OpenAI reales en `logs/telegram_runs/telegram_chat_20260510.jsonl` dejan tokens en `null`.
- Impacto operacional: métricas mezcladas, dashboards manuales engañosos y comparaciones proveedor vs proveedor poco fiables.
- Cómo detectarlo: comparar un trace Ollama, uno OpenAI y la respuesta `/chat`.
- Cambio mínimo recomendado: fijar un contrato mínimo común de trace y marcar como opcionales los campos dependientes del proveedor.

### MEDIO - El arranque del bot no es reproducible ni automatizable
- Evidencia en repo: `scripts/run_telegram.py` pide modelo, temperatura y uso de RAG por `input()`; además `FASTAPI_URL` está fijado en `app/adapters/backend_client.py`.
- Impacto operacional: una demo depende de respuestas interactivas y no de configuración auditada.
- Cómo detectarlo: intentar levantar el bot sin terminal interactiva o desde contenedor.
- Cambio mínimo recomendado: aceptar configuración por variables de entorno o flags, y loggear la configuración efectiva al arrancar.

### MEDIO - Git hygiene inconsistente con los artefactos de eval
- Evidencia en repo: `.gitignore` ignora `evals/runs/`, pero `git ls-files` sigue mostrando JSON dentro de `evals/runs/`.
- Impacto operacional: se mezclan evidencias temporales con historial del producto; sube ruido y riesgo de confundir baseline con run casual.
- Cómo detectarlo: ejecutar `git ls-files | rg '^evals/runs/'`.
- Cambio mínimo recomendado: dejar en Git solo ejemplos deliberados o mover muestras canónicas a otra carpeta no efímera.

### MEDIO - El retrieval actual escala por lectura completa
- Evidencia en repo: `DB/chunks/document_context.py` hace `SELECT` completo y rankea en Python.
- Impacto operacional: con más corpus subirá la latencia y bajará el determinismo temporal del demo.
- Cómo detectarlo: medir tiempo de retrieval con corpus creciente y revisar tamaño de `documents.sqlite`.
- Cambio mínimo recomendado: instrumentar latencia de retrieval y definir un límite de corpus soportado antes de optimizar.

## 5. Siguientes pasos recomendados
### Fase 1 - Higiene y reproducibilidad local
- Dejar la suite de tests en verde.
- Añadir un README corto de arranque real del runtime principal.
- Aclarar qué artefactos son efímeros: `logs/`, `evals/runs/`, `DB/profiles/`, `TELEGRAM_DOCS/`.
- Definir comandos oficiales con `.venv/bin/python`.
- Añadir un smoke test manual de `/health` y `/chat`.

### Fase 2 - Observabilidad mínima
- Fijar un contrato mínimo para `trace_id`, `provider`, `model`, `use_rag`, `retrieval_status`, `chunk_ids`, `source_filenames`, `latency_ms`, `error_code`, `warnings`.
- Separar campo común y campo específico del proveedor.
- Medir retrieval y generación por separado.
- Registrar configuración efectiva: `temperature`, `top_k`, modelo y proveedor.

### Fase 3 - Evals
- Arreglar primero la regresión de `tests/test_run_telegram_evals.py`.
- Congelar un set pequeño y defendible de preguntas RAG.
- Reutilizar siempre las mismas fuentes permitidas por caso.
- Comparar al menos dos modelos y dos temperaturas con salida reproducible.
- Separar eval de regresión y eval exploratoria.

### Fase 4 - Docker mínimo
- Corregir la imagen para incluir dependencias reales del runtime.
- Añadir `HEALTHCHECK`.
- Declarar variables de entorno mínimas.
- Documentar volúmenes para `DB/chunks/`, `logs/` y artefactos si aplica.
- Si luego hace falta, añadir `compose.yml`; ahora mismo no existe.

### Fase 5 - Preparación cloud opcional
- Mantener un solo proceso claro y persistente.
- Externalizar secretos y no meter tokens en imagen.
- Decidir dónde vivirán SQLite y logs.
- Definir backups y rotación de artefactos.
- Aceptar que sin observabilidad mínima y healthchecks no hay despliegue serio.

## 6. Plan de aprendizaje IA/MLOps asociado
- Fase 1: aprendes operación básica, reproducibilidad local, dependencias y disciplina de arranque.
- Fase 2: aprendes observabilidad útil, diferencia entre logs, trazas y métricas, y contratos de telemetría.
- Fase 3: aprendes evals de regresión, drift, baselines y comparación entre modelos.
- Fase 4: aprendes empaquetado, dependencia del filesystem, variables de entorno y salud del servicio.
- Fase 5: aprendes la distancia real entre prototipo local y producción: secretos, persistencia, backups, coste y debugging remoto.

## 7. Backlog priorizado
| prioridad | tarea | archivo/ruta afectada | motivo | dificultad | riesgo | validación esperada |
| --- | --- | --- | --- | --- | --- | --- |
| P1 | Dejar tests en verde | `evals/run_telegram_evals.py`, `tests/test_run_telegram_evals.py` | Recuperar confianza base | Baja | Alto | `unittest` sin fallos |
| P1 | Documentar runtime real | `README.md`, `docs/` | Evitar arranques incorrectos | Baja | Alto | Un tercero arranca `/chat` sin dudas |
| P1 | Declarar artefactos efímeros | `.gitignore`, `evals/runs/`, `logs/`, `DB/profiles/` | Mejorar higiene del repo | Baja | Medio | `git status` limpio tras runs |
| P1 | Crear smoke commands oficiales | `README.md` o `docs/` | Reproducibilidad local | Baja | Medio | `/health` y `/chat` responden |
| P2 | Fijar contrato mínimo de trazas | `app/observability/telegram_trace.py`, `app/services/bot_service.py`, `app/schemas.py` | Hacer observabilidad comparable | Media | Alto | Un trace Ollama y uno OpenAI comparten esquema base |
| P2 | Medir retrieval por separado | `app/main.py`, RAG | No mezclar latencias | Media | Medio | Trace con latencia de retrieval y total |
| P2 | Parametrizar arranque del bot | `scripts/run_telegram.py`, `app/adapters/backend_client.py` | Quitar dependencia interactiva | Media | Medio | Bot arranca solo con env/flags |
| P3 | Congelar set corto de eval RAG | `evals/run_telegram_evals.py`, `evals/cases/` | Demo defendible | Media | Medio | Misma batería, mismo criterio |
| P3 | Separar artefactos de eval canónicos y efímeros | `evals/` | Evitar drift en Git | Baja | Medio | Samples deliberados fuera de `runs/` |
| P4 | Corregir Docker mínimo | `Dockerfile` | Hacer la demo portable de verdad | Media | Crítico | Imagen arranca `/chat` con RAG |

## 8. Qué NO hacer todavía
- Kubernetes.
- Microservicios.
- LangChain o CrewAI si no resuelven un problema real del repo.
- Cloud complejo antes de tener tests, healthchecks y trazas mínimas.
- Dashboards grandes sin contrato estable de métricas.
- Vector DB si `SQLite + RAG` simple aún sirve para el tamaño actual.
- Agentes autónomos sin políticas, evals y observabilidad suficientes.

## 9. Comandos de validación recomendados
```bash
# FastAPI principal
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

# Health
curl -s http://127.0.0.1:8000/health

# Chat con RAG
curl -s http://127.0.0.1:8000/chat \
  -H 'content-type: application/json' \
  -d '{"message":"¿Que hace NUCLEO?","use_rag":true,"top_k":3}'

# Bot de Telegram
.venv/bin/python scripts/run_telegram.py

# Evals deterministas
.venv/bin/python scripts/run_chat_evals.py --compare-baseline

# Evals Telegram por temperatura
.venv/bin/python evals/run_telegram_evals.py

# Logs y trazas
tail -n 20 logs/telegram_runs/telegram_chat_20260510.jsonl

# Tests
.venv/bin/python -m unittest discover -s tests

# Higiene git
git status --short
git ls-files | rg '^evals/runs/|^logs/|\\.jsonl$|\\.sqlite$|\\.db$'
```

## 10. Conclusión ejecutiva
Los 3 próximos pasos concretos que haría son:

1. Dejar la base en verde: arreglar los 2 fallos actuales de tests y fijar comandos de validación reproducibles.
2. Aclarar el mapa del sistema: runtime principal vs laboratorios vs datos efímeros, empezando por `README.md` y rutas de arranque.
3. Cerrar el contrato mínimo de observabilidad para `/chat` y Telegram antes de añadir más features o hablar de cloud.
