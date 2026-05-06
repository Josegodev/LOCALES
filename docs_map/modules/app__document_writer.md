# MODULO: app/document_writer.py

## PROPOSITO
Escritura controlada de documentos `.txt` y `.md` en `TELEGRAM_DOCS`.

## TRAZABILIDAD
- Archivo real: `app/document_writer.py`
- Tamano: 1.8 KB
- Lenguaje detectado: Python
- Parseo AST: OK

## IMPORTS
### Internos
- Ninguno detectado.

### Externos
- Ninguno detectado.

### Stdlib
- linea 1: `from pathlib import Path`
- linea 2: `from datetime import datetime`
- linea 2: `from datetime import timezone`

### Posibles acoplamientos peligrosos
- No se detectan imports ambiguos por nombre repetido.

## CLASES
### DocumentWriteError
- Linea: 9
- Bases: `Exception`
- Metodos:
  - linea 10: `def __init__(self, code: str, detail: str)`

## FUNCIONES
### create_document()

#### Firma
```python
def create_document(filename: str, content: str, overwrite: bool=False) -> dict
```
- Lineas: 16-57

#### Responsabilidad observada
Responsabilidad derivada del nombre y cuerpo; ver efectos laterales y llamadas para detalle exacto.

#### Entradas
- Argumentos declarados: `filename: str, content: str, overwrite: bool=False`

#### Salida
- Anotacion de retorno: `dict`

#### Efectos laterales
- puede lanzar excepciones

#### Errores / excepciones
- linea 18: `raise DocumentWriteError('filename_required', 'filename requerido')`
- linea 23: `raise DocumentWriteError('path_not_allowed', 'no se permiten rutas')`
- linea 26: `raise DocumentWriteError('extension_not_allowed', 'extensión no permitida')`
- linea 29: `raise DocumentWriteError('content_invalid', 'content debe ser texto')`
- linea 32: `raise DocumentWriteError('content_too_large', 'contenido demasiado grande')`
- linea 45: `raise DocumentWriteError('file_exists', 'el archivo ya existe')`
- linea 42: `raise DocumentWriteError('path_traversal_blocked', 'fuera del directorio permitido')`

#### Determinismo
- PARCIAL: incluye tiempo, UUID o latencia.

## CONTRATOS Y RIESGOS LOCALES
- No se detectan riesgos locales especificos mas alla de los efectos laterales documentados.
