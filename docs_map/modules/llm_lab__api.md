# MODULO: llm_lab/api.py

## PROPOSITO
FastAPI de laboratorio aislado para RAG local, propuestas, respuestas y evaluacion con trazas.

## TRAZABILIDAD
- Archivo real: `llm_lab/api.py`
- Tamano: 12.6 KB
- Lenguaje detectado: Python
- Parseo AST: OK

## IMPORTS
### Internos
- linea 15: `from .model_adapter import ModelAdapter`
- linea 16: `from .validator import validate_answer_output`
- linea 16: `from .validator import validate_proposal_output`

### Externos
- linea 3: `from __future__ import annotations`
- linea 13: `from fastapi import FastAPI`
- linea 13: `from fastapi import HTTPException`

### Stdlib
- linea 5: `json`
- linea 6: `re`
- linea 7: `time`
- linea 8: `uuid`
- linea 9: `from datetime import datetime`
- linea 9: `from datetime import timezone`
- linea 10: `from pathlib import Path`
- linea 11: `from typing import Any`

### Posibles acoplamientos peligrosos
- Linea 16: import bare `validator`; AMBIGUO si se ejecuta desde otro cwd porque hay nombres repetidos en el repo.
- Linea 16: import bare `validator`; AMBIGUO si se ejecuta desde otro cwd porque hay nombres repetidos en el repo.

## CLASES
- Ninguna clase definida.

## FUNCIONES
### rag_query()

#### Firma
```python
def rag_query(payload: dict[str, Any]) -> dict[str, Any]
```
- Lineas: 28-49
- Decoradores: `app.post('/rag/query')`

#### Responsabilidad observada
Gestiona una superficie HTTP o validacion asociada a endpoint FastAPI, segun decoradores y excepciones observadas.

#### Entradas
- Argumentos declarados: `payload: dict[str, Any]`

#### Salida
- Anotacion de retorno: `dict[str, Any]`

#### Efectos laterales
- sin efectos externos evidentes por lectura estatica

#### Errores / excepciones
- no se observan `raise` directos en esta funcion

#### Determinismo
- PARCIAL: incluye tiempo, UUID o latencia.

### model_proposal()

#### Firma
```python
def model_proposal(payload: dict[str, Any]) -> dict[str, Any]
```
- Lineas: 53-57
- Decoradores: `app.post('/model/proposal')`

#### Responsabilidad observada
Gestiona una superficie HTTP o validacion asociada a endpoint FastAPI, segun decoradores y excepciones observadas.

#### Entradas
- Argumentos declarados: `payload: dict[str, Any]`

#### Salida
- Anotacion de retorno: `dict[str, Any]`

#### Efectos laterales
- sin efectos externos evidentes por lectura estatica

#### Errores / excepciones
- no se observan `raise` directos en esta funcion

#### Determinismo
- PARCIAL: incluye tiempo, UUID o latencia.

### model_answer()

#### Firma
```python
def model_answer(payload: dict[str, Any]) -> dict[str, Any]
```
- Lineas: 61-65
- Decoradores: `app.post('/model/answer')`

#### Responsabilidad observada
Gestiona una superficie HTTP o validacion asociada a endpoint FastAPI, segun decoradores y excepciones observadas.

#### Entradas
- Argumentos declarados: `payload: dict[str, Any]`

#### Salida
- Anotacion de retorno: `dict[str, Any]`

#### Efectos laterales
- sin efectos externos evidentes por lectura estatica

#### Errores / excepciones
- no se observan `raise` directos en esta funcion

#### Determinismo
- PARCIAL: incluye tiempo, UUID o latencia.

### eval_run()

#### Firma
```python
def eval_run(payload: dict[str, Any] | None=None) -> dict[str, Any]
```
- Lineas: 69-99
- Decoradores: `app.post('/eval/run')`

#### Responsabilidad observada
Gestiona una superficie HTTP o validacion asociada a endpoint FastAPI, segun decoradores y excepciones observadas.

#### Entradas
- Argumentos declarados: `payload: dict[str, Any] | None=None`

#### Salida
- Anotacion de retorno: `dict[str, Any]`

#### Efectos laterales
- sin efectos externos evidentes por lectura estatica

#### Errores / excepciones
- no se observan `raise` directos en esta funcion

#### Determinismo
- PARCIAL: incluye tiempo, UUID o latencia.

### _proposal_core()

#### Firma
```python
def _proposal_core(payload: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]
```
- Lineas: 102-133

#### Responsabilidad observada
Responsabilidad derivada del nombre y cuerpo; ver efectos laterales y llamadas para detalle exacto.

#### Entradas
- Argumentos declarados: `payload: dict[str, Any]`

#### Salida
- Anotacion de retorno: `tuple[dict[str, Any], dict[str, Any]]`

#### Efectos laterales
- sin efectos externos evidentes por lectura estatica

#### Errores / excepciones
- no se observan `raise` directos en esta funcion

#### Determinismo
- NO_DETERMINISTA: depende de red/modelo/servicio externo.

### _answer_core()

#### Firma
```python
def _answer_core(payload: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]
```
- Lineas: 136-167

#### Responsabilidad observada
Responsabilidad derivada del nombre y cuerpo; ver efectos laterales y llamadas para detalle exacto.

#### Entradas
- Argumentos declarados: `payload: dict[str, Any]`

#### Salida
- Anotacion de retorno: `tuple[dict[str, Any], dict[str, Any]]`

#### Efectos laterales
- sin efectos externos evidentes por lectura estatica

#### Errores / excepciones
- no se observan `raise` directos en esta funcion

#### Determinismo
- NO_DETERMINISTA: depende de red/modelo/servicio externo.

### _run_eval_case()

#### Firma
```python
def _run_eval_case(case: dict[str, Any]) -> dict[str, Any]
```
- Lineas: 170-213

#### Responsabilidad observada
Responsabilidad derivada del nombre y cuerpo; ver efectos laterales y llamadas para detalle exacto.

#### Entradas
- Argumentos declarados: `case: dict[str, Any]`

#### Salida
- Anotacion de retorno: `dict[str, Any]`

#### Efectos laterales
- puede lanzar excepciones

#### Errores / excepciones
- linea 193: `raise ValueError(f'unknown eval kind: {kind}')`

#### Determinismo
- DETERMINISTA para las mismas entradas y mismo estado en memoria.

### _check_expectations()

#### Firma
```python
def _check_expectations(*, output: dict[str, Any], trace: dict[str, Any], expect: dict[str, Any]) -> list[dict[str, Any]]
```
- Lineas: 216-235

#### Responsabilidad observada
Responsabilidad derivada del nombre y cuerpo; ver efectos laterales y llamadas para detalle exacto.

#### Entradas
- Argumentos declarados: `*, output: dict[str, Any], trace: dict[str, Any], expect: dict[str, Any]`

#### Salida
- Anotacion de retorno: `list[dict[str, Any]]`

#### Efectos laterales
- sin efectos externos evidentes por lectura estatica

#### Errores / excepciones
- no se observan `raise` directos en esta funcion

#### Determinismo
- DETERMINISTA para las mismas entradas y mismo estado en memoria.

### _query_local_docs()

#### Firma
```python
def _query_local_docs(*, query: str, top_k: int) -> list[dict[str, Any]]
```
- Lineas: 238-260

#### Responsabilidad observada
Recupera informacion local a partir de una consulta textual.

#### Entradas
- Argumentos declarados: `*, query: str, top_k: int`

#### Salida
- Anotacion de retorno: `list[dict[str, Any]]`

#### Efectos laterales
- I/O de fichero

#### Errores / excepciones
- no se observan `raise` directos en esta funcion

#### Determinismo
- PARCIAL: depende de estado de disco o subproceso.

### _excerpt()

#### Firma
```python
def _excerpt(*, text: str, terms: list[str], radius: int=160) -> str
```
- Lineas: 263-269

#### Responsabilidad observada
Responsabilidad derivada del nombre y cuerpo; ver efectos laterales y llamadas para detalle exacto.

#### Entradas
- Argumentos declarados: `*, text: str, terms: list[str], radius: int=160`

#### Salida
- Anotacion de retorno: `str`

#### Efectos laterales
- sin efectos externos evidentes por lectura estatica

#### Errores / excepciones
- no se observan `raise` directos en esta funcion

#### Determinismo
- DETERMINISTA para las mismas entradas y mismo estado en memoria.

### _build_prompt()

#### Firma
```python
def _build_prompt(*, kind: str, user_text: str, context: dict[str, Any]) -> str
```
- Lineas: 272-282

#### Responsabilidad observada
Construye estructura o payload usado por otra capa.

#### Entradas
- Argumentos declarados: `*, kind: str, user_text: str, context: dict[str, Any]`

#### Salida
- Anotacion de retorno: `str`

#### Efectos laterales
- sin efectos externos evidentes por lectura estatica

#### Errores / excepciones
- no se observan `raise` directos en esta funcion

#### Determinismo
- DETERMINISTA para las mismas entradas y mismo estado en memoria.

### _write_trace()

#### Firma
```python
def _write_trace(*, endpoint: str, input_payload: dict[str, Any], prompt: str, provider: str, provider_endpoint: str, model_id: str, raw_output: Any, validated_output: dict[str, Any], fallback_used: bool, fallback_reason: str | None, latency_ms: int) -> None
```
- Lineas: 285-316

#### Responsabilidad observada
Responsabilidad derivada del nombre y cuerpo; ver efectos laterales y llamadas para detalle exacto.

#### Entradas
- Argumentos declarados: `*, endpoint: str, input_payload: dict[str, Any], prompt: str, provider: str, provider_endpoint: str, model_id: str, raw_output: Any, validated_output: dict[str, Any], fallback_used: bool, fallback_reason: str | None, latency_ms: int`

#### Salida
- Anotacion de retorno: `None`

#### Efectos laterales
- I/O de fichero

#### Errores / excepciones
- no se observan `raise` directos en esta funcion

#### Determinismo
- PARCIAL: incluye tiempo, UUID o latencia.

### _load_eval_cases()

#### Firma
```python
def _load_eval_cases() -> list[dict[str, Any]]
```
- Lineas: 319-329

#### Responsabilidad observada
Gestiona una superficie HTTP o validacion asociada a endpoint FastAPI, segun decoradores y excepciones observadas.

#### Entradas
- Argumentos declarados: ``

#### Salida
- Anotacion de retorno: `list[dict[str, Any]]`

#### Efectos laterales
- I/O de fichero
- puede lanzar excepciones

#### Errores / excepciones
- linea 328: `raise HTTPException(status_code=500, detail='eval_cases.json must contain a list')`
- linea 323: `raise HTTPException(status_code=500, detail='eval_cases.json not found') from exc`
- linea 325: `raise HTTPException(status_code=500, detail='eval_cases.json is not valid JSON') from exc`

#### Determinismo
- PARCIAL: depende de estado de disco o subproceso.

### _required_string()

#### Firma
```python
def _required_string(payload: dict[str, Any], field: str) -> str
```
- Lineas: 332-336

#### Responsabilidad observada
Gestiona una superficie HTTP o validacion asociada a endpoint FastAPI, segun decoradores y excepciones observadas.

#### Entradas
- Argumentos declarados: `payload: dict[str, Any], field: str`

#### Salida
- Anotacion de retorno: `str`

#### Efectos laterales
- puede lanzar excepciones

#### Errores / excepciones
- linea 335: `raise HTTPException(status_code=400, detail=f'{field} must be a non-empty string')`

#### Determinismo
- DETERMINISTA para las mismas entradas y mismo estado en memoria.

### _optional_string()

#### Firma
```python
def _optional_string(value: Any, field: str) -> str
```
- Lineas: 339-342

#### Responsabilidad observada
Gestiona una superficie HTTP o validacion asociada a endpoint FastAPI, segun decoradores y excepciones observadas.

#### Entradas
- Argumentos declarados: `value: Any, field: str`

#### Salida
- Anotacion de retorno: `str`

#### Efectos laterales
- puede lanzar excepciones

#### Errores / excepciones
- linea 341: `raise HTTPException(status_code=400, detail=f'{field} must be a non-empty string')`

#### Determinismo
- DETERMINISTA para las mismas entradas y mismo estado en memoria.

### _optional_string_or_none()

#### Firma
```python
def _optional_string_or_none(value: Any, field: str) -> str | None
```
- Lineas: 345-348

#### Responsabilidad observada
Responsabilidad derivada del nombre y cuerpo; ver efectos laterales y llamadas para detalle exacto.

#### Entradas
- Argumentos declarados: `value: Any, field: str`

#### Salida
- Anotacion de retorno: `str | None`

#### Efectos laterales
- sin efectos externos evidentes por lectura estatica

#### Errores / excepciones
- no se observan `raise` directos en esta funcion

#### Determinismo
- DETERMINISTA para las mismas entradas y mismo estado en memoria.

### _optional_object()

#### Firma
```python
def _optional_object(value: Any, field: str) -> dict[str, Any]
```
- Lineas: 351-354

#### Responsabilidad observada
Gestiona una superficie HTTP o validacion asociada a endpoint FastAPI, segun decoradores y excepciones observadas.

#### Entradas
- Argumentos declarados: `value: Any, field: str`

#### Salida
- Anotacion de retorno: `dict[str, Any]`

#### Efectos laterales
- puede lanzar excepciones

#### Errores / excepciones
- linea 353: `raise HTTPException(status_code=400, detail=f'{field} must be an object')`

#### Determinismo
- DETERMINISTA para las mismas entradas y mismo estado en memoria.

### _bounded_int()

#### Firma
```python
def _bounded_int(value: Any, field: str, *, minimum: int, maximum: int) -> int
```
- Lineas: 357-362

#### Responsabilidad observada
Gestiona una superficie HTTP o validacion asociada a endpoint FastAPI, segun decoradores y excepciones observadas.

#### Entradas
- Argumentos declarados: `value: Any, field: str, *, minimum: int, maximum: int`

#### Salida
- Anotacion de retorno: `int`

#### Efectos laterales
- puede lanzar excepciones

#### Errores / excepciones
- linea 359: `raise HTTPException(status_code=400, detail=f'{field} must be an integer')`
- linea 361: `raise HTTPException(status_code=400, detail=f'{field} must be between {minimum} and {maximum}')`

#### Determinismo
- DETERMINISTA para las mismas entradas y mismo estado en memoria.

### _latency_ms()

#### Firma
```python
def _latency_ms(started: float) -> int
```
- Lineas: 365-366

#### Responsabilidad observada
Responsabilidad derivada del nombre y cuerpo; ver efectos laterales y llamadas para detalle exacto.

#### Entradas
- Argumentos declarados: `started: float`

#### Salida
- Anotacion de retorno: `int`

#### Efectos laterales
- sin efectos externos evidentes por lectura estatica

#### Errores / excepciones
- no se observan `raise` directos en esta funcion

#### Determinismo
- PARCIAL: incluye tiempo, UUID o latencia.

## CONTRATOS Y RIESGOS LOCALES
- No se detectan riesgos locales especificos mas alla de los efectos laterales documentados.
