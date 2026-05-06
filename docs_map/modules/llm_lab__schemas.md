# MODULO: llm_lab/schemas.py

## PROPOSITO
Contratos JSON compartidos de llm_lab y fallbacks.

## TRAZABILIDAD
- Archivo real: `llm_lab/schemas.py`
- Tamano: 1.5 KB
- Lenguaje detectado: Python
- Parseo AST: OK

## IMPORTS
### Internos
- Ninguno detectado.

### Externos
- linea 7: `from __future__ import annotations`

### Stdlib
- linea 9: `copy`
- linea 10: `from dataclasses import dataclass`
- linea 11: `from typing import Any`

### Posibles acoplamientos peligrosos
- No se detectan imports ambiguos por nombre repetido.

## CLASES
### ValidationResult
- Linea: 40
- Bases: `sin base explicita`
- Campos / atributos observados:
  - linea 43: `validated_output: JSONDict`
  - linea 44: `fallback_used: bool`
  - linea 45: `fallback_reason: str | None = None`

## FUNCIONES
### proposal_fallback()

#### Firma
```python
def proposal_fallback(reason: str='validation_failed') -> JSONDict
```
- Lineas: 48-52

#### Responsabilidad observada
Responsabilidad derivada del nombre y cuerpo; ver efectos laterales y llamadas para detalle exacto.

#### Entradas
- Argumentos declarados: `reason: str='validation_failed'`

#### Salida
- Anotacion de retorno: `JSONDict`

#### Efectos laterales
- sin efectos externos evidentes por lectura estatica

#### Errores / excepciones
- no se observan `raise` directos en esta funcion

#### Determinismo
- DETERMINISTA para las mismas entradas y mismo estado en memoria.

### answer_fallback()

#### Firma
```python
def answer_fallback(reason: str='validation_failed') -> JSONDict
```
- Lineas: 55-59

#### Responsabilidad observada
Responsabilidad derivada del nombre y cuerpo; ver efectos laterales y llamadas para detalle exacto.

#### Entradas
- Argumentos declarados: `reason: str='validation_failed'`

#### Salida
- Anotacion de retorno: `JSONDict`

#### Efectos laterales
- sin efectos externos evidentes por lectura estatica

#### Errores / excepciones
- no se observan `raise` directos en esta funcion

#### Determinismo
- DETERMINISTA para las mismas entradas y mismo estado en memoria.

## CONTRATOS Y RIESGOS LOCALES
- No se detectan riesgos locales especificos mas alla de los efectos laterales documentados.
