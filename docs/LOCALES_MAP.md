# LOCALES Map

## 1. Resumen de LOCALES

LOCALES es un sistema local de IA/LLMOps centrado en un backend `FastAPI` con contrato principal `POST /chat`.
El runtime actual coordina validación, selección de proveedor/modelo, retrieval documental, generación, fallback y persistencia de runs.
El sistema soporta RAG local sobre SQLite y RAG remoto por HTTP, con evidencia trazable en `chunk_ids`, `document_ids` y `source_filenames`.
La observabilidad actual es local: logs JSON, `trace_id`, runs persistidos y métricas operativas derivadas.
El frontend detectado es estático y consume el backend por HTTP.
También conviven dos subespacios auxiliares: `DB/` como laboratorio SQLite separado y `llm_lab/` como laboratorio experimental aislado.
El estado observado del repo es de hardening: cierre de contratos, reducción de drift, mejora de determinismo y manejo de errores.

## 2. Mapa de lectura recomendado

1. [[README]]
2. [[ARCHITECTURE]]
3. [[COMPONENT_MAP]]
4. [[RUNTIME_FLOW]]
5. [[RAG_AND_EVIDENCE]]
6. [[OBSERVABILITY]]
7. [[LOCAL_DEPLOYMENT]]
8. [[TECH_DEBT_AND_RISKS]]
9. [[AGENTIC_EVOLUTION]]
10. [[python/INDEX]]
11. [[GLOSSARY]]

Lecturas de apoyo:

- [[INDEX]]
- [[remote_rag_service]]
- [[contracts/chat_runtime_refactor_contract|contracts/chat_runtime_refactor_contract.md]]

Pendiente:

- Runbook específico de incidentes operativos: pendiente
- Documento específico de auth/CORS para operación local y exposición remota: pendiente

## 3. Tabla de componentes principales

| Componente | Ruta o documento guía | Responsabilidad operativa |
| --- | --- | --- |
| Gateway backend | [[ARCHITECTURE]] | Expone `POST /chat` y endpoints de inspección. |
| Runtime de chat | [[RUNTIME_FLOW]] | Ejecuta validación, retrieval, generación, fallback y persistencia. |
| Mapa de componentes | [[COMPONENT_MAP]] | Resume módulos, scripts, datos y acoplamientos. |
| RAG y evidencia | [[RAG_AND_EVIDENCE]] | Describe corpus, retrieval, contratos de evidencia y riesgos de contaminación. |
| Observabilidad | [[OBSERVABILITY]] | Resume logs, runs, métricas y huecos de trazabilidad. |
| Despliegue local | [[LOCAL_DEPLOYMENT]] | Explica arranque local, variables, puertos y riesgos de despliegue. |
| Riesgos y deuda | [[TECH_DEBT_AND_RISKS]] | Centraliza drift, deuda técnica y riesgos operativos. |
| Evolución futura | [[AGENTIC_EVOLUTION]] | Define una evolución incremental hacia un sistema agentic sin romper el estado actual. |
| Código por archivo | [[python/INDEX]] | Permite navegar archivo por archivo siguiendo dependencias reales. |
| Glosario | [[GLOSSARY]] | Aclara vocabulario operativo y conceptos del sistema. |

## 4. Flujo operativo de una petición

Flujo principal observado:

`usuario/frontend -> FastAPI -> runtime de chat -> retrieval opcional -> proveedor LLM -> respuesta -> persistencia/logs/evals`

Orden de lectura para entenderlo:

1. [[ARCHITECTURE]]
2. [[RUNTIME_FLOW]]
3. [[RAG_AND_EVIDENCE]]
4. [[OBSERVABILITY]]

Resumen operativo:

- entra un `ChatRequest`;
- se valida payload y contrato mínimo;
- se resuelve `provider/model`;
- si procede, se ejecuta retrieval local o remoto;
- si no hay evidencia suficiente, se responde con safe refusal;
- si hay evidencia o el flujo no es documental, se llama al proveedor LLM;
- se construye `ChatResponse`;
- se intenta persistir el run y emitir logs finales.

## 5. Superficie de fallo

Fallos relevantes a vigilar:

- payload inválido;
- `model` ausente;
- par `provider/model` incoherente;
- proveedor no disponible;
- timeout de proveedor;
- RAG remoto no disponible;
- RAG local sin evidencia suficiente;
- respuesta documental sin evidencia usable;
- persistencia de run fallida;
- configuración ambigua de runs/traces;
- CORS o auth mal configurados.

Documentos para analizar esta superficie:

- [[RUNTIME_FLOW]]
- [[OBSERVABILITY]]
- [[TECH_DEBT_AND_RISKS]]
- [[LOCAL_DEPLOYMENT]]

## 6. Observabilidad mínima

Señales mínimas hoy disponibles:

- `trace_id`
- `status`
- `provider`
- `model`
- `temperature`
- `retrieval_status`
- `fallback_used`
- `chunk_ids`
- `source_filenames`
- `latency_ms`
- runs persistidos
- logs JSON estructurados

Para profundizar:

- [[OBSERVABILITY]]
- [[RUNTIME_FLOW]]
- [[TECH_DEBT_AND_RISKS]]

Incertidumbres:

- la frontera exacta entre “run” y “trace” no está completamente consolidada;
- la observabilidad de OpenAI es más pobre que la de Ollama en el código inspeccionado.

## 7. Evolución hacia sistema agentic

Ruta recomendada:

1. endurecer monolito instrumentado;
2. explicitar runtime;
3. introducir tools controladas;
4. añadir planner limitado y auditable;
5. separar planner/policy/tools/memory/evaluator cuando el sistema ya sea observable.

Documento guía:

- [[AGENTIC_EVOLUTION]]

Soporte contextual:

- [[ARCHITECTURE]]
- [[RUNTIME_FLOW]]
- [[TECH_DEBT_AND_RISKS]]

## 8. Preguntas de debugging

Cuando algo falla, empezar por estas preguntas:

1. ¿El problema ocurre antes de entrar en `POST /chat` o dentro del runtime?
2. ¿Hay `trace_id` y run persistido?
3. ¿El fallo es de contrato HTTP, de provider/model o de retrieval?
4. ¿El `retrieval_status` es coherente con la respuesta final?
5. ¿La evidencia está realmente poblada en `chunk_ids` o `source_filenames`?
6. ¿El proveedor devolvió métricas nativas o solo latencia general?
7. ¿La configuración local coincide con el almacén real de runs?
8. ¿El despliegue activo usa RAG local o remoto?
9. ¿El comportamiento observado coincide con los riesgos ya descritos?

Documentos de apoyo para debugging:

- [[RUNTIME_FLOW]]
- [[RAG_AND_EVIDENCE]]
- [[OBSERVABILITY]]
- [[LOCAL_DEPLOYMENT]]
- [[TECH_DEBT_AND_RISKS]]
- [[python/INDEX]]

## 9. Enlaces relacionados

- [[README]]
- [[INDEX]]
- [[ARCHITECTURE]]
- [[COMPONENT_MAP]]
- [[RUNTIME_FLOW]]
- [[RAG_AND_EVIDENCE]]
- [[OBSERVABILITY]]
- [[LOCAL_DEPLOYMENT]]
- [[TECH_DEBT_AND_RISKS]]
- [[AGENTIC_EVOLUTION]]
- [[python/INDEX]]
- [[GLOSSARY]]

## Relacionado

- [[README]]
- [[ARCHITECTURE]]
- [[RUNTIME_FLOW]]
- [[TECH_DEBT_AND_RISKS]]
- [[GLOSSARY]]
