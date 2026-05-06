# MODULO: app/telegram_client.py

## PROPOSITO
Modulo utilitario; proposito exacto derivado de sus funciones listadas.

## TRAZABILIDAD
- Archivo real: `app/telegram_client.py`
- Tamano: 352 B
- Lenguaje detectado: Python
- Parseo AST: OK

## IMPORTS
### Internos
- Ninguno detectado.

### Externos
- linea 1: `requests`

### Stdlib
- Ninguno detectado.

### Posibles acoplamientos peligrosos
- No se detectan imports ambiguos por nombre repetido.

## CLASES
- Ninguna clase definida.

## FUNCIONES
### send_telegram_message()

#### Firma
```python
def send_telegram_message(bot_token: str, chat_id: int, text: str) -> None
```
- Lineas: 4-16

#### Responsabilidad observada
Realiza llamada HTTP a un servicio externo/local y procesa la respuesta.

#### Entradas
- Argumentos declarados: `bot_token: str, chat_id: int, text: str`

#### Salida
- Anotacion de retorno: `None`

#### Efectos laterales
- I/O de red HTTP

#### Errores / excepciones
- no se observan `raise` directos en esta funcion

#### Determinismo
- NO_DETERMINISTA: depende de red/modelo/servicio externo.

## CONTRATOS Y RIESGOS LOCALES
- INFORMATIVO: depende de servicios HTTP externos/locales y de timeouts.
