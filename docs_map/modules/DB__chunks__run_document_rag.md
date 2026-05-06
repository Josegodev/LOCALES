# MODULO: DB/chunks/run_document_rag.py

## PROPOSITO
Script CLI o ejecutable local con funcion `main`; detalles en funciones.

## TRAZABILIDAD
- Archivo real: `DB/chunks/run_document_rag.py`
- Tamano: 1.9 KB
- Lenguaje detectado: Python
- Parseo AST: OK

## IMPORTS
### Internos
- linea 5: `from document_context import build_document_prompt`
- linea 6: `from lmstudio_client import ask_lmstudio`

### Externos
- linea 1: `from __future__ import annotations`

### Stdlib
- linea 3: `argparse`

### Posibles acoplamientos peligrosos
- Linea 5: import bare `document_context`; acopla al directorio `DB/chunks`.
- Linea 6: import bare `lmstudio_client`; AMBIGUO si se ejecuta desde otro cwd porque hay nombres repetidos en el repo.

## CLASES
- Ninguna clase definida.

## FUNCIONES
### ask_once()

#### Firma
```python
def ask_once(query: str, top_k: int) -> None
```
- Lineas: 9-31

#### Responsabilidad observada
Responsabilidad derivada del nombre y cuerpo; ver efectos laterales y llamadas para detalle exacto.

#### Entradas
- Argumentos declarados: `query: str, top_k: int`

#### Salida
- Anotacion de retorno: `None`

#### Efectos laterales
- salida por stdout/stderr

#### Errores / excepciones
- no se observan `raise` directos en esta funcion

#### Determinismo
- NO_DETERMINISTA: depende de red/modelo/servicio externo.

### interactive_loop()

#### Firma
```python
def interactive_loop(top_k: int) -> None
```
- Lineas: 34-51

#### Responsabilidad observada
Responsabilidad derivada del nombre y cuerpo; ver efectos laterales y llamadas para detalle exacto.

#### Entradas
- Argumentos declarados: `top_k: int`

#### Salida
- Anotacion de retorno: `None`

#### Efectos laterales
- salida por stdout/stderr

#### Errores / excepciones
- no se observan `raise` directos en esta funcion

#### Determinismo
- DETERMINISTA para las mismas entradas y mismo estado en memoria.

### main()

#### Firma
```python
def main() -> None
```
- Lineas: 54-73

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
