# Runtime Graph

## Qué representa

`runtime_graph.json` es un grafo estático y operativo del camino principal de ejecución de LOCALES.

Representa solo relaciones con evidencia suficiente entre:

- entrada operativa `frontend/`;
- endpoint `POST /chat`;
- cadena HTTP `routes_chat -> runtime_bridge -> app.main`;
- fachada `ChatService` y `ChatDependencies`;
- runtime central `app/chat_runtime.py`;
- dispatch a proveedores LLM;
- RAG local y RAG remoto;
- observabilidad mínima (`trace_id`, logs, runs persistidos);
- flujo especial `/creardoc`.

La idea es simple: responder a la pregunta “si entra una petición por `/chat`, ¿qué piezas reales del repo pueden intervenir después?”.

## Qué no representa

Este grafo no intenta representar todo el repositorio.

Quedan fuera a propósito:

- tests;
- rutas de métricas y listados que no participan en el camino principal de `POST /chat`;
- laboratorios `DB/` ajenos al runtime principal;
- `llm_lab/`;
- relaciones dudosas o solo sugeridas por nombres;
- rutas legacy o con drift si no aparecen como camino activo del runtime.

Ejemplo importante:

- `app/observability/chat_trace.py` existe, pero no se ha modelado como camino activo del runtime porque la documentación principal apunta hoy a `app/observability/chat_runs.py` como almacén operativo canónico de runs, y `[[OBSERVABILITY]]` marca riesgo de drift entre ambos.

## Grafo estático vs trazas runtime

Hay dos niveles que conviene no mezclar:

### Grafo estático

Describe dependencias y llamadas posibles observadas en código y documentación:

- imports;
- funciones llamadas;
- endpoints servidos;
- almacenes leídos o escritos.

Sirve para entender arquitectura, acoplamiento y superficie de fallo.

### Trazas runtime

Describen lo que ocurrió en una ejecución concreta:

- `trace_id`;
- proveedor y modelo elegidos;
- si hubo RAG local o remoto;
- latencias;
- evidencia recuperada;
- warnings;
- estado final del run.

Sirven para debugging y observabilidad de una petición real.

Conclusión práctica:

- el grafo responde “qué puede pasar”;
- la traza responde “qué pasó esta vez”.

## Riesgos de inferencia incorrecta

Hay varios puntos donde conviene ser riguroso:

1. `app/chat_runtime.py` admite inyección mediante `ChatDependencies`, así que el grafo refleja el camino por defecto, no todas las sustituciones posibles.
2. `app/api/runtime_bridge.py` usa import dinámico hacia `app.main`, así que esa arista es real pero menos explícita que un `import` normal.
3. El cambio entre RAG local y remoto depende de `settings.use_remote_rag`; por eso ambas ramas existen en el grafo aunque no se activen a la vez.
4. La documentación de arquitectura menciona componentes como `app/chat/retrieval.py`, pero el camino activo documentado del runtime actual muestra llamadas directas desde `app/chat_runtime.py` a `DB/chunks/document_context.py` y `app/rag_client.py`. Para evitar inventar relaciones, el JSON prioriza esa evidencia activa.
5. Los nodos `documents.sqlite`, `CHAT_RUNS/` y `outputs/documents/` se representan como almacenes operativos observados, no como contrato formal versionado.

## Cómo validarlo

Valídalo por capas, de menor a mayor:

### 1. Imports documentados

Revisa los `.md` espejo en `docs/python/`:

- `docs/python/app/chat_runtime.md:1`
- `docs/python/app/llm_client.md:1`
- `docs/python/app/rag_client.md:1`
- `docs/python/app/observability/chat_runs.md:1`
- `docs/python/DB/chunks/document_context.md:1`
- `docs/python/rag_service/main.md:1`

Ahí están las dependencias internas directas usadas como base de las aristas `imports`.

### 2. Llamadas reales

Confirma las aristas `calls` con búsquedas puntuales:

- `app/api/routes_chat.py:11`
- `app/api/runtime_bridge.py:4`
- `app/main.py:124`
- `app/chat/service.py:12`
- `app/chat_runtime.py:655`
- `app/rag_client.py:53`
- `rag_service/main.py:118`
- `app/tools/create_document.py:182`

Esas ubicaciones contienen las llamadas clave usadas en el grafo.

### 3. Logs y artefactos

Contrasta el grafo con las señales reales:

- logs JSON emitidos por `app/observability/logging.py`;
- runs persistidos en `CHAT_RUNS/`;
- respuesta pública con `trace_id`, `retrieval_status`, `provider`, `model` y evidencia.

Si una arista aparece en el grafo pero nunca deja rastro operativo, probablemente hay drift o una rama muerta.

### 4. Tests útiles

Sin tocar tests, los más útiles para contrastar este grafo son:

- `tests/test_chat_only_runtime.py`
- `tests/test_chat_service.py`
- `tests/test_provider_model_resolution.py`
- `tests/test_remote_rag_service.py`
- `tests/test_chat_runs_contract.py`

No prueban todo el grafo, pero sí validan varios contratos centrales.

## Lectura recomendada después

Si quieres entender mejor cada zona del grafo, sigue este orden:

1. [[RUNTIME_FLOW]]
2. [[ARCHITECTURE]]
3. [[RAG_AND_EVIDENCE]]
4. [[OBSERVABILITY]]
5. [[TECH_DEBT_AND_RISKS]]

## Relacionado

- [[LOCALES_MAP]]
- [[RUNTIME_FLOW]]
- [[ARCHITECTURE]]
- [[RAG_AND_EVIDENCE]]
- [[OBSERVABILITY]]
- [[TECH_DEBT_AND_RISKS]]
- [[GLOSSARY]]
