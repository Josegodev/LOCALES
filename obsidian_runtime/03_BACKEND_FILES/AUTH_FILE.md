# app/auth.py

## Ruta real

`app/auth.py`

## Responsabilidad observada

Controla el acceso al endpoint `/chat` antes de entrar al runtime.

## Símbolos relevantes

- `bearer_scheme`
- `require_chat_access(...)`

## Quién lo llama

- `app/api/routes_chat.py`
- otros routers de runs si aplican

## Entradas

- header `Authorization`
- configuración de auth

## Salidas

- permite continuar o lanza error HTTP

## Riesgos

- una configuración incorrecta bloquea todo el flujo antes del runtime

## Relacionado

- [[FASTAPI]]
- [[ERRORS]]
- [[DEBUG_UI_BACKEND_FAILURE]]
