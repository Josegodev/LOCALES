# MODULO: DB/lmstudio_client.py

## PROPOSITO
Cliente HTTP urllib para la API DB/perfiles contra LM Studio.

## TRAZABILIDAD
- Archivo real: `DB/lmstudio_client.py`
- Tamano: 2.2 KB
- Lenguaje detectado: Python
- Parseo AST: OK

## IMPORTS
### Internos
- Ninguno detectado.

### Externos
- Ninguno detectado.

### Stdlib
- linea 1: `json`
- linea 2: `urllib.error`
- linea 3: `urllib.request`
- linea 4: `from pathlib import Path`
- linea 5: `from typing import Any`

### Posibles acoplamientos peligrosos
- No se detectan imports ambiguos por nombre repetido.

## CLASES
- Ninguna clase definida.

## FUNCIONES
### load_config()

#### Firma
```python
def load_config() -> dict[str, Any]
```
- Lineas: 12-16

#### Responsabilidad observada
Responsabilidad derivada del nombre y cuerpo; ver efectos laterales y llamadas para detalle exacto.

#### Entradas
- Argumentos declarados: ``

#### Salida
- Anotacion de retorno: `dict[str, Any]`

#### Efectos laterales
- I/O de fichero
- puede lanzar excepciones

#### Errores / excepciones
- linea 14: `raise FileNotFoundError(f'No existe config.json: {CONFIG_PATH}')`

#### Determinismo
- PARCIAL: depende de estado de disco o subproceso.

### send_chat_completion()

#### Firma
```python
def send_chat_completion(payload: dict[str, Any]) -> dict[str, Any]
```
- Lineas: 19-60

#### Responsabilidad observada
Realiza llamada HTTP a un servicio externo/local y procesa la respuesta.

#### Entradas
- Argumentos declarados: `payload: dict[str, Any]`

#### Salida
- Anotacion de retorno: `dict[str, Any]`

#### Efectos laterales
- I/O de red HTTP
- puede lanzar excepciones

#### Errores / excepciones
- linea 51: `raise RuntimeError(f'LM Studio HTTP {exc.code}: {error_body}') from exc`
- linea 54: `raise RuntimeError(f'No se pudo conectar a LM Studio: {exc}') from exc`
- linea 60: `raise RuntimeError(f'Respuesta no JSON de LM Studio: {response_body}') from exc`

#### Determinismo
- NO_DETERMINISTA: depende de red/modelo/servicio externo.

### extract_message_content()

#### Firma
```python
def extract_message_content(response_json: dict[str, Any]) -> str
```
- Lineas: 63-79

#### Responsabilidad observada
Responsabilidad derivada del nombre y cuerpo; ver efectos laterales y llamadas para detalle exacto.

#### Entradas
- Argumentos declarados: `response_json: dict[str, Any]`

#### Salida
- Anotacion de retorno: `str`

#### Efectos laterales
- puede lanzar excepciones

#### Errores / excepciones
- linea 72: `raise RuntimeError(f'Contenido no textual recibido: {content}')`
- linea 77: `raise RuntimeError('Respuesta vacía del modelo')`
- linea 69: `raise RuntimeError(f'Respuesta inesperada de LM Studio: {response_json}') from exc`

#### Determinismo
- DETERMINISTA para las mismas entradas y mismo estado en memoria.

## CONTRATOS Y RIESGOS LOCALES
- INFORMATIVO: depende de servicios HTTP externos/locales y de timeouts.
