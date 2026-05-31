# LOCALES Technical Docs

## Alcance

`LOCALES` es un sistema local de IA/LLMOps centrado en un gateway de chat con `FastAPI`, selección de proveedor/modelo, RAG local o remoto, persistencia de runs y un frontend estático para operación local.

Esta documentación:

- se ha generado a partir de archivos existentes en el repositorio;
- describe estado técnico y operativo;
- no es documentación comercial ni promesa de roadmap cerrado;
- marca como `pendiente de confirmar` lo que no queda totalmente probado por código o archivos del repo.

## Mapa operativo

Para navegar el sistema desde una perspectiva práctica de arquitectura, runtime, RAG, observabilidad, riesgos y evolución agentic, empieza por [[LOCALES_MAP]].

## Cómo leer esta documentación

Orden recomendado:

1. [[ARCHITECTURE]]
2. [[COMPONENT_MAP]]
3. [[RUNTIME_FLOW]]
4. [[RAG_AND_EVIDENCE]]
5. [[OBSERVABILITY]]
6. [[python/INDEX|python/INDEX.md]]
7. [[TECH_DEBT_AND_RISKS]]
8. [[LOCAL_DEPLOYMENT]]
9. [[AGENTIC_EVOLUTION]]
10. [[GLOSSARY]]

## Mapa de documentos

- [[ARCHITECTURE]]: arquitectura actual, contratos, endpoints y acoplamientos.
- [[COMPONENT_MAP]]: inventario operativo de carpetas, módulos y scripts.
- [[RUNTIME_FLOW]]: recorrido real de una petición `POST /chat`.
- [[RAG_AND_EVIDENCE]]: recuperación documental, evidencia y riesgos de drift.
- [[OBSERVABILITY]]: logs, runs, métricas y huecos de trazabilidad.
- [[python/INDEX|python/INDEX.md]]: espejo documental de los archivos Python del repo, con un `.md` por archivo y enlaces por dependencias reales.
- [[AGENTIC_EVOLUTION]]: evolución incremental hacia un sistema agentic sin humo.
- [[LOCAL_DEPLOYMENT]]: despliegue local observado en el repo.
- [[TECH_DEBT_AND_RISKS]]: deuda técnica y riesgos operativos detectables.
- [[GLOSSARY]]: glosario práctico para mantenimiento.
- [[INDEX]]: índice navegable resumido.

## Documentación complementaria existente

Estos documentos ya estaban en el repo y pueden aportar contexto adicional:

- [[remote_rag_service]]
- [[cloudflare_vercel_demo]]
- [[contracts/chat_runtime_refactor_contract|contracts/chat_runtime_refactor_contract.md]]

## Advertencias importantes

- El backend actual conserva una zona central monolítica en `app/chat_runtime.py`.
- Existen rutas y artefactos de observabilidad parcialmente solapados.
- `DB/` y `llm_lab/` existen en el mismo repo, pero no equivalen al runtime principal de `POST /chat`.

## Relacionado

- [[ARCHITECTURE]]
- [[INDEX]]
- [[python/INDEX]]
- [[GLOSSARY]]
