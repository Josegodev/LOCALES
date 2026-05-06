# MODULO: DB/chunks/ingest_all_pdfs.py

## PROPOSITO
Script CLI o ejecutable local con funcion `main`; detalles en funciones.

## TRAZABILIDAD
- Archivo real: `DB/chunks/ingest_all_pdfs.py`
- Tamano: 3.0 KB
- Lenguaje detectado: Python
- Parseo AST: OK

## IMPORTS
### Internos
- Ninguno detectado.

### Externos
- linea 1: `from __future__ import annotations`

### Stdlib
- linea 3: `argparse`
- linea 4: `sqlite3`
- linea 5: `subprocess`
- linea 6: `sys`
- linea 7: `from pathlib import Path`

### Posibles acoplamientos peligrosos
- No se detectan imports ambiguos por nombre repetido.

## CLASES
- Ninguna clase definida.

## FUNCIONES
### find_pdfs()

#### Firma
```python
def find_pdfs(pdf_dir: Path) -> list[Path]
```
- Lineas: 16-25

#### Responsabilidad observada
Responsabilidad derivada del nombre y cuerpo; ver efectos laterales y llamadas para detalle exacto.

#### Entradas
- Argumentos declarados: `pdf_dir: Path`

#### Salida
- Anotacion de retorno: `list[Path]`

#### Efectos laterales
- puede lanzar excepciones

#### Errores / excepciones
- linea 18: `raise FileNotFoundError(f'No existe la carpeta PDF: {pdf_dir}')`
- linea 23: `raise RuntimeError(f'No hay PDFs en: {pdf_dir}')`

#### Determinismo
- DETERMINISTA para las mismas entradas y mismo estado en memoria.

### ingest_pdf()

#### Firma
```python
def ingest_pdf(pdf_path: Path) -> None
```
- Lineas: 28-52

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
- linea 50: `raise RuntimeError(f'Falló ingesta de {pdf_path.name} con código {result.returncode}')`

#### Determinismo
- PARCIAL: depende de estado de disco o subproceso.

### validate_sqlite()

#### Firma
```python
def validate_sqlite() -> None
```
- Lineas: 55-105

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
- linea 60: `raise RuntimeError(f'No existe la base SQLite: {DB_PATH}')`
- linea 99: `raise RuntimeError('No hay documentos registrados')`
- linea 102: `raise RuntimeError('No hay chunks registrados')`

#### Determinismo
- PARCIAL: depende de estado de disco o subproceso.

### main()

#### Firma
```python
def main() -> None
```
- Lineas: 108-129

#### Responsabilidad observada
Punto de entrada CLI: parsea argumentos y coordina funciones del modulo.

#### Entradas
- Argumentos declarados: ``

#### Salida
- Anotacion de retorno: `None`

#### Efectos laterales
- salida por stdout/stderr

#### Errores / excepciones
- no se observan `raise` directos en esta funcion

#### Determinismo
- DETERMINISTA para las mismas entradas y mismo estado en memoria.

## CONTRATOS Y RIESGOS LOCALES
- INFORMATIVO: ejecuta subprocesos; el resultado depende del interprete y cwd usados.
