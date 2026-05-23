# Cloudflare Tunnel + Vercel demo

## Problema que resuelve

En este modo de demo el frontend corre en HTTPS dentro de Vercel y el backend FastAPI corre localmente en `127.0.0.1:8000`.

El túnel de Cloudflare publica temporalmente ese backend local con una URL HTTPS pública tipo:

- `https://xxxxx.trycloudflare.com`

La URL que debes pegar en el frontend es **solo esa URL pública**. No pegues el comando de terminal.

## Levantar backend local

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Comprobación local:

```bash
curl -i http://127.0.0.1:8000/health
```

Respuesta esperada:

- HTTP `200`
- body con `{"status":"ok"}`

## Levantar Cloudflare Tunnel

```bash
cloudflared tunnel --url http://127.0.0.1:8000
```

Cloudflare mostrará una URL pública parecida a:

- `https://sender-turned-editorial-among.trycloudflare.com`

## Qué pegar en el frontend de Vercel

Pega únicamente:

```text
https://sender-turned-editorial-among.trycloudflare.com
```

No pegues esto:

```text
cloudflared tunnel --url http://127.0.0.1:8000
```

Ese comando se ejecuta en terminal. No es una URL pública consumible por el frontend.

## Por qué `/` y `/health` no significan lo mismo

- `/health` es la prueba correcta de disponibilidad del backend.
- `/docs` sirve para comprobar que FastAPI sigue expuesto.
- `/` ahora devuelve JSON informativo para evitar confusión al abrir la base del túnel en navegador.

Comprobaciones recomendadas:

```bash
curl -i http://127.0.0.1:8000/health
curl -i https://xxxxx.trycloudflare.com/health
```

Y además:

- abrir `https://xxxxx.trycloudflare.com/docs`

## Cómo detectar CORS desde DevTools

Señales habituales:

- `Failed to fetch`
- petición `OPTIONS` rechazada
- ausencia de `access-control-allow-origin`

En el navegador:

1. abre DevTools
2. ve a la pestaña `Network`
3. localiza la petición a `/health` o `/chat`
4. revisa `Status`, `Response Headers` y errores de consola

## Checklist rápido

1. `curl -i http://127.0.0.1:8000/health`
2. `curl -i https://xxxxx.trycloudflare.com/health`
3. abrir `https://xxxxx.trycloudflare.com/docs`
4. pegar solo `https://xxxxx.trycloudflare.com` en `Backend base URL`
5. pulsar `Health`
6. comprobar en consola del navegador:
   - `[backend] raw base url`
   - `[backend] normalized base url`
   - `[backend] health url`
   - `[backend] docs url`

## CORS en modo demo

Si el frontend en Vercel sigue fallando aunque `/health` responda desde terminal:

- revisa `FRONTEND_ALLOWED_ORIGINS`
- comprueba si incluye el dominio real de Vercel
- para demo controlada puedes usar:

```text
FRONTEND_ALLOWED_ORIGINS=*
```

Eso es útil para pruebas rápidas, pero conviene cerrar la lista de orígenes en entornos más estables.
