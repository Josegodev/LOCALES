# MODULO: DB/chunks/run_ingest_pipeline.py

## PROPOSITO
Script CLI o ejecutable local con funcion `main`; detalles en funciones.

## TRAZABILIDAD
- Archivo real: `DB/chunks/run_ingest_pipeline.py`
- Tamano: 3.6 KB
- Lenguaje detectado: Python
- Parseo AST: OK

## IMPORTS
### Internos
- linea 9: `from document_context import build_document_prompt`
- linea 10: `from search_docs import search_chunks`

### Externos
- linea 1: `from __future__ import annotations`

### Stdlib
- linea 3: `argparse`
- linea 4: `sqlite3`
- linea 5: `subprocess`
- linea 6: `sys`
- linea 7: `from pathlib import Path`

### Posibles acoplamientos peligrosos
- Linea 9: import bare `document_context`; acopla al directorio `DB/chunks`.

## CLASES
- Ninguna clase definida.

## FUNCIONES
### run_ingest()

#### Firma
```python
def run_ingest(pdf_path: Path) -> None
```
- Lineas: 18-39

#### Responsabilidad observada
Responsabilidad derivada del nombre y cuerpo; ver efectos laterales y llamadas para detalle exacto.

#### Entradas
- Argumentos declarados: `pdf_path: Path`

#### Salida
- Anotacion de retorno: `None`

#### Efectos laterales
- subproceso externo
- salida por stdout/stderr
- puede lanzar excepciones

#### Errores / excepciones
- linea 39: `raise RuntimeError(f'ingest_pdf_markdown.py falló con código {result.returncode}')`

#### Determinismo
- PARCIAL: depende de estado de disco o subproceso.

### validate_sqlite()

#### Firma
```python
def validate_sqlite() -> None
```
- Lineas: 42-77

#### Responsabilidad observada
Lee o escribe estado SQLite segun las consultas presentes en la funcion.

#### Entradas
- Argumentos declarados: ``

#### Salida
- Anotacion de retorno: `None`

#### Efectos laterales
- I/O SQLite
- salida por stdout/stderr
- puede lanzar excepciones

#### Errores / excepciones
- linea 71: `raise RuntimeError('No hay documentos en SQLite')`
- linea 74: `raise RuntimeError('No hay chunks en SQLite')`

#### Determinismo
- PARCIAL: depende de estado de disco o subproceso.

### validate_search()

#### Firma
```python
def validate_search(query: str, top_k: int) -> None
```
- Lineas: 80-96

#### Responsabilidad observada
Valida estructura de datos y produce aceptacion/fallback segun contrato local.

#### Entradas
- Argumentos declarados: `query: str, top_k: int`

#### Salida
- Anotacion de retorno: `None`

#### Efectos laterales
- salida por stdout/stderr
- puede lanzar excepciones

#### Errores / excepciones
- linea 89: `raise RuntimeError('search_docs.py no recuperó resultados')`

#### Determinismo
- DETERMINISTA para las mismas entradas y mismo estado en memoria.

### validate_document_context()

#### Firma
```python
def validate_document_context(query: str, top_k: int) -> None
```
- Lineas: 99-112

#### Responsabilidad observada
Valida estructura de datos y produce aceptacion/fallback segun contrato local.

#### Entradas
- Argumentos declarados: `query: str, top_k: int`

#### Salida
- Anotacion de retorno: `None`

#### Efectos laterales
- salida por stdout/stderr
- puede lanzar excepciones

#### Errores / excepciones
- linea 109: `raise RuntimeError('document_context.py no generó evidencia')`

#### Determinismo
- DETERMINISTA para las mismas entradas y mismo estado en memoria.

### main()

#### Firma
```python
def main() -> None
```
- Lineas: 115-145

#### Responsabilidad observada
Punto de entrada CLI: parsea argumentos y coordina funciones del modulo.

#### Entradas
- Argumentos declarados: ``

#### Salida
- Anotacion de retorno: `None`

#### Efectos laterales
- salida por stdout/stderr
- puede lanzar excepciones

#### Errores / excepciones
- linea 138: `raise FileNotFoundError(f'No existe el PDF: {pdf_path}')`

#### Determinismo
- DETERMINISTA para las mismas entradas y mismo estado en memoria.

## CONTRATOS Y RIESGOS LOCALES
- INFORMATIVO: ejecuta subprocesos; el resultado depende del interprete y cwd usados.
