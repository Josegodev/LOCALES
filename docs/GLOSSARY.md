# Glosario práctico

## `runtime`

Pieza que ejecuta el trabajo real de una petición. En este repo, el runtime principal de chat vive sobre todo en `app/chat_runtime.py`.

## `orchestrator`

Código que coordina pasos distintos: validación, retrieval, llamada al modelo, fallback y persistencia. Aquí el orquestador actual es, de hecho, gran parte del runtime.

## `RAG`

Siglas de Retrieval-Augmented Generation. Significa: antes de responder, el sistema busca documentos o fragmentos relevantes para dar una respuesta más fundamentada.

## `chunk`

Fragmento de un documento más grande. Se usa porque es más práctico recuperar partes pequeñas que documentos completos.

## `retrieval_status`

Campo que indica qué pasó en la fase de recuperación documental. Ejemplos observados: `EVIDENCE_FOUND`, `NO_EVIDENCE_FOR_ANSWER`, `DISABLED`.

## `trace_id`

Identificador único de una ejecución. Sirve para seguir un mismo chat en logs, runs y respuestas.

## `provider`

Proveedor del modelo. En este repo puede ser `ollama` o `openai`.

## `model`

Nombre concreto del modelo usado por el proveedor, por ejemplo `granite4.1:8b` o `gpt-5.5`.

## `fallback`

Camino alternativo cuando el flujo normal no puede completarse bien. Aquí suele significar una negativa segura o una degradación controlada.

## `tool call`

Invocación de una herramienta desde el runtime. En este repo la tool visible es la creación de documentos Markdown con `/creardoc`.

## `planner`

Componente que decide una secuencia de pasos para alcanzar un objetivo. No existe todavía como pieza explícita en el backend principal.

## `policy engine`

Componente que decide qué está permitido o prohibido. Tampoco existe todavía como módulo explícito en el runtime principal.

## `agent`

Sistema que no solo responde texto, sino que puede planificar, usar herramientas, consultar memoria y seguir políticas. Este repo aún no es eso de forma estructurada.

## `eval`

Evaluación automática o semiautomática para comprobar si el sistema respeta ciertos contratos. Aquí se usan casos, baseline y runs de evaluación.

## `structured logging`

Forma de loguear en JSON o con campos fijos, para que luego sea más fácil buscar errores, tiempos o trazas.

## `latency`

Tiempo que tarda una operación. En este repo suele aparecer como `latency_ms`, es decir, milisegundos.

## `tokens`

Unidades pequeñas de texto que usan los modelos para medir entrada y salida. No siempre equivalen a palabras completas.

## `local model`

Modelo servido en la máquina o red local, por ejemplo mediante `Ollama` o `LM Studio`.

## `managed API`

Proveedor externo que ofrece el modelo como servicio remoto, por ejemplo OpenAI.

## `safe refusal`

Respuesta segura que evita inventar cuando no hay evidencia documental suficiente.

## `evidence_used`

Bandera que indica si la respuesta realmente se apoyó en evidencia documental.

## `answer_mode`

Campo que clasifica el tipo de respuesta final. Ejemplos observados: `documentary_answer`, `safe_refusal`, `standard_answer`.

## `allowlist`

Lista explícita de elementos permitidos. En retrieval aparece como `allowed_source_filenames`, para limitar la búsqueda a ciertos archivos.

## `active document`

Documento que el usuario o el frontend marca como contexto principal. Sirve para orientar búsquedas ambiguas hacia una fuente concreta.

## `observability`

Capacidad de entender qué hizo el sistema, cuánto tardó y por qué falló. Incluye logs, métricas, traces y runs.

## `drift`

Diferencia no deseada entre dos sitios que deberían contar la misma historia. Ejemplo: dos endpoints parecidos, dos almacenes de runs o dos contratos que divergen.

## Relacionado

- [[README]]
- [[ARCHITECTURE]]
- [[RUNTIME_FLOW]]
