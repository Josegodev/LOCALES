# MODULO: DB/chat_once.py

## PROPOSITO
Script CLI o ejecutable local con funcion `main`; detalles en funciones.

## TRAZABILIDAD
- Archivo real: `DB/chat_once.py`
- Tamano: 3.4 KB
- Lenguaje detectado: Python
- Parseo AST: OK

## IMPORTS
### Internos
- linea 5: `from db_store import ensure_profile_exists`
- linea 5: `from db_store import get_memory_context`
- linea 5: `from db_store import save_exchange`
- linea 10: `from lmstudio_client import extract_message_content`
- linea 10: `from lmstudio_client import load_config`
- linea 10: `from lmstudio_client import send_chat_completion`

### Externos
- Ninguno detectado.

### Stdlib
- linea 1: `argparse`
- linea 2: `sys`
- linea 3: `from typing import Any`

### Posibles acoplamientos peligrosos
- Linea 5: import bare `db_store`; acopla el modulo al cwd/directorio `DB`.
- Linea 5: import bare `db_store`; acopla el modulo al cwd/directorio `DB`.
- Linea 5: import bare `db_store`; acopla el modulo al cwd/directorio `DB`.
- Linea 10: import bare `lmstudio_client`; AMBIGUO si se ejecuta desde otro cwd porque hay nombres repetidos en el repo.
- Linea 10: import bare `lmstudio_client`; AMBIGUO si se ejecuta desde otro cwd porque hay nombres repetidos en el repo.
- Linea 10: import bare `lmstudio_client`; AMBIGUO si se ejecuta desde otro cwd porque hay nombres repetidos en el repo.

## CLASES
- Ninguna clase definida.

## FUNCIONES
### build_messages()

#### Firma
```python
def build_messages(system_prompt: str, approved_memory: list[str], user_prompt: str) -> list[dict[str, str]]
```
- Lineas: 17-53

#### Responsabilidad observada
Construye estructura o payload usado por otra capa.

#### Entradas
- Argumentos declarados: `system_prompt: str, approved_memory: list[str], user_prompt: str`

#### Salida
- Anotacion de retorno: `list[dict[str, str]]`

#### Efectos laterales
- sin efectos externos evidentes por lectura estatica

#### Errores / excepciones
- no se observan `raise` directos en esta funcion

#### Determinismo
- DETERMINISTA para las mismas entradas y mismo estado en memoria.

### build_payload()

#### Firma
```python
def build_payload(model_name: str, parameters: dict[str, Any], messages: list[dict[str, str]]) -> dict[str, Any]
```
- Lineas: 56-69

#### Responsabilidad observada
Construye estructura o payload usado por otra capa.

#### Entradas
- Argumentos declarados: `model_name: str, parameters: dict[str, Any], messages: list[dict[str, str]]`

#### Salida
- Anotacion de retorno: `dict[str, Any]`

#### Efectos laterales
- sin efectos externos evidentes por lectura estatica

#### Errores / excepciones
- no se observan `raise` directos en esta funcion

#### Determinismo
- DETERMINISTA para las mismas entradas y mismo estado en memoria.

### main()

#### Firma
```python
def main() -> None
```
- Lineas: 72-145

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
- linea 84: `raise SystemExit(f'Perfil inactivo: {args.slug}')`
- linea 145: `raise SystemExit(1)`

#### Determinismo
- NO_DETERMINISTA: depende de red/modelo/servicio externo.

## CONTRATOS Y RIESGOS LOCALES
- No se detectan riesgos locales especificos mas alla de los efectos laterales documentados.
