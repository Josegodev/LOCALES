# LLM Lab

Isolated experimental lab for evaluating local or cloud LLM behavior before any
runtime integration.

## Scope

- No real actions are executed.
- No system state is modified outside `llm_lab/artifacts`.
- The lab does not import NUCLEO or `app/`.
- Model output is treated as untrusted text.
- Validation failures return a deterministic fallback.

## Proposal Contract

```json
{
  "suggested_action": "string | none",
  "arguments": {},
  "confidence": 0.0,
  "meta": {
    "needs_clarification": true,
    "justification": "string"
  }
}
```

Fallback:

```json
{
  "suggested_action": "none",
  "arguments": {},
  "confidence": 0.0,
  "meta": {
    "needs_clarification": true,
    "justification": "fallback: validation_failed",
    "fallback_reason": "validation_failed"
  }
}
```

## Run

Install dependencies in your own environment:

```bash
python3 -m pip install -r llm_lab/requirements.txt
python3 -m uvicorn llm_lab.api:app --host 127.0.0.1 --port 8000
```

## Provider Modes

### Mock mode

Mock is the default mode. If no provider is configured, the lab uses an
in-process deterministic adapter:

```bash
unset LLM_LAB_PROVIDER
unset LLM_LAB_MODEL
unset LLM_LAB_ENDPOINT
```

You can also force it explicitly:

```bash
export LLM_LAB_PROVIDER=mock
```

Requests that pass a `model_id` beginning with `mock:` always use mock mode.
This keeps `/eval/run` reproducible even when a local provider is configured.

### Ollama mode

Start Ollama locally, then configure:

```bash
export LLM_LAB_PROVIDER=ollama
export LLM_LAB_MODEL=llama3.2
export LLM_LAB_ENDPOINT=http://127.0.0.1:11434/api/generate
```

`LLM_LAB_ENDPOINT` is optional for Ollama if you use the default endpoint above.

### LM Studio mode

Start the LM Studio local server with an OpenAI-compatible chat endpoint, then
configure:

```bash
export LLM_LAB_PROVIDER=lmstudio
export LLM_LAB_MODEL=local-model
export LLM_LAB_ENDPOINT=http://127.0.0.1:1234/v1/chat/completions
```

`LLM_LAB_ENDPOINT` is optional for LM Studio if you use the default endpoint
above.

### Timeout and fallback

Local provider calls have a hard timeout of 10 seconds. Provider errors,
timeouts, invalid JSON, and invalid schemas all return the deterministic
fallback through `validator.py`.

To return to mock after a provider fails:

```bash
unset LLM_LAB_PROVIDER
unset LLM_LAB_MODEL
unset LLM_LAB_ENDPOINT
```

## Endpoints

### POST `/rag/query`

```bash
curl -s http://127.0.0.1:8000/rag/query \
  -H 'content-type: application/json' \
  -d '{"query":"validation fallback trace","top_k":3}'
```

### POST `/model/proposal`

Mock example:

```bash
curl -s http://127.0.0.1:8000/model/proposal \
  -H 'content-type: application/json' \
  -d '{"task":"Generate a structured proposal","context":{"scope":"lab"},"model_id":"mock:proposal"}'
```

Ollama or LM Studio example using environment configuration:

```bash
curl -s http://127.0.0.1:8000/model/proposal \
  -H 'content-type: application/json' \
  -d '{"task":"Generate a structured proposal","context":{"scope":"lab"}}'
```

Force validation failure:

```bash
curl -s http://127.0.0.1:8000/model/proposal \
  -H 'content-type: application/json' \
  -d '{"task":"Return invalid output","context":{},"model_id":"mock:invalid_json"}'
```

### POST `/model/answer`

```bash
curl -s http://127.0.0.1:8000/model/answer \
  -H 'content-type: application/json' \
  -d '{"question":"What is the lab boundary?","context":{},"model_id":"mock:answer"}'
```

### POST `/eval/run`

```bash
curl -s http://127.0.0.1:8000/eval/run \
  -H 'content-type: application/json' \
  -d '{}'
```

## Traces

Each request writes one JSON trace under `llm_lab/artifacts` with:

- input
- prompt
- provider
- provider_endpoint
- model_id
- raw_output
- validated_output
- fallback_used
- fallback_reason
- latency_ms
