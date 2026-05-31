# app/testclient_compat.py

## Rol

Archivo Python con clases y funciones de soporte del sistema.

## Identidad técnica

- Ruta real: `app/testclient_compat.py`
- Tipo: `backend`
- Ámbito: `backend principal`
- Módulo lógico: `app.testclient_compat`

## Símbolos principales

- Clases: `_CompatTaskStatus`, `_CompatBlockingPortal`
- Funciones: `_compat_start_blocking_portal`, `_should_patch_blocking_portal`, `apply_blocking_portal_compat_patch`

## Dependencias internas directas

- No se han detectado imports internos directos del repositorio.

## Dependencias inversas

- [[python/app/main|app/main.py]]: depende de este archivo vía `app.testclient_compat.apply_blocking_portal_compat_patch`.

## Imports externos observados

- Paquetes o módulos externos detectados: `anyio`, `asyncio`, `concurrent`, `contextlib`, `importlib`, `inspect`, `sys`, `threading`

## Relación dentro del sistema

- Su relación operativa exacta requiere contexto adicional del flujo donde se invoca.

## Observaciones

- Sin observaciones adicionales relevantes a partir del análisis estático actual.

## Relacionado

- [[python/app/INDEX]]
- [[ARCHITECTURE]]
- [[GLOSSARY]]
