# llm_lab/api.py

## Rol

Módulo del laboratorio aislado de evaluación y validación de modelos.

## Identidad técnica

- Ruta real: `llm_lab/api.py`
- Tipo: `llm_lab`
- Ámbito: `laboratorio LLM aislado`
- Módulo lógico: `llm_lab.api`

## Símbolos principales

- Funciones: `rag_query`, `model_proposal`, `model_answer`, `eval_run`, `_proposal_core`, `_answer_core`, `_run_eval_case`, `_check_expectations`, `_query_local_docs`, `_excerpt`, `_build_prompt`, `_write_trace`, `_load_eval_cases`, `_required_string`, `_optional_string`, `_optional_string_or_none`, `_optional_object`, `_bounded_int`, `_latency_ms`

## Dependencias internas directas

- [[python/DB/validator|DB/validator.py]]: importa `validator.validate_answer_output`, `validator.validate_proposal_output`.

## Dependencias inversas

- No se han detectado dependencias internas inversas dentro del inventario analizado.

## Imports externos observados

- Paquetes o módulos externos detectados: `datetime`, `fastapi`, `json`, `model_adapter`, `pathlib`, `re`, `time`, `typing`, `uuid`

## Relación dentro del sistema

- Pertenece a un laboratorio separado del runtime principal de producción local.
- Docstring detectado: `FastAPI entrypoint for the isolated LLM lab.`.

## Observaciones

- Sin observaciones adicionales relevantes a partir del análisis estático actual.

## Relacionado

- [[python/llm_lab/INDEX]]
- [[COMPONENT_MAP]]
- [[GLOSSARY]]
