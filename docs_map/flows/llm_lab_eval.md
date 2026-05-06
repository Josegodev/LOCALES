# Flujo: llm_lab validacion y evaluacion

```text
POST /model/proposal o /model/answer
  -> _proposal_core/_answer_core
  -> ModelAdapter.generate_*
  -> raw_output
  -> validator.validate_*_output
  -> fallback determinista si falla
  -> artifacts/*.json trace
```

## Contratos

- Los mocks son deterministas por `model_id`.
- Proveedores locales se seleccionan con `LLM_LAB_PROVIDER`, `LLM_LAB_ENDPOINT`, `LLM_LAB_MODEL`.
- Toda salida vuelve como JSON validado o fallback.

## Riesgos

- El timeout local es 10 segundos por defecto.
- Si se usa LM Studio real, la salida vuelve a ser no determinista aunque el validador cierre el contrato.
