# DEBUG_UI_BACKEND_FAILURE

## Objetivo

Diagnosticar por qué la UI no consigue completar el viaje hasta el backend.

## Checklist

1. revisar `frontend/runtime-config.js`
2. validar `Backend base URL`
3. probar `GET /health`
4. revisar timeout del fetch
5. revisar auth token si aplica
6. diferenciar error local de UI vs respuesta HTTP del backend

## Señales observadas en UI

- `invalid_backend_base_url`
- `backend_base_url_missing`
- `request_timeout`
- `401 Unauthorized`
- `403 Forbidden`

## Relacionado

- [[UI]]
- [[FASTAPI]]
- [[UI_TO_RESPONSE]]
