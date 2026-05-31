# RAG y evidencia

## Estado actual

LOCALES tiene dos modos de retrieval:

- RAG local sobre SQLite.
- RAG remoto por HTTP que reutiliza el mismo motor documental.

En ambos casos, el objetivo es devolver contexto documental auditable antes de generar una respuesta con el modelo.

## Dónde están los documentos y chunks

### Almacenamiento principal detectado

- Base documental principal: `DB/chunks/documents.sqlite`
- Scripts de ingest:
  - `DB/chunks/ingest_all_pdfs.py`
  - `DB/chunks/ingest_pdf_markdown.py`
  - `DB/chunks/run_ingest_pipeline.py`
- PDFs detectados:
  - `DB/chunks/pdf/`
  - `DB/chunks/pdf metidos/`
- Markdown adicional detectado:
  - `DB/chunks/identity_nucleo_jose.md`

### Otras fuentes relacionadas

- `scripts/ingest_nucleo_md.py` parece cargar Markdown externo a SQLite.
- Esa ruta usa `MD_DIR = /home/jose-gonzalez-oliva/NUCLEO/docs`, por lo que su integración exacta con este repo requiere revisión manual.

## Cómo parece hacerse la recuperación

### Retrieval local

`DB/chunks/document_context.py` hace:

1. auditoría de la base SQLite;
2. normalización de la query;
3. extracción de términos;
4. expansión de términos;
5. detección de intención documental;
6. ranking de chunks;
7. filtrado opcional por documento activo;
8. construcción de un prompt enriquecido.

### Retrieval remoto

`rag_service/main.py`:

- recibe `query`, `top_k`, `trace_id` y filtros;
- llama al mismo `build_document_prompt(...)`;
- sanitiza los chunks antes de exponerlos;
- devuelve JSON al backend principal.

`app/rag_client.py`:

- consume `/rag/query`;
- ante timeout o error de red degrada a una respuesta controlada de `NO_EVIDENCE_FOR_ANSWER`.

## Contratos de evidencia detectados

Los siguientes campos existen de forma explícita en retrieval, runtime o respuesta pública:

| Campo | Estado |
| --- | --- |
| `retrieval_status` | Existe y es crítico. |
| `chunk_ids` | Existe. |
| `document_ids` | Existe. |
| `source_filenames` | Existe. |
| `chunks` | Existe. |
| `scores` | Existe. |
| `ranking_scores` | Existe. |
| `candidate_filenames` | Existe. |
| `selected_filenames` | Existe. |
| `query_original` | Existe. |
| `query_normalized` | Existe. |
| `query_terms` | Existe. |
| `quoted_terms` | Existe. |
| `source_intent` | Existe. |
| `selected_corpus` | Existe. |
| `active_document_id` | Existe. |
| `active_document_title` | Existe. |
| `active_context_used` | Existe. |
| `evidence_used` | Existe. |
| `fallback_used` | Existe. |

## Significado operativo de `retrieval_status`

Estados observados:

- `EVIDENCE_FOUND`
- `NO_EVIDENCE`
- `NO_EVIDENCE_FOR_ANSWER`
- `DISABLED`
- `RAG_ERROR` en capas internas

Normalización importante:

- El runtime y el servicio RAG normalizan variantes de no evidencia a `NO_EVIDENCE_FOR_ANSWER` para la superficie pública.

## Diferencia entre respuesta con evidencia y respuesta sin evidencia

### Respuesta basada en evidencia

Se da cuando:

- `retrieval_status == EVIDENCE_FOUND`
- hay chunks relevantes
- la respuesta final no queda reducida al marcador de no evidencia

Resultado esperado:

- `answer_mode = documentary_answer`
- `evidence_used = true`

### Safe refusal por falta de evidencia

Se da cuando:

- retrieval no encuentra evidencia suficiente;
- o la evidencia encontrada no pasa ciertas comprobaciones;
- o el modelo devuelve solo el marcador `NO_EVIDENCE_FOR_ANSWER`.

Resultado esperado:

- `answer_mode = safe_refusal`
- `fallback_used = true`
- evidencia pública limpiada

### Respuesta estándar sin modo documental

Se da cuando:

- el flujo no está en modo documental;
- o `use_rag=false`;
- o el `retrieval_status` no es `EVIDENCE_FOUND` pero tampoco exige marker-only safe refusal.

Resultado esperado:

- `answer_mode = standard_answer`

## Salvaguardas detectadas

- El runtime fuerza `NO_EVIDENCE_FOR_ANSWER` si los chunks no contienen ciertos términos ancla de la query.
- Hay filtrado por `allowed_source_filenames`.
- Hay lógica para contexto activo de documento cuando la consulta es corta o referencial.
- El servicio RAG remoto sanitiza las claves de cada chunk antes de devolverlas.

## Riesgos detectados

### Contaminación entre dominios documentales

- Existe intención `official_docs`, `nucleo` y `mixed`.
- Si no se usa allowlist, el sistema puede buscar en todo el corpus.
- Hay tests que demuestran este riesgo y el uso de `allowed_source_filenames` para mitigarlo.

### Chunks mal clasificados

- La clasificación por corpus y tipo depende de metadata y nombres/rutas.
- Si los documentos entran con nombres ambiguos, el ranking puede sesgarse mal.

### Evidencia insuficiente con apariencia de éxito

- Puede haber `EVIDENCE_FOUND` inicial y luego degradación a `NO_EVIDENCE_FOR_ANSWER` si el contenido no pasa validación adicional.

### Respuestas sin fuente clara

- El contrato incluye `source_filenames`, pero la trazabilidad final depende de que el retrieval los pueble bien.

### Drift entre rutas de retrieval

- Local y remoto comparten motor, lo cual reduce drift.
- Aun así, el cliente remoto y el backend pueden divergir en warnings o campos auxiliares.

## Recomendaciones incrementales de hardening

1. Cerrar formalmente el vocabulario permitido de `retrieval_status`.
2. Exigir que toda respuesta `documentary_answer` lleve al menos un `source_filename` o `chunk_id`.
3. Hacer explícito en tests cuándo `EVIDENCE_FOUND` debe degradarse a `NO_EVIDENCE_FOR_ANSWER`.
4. Consolidar la configuración de corpus y allowlists para que no exista más de una ruta semántica.
5. Añadir una verificación ligera de “evidencia mínima” antes de persistir runs exitosos.

## Incertidumbres

- `scripts/ingest_nucleo_md.py` apunta a una ruta externa a este repo; su uso operativo actual queda `pendiente de confirmar`.
- No se ha verificado aquí el contenido exacto del esquema SQLite, solo su uso por código y tests.

## Relacionado

- [[RUNTIME_FLOW]]
- [[OBSERVABILITY]]
- [[TECH_DEBT_AND_RISKS]]
- [[GLOSSARY]]
