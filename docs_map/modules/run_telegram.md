# MODULO: run_telegram.py

## PROPOSITO
Proceso de polling Telegram que reenvia mensajes a FastAPI local.

## TRAZABILIDAD
- Archivo real: `run_telegram.py`
- Tamano: 4.5 KB
- Lenguaje detectado: Python
- Parseo AST: OK

## IMPORTS
### Internos
- linea 3: `from app.config import settings`

### Externos
- linea 2: `requests`

### Stdlib
- linea 1: `time`

### Posibles acoplamientos peligrosos
- No se detectan imports ambiguos por nombre repetido.

## CLASES
- Ninguna clase definida.

## FUNCIONES
### handle_doc_command()

#### Firma
```python
def handle_doc_command(text: str) -> str
```
- Lineas: 17-51

#### Responsabilidad observada
Realiza llamada HTTP a un servicio externo/local y procesa la respuesta.

#### Entradas
- Argumentos declarados: `text: str`

#### Salida
- Anotacion de retorno: `str`

#### Efectos laterales
- I/O de red HTTP

#### Errores / excepciones
- no se observan `raise` directos en esta funcion

#### Determinismo
- NO_DETERMINISTA: depende de red/modelo/servicio externo.

### handle_doc_command()

#### Firma
```python
def handle_doc_command(text: str) -> str
```
- Lineas: 53-89

#### Responsabilidad observada
Realiza llamada HTTP a un servicio externo/local y procesa la respuesta.

#### Entradas
- Argumentos declarados: `text: str`

#### Salida
- Anotacion de retorno: `str`

#### Efectos laterales
- I/O de red HTTP

#### Errores / excepciones
- no se observan `raise` directos en esta funcion

#### Determinismo
- NO_DETERMINISTA: depende de red/modelo/servicio externo.

### get_updates()

#### Firma
```python
def get_updates() -> list[dict]
```
- Lineas: 91-105

#### Responsabilidad observada
Realiza llamada HTTP a un servicio externo/local y procesa la respuesta.

#### Entradas
- Argumentos declarados: ``

#### Salida
- Anotacion de retorno: `list[dict]`

#### Efectos laterales
- I/O de red HTTP
- puede lanzar excepciones

#### Errores / excepciones
- linea 103: `raise RuntimeError(f'Telegram getUpdates error: {data}')`

#### Determinismo
- NO_DETERMINISTA: depende de red/modelo/servicio externo.

### send_message()

#### Firma
```python
def send_message(chat_id: int, text: str) -> None
```
- Lineas: 108-114

#### Responsabilidad observada
Realiza llamada HTTP a un servicio externo/local y procesa la respuesta.

#### Entradas
- Argumentos declarados: `chat_id: int, text: str`

#### Salida
- Anotacion de retorno: `None`

#### Efectos laterales
- I/O de red HTTP

#### Errores / excepciones
- no se observan `raise` directos en esta funcion

#### Determinismo
- NO_DETERMINISTA: depende de red/modelo/servicio externo.

### ask_fastapi()

#### Firma
```python
def ask_fastapi(message: str) -> dict
```
- Lineas: 117-124

#### Responsabilidad observada
Realiza llamada HTTP a un servicio externo/local y procesa la respuesta.

#### Entradas
- Argumentos declarados: `message: str`

#### Salida
- Anotacion de retorno: `dict`

#### Efectos laterales
- I/O de red HTTP

#### Errores / excepciones
- no se observan `raise` directos en esta funcion

#### Determinismo
- NO_DETERMINISTA: depende de red/modelo/servicio externo.

### ask_backend()

#### Firma
```python
def ask_backend(text: str) -> str
```
- Lineas: 126-140

#### Responsabilidad observada
Realiza llamada HTTP a un servicio externo/local y procesa la respuesta.

#### Entradas
- Argumentos declarados: `text: str`

#### Salida
- Anotacion de retorno: `str`

#### Efectos laterales
- I/O de red HTTP

#### Errores / excepciones
- no se observan `raise` directos en esta funcion

#### Determinismo
- NO_DETERMINISTA: depende de red/modelo/servicio externo.

### handle_message()

#### Firma
```python
def handle_message(msg: dict) -> None
```
- Lineas: 142-163

#### Responsabilidad observada
Responsabilidad derivada del nombre y cuerpo; ver efectos laterales y llamadas para detalle exacto.

#### Entradas
- Argumentos declarados: `msg: dict`

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
- Lineas: 166-187

#### Responsabilidad observada
Responsabilidad derivada del nombre y cuerpo; ver efectos laterales y llamadas para detalle exacto.

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
- CRITICO: `handle_doc_command` esta definido dos veces; la segunda definicion pisa la primera.
- CRITICO: `ask_backend()` envia `slug/prompt` a `app/main.py /chat`, contrato incompatible con `ChatRequest(message=...)`; funcion no usada en `handle_message`, pero queda como riesgo de drift.
- INFORMATIVO: no se usa `telegram_allowed_chat_ids` aunque existe en configuracion.
- INFORMATIVO: depende de servicios HTTP externos/locales y de timeouts.
