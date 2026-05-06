# MODULO: DB/chunks/ingest_pdf_markdown.py

## PROPOSITO
Script CLI o ejecutable local con funcion `main`; detalles en funciones.

## TRAZABILIDAD
- Archivo real: `DB/chunks/ingest_pdf_markdown.py`
- Tamano: 3.8 KB
- Lenguaje detectado: Python
- Parseo AST: OK

## IMPORTS
### Internos
- Ninguno detectado.

### Externos
- linea 1: `from __future__ import annotations`
- linea 9: `pymupdf4llm`

### Stdlib
- linea 3: `argparse`
- linea 4: `hashlib`
- linea 5: `sqlite3`
- linea 6: `from datetime import datetime`
- linea 6: `from datetime import timezone`
- linea 7: `from pathlib import Path`

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
- Lineas: 15-16

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

### sha256_file()

#### Firma
```python
def sha256_file(path: Path) -> str
```
- Lineas: 19-26

#### Responsabilidad observada
Responsabilidad derivada del nombre y cuerpo; ver efectos laterales y llamadas para detalle exacto.

#### Entradas
- Argumentos declarados: `path: Path`

#### Salida
- Anotacion de retorno: `str`

#### Efectos laterales
- sin efectos externos evidentes por lectura estatica

#### Errores / excepciones
- no se observan `raise` directos en esta funcion

#### Determinismo
- DETERMINISTA para las mismas entradas y mismo estado en memoria.

### init_db()

#### Firma
```python
def init_db(conn: sqlite3.Connection) -> None
```
- Lineas: 29-58

#### Responsabilidad observada
Responsabilidad derivada del nombre y cuerpo; ver efectos laterales y llamadas para detalle exacto.

#### Entradas
- Argumentos declarados: `conn: sqlite3.Connection`

#### Salida
- Anotacion de retorno: `None`

#### Efectos laterales
- sin efectos externos evidentes por lectura estatica

#### Errores / excepciones
- no se observan `raise` directos en esta funcion

#### Determinismo
- DETERMINISTA para las mismas entradas y mismo estado en memoria.

### chunk_markdown()

#### Firma
```python
def chunk_markdown(markdown: str, chunk_size: int=1200, overlap: int=200) -> list[str]
```
- Lineas: 61-86

#### Responsabilidad observada
Responsabilidad derivada del nombre y cuerpo; ver efectos laterales y llamadas para detalle exacto.

#### Entradas
- Argumentos declarados: `markdown: str, chunk_size: int=1200, overlap: int=200`

#### Salida
- Anotacion de retorno: `list[str]`

#### Efectos laterales
- sin efectos externos evidentes por lectura estatica

#### Errores / excepciones
- no se observan `raise` directos en esta funcion

#### Determinismo
- DETERMINISTA para las mismas entradas y mismo estado en memoria.

### ingest_pdf()

#### Firma
```python
def ingest_pdf(pdf_path: Path) -> None
```
- Lineas: 89-154

#### Responsabilidad observada
Lee o escribe estado SQLite segun las consultas presentes en la funcion.

#### Entradas
- Argumentos declarados: `pdf_path: Path`

#### Salida
- Anotacion de retorno: `None`

#### Efectos laterales
- I/O SQLite
- salida por stdout/stderr
- puede lanzar excepciones

#### Errores / excepciones
- linea 96: `raise RuntimeError('No se pudo extraer texto del PDF. Puede ser escaneado o requerir OCR.')`

#### Determinismo
- PARCIAL: incluye tiempo, UUID o latencia.

### main()

#### Firma
```python
def main() -> None
```
- Lineas: 157-162

#### Responsabilidad observada
Punto de entrada CLI: parsea argumentos y coordina funciones del modulo.

#### Entradas
- Argumentos declarados: ``

#### Salida
- Anotacion de retorno: `None`

#### Efectos laterales
- sin efectos externos evidentes por lectura estatica

#### Errores / excepciones
- no se observan `raise` directos en esta funcion

#### Determinismo
- DETERMINISTA para las mismas entradas y mismo estado en memoria.

## CONTRATOS Y RIESGOS LOCALES
- No se detectan riesgos locales especificos mas alla de los efectos laterales documentados.
