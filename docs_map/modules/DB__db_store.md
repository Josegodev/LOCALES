# MODULO: DB/db_store.py

## PROPOSITO
Capa de persistencia SQLite para registry, raw y memory por perfil.

## TRAZABILIDAD
- Archivo real: `DB/db_store.py`
- Tamano: 17.7 KB
- Lenguaje detectado: Python
- Parseo AST: OK

## IMPORTS
### Internos
- Ninguno detectado.

### Externos
- Ninguno detectado.

### Stdlib
- linea 1: `hashlib`
- linea 2: `json`
- linea 3: `sqlite3`
- linea 4: `from datetime import datetime`
- linea 4: `from datetime import timedelta`
- linea 4: `from datetime import timezone`
- linea 5: `from pathlib import Path`
- linea 6: `from typing import Any`

### Posibles acoplamientos peligrosos
- No se detectan imports ambiguos por nombre repetido.

## CLASES
- Ninguna clase definida.

## FUNCIONES
### now_iso()

#### Firma
```python
def now_iso() -> str
```
- Lineas: 16-17

#### Responsabilidad observada
Responsabilidad derivada del nombre y cuerpo; ver efectos laterales y llamadas para detalle exacto.

#### Entradas
- Argumentos declarados: ``

#### Salida
- Anotacion de retorno: `str`

#### Efectos laterales
- sin efectos externos evidentes por lectura estatica

#### Errores / excepciones
- no se observan `raise` directos en esta funcion

#### Determinismo
- PARCIAL: incluye tiempo, UUID o latencia.

### sha256_text()

#### Firma
```python
def sha256_text(value: str) -> str
```
- Lineas: 20-21

#### Responsabilidad observada
Responsabilidad derivada del nombre y cuerpo; ver efectos laterales y llamadas para detalle exacto.

#### Entradas
- Argumentos declarados: `value: str`

#### Salida
- Anotacion de retorno: `str`

#### Efectos laterales
- sin efectos externos evidentes por lectura estatica

#### Errores / excepciones
- no se observan `raise` directos en esta funcion

#### Determinismo
- DETERMINISTA para las mismas entradas y mismo estado en memoria.

### byte_len()

#### Firma
```python
def byte_len(value: str | None) -> int
```
- Lineas: 24-27

#### Responsabilidad observada
Responsabilidad derivada del nombre y cuerpo; ver efectos laterales y llamadas para detalle exacto.

#### Entradas
- Argumentos declarados: `value: str | None`

#### Salida
- Anotacion de retorno: `int`

#### Efectos laterales
- sin efectos externos evidentes por lectura estatica

#### Errores / excepciones
- no se observan `raise` directos en esta funcion

#### Determinismo
- DETERMINISTA para las mismas entradas y mismo estado en memoria.

### safe_slug()

#### Firma
```python
def safe_slug(value: str) -> str
```
- Lineas: 30-43

#### Responsabilidad observada
Responsabilidad derivada del nombre y cuerpo; ver efectos laterales y llamadas para detalle exacto.

#### Entradas
- Argumentos declarados: `value: str`

#### Salida
- Anotacion de retorno: `str`

#### Efectos laterales
- puede lanzar excepciones

#### Errores / excepciones
- linea 35: `raise ValueError('slug vacío')`
- linea 38: `raise ValueError('slug inválido: no puede empezar por punto')`
- linea 41: `raise ValueError("slug inválido: contiene '..'")`

#### Determinismo
- DETERMINISTA para las mismas entradas y mismo estado en memoria.

### read_schema()

#### Firma
```python
def read_schema(name: str) -> str
```
- Lineas: 46-52

#### Responsabilidad observada
Responsabilidad derivada del nombre y cuerpo; ver efectos laterales y llamadas para detalle exacto.

#### Entradas
- Argumentos declarados: `name: str`

#### Salida
- Anotacion de retorno: `str`

#### Efectos laterales
- I/O de fichero
- puede lanzar excepciones

#### Errores / excepciones
- linea 50: `raise FileNotFoundError(f'No existe el schema: {path}')`

#### Determinismo
- PARCIAL: depende de estado de disco o subproceso.

### connect_sqlite()

#### Firma
```python
def connect_sqlite(path: Path) -> sqlite3.Connection
```
- Lineas: 55-62

#### Responsabilidad observada
Lee o escribe estado SQLite segun las consultas presentes en la funcion.

#### Entradas
- Argumentos declarados: `path: Path`

#### Salida
- Anotacion de retorno: `sqlite3.Connection`

#### Efectos laterales
- I/O SQLite

#### Errores / excepciones
- no se observan `raise` directos en esta funcion

#### Determinismo
- PARCIAL: depende de estado de disco o subproceso.

### compact_db()

#### Firma
```python
def compact_db(path: Path) -> None
```
- Lineas: 65-71

#### Responsabilidad observada
Lee o escribe estado SQLite segun las consultas presentes en la funcion.

#### Entradas
- Argumentos declarados: `path: Path`

#### Salida
- Anotacion de retorno: `None`

#### Efectos laterales
- I/O SQLite

#### Errores / excepciones
- no se observan `raise` directos en esta funcion

#### Determinismo
- PARCIAL: depende de estado de disco o subproceso.

### db_total_size_bytes()

#### Firma
```python
def db_total_size_bytes(path: Path) -> int
```
- Lineas: 74-82

#### Responsabilidad observada
Responsabilidad derivada del nombre y cuerpo; ver efectos laterales y llamadas para detalle exacto.

#### Entradas
- Argumentos declarados: `path: Path`

#### Salida
- Anotacion de retorno: `int`

#### Efectos laterales
- sin efectos externos evidentes por lectura estatica

#### Errores / excepciones
- no se observan `raise` directos en esta funcion

#### Determinismo
- DETERMINISTA para las mismas entradas y mismo estado en memoria.

### init_registry()

#### Firma
```python
def init_registry() -> None
```
- Lineas: 85-92

#### Responsabilidad observada
Lee o escribe estado SQLite segun las consultas presentes en la funcion.

#### Entradas
- Argumentos declarados: ``

#### Salida
- Anotacion de retorno: `None`

#### Efectos laterales
- I/O SQLite

#### Errores / excepciones
- no se observan `raise` directos en esta funcion

#### Determinismo
- PARCIAL: depende de estado de disco o subproceso.

### get_profile_dir()

#### Firma
```python
def get_profile_dir(slug: str) -> Path
```
- Lineas: 95-96

#### Responsabilidad observada
Responsabilidad derivada del nombre y cuerpo; ver efectos laterales y llamadas para detalle exacto.

#### Entradas
- Argumentos declarados: `slug: str`

#### Salida
- Anotacion de retorno: `Path`

#### Efectos laterales
- sin efectos externos evidentes por lectura estatica

#### Errores / excepciones
- no se observan `raise` directos en esta funcion

#### Determinismo
- DETERMINISTA para las mismas entradas y mismo estado en memoria.

### get_raw_db_path()

#### Firma
```python
def get_raw_db_path(slug: str) -> Path
```
- Lineas: 99-100

#### Responsabilidad observada
Responsabilidad derivada del nombre y cuerpo; ver efectos laterales y llamadas para detalle exacto.

#### Entradas
- Argumentos declarados: `slug: str`

#### Salida
- Anotacion de retorno: `Path`

#### Efectos laterales
- sin efectos externos evidentes por lectura estatica

#### Errores / excepciones
- no se observan `raise` directos en esta funcion

#### Determinismo
- DETERMINISTA para las mismas entradas y mismo estado en memoria.

### get_memory_db_path()

#### Firma
```python
def get_memory_db_path(slug: str) -> Path
```
- Lineas: 103-104

#### Responsabilidad observada
Responsabilidad derivada del nombre y cuerpo; ver efectos laterales y llamadas para detalle exacto.

#### Entradas
- Argumentos declarados: `slug: str`

#### Salida
- Anotacion de retorno: `Path`

#### Efectos laterales
- sin efectos externos evidentes por lectura estatica

#### Errores / excepciones
- no se observan `raise` directos en esta funcion

#### Determinismo
- DETERMINISTA para las mismas entradas y mismo estado en memoria.

### create_model_profile()

#### Firma
```python
def create_model_profile(slug: str, model_name: str, runtime: str='lmstudio', parameters: dict[str, Any] | None=None, system_prompt: str='', raw_retention_days: int=14, raw_max_rows: int=500, raw_max_mb: int=200, memory_max_items: int=200) -> int
```
- Lineas: 107-187

#### Responsabilidad observada
Lee o escribe estado SQLite segun las consultas presentes en la funcion.

#### Entradas
- Argumentos declarados: `slug: str, model_name: str, runtime: str='lmstudio', parameters: dict[str, Any] | None=None, system_prompt: str='', raw_retention_days: int=14, raw_max_rows: int=500, raw_max_mb: int=200, memory_max_items: int=200`

#### Salida
- Anotacion de retorno: `int`

#### Efectos laterales
- I/O SQLite
- puede lanzar excepciones

#### Errores / excepciones
- linea 123: `raise ValueError('model_name vacío')`
- linea 126: `raise ValueError('runtime vacío')`
- linea 129: `raise ValueError('raw_retention_days debe ser > 0')`
- linea 132: `raise ValueError('raw_max_rows debe ser > 0')`
- linea 135: `raise ValueError('raw_max_mb debe ser > 0')`
- linea 138: `raise ValueError('memory_max_items debe ser > 0')`

#### Determinismo
- PARCIAL: incluye tiempo, UUID o latencia.

### ensure_profile_exists()

#### Firma
```python
def ensure_profile_exists(slug: str) -> dict[str, Any]
```
- Lineas: 190-231

#### Responsabilidad observada
Lee o escribe estado SQLite segun las consultas presentes en la funcion.

#### Entradas
- Argumentos declarados: `slug: str`

#### Salida
- Anotacion de retorno: `dict[str, Any]`

#### Efectos laterales
- I/O SQLite
- puede lanzar excepciones

#### Errores / excepciones
- linea 217: `raise ValueError(f'No existe el perfil de modelo: {clean_slug}')`

#### Determinismo
- PARCIAL: depende de estado de disco o subproceso.

### list_model_profiles()

#### Firma
```python
def list_model_profiles(active_only: bool=True) -> list[dict[str, Any]]
```
- Lineas: 234-278

#### Responsabilidad observada
Lee o escribe estado SQLite segun las consultas presentes en la funcion.

#### Entradas
- Argumentos declarados: `active_only: bool=True`

#### Salida
- Anotacion de retorno: `list[dict[str, Any]]`

#### Efectos laterales
- I/O SQLite

#### Errores / excepciones
- no se observan `raise` directos en esta funcion

#### Determinismo
- PARCIAL: depende de estado de disco o subproceso.

### save_exchange()

#### Firma
```python
def save_exchange(slug: str, user_prompt: str, request_payload: dict[str, Any], model_output: str | None, response_payload: dict[str, Any] | None, status: str, error_text: str | None=None) -> dict[str, int]
```
- Lineas: 281-385

#### Responsabilidad observada
Lee o escribe estado SQLite segun las consultas presentes en la funcion.

#### Entradas
- Argumentos declarados: `slug: str, user_prompt: str, request_payload: dict[str, Any], model_output: str | None, response_payload: dict[str, Any] | None, status: str, error_text: str | None=None`

#### Salida
- Anotacion de retorno: `dict[str, int]`

#### Efectos laterales
- I/O SQLite
- puede lanzar excepciones

#### Errores / excepciones
- linea 293: `raise ValueError(f'Perfil inactivo: {slug}')`
- linea 296: `raise ValueError('user_prompt vacío')`
- linea 301: `raise ValueError("status debe ser 'ok' o 'error'")`
- linea 305: `raise ValueError("model_output vacío para status='ok'")`

#### Determinismo
- PARCIAL: incluye tiempo, UUID o latencia.

### approve_memory()

#### Firma
```python
def approve_memory(slug: str, output_id: int, saved_text: str, reason: str | None=None) -> int
```
- Lineas: 388-471

#### Responsabilidad observada
Lee o escribe estado SQLite segun las consultas presentes en la funcion.

#### Entradas
- Argumentos declarados: `slug: str, output_id: int, saved_text: str, reason: str | None=None`

#### Salida
- Anotacion de retorno: `int`

#### Efectos laterales
- I/O SQLite
- puede lanzar excepciones

#### Errores / excepciones
- linea 399: `raise ValueError('saved_text vacío')`
- linea 415: `raise ValueError(f'No existe output_id={output_id} en perfil {profile['slug']}')`
- linea 422: `raise ValueError("No se puede aprobar memoria desde un output con status!='ok'")`
- linea 425: `raise ValueError('No se puede aprobar memoria sin source_output_hash')`
- linea 457: `raise ValueError('Ese saved_text ya existe en la memoria de este perfil') from exc`

#### Determinismo
- PARCIAL: incluye tiempo, UUID o latencia.

### get_memory_context()

#### Firma
```python
def get_memory_context(slug: str, limit: int=20) -> list[str]
```
- Lineas: 474-494

#### Responsabilidad observada
Lee o escribe estado SQLite segun las consultas presentes en la funcion.

#### Entradas
- Argumentos declarados: `slug: str, limit: int=20`

#### Salida
- Anotacion de retorno: `list[str]`

#### Efectos laterales
- I/O SQLite
- puede lanzar excepciones

#### Errores / excepciones
- linea 478: `raise ValueError('limit debe ser > 0')`

#### Determinismo
- PARCIAL: depende de estado de disco o subproceso.

### pin_prompt()

#### Firma
```python
def pin_prompt(slug: str, prompt_id: int, pinned: bool=True) -> None
```
- Lineas: 497-513

#### Responsabilidad observada
Lee o escribe estado SQLite segun las consultas presentes en la funcion.

#### Entradas
- Argumentos declarados: `slug: str, prompt_id: int, pinned: bool=True`

#### Salida
- Anotacion de retorno: `None`

#### Efectos laterales
- I/O SQLite
- puede lanzar excepciones

#### Errores / excepciones
- linea 513: `raise ValueError(f'No existe prompt_id={prompt_id}')`

#### Determinismo
- PARCIAL: depende de estado de disco o subproceso.

### enforce_memory_limit()

#### Firma
```python
def enforce_memory_limit(slug: str) -> int
```
- Lineas: 516-553

#### Responsabilidad observada
Lee o escribe estado SQLite segun las consultas presentes en la funcion.

#### Entradas
- Argumentos declarados: `slug: str`

#### Salida
- Anotacion de retorno: `int`

#### Efectos laterales
- I/O SQLite

#### Errores / excepciones
- no se observan `raise` directos en esta funcion

#### Determinismo
- PARCIAL: depende de estado de disco o subproceso.

### prune_raw()

#### Firma
```python
def prune_raw(slug: str) -> dict[str, int]
```
- Lineas: 556-632

#### Responsabilidad observada
Lee o escribe estado SQLite segun las consultas presentes en la funcion.

#### Entradas
- Argumentos declarados: `slug: str`

#### Salida
- Anotacion de retorno: `dict[str, int]`

#### Efectos laterales
- I/O SQLite

#### Errores / excepciones
- no se observan `raise` directos en esta funcion

#### Determinismo
- PARCIAL: incluye tiempo, UUID o latencia.

### raw_stats()

#### Firma
```python
def raw_stats(slug: str) -> dict[str, Any]
```
- Lineas: 635-670

#### Responsabilidad observada
Lee o escribe estado SQLite segun las consultas presentes en la funcion.

#### Entradas
- Argumentos declarados: `slug: str`

#### Salida
- Anotacion de retorno: `dict[str, Any]`

#### Efectos laterales
- I/O SQLite

#### Errores / excepciones
- no se observan `raise` directos en esta funcion

#### Determinismo
- PARCIAL: depende de estado de disco o subproceso.

### memory_stats()

#### Firma
```python
def memory_stats(slug: str) -> dict[str, Any]
```
- Lineas: 673-694

#### Responsabilidad observada
Lee o escribe estado SQLite segun las consultas presentes en la funcion.

#### Entradas
- Argumentos declarados: `slug: str`

#### Salida
- Anotacion de retorno: `dict[str, Any]`

#### Efectos laterales
- I/O SQLite

#### Errores / excepciones
- no se observan `raise` directos en esta funcion

#### Determinismo
- PARCIAL: depende de estado de disco o subproceso.

## CONTRATOS Y RIESGOS LOCALES
- No se detectan riesgos locales especificos mas alla de los efectos laterales documentados.
