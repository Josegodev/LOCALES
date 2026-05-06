# MODULO: DB/chunks/document_context.py

## PROPOSITO
Recuperacion documental local desde `DB/chunks/documents.sqlite` y construccion de prompt RAG.

## TRAZABILIDAD
- Archivo real: `DB/chunks/document_context.py`
- Tamano: 3.0 KB
- Lenguaje detectado: Python
- Parseo AST: OK

## IMPORTS
### Internos
- Ninguno detectado.

### Externos
- linea 1: `from __future__ import annotations`

### Stdlib
- linea 3: `sqlite3`
- linea 4: `from pathlib import Path`

### Posibles acoplamientos peligrosos
- No se detectan imports ambiguos por nombre repetido.

## CLASES
- Ninguna clase definida.

## FUNCIONES
### normalize_terms()

#### Firma
```python
def normalize_terms(query: str) -> list[str]
```
- Lineas: 11-26

#### Responsabilidad observada
Responsabilidad derivada del nombre y cuerpo; ver efectos laterales y llamadas para detalle exacto.

#### Entradas
- Argumentos declarados: `query: str`

#### Salida
- Anotacion de retorno: `list[str]`

#### Efectos laterales
- sin efectos externos evidentes por lectura estatica

#### Errores / excepciones
- no se observan `raise` directos en esta funcion

#### Determinismo
- DETERMINISTA para las mismas entradas y mismo estado en memoria.

### search_chunks()

#### Firma
```python
def search_chunks(query: str, limit: int=5) -> list[dict]
```
- Lineas: 29-75

#### Responsabilidad observada
Lee o escribe estado SQLite segun las consultas presentes en la funcion.

#### Entradas
- Argumentos declarados: `query: str, limit: int=5`

#### Salida
- Anotacion de retorno: `list[dict]`

#### Efectos laterales
- I/O SQLite

#### Errores / excepciones
- no se observan `raise` directos en esta funcion

#### Determinismo
- PARCIAL: depende de estado de disco o subproceso.

### build_document_prompt()

#### Firma
```python
def build_document_prompt(query: str, limit: int=5) -> dict
```
- Lineas: 78-130

#### Responsabilidad observada
Construye estructura o payload usado por otra capa.

#### Entradas
- Argumentos declarados: `query: str, limit: int=5`

#### Salida
- Anotacion de retorno: `dict`

#### Efectos laterales
- sin efectos externos evidentes por lectura estatica

#### Errores / excepciones
- no se observan `raise` directos en esta funcion

#### Determinismo
- DETERMINISTA para las mismas entradas y mismo estado en memoria.

## CONTRATOS Y RIESGOS LOCALES
- No se detectan riesgos locales especificos mas alla de los efectos laterales documentados.
