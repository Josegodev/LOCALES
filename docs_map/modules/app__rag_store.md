# MODULO: app/rag_store.py

## PROPOSITO
Modulo utilitario; proposito exacto derivado de sus funciones listadas.

## TRAZABILIDAD
- Archivo real: `app/rag_store.py`
- Tamano: 1003 B
- Lenguaje detectado: Python
- Parseo AST: OK

## IMPORTS
### Internos
- Ninguno detectado.

### Externos
- Ninguno detectado.

### Stdlib
- linea 1: `sqlite3`
- linea 2: `from pathlib import Path`

### Posibles acoplamientos peligrosos
- No se detectan imports ambiguos por nombre repetido.

## CLASES
- Ninguna clase definida.

## FUNCIONES
### search_chunks()

#### Firma
```python
def search_chunks(query: str, limit: int=3) -> list[dict]
```
- Lineas: 8-46

#### Responsabilidad observada
Lee o escribe estado SQLite segun las consultas presentes en la funcion.

#### Entradas
- Argumentos declarados: `query: str, limit: int=3`

#### Salida
- Anotacion de retorno: `list[dict]`

#### Efectos laterales
- I/O SQLite

#### Errores / excepciones
- no se observan `raise` directos en esta funcion

#### Determinismo
- PARCIAL: depende de estado de disco o subproceso.

## CONTRATOS Y RIESGOS LOCALES
- CRITICO: ruta relativa `chunks/document_chunks.sqlite`; depende del cwd y no coincide con `DB/chunks/documents.sqlite`.
