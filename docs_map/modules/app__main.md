# MODULO: app/main.py

## PROPOSITO
FastAPI productiva local: expone health, escritura de documentos desde Telegram y chat RAG contra LM Studio.

## TRAZABILIDAD
- Archivo real: `app/main.py`
- Tamano: 2.5 KB
- Lenguaje detectado: Python
- Parseo AST: OK

## IMPORTS
### Internos
- linea 2: `from DB.chunks.document_context import build_document_prompt`
- linea 3: `from app.config import settings`
- linea 4: `from app.schemas import ChatRequest`
- linea 4: `from app.schemas import ChatResponse`
- linea 5: `from app.lmstudio_client import ask_lmstudio`
- linea 5: `from app.lmstudio_client import LLMError`
- linea 7: `from app.schemas import DocumentCreateRequest`
- linea 7: `from app.schemas import DocumentCreateResponse`
- linea 8: `from app.document_writer import create_document`
- linea 8: `from app.document_writer import DocumentWriteError`

### Externos
- linea 1: `from fastapi import FastAPI`
- linea 1: `from fastapi import HTTPException`
- linea 6: `from fastapi import HTTPException`

### Stdlib
- Ninguno detectado.

### Posibles acoplamientos peligrosos
- No se detectan imports ambiguos por nombre repetido.

## CLASES
- Ninguna clase definida.

## FUNCIONES
### health()

#### Firma
```python
def health() -> dict
```
- Lineas: 15-16
- Decoradores: `app.get('/health')`

#### Responsabilidad observada
Gestiona una superficie HTTP o validacion asociada a endpoint FastAPI, segun decoradores y excepciones observadas.

#### Entradas
- Argumentos declarados: ``

#### Salida
- Anotacion de retorno: `dict`

#### Efectos laterales
- sin efectos externos evidentes por lectura estatica

#### Errores / excepciones
- no se observan `raise` directos en esta funcion

#### Determinismo
- DETERMINISTA para las mismas entradas y mismo estado en memoria.

### create_document_endpoint()

#### Firma
```python
def create_document_endpoint(request: DocumentCreateRequest) -> DocumentCreateResponse
```
- Lineas: 20-43
- Decoradores: `app.post('/documents', response_model=DocumentCreateResponse)`

#### Responsabilidad observada
Gestiona una superficie HTTP o validacion asociada a endpoint FastAPI, segun decoradores y excepciones observadas.

#### Entradas
- Argumentos declarados: `request: DocumentCreateRequest`

#### Salida
- Anotacion de retorno: `DocumentCreateResponse`

#### Efectos laterales
- puede lanzar excepciones

#### Errores / excepciones
- linea 28: `raise HTTPException(status_code=400, detail={'status': 'error', 'code': exc.code, 'message': exc.detail})`
- linea 37: `raise HTTPException(status_code=500, detail={'code': 'document_write_internal_error', 'message': str(e)})`

#### Determinismo
- DETERMINISTA para las mismas entradas y mismo estado en memoria.

### chat()

#### Firma
```python
def chat(request: ChatRequest) -> ChatResponse
```
- Lineas: 46-84
- Decoradores: `app.post('/chat', response_model=ChatResponse)`

#### Responsabilidad observada
Gestiona una superficie HTTP o validacion asociada a endpoint FastAPI, segun decoradores y excepciones observadas.

#### Entradas
- Argumentos declarados: `request: ChatRequest`

#### Salida
- Anotacion de retorno: `ChatResponse`

#### Efectos laterales
- salida por stdout/stderr
- puede lanzar excepciones

#### Errores / excepciones
- linea 77: `raise HTTPException(status_code=502, detail={'status': 'error', 'code': exc.code, 'message': exc.message})`

#### Determinismo
- NO_DETERMINISTA: depende de red/modelo/servicio externo.

## CONTRATOS Y RIESGOS LOCALES
- CRITICO: `HTTPException` se importa dos veces; no rompe runtime, pero indica drift de edicion.
- CRITICO: `ChatResponse` no declara `retrieval_status` ni `chunks`, pero el endpoint intenta pasarlos; Pydantic puede descartarlos o fallar segun configuracion/version. AMBIGUO sin ejecutar version exacta.
- INFORMATIVO: `/chat` usa contrato `message/model`, distinto del `/chat` de `DB/api_server.py` que usa `slug/prompt`.
