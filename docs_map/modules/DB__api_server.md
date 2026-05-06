# MODULO: DB/api_server.py

## PROPOSITO
API experimental de perfiles LM Studio + SQLite con raw prompts, outputs y memoria aprobada.

## TRAZABILIDAD
- Archivo real: `DB/api_server.py`
- Tamano: 8.6 KB
- Lenguaje detectado: Python
- Parseo AST: OK

## IMPORTS
### Internos
- linea 7: `from db_store import approve_memory`
- linea 7: `from db_store import create_model_profile`
- linea 7: `from db_store import ensure_profile_exists`
- linea 7: `from db_store import enforce_memory_limit`
- linea 7: `from db_store import get_memory_context`
- linea 7: `from db_store import list_model_profiles`
- linea 7: `from db_store import memory_stats`
- linea 7: `from db_store import prune_raw`
- linea 7: `from db_store import raw_stats`
- linea 7: `from db_store import save_exchange`
- linea 20: `from lmstudio_client import extract_message_content`
- linea 20: `from lmstudio_client import load_config`
- linea 20: `from lmstudio_client import send_chat_completion`

### Externos
- linea 4: `from fastapi import FastAPI`
- linea 4: `from fastapi import HTTPException`
- linea 4: `from fastapi import Query`
- linea 5: `from pydantic import BaseModel`
- linea 5: `from pydantic import Field`

### Stdlib
- linea 1: `sqlite3`
- linea 2: `from typing import Any`

### Posibles acoplamientos peligrosos
- Linea 7: import bare `db_store`; acopla el modulo al cwd/directorio `DB`.
- Linea 7: import bare `db_store`; acopla el modulo al cwd/directorio `DB`.
- Linea 7: import bare `db_store`; acopla el modulo al cwd/directorio `DB`.
- Linea 7: import bare `db_store`; acopla el modulo al cwd/directorio `DB`.
- Linea 7: import bare `db_store`; acopla el modulo al cwd/directorio `DB`.
- Linea 7: import bare `db_store`; acopla el modulo al cwd/directorio `DB`.
- Linea 7: import bare `db_store`; acopla el modulo al cwd/directorio `DB`.
- Linea 7: import bare `db_store`; acopla el modulo al cwd/directorio `DB`.
- Linea 7: import bare `db_store`; acopla el modulo al cwd/directorio `DB`.
- Linea 7: import bare `db_store`; acopla el modulo al cwd/directorio `DB`.
- Linea 20: import bare `lmstudio_client`; AMBIGUO si se ejecuta desde otro cwd porque hay nombres repetidos en el repo.
- Linea 20: import bare `lmstudio_client`; AMBIGUO si se ejecuta desde otro cwd porque hay nombres repetidos en el repo.
- Linea 20: import bare `lmstudio_client`; AMBIGUO si se ejecuta desde otro cwd porque hay nombres repetidos en el repo.

## CLASES
### CreateProfileRequest
- Linea: 44
- Bases: `BaseModel`
- Campos / atributos observados:
  - linea 45: `slug: str = Field(..., min_length=1)`
  - linea 46: `model_name: str = Field(..., min_length=1)`
  - linea 48: `temperature: float = 0.2`
  - linea 49: `top_p: float | None = None`
  - linea 50: `max_tokens: int | None = None`
  - linea 52: `system_prompt: str = DEFAULT_SYSTEM_PROMPT`
  - linea 54: `raw_retention_days: int = 14`
  - linea 55: `raw_max_rows: int = 500`
  - linea 56: `raw_max_mb: int = 200`
  - linea 57: `memory_max_items: int = 200`
### ChatRequest
- Linea: 60
- Bases: `BaseModel`
- Campos / atributos observados:
  - linea 61: `slug: str = Field(..., min_length=1)`
  - linea 62: `prompt: str = Field(..., min_length=1)`
  - linea 63: `memory_limit: int | None = None`
### ApproveMemoryRequest
- Linea: 66
- Bases: `BaseModel`
- Campos / atributos observados:
  - linea 67: `output_id: int`
  - linea 68: `saved_text: str = Field(..., min_length=1)`
  - linea 69: `reason: str | None = None`

## FUNCIONES
### build_messages()

#### Firma
```python
def build_messages(system_prompt: str, approved_memory: list[str], user_prompt: str) -> list[dict[str, str]]
```
- Lineas: 72-108

#### Responsabilidad observada
Construye estructura o payload usado por otra capa.

#### Entradas
- Argumentos declarados: `system_prompt: str, approved_memory: list[str], user_prompt: str`

#### Salida
- Anotacion de retorno: `list[dict[str, str]]`

#### Efectos laterales
- sin efectos externos evidentes por lectura estatica

#### Errores / excepciones
- no se observan `raise` directos en esta funcion

#### Determinismo
- DETERMINISTA para las mismas entradas y mismo estado en memoria.

### build_payload()

#### Firma
```python
def build_payload(model_name: str, parameters: dict[str, Any], messages: list[dict[str, str]]) -> dict[str, Any]
```
- Lineas: 111-124

#### Responsabilidad observada
Construye estructura o payload usado por otra capa.

#### Entradas
- Argumentos declarados: `model_name: str, parameters: dict[str, Any], messages: list[dict[str, str]]`

#### Salida
- Anotacion de retorno: `dict[str, Any]`

#### Efectos laterales
- sin efectos externos evidentes por lectura estatica

#### Errores / excepciones
- no se observan `raise` directos en esta funcion

#### Determinismo
- DETERMINISTA para las mismas entradas y mismo estado en memoria.

### health()

#### Firma
```python
def health() -> dict[str, Any]
```
- Lineas: 128-134
- Decoradores: `app.get('/health')`

#### Responsabilidad observada
Gestiona una superficie HTTP o validacion asociada a endpoint FastAPI, segun decoradores y excepciones observadas.

#### Entradas
- Argumentos declarados: ``

#### Salida
- Anotacion de retorno: `dict[str, Any]`

#### Efectos laterales
- sin efectos externos evidentes por lectura estatica

#### Errores / excepciones
- no se observan `raise` directos en esta funcion

#### Determinismo
- DETERMINISTA para las mismas entradas y mismo estado en memoria.

### get_profiles()

#### Firma
```python
def get_profiles() -> dict[str, Any]
```
- Lineas: 138-141
- Decoradores: `app.get('/profiles')`

#### Responsabilidad observada
Gestiona una superficie HTTP o validacion asociada a endpoint FastAPI, segun decoradores y excepciones observadas.

#### Entradas
- Argumentos declarados: ``

#### Salida
- Anotacion de retorno: `dict[str, Any]`

#### Efectos laterales
- sin efectos externos evidentes por lectura estatica

#### Errores / excepciones
- no se observan `raise` directos en esta funcion

#### Determinismo
- DETERMINISTA para las mismas entradas y mismo estado en memoria.

### create_profile()

#### Firma
```python
def create_profile(request: CreateProfileRequest) -> dict[str, Any]
```
- Lineas: 145-182
- Decoradores: `app.post('/profiles')`

#### Responsabilidad observada
Gestiona una superficie HTTP o validacion asociada a endpoint FastAPI, segun decoradores y excepciones observadas.

#### Entradas
- Argumentos declarados: `request: CreateProfileRequest`

#### Salida
- Anotacion de retorno: `dict[str, Any]`

#### Efectos laterales
- puede lanzar excepciones

#### Errores / excepciones
- linea 171: `raise HTTPException(status_code=409, detail=f'El perfil ya existe: {request.slug}') from exc`
- linea 177: `raise HTTPException(status_code=400, detail=str(exc)) from exc`

#### Determinismo
- DETERMINISTA para las mismas entradas y mismo estado en memoria.

### get_profile()

#### Firma
```python
def get_profile(slug: str) -> dict[str, Any]
```
- Lineas: 186-191
- Decoradores: `app.get('/profiles/{slug}')`

#### Responsabilidad observada
Gestiona una superficie HTTP o validacion asociada a endpoint FastAPI, segun decoradores y excepciones observadas.

#### Entradas
- Argumentos declarados: `slug: str`

#### Salida
- Anotacion de retorno: `dict[str, Any]`

#### Efectos laterales
- puede lanzar excepciones

#### Errores / excepciones
- linea 191: `raise HTTPException(status_code=404, detail=str(exc)) from exc`

#### Determinismo
- DETERMINISTA para las mismas entradas y mismo estado en memoria.

### get_profile_stats()

#### Firma
```python
def get_profile_stats(slug: str) -> dict[str, Any]
```
- Lineas: 195-203
- Decoradores: `app.get('/profiles/{slug}/stats')`

#### Responsabilidad observada
Gestiona una superficie HTTP o validacion asociada a endpoint FastAPI, segun decoradores y excepciones observadas.

#### Entradas
- Argumentos declarados: `slug: str`

#### Salida
- Anotacion de retorno: `dict[str, Any]`

#### Efectos laterales
- puede lanzar excepciones

#### Errores / excepciones
- linea 203: `raise HTTPException(status_code=404, detail=str(exc)) from exc`

#### Determinismo
- DETERMINISTA para las mismas entradas y mismo estado en memoria.

### get_profile_memory()

#### Firma
```python
def get_profile_memory(slug: str, limit: int=Query(default=20, ge=1, le=500)) -> dict[str, Any]
```
- Lineas: 207-221
- Decoradores: `app.get('/profiles/{slug}/memory')`

#### Responsabilidad observada
Gestiona una superficie HTTP o validacion asociada a endpoint FastAPI, segun decoradores y excepciones observadas.

#### Entradas
- Argumentos declarados: `slug: str, limit: int=Query(default=20, ge=1, le=500)`

#### Salida
- Anotacion de retorno: `dict[str, Any]`

#### Efectos laterales
- puede lanzar excepciones

#### Errores / excepciones
- linea 215: `raise HTTPException(status_code=404, detail=str(exc)) from exc`

#### Determinismo
- DETERMINISTA para las mismas entradas y mismo estado en memoria.

### approve_profile_memory()

#### Firma
```python
def approve_profile_memory(slug: str, request: ApproveMemoryRequest) -> dict[str, Any]
```
- Lineas: 225-244
- Decoradores: `app.post('/profiles/{slug}/memory/approve')`

#### Responsabilidad observada
Gestiona una superficie HTTP o validacion asociada a endpoint FastAPI, segun decoradores y excepciones observadas.

#### Entradas
- Argumentos declarados: `slug: str, request: ApproveMemoryRequest`

#### Salida
- Anotacion de retorno: `dict[str, Any]`

#### Efectos laterales
- puede lanzar excepciones

#### Errores / excepciones
- linea 238: `raise HTTPException(status_code=400, detail=str(exc)) from exc`

#### Determinismo
- DETERMINISTA para las mismas entradas y mismo estado en memoria.

### chat()

#### Firma
```python
def chat(request: ChatRequest) -> dict[str, Any]
```
- Lineas: 248-335
- Decoradores: `app.post('/chat')`

#### Responsabilidad observada
Gestiona una superficie HTTP o validacion asociada a endpoint FastAPI, segun decoradores y excepciones observadas.

#### Entradas
- Argumentos declarados: `request: ChatRequest`

#### Salida
- Anotacion de retorno: `dict[str, Any]`

#### Efectos laterales
- puede lanzar excepciones

#### Errores / excepciones
- linea 252: `raise HTTPException(status_code=400, detail='prompt vacío')`
- linea 261: `raise HTTPException(status_code=400, detail=f'Perfil inactivo: {request.slug}')`
- linea 258: `raise HTTPException(status_code=404, detail=str(exc)) from exc`
- linea 326: `raise HTTPException(status_code=502, detail={'status': 'error', 'slug': profile['slug'], 'prompt_id': ids['prompt_id'], 'output_id': ids['output_id'], 'error': str(exc)}) from exc`

#### Determinismo
- NO_DETERMINISTA: depende de red/modelo/servicio externo.

### prune_profile()

#### Firma
```python
def prune_profile(slug: str) -> dict[str, Any]
```
- Lineas: 339-349
- Decoradores: `app.post('/profiles/{slug}/prune')`

#### Responsabilidad observada
Gestiona una superficie HTTP o validacion asociada a endpoint FastAPI, segun decoradores y excepciones observadas.

#### Entradas
- Argumentos declarados: `slug: str`

#### Salida
- Anotacion de retorno: `dict[str, Any]`

#### Efectos laterales
- puede lanzar excepciones

#### Errores / excepciones
- linea 344: `raise HTTPException(status_code=404, detail=str(exc)) from exc`

#### Determinismo
- DETERMINISTA para las mismas entradas y mismo estado en memoria.

### enforce_profile_memory_limit()

#### Firma
```python
def enforce_profile_memory_limit(slug: str) -> dict[str, Any]
```
- Lineas: 353-363
- Decoradores: `app.post('/profiles/{slug}/memory/enforce-limit')`

#### Responsabilidad observada
Gestiona una superficie HTTP o validacion asociada a endpoint FastAPI, segun decoradores y excepciones observadas.

#### Entradas
- Argumentos declarados: `slug: str`

#### Salida
- Anotacion de retorno: `dict[str, Any]`

#### Efectos laterales
- puede lanzar excepciones

#### Errores / excepciones
- linea 358: `raise HTTPException(status_code=404, detail=str(exc)) from exc`

#### Determinismo
- DETERMINISTA para las mismas entradas y mismo estado en memoria.

## CONTRATOS Y RIESGOS LOCALES
- No se detectan riesgos locales especificos mas alla de los efectos laterales documentados.
