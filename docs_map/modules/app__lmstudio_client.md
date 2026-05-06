# MODULO: app/lmstudio_client.py

## PROPOSITO
Cliente HTTP de la app productiva hacia LM Studio compatible OpenAI.

## TRAZABILIDAD
- Archivo real: `app/lmstudio_client.py`
- Tamano: 3.3 KB
- Lenguaje detectado: Python
- Parseo AST: OK

## IMPORTS
### Internos
- linea 6: `from app.config import settings`

### Externos
- linea 3: `traceback`
- linea 4: `requests`

### Stdlib
- linea 1: `time`
- linea 2: `json`

### Posibles acoplamientos peligrosos
- No se detectan imports ambiguos por nombre repetido.

## CLASES
### LLMError
- Linea: 9
- Bases: `Exception`
- Metodos:
  - linea 10: `def __init__(self, code: str, message: str)`

## FUNCIONES
### ask_lmstudio()

#### Firma
```python
def ask_lmstudio(message: str, model: str | None=None, max_tokens: int | None=None, temperature: float | None=None) -> dict
```
- Lineas: 16-110

#### Responsabilidad observada
Realiza llamada HTTP a un servicio externo/local y procesa la respuesta.

#### Entradas
- Argumentos declarados: `message: str, model: str | None=None, max_tokens: int | None=None, temperature: float | None=None`

#### Salida
- Anotacion de retorno: `dict`

#### Efectos laterales
- I/O de red HTTP
- salida por stdout/stderr
- puede lanzar excepciones

#### Errores / excepciones
- linea 74: `raise LLMError('LMSTUDIO_HTTP_ERROR', f'LM Studio devolvió HTTP {response.status_code}: {response.text[:300]}')`
- linea 95: `raise LLMError('EMPTY_RESPONSE', f'LM Studio devolvió content vacío. model={data.get('model')!r}, finish_reason={choice.get('finish_reason')!r}, reasoning_content_present={bool(message_payload.get('reasoning_content'))}.')`
- linea 59: `raise LLMError('LMSTUDIO_UNAVAILABLE', 'LM Studio no está disponible.')`
- linea 62: `raise LLMError('TIMEOUT', 'LM Studio ha agotado el tiempo de respuesta.')`
- linea 65: `raise LLMError('HTTP_ERROR', str(exc))`
- linea 86: `raise LLMError('INVALID_RESPONSE', 'Respuesta inválida de LM Studio.')`

#### Determinismo
- NO_DETERMINISTA: depende de red/modelo/servicio externo.

## CONTRATOS Y RIESGOS LOCALES
- INFORMATIVO: depende de servicios HTTP externos/locales y de timeouts.
