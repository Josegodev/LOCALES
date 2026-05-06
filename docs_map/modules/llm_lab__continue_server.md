# MODULO: llm_lab/continue_server.py

## PROPOSITO
Adaptador OpenAI-compatible minimo para Continue hacia llm_lab.

## TRAZABILIDAD
- Archivo real: `llm_lab/continue_server.py`
- Tamano: 1.4 KB
- Lenguaje detectado: Python
- Parseo AST: OK

## IMPORTS
### Internos
- Ninguno detectado.

### Externos
- linea 1: `from __future__ import annotations`
- linea 3: `from fastapi import FastAPI`
- linea 4: `from pydantic import BaseModel`
- linea 4: `from pydantic import Field`

### Stdlib
- linea 5: `from typing import Any`

### Posibles acoplamientos peligrosos
- No se detectan imports ambiguos por nombre repetido.

## CLASES
### ChatMessage
- Linea: 11
- Bases: `BaseModel`
- Campos / atributos observados:
  - linea 12: `role: str`
  - linea 13: `content: str`
### ChatCompletionRequest
- Linea: 16
- Bases: `BaseModel`
- Campos / atributos observados:
  - linea 17: `model: str = 'nucleo-lab'`
  - linea 18: `messages: list[ChatMessage]`
  - linea 19: `temperature: float | None = None`
  - linea 20: `max_tokens: int | None = None`
  - linea 21: `stream: bool = False`

## FUNCIONES
### chat_completions()

#### Firma
```python
def chat_completions(req: ChatCompletionRequest) -> dict[str, Any]
```
- Lineas: 25-60
- Decoradores: `app.post('/v1/chat/completions')`

#### Responsabilidad observada
Gestiona una superficie HTTP o validacion asociada a endpoint FastAPI, segun decoradores y excepciones observadas.

#### Entradas
- Argumentos declarados: `req: ChatCompletionRequest`

#### Salida
- Anotacion de retorno: `dict[str, Any]`

#### Efectos laterales
- sin efectos externos evidentes por lectura estatica

#### Errores / excepciones
- no se observan `raise` directos en esta funcion

#### Determinismo
- DETERMINISTA para las mismas entradas y mismo estado en memoria.

## CONTRATOS Y RIESGOS LOCALES
- No se detectan riesgos locales especificos mas alla de los efectos laterales documentados.
