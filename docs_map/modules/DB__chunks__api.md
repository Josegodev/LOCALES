# MODULO: DB/chunks/api.py

## PROPOSITO
API FastAPI separada para chat documental sobre chunks.

## TRAZABILIDAD
- Archivo real: `DB/chunks/api.py`
- Tamano: 1.6 KB
- Lenguaje detectado: Python
- Parseo AST: OK

## IMPORTS
### Internos
- linea 8: `from document_context import build_document_prompt`
- linea 9: `from lmstudio_client import ask_lmstudio`

### Externos
- linea 1: `from __future__ import annotations`
- linea 5: `from fastapi import FastAPI`
- linea 6: `from pydantic import BaseModel`
- linea 6: `from pydantic import Field`

### Stdlib
- linea 3: `from typing import Any`

### Posibles acoplamientos peligrosos
- Linea 8: import bare `document_context`; acopla al directorio `DB/chunks`.
- Linea 9: import bare `lmstudio_client`; AMBIGUO si se ejecuta desde otro cwd porque hay nombres repetidos en el repo.

## CLASES
### DocumentChatRequest
- Linea: 15
- Bases: `BaseModel`
- Campos / atributos observados:
  - linea 16: `query: str = Field(min_length=1, max_length=1000)`
  - linea 17: `top_k: int = Field(default=3, ge=1, le=10)`
### RetrievedChunk
- Linea: 20
- Bases: `BaseModel`
- Campos / atributos observados:
  - linea 21: `id: int`
  - linea 22: `filename: str`
  - linea 23: `chunk_index: int`
  - linea 24: `char_count: int`
  - linea 25: `score: int | None = None`
### DocumentChatResponse
- Linea: 28
- Bases: `BaseModel`
- Campos / atributos observados:
  - linea 29: `status: str`
  - linea 30: `query: str`
  - linea 31: `chunks: list[RetrievedChunk]`
  - linea 32: `answer: str`

## FUNCIONES
### health()

#### Firma
```python
def health() -> dict[str, str]
```
- Lineas: 36-37
- Decoradores: `app.get('/health')`

#### Responsabilidad observada
Gestiona una superficie HTTP o validacion asociada a endpoint FastAPI, segun decoradores y excepciones observadas.

#### Entradas
- Argumentos declarados: ``

#### Salida
- Anotacion de retorno: `dict[str, str]`

#### Efectos laterales
- sin efectos externos evidentes por lectura estatica

#### Errores / excepciones
- no se observan `raise` directos en esta funcion

#### Determinismo
- DETERMINISTA para las mismas entradas y mismo estado en memoria.

### document_chat()

#### Firma
```python
def document_chat(request: DocumentChatRequest) -> dict[str, Any]
```
- Lineas: 41-73
- Decoradores: `app.post('/document-chat', response_model=DocumentChatResponse)`

#### Responsabilidad observada
Gestiona una superficie HTTP o validacion asociada a endpoint FastAPI, segun decoradores y excepciones observadas.

#### Entradas
- Argumentos declarados: `request: DocumentChatRequest`

#### Salida
- Anotacion de retorno: `dict[str, Any]`

#### Efectos laterales
- sin efectos externos evidentes por lectura estatica

#### Errores / excepciones
- no se observan `raise` directos en esta funcion

#### Determinismo
- NO_DETERMINISTA: depende de red/modelo/servicio externo.

## CONTRATOS Y RIESGOS LOCALES
- No se detectan riesgos locales especificos mas alla de los efectos laterales documentados.
