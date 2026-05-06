# MODULO: DB/prune.py

## PROPOSITO
Script CLI o ejecutable local con funcion `main`; detalles en funciones.

## TRAZABILIDAD
- Archivo real: `DB/prune.py`
- Tamano: 538 B
- Lenguaje detectado: Python
- Parseo AST: OK

## IMPORTS
### Internos
- linea 2: `from db_store import prune_raw`
- linea 2: `from db_store import raw_stats`
- linea 2: `from db_store import memory_stats`

### Externos
- Ninguno detectado.

### Stdlib
- linea 1: `argparse`

### Posibles acoplamientos peligrosos
- Linea 2: import bare `db_store`; acopla el modulo al cwd/directorio `DB`.
- Linea 2: import bare `db_store`; acopla el modulo al cwd/directorio `DB`.
- Linea 2: import bare `db_store`; acopla el modulo al cwd/directorio `DB`.

## CLASES
- Ninguna clase definida.

## FUNCIONES
### main()

#### Firma
```python
def main() -> None
```
- Lineas: 5-22

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
- No se detectan riesgos locales especificos mas alla de los efectos laterales documentados.
