# DEBUG_CHAT_FAILURE

## Objetivo

Diagnosticar un fallo general en `POST /chat`.

## Checklist

1. comprobar base URL y `GET /health`
2. confirmar que el payload contiene `message` y `model`
3. revisar `trace_id` en la respuesta o en el error
4. distinguir si falló antes o dentro del runtime
5. revisar `retrieval_status`
6. revisar si hubo persistencia del run

## Preguntas clave

- ¿falla la UI o el backend?
- ¿es `422`, `403`, `400`, `5xx`?
- ¿llega a llamarse al modelo?
- ¿hay `safe_refusal` o error duro?

## Relacionado

- [[UI_TO_RESPONSE]]
- [[POST_CHAT_FLOW]]
- [[ERRORS]]
