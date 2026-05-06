# MODULO: app/schemas.py

## PROPOSITO
Contratos Pydantic HTTP de la app productiva.

## TRAZABILIDAD
- Archivo real: `app/schemas.py`
- Tamano: 1008 B
- Lenguaje detectado: Python
- Parseo AST: OK

## IMPORTS
### Internos
- Ninguno detectado.

### Externos
- linea 1: `from pydantic import BaseModel`
- linea 1: `from pydantic import Field`

### Stdlib
- Ninguno detectado.

### Posibles acoplamientos peligrosos
- No se detectan imports ambiguos por nombre repetido.

## CLASES
### ChatRequest
- Linea: 4
- Bases: `BaseModel`
- Campos / atributos observados:
  - linea 5: `message: str = Field(min_length=1, max_length=4000)`
  - linea 6: `model: str | None = None`
  - linea 7: `max_tokens: int | None = Field(default=None, ge=1, le=2048)`
  - linea 8: `temperature: float | None = Field(default=None, ge=0.0, le=2.0)`
  - linea 9: `top_k: int | None = Field(default=3, ge=1, le=10)`
### ChatResponse
- Linea: 11
- Bases: `BaseModel`
- Campos / atributos observados:
  - linea 12: `status: str`
  - linea 13: `model: str`
  - linea 14: `answer: str`
  - linea 15: `latency_ms: int`
### ErrorResponse
- Linea: 17
- Bases: `BaseModel`
- Campos / atributos observados:
  - linea 18: `status: str`
  - linea 19: `code: str`
  - linea 20: `message: str`
### DocumentCreateRequest
- Linea: 22
- Bases: `BaseModel`
- Campos / atributos observados:
  - linea 23: `filename: str = Field(min_length=1, max_length=120)`
  - linea 24: `content: str = Field(default='', max_length=50000)`
  - linea 25: `overwrite: bool = False`
### DocumentCreateResponse
- Linea: 27
- Bases: `BaseModel`
- Campos / atributos observados:
  - linea 28: `status: str`
  - linea 29: `filename: str`
  - linea 30: `path: str`
  - linea 31: `chars: int`
  - linea 32: `created_at: str`
### DocumentCreateRequest
- Linea: 34
- Bases: `BaseModel`
- Campos / atributos observados:
  - linea 35: `filename: str = Field(min_length=1, max_length=120)`
  - linea 36: `content: str = Field(default='', max_length=50000)`
  - linea 37: `overwrite: bool = False`

## FUNCIONES
- Ninguna funcion de nivel modulo.
## CONTRATOS Y RIESGOS LOCALES
- CRITICO: `DocumentCreateRequest` esta definido dos veces; la segunda definicion pisa la primera en Python.
- INFORMATIVO: `ChatResponse` no incluye campos que `app/main.py` intenta anadir (`retrieval_status`, `chunks`).
