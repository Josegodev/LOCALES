# Remote RAG Service

## Estado actual entendido

El corpus RAG vive en Linux junto con SQLite y los PDFs. FastAPI puede seguir usando RAG local por defecto, pero cuando `USE_REMOTE_RAG=true` consulta el servicio HTTP remoto. El RAG remoto conserva paridad de filtro por fuente con el RAG local mediante `allowed_source_filenames`.

## Ejecutar en Linux

Ejecuta el servicio RAG en la maquina que tiene `DB/chunks/documents.sqlite` y los documentos:

```bash
export DOCUMENTS_DB_PATH=DB/chunks/documents.sqlite
python3 -m uvicorn rag_service.main:app --host 0.0.0.0 --port 9000
```

Si es posible, limita el bind o el firewall a la LAN. No expongas este puerto a Internet.

## Ejecutar FastAPI en Windows

```bat
set USE_REMOTE_RAG=true
set RAG_SERVICE_URL=http://192.168.1.51:9000
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Comprobar salud

Desde Windows:

```bash
curl http://192.168.1.51:9000/rag/health
```

La respuesta debe incluir `status: ok` y `retrieval_ready: true` cuando la base contiene documentos y chunks.

## Probar chat con RAG remoto

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d "{\"message\":\"Que es un transformer?\",\"use_rag\":true}"
```

Si el servicio remoto no responde, `/chat` sigue contestando con fallback del modelo y una advertencia `RAG_SERVICE_UNAVAILABLE`.

## Filtrar por fuentes

`/rag/query` acepta `allowed_source_filenames` con nombres de archivo permitidos:

```json
{
  "query": "runtime planner policy",
  "top_k": 5,
  "trace_id": "12345678123456781234567812345678",
  "allowed_source_filenames": ["NUCLEO_RUNTIME.md"]
}
```

Si `allowed_source_filenames` es `null` o una lista vacia, el servicio busca en todo el corpus. Si la lista contiene nombres, solo devuelve chunks de esos archivos. Si no hay chunks coincidentes, responde `NO_EVIDENCE_FOR_ANSWER` sin warning adicional.

## Limitaciones conocidas

El cliente remoto envia `query`, `top_k`, `trace_id` y `allowed_source_filenames`. El contexto activo de documento se conserva en modo local, pero todavia no se envia al servicio remoto.
