# MODULO: llm_lab/model_adapter.py

## PROPOSITO
Frontera entre llm_lab y proveedores mock, Ollama o LM Studio.

## TRAZABILIDAD
- Archivo real: `llm_lab/model_adapter.py`
- Tamano: 11.1 KB
- Lenguaje detectado: Python
- Parseo AST: OK

## IMPORTS
### Internos
- Ninguno detectado.

### Externos
- linea 7: `from __future__ import annotations`

### Stdlib
- linea 9: `json`
- linea 10: `os`
- linea 11: `socket`
- linea 12: `from dataclasses import dataclass`
- linea 13: `from typing import Any`
- linea 14: `from urllib import error`
- linea 14: `from urllib import request`

### Posibles acoplamientos peligrosos
- No se detectan imports ambiguos por nombre repetido.

## CLASES
### AdapterConfig
- Linea: 23
- Bases: `sin base explicita`
- Campos / atributos observados:
  - linea 24: `provider: str`
  - linea 25: `endpoint: str`
  - linea 26: `model_id: str`
### AdapterResult
- Linea: 30
- Bases: `sin base explicita`
- Campos / atributos observados:
  - linea 31: `provider: str`
  - linea 32: `endpoint: str`
  - linea 33: `model_id: str`
  - linea 34: `raw_output: str`
### ModelAdapter
- Linea: 37
- Bases: `sin base explicita`
- Campos / atributos observados:
  - linea 40: `proposal_models = {'mock:proposal', 'mock:invalid_json', 'mock:invalid_schema', 'mock:adapter_error'}`
  - linea 41: `answer_models = {'mock:answer', 'mock:invalid_json', 'mock:invalid_schema', 'mock:adapter_error'}`
- Metodos:
  - linea 43: `def __init__(self, timeout_seconds: int=DEFAULT_TIMEOUT_SECONDS) -> None`
  - linea 46: `def generate_proposal(self, *, prompt: str, model_id: str | None, task: str, context: dict[str, Any]) -> AdapterResult`
  - linea 66: `def generate_answer(self, *, prompt: str, model_id: str | None, question: str, context: dict[str, Any]) -> AdapterResult`
  - linea 86: `def _generate_proposal(self, *, config: AdapterConfig, prompt: str, task: str, context: dict[str, Any]) -> str`
  - linea 137: `def _generate_answer(self, *, config: AdapterConfig, prompt: str, question: str, context: dict[str, Any]) -> str`
  - linea 180: `def _resolve_config(self, *, kind: str, requested_model_id: str | None) -> AdapterConfig`
  - linea 220: `def _call_local_provider(self, *, config: AdapterConfig, prompt: str) -> str`
  - linea 231: `def _call_ollama(self, *, config: AdapterConfig, prompt: str) -> str`
  - linea 247: `def _call_lmstudio(self, *, config: AdapterConfig, prompt: str) -> str`
  - linea 269: `def _post_json(self, *, endpoint: str, payload: dict[str, Any]) -> dict[str, Any]`

## FUNCIONES
### _looks_like_execution()

#### Firma
```python
def _looks_like_execution(text: str) -> bool
```
- Lineas: 300-303

#### Responsabilidad observada
Responsabilidad derivada del nombre y cuerpo; ver efectos laterales y llamadas para detalle exacto.

#### Entradas
- Argumentos declarados: `text: str`

#### Salida
- Anotacion de retorno: `bool`

#### Efectos laterales
- sin efectos externos evidentes por lectura estatica

#### Errores / excepciones
- no se observan `raise` directos en esta funcion

#### Determinismo
- DETERMINISTA para las mismas entradas y mismo estado en memoria.

### _adapter_error()

#### Firma
```python
def _adapter_error(exc: Exception) -> str
```
- Lineas: 306-313

#### Responsabilidad observada
Responsabilidad derivada del nombre y cuerpo; ver efectos laterales y llamadas para detalle exacto.

#### Entradas
- Argumentos declarados: `exc: Exception`

#### Salida
- Anotacion de retorno: `str`

#### Efectos laterales
- sin efectos externos evidentes por lectura estatica

#### Errores / excepciones
- no se observan `raise` directos en esta funcion

#### Determinismo
- DETERMINISTA para las mismas entradas y mismo estado en memoria.

## CONTRATOS Y RIESGOS LOCALES
- INFORMATIVO: depende de servicios HTTP externos/locales y de timeouts.
