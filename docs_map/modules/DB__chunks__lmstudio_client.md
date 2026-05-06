# MODULO: DB/chunks/lmstudio_client.py

## PROPOSITO
Modulo utilitario; proposito exacto derivado de sus funciones listadas.

## TRAZABILIDAD
- Archivo real: `DB/chunks/lmstudio_client.py`
- Tamano: 1.1 KB
- Lenguaje detectado: Python
- Parseo AST: OK

## IMPORTS
### Internos
- Ninguno detectado.

### Externos
- linea 1: `from __future__ import annotations`
- linea 3: `requests`

### Stdlib
- Ninguno detectado.

### Posibles acoplamientos peligrosos
- No se detectan imports ambiguos por nombre repetido.

## CLASES
- Ninguna clase definida.

## FUNCIONES
### ask_lmstudio()

#### Firma
```python
def ask_lmstudio(prompt: str, model: str=DEFAULT_MODEL, timeout: int=120) -> str
```
- Lineas: 10-42

#### Responsabilidad observada
Realiza llamada HTTP a un servicio externo/local y procesa la respuesta.

#### Entradas
- Argumentos declarados: `prompt: str, model: str=DEFAULT_MODEL, timeout: int=120`

#### Salida
- Anotacion de retorno: `str`

#### Efectos laterales
- I/O de red HTTP
- puede lanzar excepciones

#### Errores / excepciones
- linea 42: `raise RuntimeError(f'Respuesta inesperada de LM Studio: {data}') from exc`

#### Determinismo
- NO_DETERMINISTA: depende de red/modelo/servicio externo.

## CONTRATOS Y RIESGOS LOCALES
- CRITICO: default `local-model` no esta cerrado a un modelo real verificado; riesgo de comportamiento dependiente de LM Studio.
- INFORMATIVO: depende de servicios HTTP externos/locales y de timeouts.
