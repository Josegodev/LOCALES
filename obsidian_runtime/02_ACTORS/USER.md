# USER

## Responsabilidad

Inicia la petición desde la UI y consume la respuesta renderizada.

## Entradas

- escribe `message`
- elige modelo
- decide si activa RAG
- puede prefijar `/creardoc`

## Salidas

- produce una intención de chat o de tool
- recibe `answer`, `trace_id`, `retrieval_status`, evidencia y errores visibles

## Módulos relacionados

- `frontend/index.html`
- `frontend/app.js`

## Fallos posibles

- enviar sin mensaje
- enviar con backend base URL inválida
- usar un modelo no disponible en el backend

## Relacionado

- [[UI]]
- [[UI_TO_RESPONSE]]
- [[DEBUG_UI_BACKEND_FAILURE]]
