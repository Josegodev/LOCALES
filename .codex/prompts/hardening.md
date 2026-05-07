# Checklist de hardening para Codex

## Antes de editar
1. Confirmar archivo objetivo y frontera (`runtime` vs `llm_lab`).
2. Identificar riesgo tecnico concreto y contrato afectado.
3. Elegir el cambio minimo verificable.

## Durante la edicion
- No anadir frameworks ni capas nuevas.
- No tocar logica de runtime si el cambio es de integracion Codex.
- No iniciar servicios ni procesos de larga vida.

## Despues de editar
- Mostrar un diff corto y legible.
- Ejecutar validacion minima del archivo editado.
- Documentar riesgos de drift si hay decisiones duplicadas.
