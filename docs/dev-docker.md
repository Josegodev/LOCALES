# Docker dev local

## Objetivo

Este flujo levanta tres servicios de desarrollo con un solo comando:

- `backend` en `http://localhost:8000`
- `rag` en `http://localhost:8001`
- `frontend` en `http://localhost:3000`

Se mantiene `Ollama` fuera de Docker y el backend lo consulta en `http://host.docker.internal:11434`.

## Estado actual entendido

Contratos reales detectados en el repo:

- frontend estático en `frontend/`
- backend principal en `app.main:app`
- RAG remoto en `rag_service.main:app`
- healthchecks en `/health`
- base documental en `DB/chunks/documents.sqlite`
- runs persistidos en `CHAT_RUNS/`
- documentos generados en `outputs/documents/`

Importante:

- `CHAT_RUNS_PATH` apunta a `CHAT_RUNS`, no a `outputs/chat_runs`
- la salida documental no usa variable de entorno; hoy está fijada en `outputs/documents/`

## Cómo levantar

```bash
docker compose -f docker-compose.dev.yml up --build
```

## Cómo parar

```bash
docker compose -f docker-compose.dev.yml down
```

## Cómo ver logs

```bash
docker compose -f docker-compose.dev.yml logs -f backend
docker compose -f docker-compose.dev.yml logs -f rag
docker compose -f docker-compose.dev.yml logs -f frontend
```

## Cómo entrar al contenedor

```bash
docker compose -f docker-compose.dev.yml exec backend sh
docker compose -f docker-compose.dev.yml exec rag sh
docker compose -f docker-compose.dev.yml exec frontend sh
```

## Cómo comprobar backend -> rag

Desde el host:

```bash
curl http://localhost:8001/health
```

Desde el contenedor backend:

```bash
docker compose -f docker-compose.dev.yml exec backend curl http://rag:8001/health
```

Si la imagen no trae `curl`, usa Python:

```bash
docker compose -f docker-compose.dev.yml exec backend python -c "import urllib.request; print(urllib.request.urlopen('http://rag:8001/health').read().decode())"
```

## Cómo comprobar backend -> Ollama host

```bash
docker compose -f docker-compose.dev.yml exec backend curl http://host.docker.internal:11434/api/tags
```

Alternativa con Python:

```bash
docker compose -f docker-compose.dev.yml exec backend python -c "import urllib.request; print(urllib.request.urlopen('http://host.docker.internal:11434/api/tags').status)"
```

Si `Ollama` no está arrancado, el backend seguirá resolviendo la URL correcta pero devolverá errores explícitos del adaptador, por ejemplo `Ollama no disponible`.

## Persistencia en desarrollo

El compose monta bind mounts para no perder estado:

- `.:/app`
- `./DB:/app/DB`
- `./outputs:/app/outputs`
- `./evals:/app/evals`
- `./CHAT_RUNS:/app/CHAT_RUNS`

## Notas de hardening

- `backend` usa `RAG_SERVICE_URL=http://rag:8001` para evitar rutas hardcodeadas al host
- `frontend` usa `http://localhost:8000` porque el navegador no puede resolver el nombre Docker `backend`
- `uvicorn --reload` observa carpetas de código y excluye `documents.sqlite` para evitar recargas espurias por escritura de datos
