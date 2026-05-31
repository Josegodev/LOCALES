# scripts/probe_openai_models.py

## Rol

Script operativo o de soporte ejecutable desde CLI.

## Identidad técnica

- Ruta real: `scripts/probe_openai_models.py`
- Tipo: `script`
- Ámbito: `scripts operativos`
- Módulo lógico: `scripts.probe_openai_models`

## Símbolos principales

- Clases: `ProbeResult`
- Funciones: `_require_api_key`, `_build_client`, `_error_type_from_exception`, `_probe_model`, `main`

## Dependencias internas directas

- [[python/app/config|app/config.py]]: importa `app.config.settings`.

## Dependencias inversas

- No se han detectado dependencias internas inversas dentro del inventario analizado.

## Imports externos observados

- Paquetes o módulos externos detectados: `openai`, `pathlib`, `pydantic`, `sys`, `time`

## Relación dentro del sistema

- Se usa como herramienta operativa o de mantenimiento fuera del ciclo HTTP principal.

## Observaciones

- Sin observaciones adicionales relevantes a partir del análisis estático actual.

## Relacionado

- [[python/scripts/INDEX]]
- [[LOCAL_DEPLOYMENT]]
- [[GLOSSARY]]
