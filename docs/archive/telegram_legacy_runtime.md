# Telegram Legacy Runtime

Telegram fue retirado del repositorio operativo y ya no forma parte del contrato activo de FastAPI.

Estado actual:

- `app/main.py` no importa módulos Telegram
- FastAPI no expone rutas `/telegram/*`
- FastAPI no expone rutas de eval legacy
- el frontend principal no llama a endpoints Telegram ni eval legacy
- el contrato chat-only es la única ruta soportada

Motivo de este archivo:

- dejar constancia breve de que Telegram existió
- explicar que la retirada fue intencional
- evitar que futuras refactorizaciones intenten reactivarlo por accidente

## Relacionado

- [[README]]
- [[ARCHITECTURE]]
- [[GLOSSARY]]
