# app/chat_eval_runner.py

## Rol

Archivo Python con clases y funciones de soporte del sistema.

## Identidad técnica

- Ruta real: `app/chat_eval_runner.py`
- Tipo: `backend`
- Ámbito: `backend principal`
- Módulo lógico: `app.chat_eval_runner`

## Símbolos principales

- Clases: `RunnerConfigError`, `BackendUnavailableError`
- Funciones: `_utc_now`, `repo_path`, `load_json_file`, `load_cases`, `load_baseline`, `validate_baseline_case_ids`, `build_case_index`, `build_baseline_index`, `build_chat_payload`, `extract_response_text`, `normalize_chat_result`, `comparison_value`, `preview_text`, `compare_case_result`, `build_backend_error_result`, `summarize_results`, `build_run_filename`, `build_run_payload`, `write_run_file`, `_parse_created_at`
- Funciones adicionales: `6` más.

## Dependencias internas directas

- No se han detectado imports internos directos del repositorio.

## Dependencias inversas

- [[python/app/main|app/main.py]]: depende de este archivo vía `app.chat_eval_runner`.
- [[python/scripts/run_chat_evals|scripts/run_chat_evals.py]]: depende de este archivo vía `app.chat_eval_runner.BackendUnavailableError`, `app.chat_eval_runner.DEFAULT_BASELINE_PATH`, `app.chat_eval_runner.DEFAULT_BASE_URL`, `app.chat_eval_runner.DEFAULT_CASES_PATH`, `app.chat_eval_runner.DEFAULT_OUT_DIR`, `app.chat_eval_runner.DEFAULT_TIMEOUT`, `app.chat_eval_runner.RUN_VERSION`, `app.chat_eval_runner.RunnerConfigError`, `app.chat_eval_runner.build_backend_error_result`, `app.chat_eval_runner.build_baseline_index`, `app.chat_eval_runner.build_case_index`, `app.chat_eval_runner.build_chat_payload`, `app.chat_eval_runner.build_run_filename`, `app.chat_eval_runner.build_run_payload`, `app.chat_eval_runner.compare_case_result`, `app.chat_eval_runner.comparison_value`, `app.chat_eval_runner.extract_response_text`, `app.chat_eval_runner.load_baseline`, `app.chat_eval_runner.load_cases`, `app.chat_eval_runner.load_json_file`, `app.chat_eval_runner.main`, `app.chat_eval_runner.normalize_chat_result`, `app.chat_eval_runner.parse_args`, `app.chat_eval_runner.preview_text`, `app.chat_eval_runner.print_summary`, `app.chat_eval_runner.repo_path`, `app.chat_eval_runner.request_case_result`, `app.chat_eval_runner.run_chat_evals`, `app.chat_eval_runner.summarize_results`, `app.chat_eval_runner.validate_baseline_case_ids`, `app.chat_eval_runner.write_run_file`.

## Imports externos observados

- Paquetes o módulos externos detectados: `argparse`, `datetime`, `json`, `os`, `pathlib`, `requests`, `sys`, `typing`, `uuid`

## Relación dentro del sistema

- Su relación operativa exacta requiere contexto adicional del flujo donde se invoca.

## Observaciones

- Sin observaciones adicionales relevantes a partir del análisis estático actual.

## Relacionado

- [[python/app/INDEX]]
- [[ARCHITECTURE]]
- [[GLOSSARY]]
