# app/chat/dependencies.py

## Ruta real

`app/chat/dependencies.py`

## Responsabilidad observada

Define el paquete de dependencias inyectables del runtime.

## Clases principales

- `ChatDependencies`

## Quién lo llama

- `app/main.py`
- `app/chat/service.py`
- tests con inyección explícita

## A quién llama

- no llama; define contrato de inyección

## Entradas

- funciones de chat, retrieval, persistencia, logging y settings

## Salidas

- objeto `ChatDependencies`

## Efectos secundarios

- permite sustituir caminos en tests

## Riesgos

- coexistencia con imports legacy directos en `app/chat_runtime.py`

## Relacionado

- [[CHAT_SERVICE]]
- [[CHAT_RUNTIME]]
- [[PROVIDER_MODEL]]
