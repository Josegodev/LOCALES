# Deuda técnica y riesgos

## Acoplamiento

### Runtime principal demasiado concentrado

- Descripción: `app/chat_runtime.py` combina orquestación, retrieval, fallback, tool, persistencia y logging.
- Evidencia: `app/chat_runtime.py`
- Impacto: dificulta aislar errores y endurecer contratos internos.
- Propuesta mínima de mejora: seguir extrayendo funciones a `app/chat/` sin cambiar `POST /chat`.
- Riesgo de tocarlo: medio-alto.

### Backend principal acoplado a `DB/chunks`

- Descripción: el gateway importa directamente `build_document_prompt` desde `DB.chunks.document_context`.
- Evidencia: `app/main.py`
- Impacto: dificulta sustituir o encapsular retrieval sin tocar el gateway.
- Propuesta mínima de mejora: encapsular la dependencia detrás de una interfaz ya existente en `ChatDependencies`.
- Riesgo de tocarlo: medio.

## Contratos

### Doble familia de endpoints de runs

- Descripción: conviven `/api/chat/runs` y `/api/chat-runs`.
- Evidencia: `app/api/routes_chat_runs.py`, `app/chat_runs/router.py`, `app/main.py`
- Impacto: drift funcional y confusión de frontend/operación.
- Propuesta mínima de mejora: declarar uno como canónico y documentar el otro como compatibilidad.
- Riesgo de tocarlo: medio.

### Drift entre run store y `.env.example`

- Descripción: la configuración de ejemplo usa `CHAT_RUNS_PATH=data/chat_runs.jsonl`, pero la implementación opera con directorios de JSON por archivo.
- Evidencia: `.env.example`, `app/observability/chat_runs.py`
- Impacto: configuración engañosa y carga/persistencia ambiguas.
- Propuesta mínima de mejora: corregir la documentación/config de ejemplo.
- Riesgo de tocarlo: bajo.

## Observabilidad

### Ambigüedad entre runs y traces

- Descripción: existe `chat_trace.py`, pero los endpoints de traces inspeccionados leen runs.
- Evidencia: `app/observability/chat_trace.py`, `app/api/routes_traces.py`, `app/main.py`
- Impacto: confusión en debugging y duplicación de artefactos.
- Propuesta mínima de mejora: definir una fuente canónica y renombrar/documentar la secundaria.
- Riesgo de tocarlo: medio.

### Observabilidad desigual entre proveedores

- Descripción: Ollama expone métricas nativas ricas; OpenAI no las expone igual en el adaptador inspeccionado.
- Evidencia: `app/adapters/ollama_client.py`, `app/adapters/openai_client.py`
- Impacto: comparativas incompletas entre proveedores.
- Propuesta mínima de mejora: persistir explícitamente `observability_level` y documentar diferencias.
- Riesgo de tocarlo: bajo.

## Errores silenciosos

### Fallo de persistencia no rompe la respuesta

- Descripción: si guardar el run falla, el chat puede responder y solo deja un log.
- Evidencia: bloque `finally` en `app/chat_runtime.py`
- Impacto: pérdida de trazabilidad operativa.
- Propuesta mínima de mejora: contador explícito o endpoint de salud de persistencia.
- Riesgo de tocarlo: bajo.

## Seguridad

### Modo `local_open`

- Descripción: `/chat` puede quedar abierto sin token.
- Evidencia: `app/auth.py`, `.env.example`
- Impacto: exposición accidental si se publica el backend.
- Propuesta mínima de mejora: documentar `local_open` como solo desarrollo y endurecer defaults fuera de `local`.
- Riesgo de tocarlo: bajo.

### Servicio RAG remoto expuesto por LAN o más

- Descripción: el servicio remoto escucha en `0.0.0.0` según la documentación existente.
- Evidencia: `docs/remote_rag_service.md`
- Impacto: exposición de corpus/documentos y superficie adicional.
- Propuesta mínima de mejora: limitar bind o firewall y documentarlo como obligatorio.
- Riesgo de tocarlo: bajo.

## Persistencia

### Multiplicidad de artefactos de ejecución

- Descripción: hay `CHAT_RUNS/`, `data/chat_traces.jsonl` y `evals/runs/`.
- Evidencia: árbol del repo y módulos de observabilidad/evals
- Impacto: mayor entropía operativa y riesgo de leer la fuente equivocada.
- Propuesta mínima de mejora: declarar propósito canónico de cada almacén.
- Riesgo de tocarlo: bajo.

## Tests

### Cobertura buena pero con zonas heredadas

- Descripción: hay bastantes tests de contrato, pero siguen coexistiendo rutas y almacenes heredados.
- Evidencia: `tests/`
- Impacto: se puede mantener compatibilidad sin cerrar del todo el diseño.
- Propuesta mínima de mejora: añadir tests que fallen si reaparece drift entre traces, runs y paths.
- Riesgo de tocarlo: bajo.

## Configuración

### Docker depende de volumen para que exista `DB/`

- Descripción: el runtime importa `DB/`, pero `Dockerfile` no lo copia.
- Evidencia: `Dockerfile`, `app/main.py`, `docker-compose.yml`
- Impacto: la imagen aislada puede no ser autoportante.
- Propuesta mínima de mejora: documentar que compose es la vía soportada o copiar lo necesario explícitamente.
- Riesgo de tocarlo: medio.

### Script con ruta absoluta externa

- Descripción: `scripts/ingest_nucleo_md.py` apunta a `/home/jose-gonzalez-oliva/NUCLEO/docs`.
- Evidencia: `scripts/ingest_nucleo_md.py`
- Impacto: baja reproducibilidad fuera de la máquina original.
- Propuesta mínima de mejora: parametrizar la ruta por variable o CLI.
- Riesgo de tocarlo: bajo.

## Coste operacional

### Doble modo de proveedor con observabilidad asimétrica

- Descripción: operar Ollama y OpenAI en el mismo contrato añade complejidad comparativa.
- Evidencia: `app/llm_client.py`, adaptadores
- Impacto: tuning y análisis de calidad/latencia menos homogéneos.
- Propuesta mínima de mejora: comparar por `provider`, no solo por `model`.
- Riesgo de tocarlo: bajo.

## Vendor lock-in

### Dependencia parcial de OpenAI SDK y Ollama HTTP

- Descripción: el sistema ya soporta dos proveedores, lo que reduce lock-in funcional.
- Evidencia: `app/adapters/openai_client.py`, `app/adapters/ollama_client.py`
- Impacto: lock-in moderado, no extremo.
- Propuesta mínima de mejora: mantener el contrato común de `ask_chat(...)`.
- Riesgo de tocarlo: bajo.

## Reproducibilidad

### Frontend estático con `package-lock.json` sin `package.json`

- Descripción: existe lockfile, pero no se detecta manifest completo de Node.
- Evidencia: `frontend/package-lock.json`, ausencia de `frontend/package.json`
- Impacto: dudas sobre el flujo real de build o mantenimiento del frontend.
- Propuesta mínima de mejora: documentar si el frontend es 100% estático y si el lockfile es residual.
- Riesgo de tocarlo: bajo.

## Relacionado

- [[ARCHITECTURE]]
- [[RUNTIME_FLOW]]
- [[OBSERVABILITY]]
- [[AGENTIC_EVOLUTION]]
- [[GLOSSARY]]
