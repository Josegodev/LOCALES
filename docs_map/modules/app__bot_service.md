# MODULO: app/bot_service.py

## PROPOSITO
Modulo utilitario; proposito exacto derivado de sus funciones listadas.

## TRAZABILIDAD
- Archivo real: `app/bot_service.py`
- Tamano: 79 B
- Lenguaje detectado: Python
- Parseo AST: OK

## IMPORTS
### Internos
- Ninguno detectado.

### Externos
- Ninguno detectado.

### Stdlib
- Ninguno detectado.

### Posibles acoplamientos peligrosos
- No se detectan imports ambiguos por nombre repetido.

## CLASES
- Ninguna clase definida.

## FUNCIONES
### build_llm_prompt()

#### Firma
```python
def build_llm_prompt(user_message: str) -> str
```
- Lineas: 1-2

#### Responsabilidad observada
Construye estructura o payload usado por otra capa.

#### Entradas
- Argumentos declarados: `user_message: str`

#### Salida
- Anotacion de retorno: `str`

#### Efectos laterales
- sin efectos externos evidentes por lectura estatica

#### Errores / excepciones
- no se observan `raise` directos en esta funcion

#### Determinismo
- DETERMINISTA para las mismas entradas y mismo estado en memoria.

## CONTRATOS Y RIESGOS LOCALES
- No se detectan riesgos locales especificos mas alla de los efectos laterales documentados.
