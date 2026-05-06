# Laboratorio local de persistencia para LM Studio

Este directorio contiene un laboratorio local para probar persistencia con SQLite uso eando LM Studio como servidor LLM compatible con la API de OpenAI.

El objetivsmodelo
- prompts y mantener separados tres tipos de datos:
- perfiles de  
- outputs brutos
- memoria persistente aprobada de forma explícita

La regla principal es simple: un prompt no es memoria, un output no es memoria y solo un `saved_text` aprobado manualmente entra en `memory.sqlite`.

## Objetivo del laboratorio

Este laboratorio sirve para:

- llamar a un modelo local servido por LM Studio mediante HTTP
- guardar cada prompt y output bruto en SQLite
- aprobar manualmente piezas concretas de texto como memoria persistente
- separar la persistencia por perfil/modelo mediante `slug`
- comprobar que un perfil no ve la memoria de otro perfil
- validar el comportamiento antes de añadir más infraestructura

No hay memoria automática, agentes, RAG, PostgreSQL ni servidor web.

## Arquitectura de carpetas

Estructura principal:

```text
DB/
  config.json
  db_store.py
  lmstudio_client.py
  setup_profile.py
  chat_once.py
  approve_memory.py
  prune.py
  registry.sqlite
  schemas/
    registry.sql
    raw.sql
    memory.sql
  profiles/
    <slug>/
      raw.sqlite
      memory.sqlite
```

`<slug>` es el identificador textual de un perfil. Por ejemplo:

```text
profiles/lmstudio_qwen35_9b_q4km_temp02/raw.sqlite
profiles/lmstudio_qwen35_9b_q4km_temp02/memory.sqlite
```

## Separación de responsabilidades

### `registry.sqlite`

Base de datos global del laboratorio.

Guarda los perfiles disponibles:

- `slug`
- runtime, por ejemplo `lmstudio`
- nombre del modelo
- parámetros del modelo en JSON
- prompt de sistema
- límites de retención RAW
- límite de memoria persistente
- estado activo/inactivo

No guarda prompts, outputs ni memoria.

### `profiles/<slug>/raw.sqlite`

Base de datos RAW de un perfil concreto.

Guarda:

- prompts de usuario
- outputs del modelo
- JSON de request enviado a LM Studio
- JSON de response recibido
- estado de la llamada: `ok` o `error`
- hash y tamaño del contenido
- marca `approved_for_memory`

`approved_for_memory` solo indica que un output fue usado como fuente para aprobar memoria. No convierte el output completo en memoria.

### `profiles/<slug>/memory.sqlite`

Base de datos de memoria aprobada de un perfil concreto.

Guarda:

- `saved_text`, que es el texto aprobado manualmente
- hash de `saved_text`
- `source_output_id`
- `source_output_hash`
- motivo opcional de aprobación
- estado activo

Esta base de datos no guarda prompts completos ni outputs completos salvo que el usuario los apruebe explícitamente como `saved_text`.

## Archivos Python

### `db_store.py`

Contiene la lógica de persistencia SQLite.

Responsabilidades principales:

- crear perfiles
- validar slugs
- inicializar schemas
- guardar prompts y outputs RAW
- aprobar memoria explícita
- consultar memoria aprobada
- podar datos RAW
- calcular estadísticas RAW y MEMORY

Es la capa central de almacenamiento. Los scripts CLI llaman a funciones de este archivo.

### `lmstudio_client.py`

Cliente HTTP mínimo para LM Studio.

Lee `config.json`, construye la URL `/chat/completions`, envía JSON por HTTP y valida que la respuesta tenga contenido textual.

### `setup_profile.py`

Crea un perfil de modelo.

Inicializa:

- entrada en `registry.sqlite`
- `profiles/<slug>/raw.sqlite`
- `profiles/<slug>/memory.sqlite`

También guarda parámetros como `temperature`, `top_p`, `max_tokens` y el prompt de sistema.

### `chat_once.py`

Ejecuta un prompt contra LM Studio usando un perfil existente.

Flujo:

1. carga el perfil desde `registry.sqlite`
2. lee memoria aprobada desde `memory.sqlite`
3. construye mensajes para LM Studio
4. llama al modelo
5. guarda prompt y output en `raw.sqlite`
6. imprime `prompt_id`, `output_id` y respuesta del modelo

Importante: aunque lee memoria aprobada para incluirla en contexto, no guarda memoria nueva.

### `approve_memory.py`

Aprueba manualmente un texto como memoria persistente.

Recibe:

- `--slug`
- `--output-id`
- `--text`
- `--reason`

Inserta `--text` como `saved_text` en `memory.sqlite` y marca el output RAW como aprobado. Al terminar imprime:

```text
memory_id=<id>
```

### `prune.py`

Poda datos RAW o muestra estadísticas.

Con `--stats` imprime dos bloques separados:

```text
RAW:
{...}

MEMORY:
{...}
```

Sin `--stats`, ejecuta la poda de RAW según los límites del perfil. La poda afecta a `raw.sqlite`, no a `memory.sqlite`.

## Schemas SQL

### `schemas/registry.sql`

Define `model_profiles`.

Esta tabla registra qué perfiles existen y con qué configuración deben ejecutarse.

### `schemas/raw.sql`

Define:

- `raw_prompts`
- `raw_outputs`

`raw_prompts` guarda prompts del usuario. `raw_outputs` guarda respuestas del modelo, payloads JSON, estado y relación con el prompt.

La relación usa clave foránea: si se borra un prompt RAW, sus outputs RAW asociados también se eliminan.

### `schemas/memory.sql`

Define `memory_items`.

Cada fila representa una memoria aprobada. `saved_text_hash` es único para evitar duplicados exactos dentro del perfil.

## Comandos de uso

Ejecuta los comandos desde `~/LOCALES/DB`:

```bash
cd ~/LOCALES/DB
```

### Verificar LM Studio

LM Studio debe estar escuchando en:

```text
http://127.0.0.1:1234/v1
```

Verificación básica:

```bash
curl http://127.0.0.1:1234/v1/models
```

El modelo validado hasta ahora es:

```text
qwen/qwen3.5-9b
```

### Crear perfil principal

```bash
python3 setup_profile.py \
  --slug lmstudio_qwen35_9b_q4km_temp02 \
  --model-name qwen/qwen3.5-9b \
  --temperature 0.2
```

Salida esperada:

```text
Perfil creado: id=<id>, slug=lmstudio_qwen35_9b_q4km_temp02
```

Si el perfil ya existe, no hace falta crearlo de nuevo.

### Lanzar un prompt

```bash
python3 chat_once.py \
  --slug lmstudio_qwen35_9b_q4km_temp02 \
  --prompt "Responde solo: OK"
```

Salida validada:

```text
prompt_id=1
output_id=1

OK
```

`prompt_id` y `output_id` pertenecen al `raw.sqlite` del perfil usado.

### Aprobar memoria

```bash
python3 approve_memory.py \
  --slug lmstudio_qwen35_9b_q4km_temp02 \
  --output-id 1 \
  --text 'El sistema separa prompts, outputs y memoria; solo el contenido aprobado se guarda como memoria persistente.' \
  --reason 'regla base'
```

Salida esperada:

```text
memory_id=<id>
```

Si el texto ya existe, el script debe fallar de forma explícita con un error de duplicado. Eso es correcto: no se debe cambiar el diseño para permitir duplicados.

### Consultar estadísticas

```bash
python3 prune.py \
  --slug lmstudio_qwen35_9b_q4km_temp02 \
  --stats
```

Salida esperada:

```text
RAW:
{
  ...
}

MEMORY:
{
  ...
}
```

### Podar RAW

```bash
python3 prune.py \
  --slug lmstudio_qwen35_9b_q4km_temp02
```

Salida esperada:

```text
PRUNE:
{
  "deleted_expired": <n>,
  "deleted_over_rows": <n>,
  "deleted_over_size": <n>
}
```

Esta operación debe borrar solo datos RAW que cumplan criterios de poda. No debe borrar memoria aprobada.

### Crear segundo perfil

```bash
python3 setup_profile.py \
  --slug lmstudio_qwen35_9b_q4km_temp07 \
  --model-name qwen/qwen3.5-9b \
  --temperature 0.7
```

Este perfil usa el mismo modelo, pero tiene su propio directorio:

```text
profiles/lmstudio_qwen35_9b_q4km_temp07/
```

Por tanto, tiene su propio `raw.sqlite` y su propio `memory.sqlite`.

### Validar aislamiento con CANARY

Se han usado marcas tipo CANARY para comprobar aislamiento entre perfiles.

Ejemplo de aprobación en `temp02`:

```bash
python3 approve_memory.py \
  --slug lmstudio_qwen35_9b_q4km_temp02 \
  --output-id <output_id_de_temp02> \
  --text 'CANARY_TEMP02_X7K9: memoria aprobada solo para el perfil temp02.' \
  --reason 'prueba aislamiento'
```

Consulta desde `temp02`:

```bash
python3 chat_once.py \
  --slug lmstudio_qwen35_9b_q4km_temp02 \
  --prompt "¿Qué sabes de CANARY_TEMP02_X7K9?"
```

Consulta desde `temp07`:

```bash
python3 chat_once.py \
  --slug lmstudio_qwen35_9b_q4km_temp07 \
  --prompt "¿Qué sabes de CANARY_TEMP02_X7K9?"
```

Resultado esperado:

- `temp02` puede ver sus memorias aprobadas
- `temp07` no debe ver memorias de `temp02`

## Reglas importantes

- Prompts no son memoria.
- Outputs no son memoria.
- Solo `saved_text` aprobado con `approve_memory.py` entra en `memory.sqlite`.
- `reasoning_content` no se usa como memoria.
- Cada `slug` tiene memoria aislada.
- Cada `slug` tiene su propio `raw.sqlite`.
- `output_id` es local al perfil, porque vive dentro del `raw.sqlite` de ese perfil.
- No se debe copiar memoria entre perfiles de forma implícita.
- No se debe guardar memoria automáticamente desde `chat_once.py`.

## Estado validado hasta ahora

Estado operativo validado:

- LM Studio funciona en `http://127.0.0.1:1234/v1`.
- Modelo usado: `qwen/qwen3.5-9b`.
- Perfil `lmstudio_qwen35_9b_q4km_temp02` existe y tiene memoria aprobada.
- Perfil `lmstudio_qwen35_9b_q4km_temp07` existe y no ve las marcas CANARY del perfil `temp02`.
- El perfil `temp02` contiene marcas `CANARY_TEMP02_X7K9` y `CANARY_TEMP02_R4M8`.
- Se validó que `temp02` ve sus memorias aprobadas.
- Se validó que `temp07` no ve memorias de `temp02`.
- Se validó que `raw.sqlite` crece con prompts y outputs.
- Se validó que `memory.sqlite` solo crece cuando se ejecuta `approve_memory.py`.

## Problemas encontrados y corregidos

- `approve_memory.py` estaba vacío.
- `prune.py` estaba vacío.
- Faltaban CLI y `main()` en esos scripts.
- Ejecutar desde `~/LOCALES` puede producir errores de ruta; el uso normal es desde `~/LOCALES/DB`.
- El perfil debe existir antes de usar `chat_once.py`; para eso se usa `setup_profile.py`.
- La CLI `sqlite3` del sistema no estaba instalada, pero el módulo `sqlite3` de Python funciona y es suficiente para este laboratorio.

## Siguientes pasos

Siguientes pasos posibles, manteniendo el laboratorio pequeño:

- validar `prune.py` borrando RAW sin tocar MEMORY
- añadir `list_profiles.py` o equivalente solo si se considera mínimo
- añadir un script de inspección de memoria solo si se considera mínimo
- probar un segundo modelo real, no solo un segundo perfil con distinta temperatura
- decidir si `reasoning_content` se guarda como dato experimental separado, no como memoria
- no introducir PostgreSQL salvo que aparezca concurrencia real
- no introducir RAG todavía
