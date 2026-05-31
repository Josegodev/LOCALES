# Evolución realista hacia un sistema agentic

## Principio rector

La evolución razonable para este repo no es “añadir agentes” de golpe. Es cerrar contratos, reducir acoplamiento y hacer la ejecución auditable antes de introducir autonomía.

## Fase 0: Monolito instrumentado

### Objetivo

Mantener `FastAPI + runtime` actual y endurecerlo.

### Cambios mínimos

- cerrar vocabularios de `retrieval_status`, `answer_mode` y `error_code`;
- consolidar una sola fuente canónica de runs/traces;
- cerrar el contrato público de `ChatRequest` y `ChatResponse`;
- documentar y probar mejor `/creardoc`.

### Riesgos

- seguir con lógica concentrada en `app/chat_runtime.py`;
- drift entre observabilidad y evals;
- ambigüedad entre runs, traces y eval runs.

### Métricas necesarias

- tasa de error;
- p95 de latencia;
- ratio de fallback;
- ratio de no evidencia;
- porcentaje de runs con evidencia trazable.

### Criterio para pasar a la siguiente fase

- contratos públicos estables;
- observabilidad mínima coherente;
- tests de regresión cubriendo errores frecuentes.

## Fase 1: Runtime explícito

### Objetivo

Separar mejor orquestación de endpoints sin cambiar el contrato público.

### Cambios mínimos

- consolidar `ChatService` como punto único de ejecución;
- seguir sacando lógica de `app/chat_runtime.py` a módulos ya existentes;
- dejar `app/api/` como capa HTTP pura;
- definir un runtime interno explícito, por ejemplo `ChatRuntime`, solo si se justifica por código existente.

### Riesgos

- crear una abstracción grande demasiado pronto;
- mover lógica sin cerrar antes los contratos.

### Métricas necesarias

- tamaño y complejidad del runtime;
- número de dependencias directas del orquestador;
- cobertura de tests del flujo principal.

### Criterio para pasar a la siguiente fase

- una sola ruta interna de ejecución de chat;
- dependencias explícitas e inyectables;
- persistencia y logging fuera del bloque principal cuando sea posible.

## Fase 2: Herramientas controladas

### Objetivo

Introducir herramientas de forma explícita y auditable, sin autonomía abierta.

### Cambios mínimos

- definir un registro simple de herramientas permitidas;
- validar argumentos de cada tool;
- registrar cada tool call con `trace_id`;
- cerrar contrato de entrada y salida de tool.

### Riesgos

- dispersar tools por el runtime sin un contrato común;
- permitir ejecución implícita no auditable.

### Métricas necesarias

- número de tool calls;
- tasa de error por tool;
- latencia por tool;
- persistencia del resultado de tool.

### Criterio para pasar a la siguiente fase

- tools explícitas, validadas y observables;
- cero tool calls “mágicas” fuera de contrato.

## Fase 3: Planner limitado

### Objetivo

Introducir planificación simple, pequeña y auditable.

### Cambios mínimos

- planner determinista o semideterminista con planes cortos;
- cada paso debe tener validación previa;
- política de aprobación explícita antes de acciones sensibles;
- trazabilidad paso a paso.

### Riesgos

- meter un planner antes de tener observabilidad suficiente;
- convertir el runtime en una caja negra difícil de depurar.

### Métricas necesarias

- pasos por plan;
- porcentaje de planes abortados;
- tool calls por plan;
- errores por fase de plan.

### Criterio para pasar a la siguiente fase

- planes pequeños y repetibles;
- auditoría clara de cada decisión;
- límites explícitos de autonomía.

## Fase 4: Sistema agentic operacional

### Objetivo

Separar responsabilidades internas sin vender humo ni romper el contrato actual.

### Cambios mínimos

- separar `Planner`, `PolicyEngine`, `ToolRegistry`, `Memory`, `Evaluator`;
- mantener una capa runtime que coordine esas piezas;
- observabilidad por paso;
- evaluación de outputs;
- límites de coste y tiempo;
- política de fallback y aprobación.

### Riesgos

- expansión arquitectónica prematura;
- acoplar memoria, policy y tools sin contratos cerrados;
- multiplicar estados difíciles de probar.

### Métricas necesarias

- coste por ejecución;
- tiempo por paso;
- ratio de pasos fallidos;
- fallback por política;
- tool success rate;
- calidad de output evaluada.

### Criterio de madurez

- cada paso auditable;
- cada decisión explicable;
- cada herramienta permitida explícitamente;
- límites operativos efectivos.

## Qué ya existe hoy y ayuda a esta evolución

- `ChatDependencies`: inicio de dependencias explícitas.
- `app/chat/`: primeras extracciones del runtime.
- contratos tipados en `app/schemas.py`.
- persistencia local de runs.
- tests de contrato.

## Qué no existe todavía como sistema agentic estructurado

- `Planner` operativo en el backend principal.
- `PolicyEngine` explícito.
- `ToolRegistry` explícito.
- memoria operacional integrada en `POST /chat`.
- evaluación de pasos internos tipo agent runtime.

## Relacionado

- [[ARCHITECTURE]]
- [[RUNTIME_FLOW]]
- [[TECH_DEBT_AND_RISKS]]
- [[GLOSSARY]]
