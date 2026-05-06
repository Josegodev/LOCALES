# MODULO: ingest_nucleo_md.py

## PROPOSITO
Script CLI o ejecutable local con funcion `main`; detalles en funciones.

## TRAZABILIDAD
- Archivo real: `ingest_nucleo_md.py`
- Tamano: 2.5 KB
- Lenguaje detectado: Python
- Parseo AST: OK

## IMPORTS
### Internos
- Ninguno detectado.

### Externos
- Ninguno detectado.

### Stdlib
- linea 1: `from pathlib import Path`
- linea 2: `sqlite3`
- linea 3: `hashlib`
- linea 4: `from datetime import datetime`

### Posibles acoplamientos peligrosos
- No se detectan imports ambiguos por nombre repetido.

## CLASES
- Ninguna clase definida.

## FUNCIONES
### utc_now()

#### Firma
```python
def utc_now() -> str
```
- Lineas: 12-13

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

### sha256()

#### Firma
```python
def sha256(text: str) -> str
```
- Lineas: 16-17

#### Responsabilidad observada
Responsabilidad derivada del nombre y cuerpo; ver efectos laterales y llamadas para detalle exacto.

#### Entradas
- Argumentos declarados: `text: str`

#### Salida
- Anotacion de retorno: `str`

#### Efectos laterales
- sin efectos externos evidentes por lectura estatica

#### Errores / excepciones
- no se observan `raise` directos en esta funcion

#### Determinismo
- DETERMINISTA para las mismas entradas y mismo estado en memoria.

### chunk_text()

#### Firma
```python
def chunk_text(text: str, max_chars: int=1800)
```
- Lineas: 20-38

#### Responsabilidad observada
Responsabilidad derivada del nombre y cuerpo; ver efectos laterales y llamadas para detalle exacto.

#### Entradas
- Argumentos declarados: `text: str, max_chars: int=1800`

#### Salida
- Sin anotacion de retorno explicita.

#### Efectos laterales
- sin efectos externos evidentes por lectura estatica

#### Errores / excepciones
- no se observan `raise` directos en esta funcion

#### Determinismo
- DETERMINISTA para las mismas entradas y mismo estado en memoria.

### ingest_file()

#### Firma
```python
def ingest_file(conn: sqlite3.Connection, path: Path)
```
- Lineas: 41-101

#### Responsabilidad observada
Responsabilidad derivada del nombre y cuerpo; ver efectos laterales y llamadas para detalle exacto.

#### Entradas
- Argumentos declarados: `conn: sqlite3.Connection, path: Path`

#### Salida
- Sin anotacion de retorno explicita.

#### Efectos laterales
- I/O de fichero
- salida por stdout/stderr

#### Errores / excepciones
- no se observan `raise` directos en esta funcion

#### Determinismo
- PARCIAL: depende de estado de disco o subproceso.

### main()

#### Firma
```python
def main()
```
- Lineas: 104-114

#### Responsabilidad observada
Lee o escribe estado SQLite segun las consultas presentes en la funcion.

#### Entradas
- Argumentos declarados: ``

#### Salida
- Sin anotacion de retorno explicita.

#### Efectos laterales
- I/O SQLite
- puede lanzar excepciones

#### Errores / excepciones
- linea 108: `raise RuntimeError(f'No hay .md en {MD_DIR}')`

#### Determinismo
- PARCIAL: depende de estado de disco o subproceso.

## CONTRATOS Y RIESGOS LOCALES
- No se detectan riesgos locales especificos mas alla de los efectos laterales documentados.
