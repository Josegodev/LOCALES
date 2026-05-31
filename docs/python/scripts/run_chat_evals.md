# scripts/run_chat_evals.py

## Rol

Script operativo o de soporte ejecutable desde CLI.

## Identidad técnica

- Ruta real: `scripts/run_chat_evals.py`
- Tipo: `script`
- Ámbito: `scripts operativos`
- Módulo lógico: `scripts.run_chat_evals`

## Símbolos principales

- No expone clases o funciones top-level; puede actuar como paquete o marcador.

## Dependencias internas directas

- [[python/app/chat_eval_runner|app/chat_eval_runner.py]]: importa `app.chat_eval_runner.BackendUnavailableError`, `app.chat_eval_runner.DEFAULT_BASELINE_PATH`, `app.chat_eval_runner.DEFAULT_BASE_URL`, `app.chat_eval_runner.DEFAULT_CASES_PATH`, `app.chat_eval_runner.DEFAULT_OUT_DIR`, `app.chat_eval_runner.DEFAULT_TIMEOUT`, `app.chat_eval_runner.RUN_VERSION`, `app.chat_eval_runner.RunnerConfigError`, `app.chat_eval_runner.build_backend_error_result`, `app.chat_eval_runner.build_baseline_index`, `app.chat_eval_runner.build_case_index`, `app.chat_eval_runner.build_chat_payload`, `app.chat_eval_runner.build_run_filename`, `app.chat_eval_runner.build_run_payload`, `app.chat_eval_runner.compare_case_result`, `app.chat_eval_runner.comparison_value`, `app.chat_eval_runner.extract_response_text`, `app.chat_eval_runner.load_baseline`, `app.chat_eval_runner.load_cases`, `app.chat_eval_runner.load_json_file`, `app.chat_eval_runner.main`, `app.chat_eval_runner.normalize_chat_result`, `app.chat_eval_runner.parse_args`, `app.chat_eval_runner.preview_text`, `app.chat_eval_runner.print_summary`, `app.chat_eval_runner.repo_path`, `app.chat_eval_runner.request_case_result`, `app.chat_eval_runner.run_chat_evals`, `app.chat_eval_runner.summarize_results`, `app.chat_eval_runner.validate_baseline_case_ids`, `app.chat_eval_runner.write_run_file`.

## Dependencias inversas

- No se han detectado dependencias internas inversas dentro del inventario analizado.

## Imports externos observados

- No se han detectado imports externos explícitos.

## Relación dentro del sistema

- Se usa como herramienta operativa o de mantenimiento fuera del ciclo HTTP principal.

## Observaciones

- Sin observaciones adicionales relevantes a partir del análisis estático actual.

## Relacionado

- [[python/scripts/INDEX]]
- [[LOCAL_DEPLOYMENT]]
- [[GLOSSARY]]
