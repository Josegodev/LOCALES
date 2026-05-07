# Contrato de integracion Codex (HARDENING)

Este directorio define reglas de trabajo para Codex. No modifica el runtime.

## Fronteras deterministas
- Runtime operativo: `app/` y `scripts/run_telegram.py`.
- Laboratorio LLM: `llm_lab/` y `DB/`.
- No mezclar dependencias de laboratorio en runtime sin solicitud explicita.

## Restricciones operativas
- No ejecutar procesos en segundo plano.
- No introducir ejecucion autonoma.
- No guardar estado oculto fuera del repositorio y variables de entorno.

## Contratos de cambio
- Preferir cambios pequenos, validaciones explicitas y errores descriptivos.
- Mantener `approval_mode = "manual"` y `sandbox = true` en `.codex/config.toml`.
- Si un contrato no existe en codigo (por ejemplo `PolicyEngine` o `ToolRegistry`), marcarlo como `PREMATURO` y no inventarlo.
