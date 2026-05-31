# Runtime vault de LOCALES

## Qué representa esta bóveda

Esta bóveda documenta el camino operativo de una petición real desde la UI hasta la respuesta visible para el usuario.

Prioriza:

- actores reales;
- módulos que intervienen en `POST /chat`;
- datos que viajan;
- ramas RAG/no RAG;
- selección `provider/model`;
- observabilidad y persistencia;
- fallos y degradaciones.

No intenta cubrir todo el repo. El foco es el runtime activo de chat.

## Resumen del runtime

El flujo observado hoy es:

`Usuario -> frontend/index.html + frontend/app.js -> frontend/api-client.js -> POST /chat -> FastAPI -> app/api/routes_chat.py -> app/api/runtime_bridge.py -> app/main.py -> ChatService -> app/chat_runtime.py -> RAG opcional -> app/llm_client.py -> adaptador Ollama/OpenAI -> ChatResponse -> app/observability/* -> UI`

El runtime puede:

- validar `ChatRequest`;
- exigir `model` explícito;
- resolver `provider/model`;
- usar RAG local o remoto;
- forzar `safe_refusal` sin evidencia;
- persistir un run aunque la respuesta ya haya salido;
- renderizar la respuesta en la UI con `trace_id`, `retrieval_status` y evidencia.

## Cómo leer esta bóveda

1. [[UI_TO_RESPONSE]]
2. [[POST_CHAT_FLOW]]
3. [[RAG_BRANCH]]
4. [[PROVIDER_BRANCH]]
5. [[ERROR_AND_FALLBACK_FLOW]]
6. [[RUNTIME_GRAPH]]
7. [[CHAT_REQUEST]]
8. [[CHAT_RESPONSE]]
9. [[TELEMETRY]]
10. [[DEBUG_CHAT_FAILURE]]

## Tipos de grafo que aparecen aquí

### Grafo documental

Explica relaciones operativas resumidas para lectura humana.

### Grafo estático

Describe imports y dependencias estructurales.

### Traza runtime observada

Describe una ejecución plausible y verificable del camino `UI -> /chat -> runtime -> respuesta`, apoyada por código y tests.

La diferencia práctica es esta:

- el grafo estático responde “qué puede conectarse”;
- la traza runtime responde “qué camino sigue una petición concreta”.

## Puntos de entrada principales

- [[UI_TO_RESPONSE]]
- [[POST_CHAT_FLOW]]
- [[RUNTIME_GRAPH]]
- [[CHAT_REQUEST]]
- [[CHAT_RESPONSE]]
- [[TELEMETRY]]
- [[DEBUG_CHAT_FAILURE]]

## Alcance y límites

- `frontend/` sí entra en esta bóveda porque inicia el flujo real.
- `DB/` solo entra donde participa directamente en RAG.
- `llm_lab/` queda fuera del camino principal.
- cualquier relación no cerrada se marca como `pendiente de confirmar`.

## Relacionado

- [[UI_TO_RESPONSE]]
- [[POST_CHAT_FLOW]]
- [[RUNTIME_GRAPH]]
- [[CHAT_REQUEST]]
- [[CHAT_RESPONSE]]
- [[TELEMETRY]]
- [[99_GLOSSARY]]
