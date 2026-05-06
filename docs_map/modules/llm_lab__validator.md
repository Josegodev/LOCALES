# MODULO: llm_lab/validator.py

## PROPOSITO
Validador de JSON de salida de modelos en llm_lab con fallback determinista.

## TRAZABILIDAD
- Archivo real: `llm_lab/validator.py`
- Tamano: 2.5 KB
- Lenguaje detectado: Python
- Parseo AST: OK

## IMPORTS
### Internos
- linea 12: `from .schemas import JSONDict`
- linea 12: `from .schemas import ValidationResult`
- linea 12: `from .schemas import answer_fallback`
- linea 12: `from .schemas import proposal_fallback`

### Externos
- linea 7: `from __future__ import annotations`

### Stdlib
- linea 9: `json`
- linea 10: `from typing import Any`

### Posibles acoplamientos peligrosos
- Linea 12: import bare `schemas`; AMBIGUO si se ejecuta desde otro cwd porque hay nombres repetidos en el repo.
- Linea 12: import bare `schemas`; AMBIGUO si se ejecuta desde otro cwd porque hay nombres repetidos en el repo.
- Linea 12: import bare `schemas`; AMBIGUO si se ejecuta desde otro cwd porque hay nombres repetidos en el repo.
- Linea 12: import bare `schemas`; AMBIGUO si se ejecuta desde otro cwd porque hay nombres repetidos en el repo.

## CLASES
- Ninguna clase definida.

## FUNCIONES
### validate_proposal_output()

#### Firma
```python
def validate_proposal_output(raw_output: str) -> ValidationResult
```
- Lineas: 15-24

#### Responsabilidad observada
Valida estructura de datos y produce aceptacion/fallback segun contrato local.

#### Entradas
- Argumentos declarados: `raw_output: str`

#### Salida
- Anotacion de retorno: `ValidationResult`

#### Efectos laterales
- sin efectos externos evidentes por lectura estatica

#### Errores / excepciones
- no se observan `raise` directos en esta funcion

#### Determinismo
- DETERMINISTA para las mismas entradas y mismo estado en memoria.

### validate_answer_output()

#### Firma
```python
def validate_answer_output(raw_output: str) -> ValidationResult
```
- Lineas: 27-36

#### Responsabilidad observada
Valida estructura de datos y produce aceptacion/fallback segun contrato local.

#### Entradas
- Argumentos declarados: `raw_output: str`

#### Salida
- Anotacion de retorno: `ValidationResult`

#### Efectos laterales
- sin efectos externos evidentes por lectura estatica

#### Errores / excepciones
- no se observan `raise` directos en esta funcion

#### Determinismo
- DETERMINISTA para las mismas entradas y mismo estado en memoria.

### _parse_json_object()

#### Firma
```python
def _parse_json_object(raw_output: str) -> JSONDict | None
```
- Lineas: 39-47

#### Responsabilidad observada
Responsabilidad derivada del nombre y cuerpo; ver efectos laterales y llamadas para detalle exacto.

#### Entradas
- Argumentos declarados: `raw_output: str`

#### Salida
- Anotacion de retorno: `JSONDict | None`

#### Efectos laterales
- sin efectos externos evidentes por lectura estatica

#### Errores / excepciones
- no se observan `raise` directos en esta funcion

#### Determinismo
- DETERMINISTA para las mismas entradas y mismo estado en memoria.

### _is_valid_proposal()

#### Firma
```python
def _is_valid_proposal(data: dict[str, Any]) -> bool
```
- Lineas: 50-57

#### Responsabilidad observada
Valida estructura de datos y produce aceptacion/fallback segun contrato local.

#### Entradas
- Argumentos declarados: `data: dict[str, Any]`

#### Salida
- Anotacion de retorno: `bool`

#### Efectos laterales
- sin efectos externos evidentes por lectura estatica

#### Errores / excepciones
- no se observan `raise` directos en esta funcion

#### Determinismo
- DETERMINISTA para las mismas entradas y mismo estado en memoria.

### _is_valid_answer()

#### Firma
```python
def _is_valid_answer(data: dict[str, Any]) -> bool
```
- Lineas: 60-65

#### Responsabilidad observada
Valida estructura de datos y produce aceptacion/fallback segun contrato local.

#### Entradas
- Argumentos declarados: `data: dict[str, Any]`

#### Salida
- Anotacion de retorno: `bool`

#### Efectos laterales
- sin efectos externos evidentes por lectura estatica

#### Errores / excepciones
- no se observan `raise` directos en esta funcion

#### Determinismo
- DETERMINISTA para las mismas entradas y mismo estado en memoria.

### _is_valid_meta()

#### Firma
```python
def _is_valid_meta(meta: Any) -> bool
```
- Lineas: 68-78

#### Responsabilidad observada
Valida estructura de datos y produce aceptacion/fallback segun contrato local.

#### Entradas
- Argumentos declarados: `meta: Any`

#### Salida
- Anotacion de retorno: `bool`

#### Efectos laterales
- sin efectos externos evidentes por lectura estatica

#### Errores / excepciones
- no se observan `raise` directos en esta funcion

#### Determinismo
- DETERMINISTA para las mismas entradas y mismo estado en memoria.

### _is_confidence()

#### Firma
```python
def _is_confidence(value: Any) -> bool
```
- Lineas: 81-84

#### Responsabilidad observada
Responsabilidad derivada del nombre y cuerpo; ver efectos laterales y llamadas para detalle exacto.

#### Entradas
- Argumentos declarados: `value: Any`

#### Salida
- Anotacion de retorno: `bool`

#### Efectos laterales
- sin efectos externos evidentes por lectura estatica

#### Errores / excepciones
- no se observan `raise` directos en esta funcion

#### Determinismo
- DETERMINISTA para las mismas entradas y mismo estado en memoria.

## CONTRATOS Y RIESGOS LOCALES
- No se detectan riesgos locales especificos mas alla de los efectos laterales documentados.
