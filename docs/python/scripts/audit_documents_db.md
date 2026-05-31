# scripts/audit_documents_db.py

## Rol

Script operativo o de soporte ejecutable desde CLI.

## Identidad técnica

- Ruta real: `scripts/audit_documents_db.py`
- Tipo: `script`
- Ámbito: `scripts operativos`
- Módulo lógico: `scripts.audit_documents_db`

## Símbolos principales

- Funciones: `_count_rows`, `audit_documents_db`

## Dependencias internas directas

- [[python/app/config|app/config.py]]: importa `app.config.settings`.

## Dependencias inversas

- [[python/rag_service/main|rag_service/main.py]]: depende de este archivo vía `scripts.audit_documents_db.audit_documents_db`.

## Imports externos observados

- Paquetes o módulos externos detectados: `json`, `pathlib`, `sqlite3`

## Relación dentro del sistema

- Se usa como herramienta operativa o de mantenimiento fuera del ciclo HTTP principal.

## Observaciones

- Sin observaciones adicionales relevantes a partir del análisis estático actual.

## Relacionado

- [[python/scripts/INDEX]]
- [[LOCAL_DEPLOYMENT]]
- [[GLOSSARY]]
