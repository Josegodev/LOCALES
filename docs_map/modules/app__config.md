# MODULO: app/config.py

## PROPOSITO
Configuracion Pydantic Settings cargada desde `.env` para LM Studio y Telegram.

## TRAZABILIDAD
- Archivo real: `app/config.py`
- Tamano: 540 B
- Lenguaje detectado: Python
- Parseo AST: OK

## IMPORTS
### Internos
- Ninguno detectado.

### Externos
- linea 1: `from pydantic_settings import BaseSettings`
- linea 1: `from pydantic_settings import SettingsConfigDict`

### Stdlib
- Ninguno detectado.

### Posibles acoplamientos peligrosos
- No se detectan imports ambiguos por nombre repetido.

## CLASES
### Settings
- Linea: 4
- Bases: `BaseSettings`
- Campos / atributos observados:
  - linea 5: `lmstudio_base_url: str = 'http://127.0.0.1:1234/v1'`
  - linea 6: `lmstudio_timeout_seconds: float = 60.0`
  - linea 7: `default_model: str = 'ibm/granite-3.2-8b'`
  - linea 9: `max_prompt_chars: int = 4000`
  - linea 10: `max_tokens: int = 512`
  - linea 11: `temperature: float = 0.2`
  - linea 13: `telegram_bot_token: str | None = None`
  - linea 14: `telegram_allowed_chat_ids: str | None = None`
  - linea 16: `model_config = SettingsConfigDict(env_file='.env', extra='forbid')`

## FUNCIONES
- Ninguna funcion de nivel modulo.
## CONTRATOS Y RIESGOS LOCALES
- No se detectan riesgos locales especificos mas alla de los efectos laterales documentados.
