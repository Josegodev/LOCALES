from DB.chunks.document_context import build_document_prompt
import app.chat_eval_runner as chat_eval_runner
from app.chat import ChatDependencies, ChatService
from app.auth import bearer_scheme, require_chat_access
from app.chat_runs.router import router as chat_runs_router
from app.config import settings
from app.evals.router import router as runs_router
from app.llm_client import ask_chat, list_chat_models, resolve_provider_model
from app.observability.chat_runs import clear_chat_runs, list_chat_runs, save_chat_run
from app.observability.logging import get_logger, log_event
from app.observability.trace import new_trace_id
from app.rag_client import query_remote_rag
from app.schemas import (
    ChatEvalListResponse,
    ChatEvalRunResponse,
    ChatEvalRunsListResponse,
    ChatModelListResponse,
    ChatOptionsResponse,
    ChatRequest,
    ChatResponse,
    ChatRunListResponse,
    ChatTraceListResponse,
    ChatTraceResetResponse,
    TEMPERATURE_DEFAULT,
    TEMPERATURE_MAX,
    TEMPERATURE_MIN,
)
from app.tools.create_document import create_document_tool
from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import ValidationError

app = FastAPI(title="Local LLM Gateway")

LOCAL_FRONTEND_FALLBACK_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]


def _resolve_cors_allowed_origins() -> list[str]:
    configured_origins = settings.frontend_allowed_origins()
    if configured_origins:
        if configured_origins == ["*"]:
            return ["*"]
        return configured_origins

    app_env = settings.app_env.strip().lower()
    if app_env in {"local", "dev"}:
        return LOCAL_FRONTEND_FALLBACK_ORIGINS

    return []


def _configure_cors(application: FastAPI) -> None:
    application.add_middleware(
        CORSMiddleware,
        allow_origins=_resolve_cors_allowed_origins(),
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )


_configure_cors(app)
app.include_router(runs_router, prefix="/api")
app.include_router(chat_runs_router, prefix="/api")


@app.middleware("http")
async def log_rejected_cors_preflight(request: Request, call_next):
    response = await call_next(request)

    if request.method == "OPTIONS" and response.status_code == 400:
        log_event(
            component="http.cors",
            event="cors_preflight_rejected",
            level=30,
            path=request.url.path,
            origin=request.headers.get("origin"),
            access_control_request_method=request.headers.get("access-control-request-method"),
            access_control_request_headers=request.headers.get("access-control-request-headers"),
        )

    return response


def _build_chat_dependencies() -> ChatDependencies:
    return ChatDependencies(
        ask_chat=ask_chat,
        build_document_prompt=build_document_prompt,
        query_remote_rag=query_remote_rag,
        resolve_provider_model=resolve_provider_model,
        save_chat_run=save_chat_run,
        log_event=log_event,
        new_trace_id=new_trace_id,
        settings=settings,
        create_document_tool=create_document_tool,
    )


def _build_chat_service() -> ChatService:
    return ChatService(_build_chat_dependencies())


def run_chat_request(
    request: ChatRequest,
    *,
    persist_trace: bool = True,
) -> ChatResponse:
    return _build_chat_service().run_chat_request(request, persist_trace=persist_trace)


def _run_chat_request(
    request: ChatRequest,
    *,
    persist_trace: bool = True,
) -> ChatResponse:
    return run_chat_request(request, persist_trace=persist_trace)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/")
def root() -> dict:
    return {
        "service": "nucleochat",
        "status": "ok",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/favicon.ico", status_code=204)
def favicon() -> Response:
    return Response(status_code=204)


@app.get("/api/models/chat", response_model=ChatModelListResponse)
def chat_models() -> dict:
    return {"status": "ok", "items": list_chat_models()}


@app.get("/api/chat/options", response_model=ChatOptionsResponse)
def chat_options() -> dict:
    return {
        "status": "ok",
        "temperature": {
            "default": TEMPERATURE_DEFAULT,
            "min": TEMPERATURE_MIN,
            "max": TEMPERATURE_MAX,
            "presets": [
                {"value": 0.0, "label": "Deterministic"},
                {"value": TEMPERATURE_DEFAULT, "label": "Technical default"},
                {"value": 0.7, "label": "Balanced"},
                {"value": 1.0, "label": "Exploratory"},
            ],
        },
    }


@app.get("/api/traces/chat", response_model=ChatTraceListResponse)
def chat_trace_runs(
    limit: int = Query(default=50, ge=1, le=200),
    _: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    authorization: str | None = Header(default=None),
) -> dict:
    require_chat_access(_, auth_header_present=authorization is not None)
    items = [record.model_dump() for record in list_chat_runs(limit=limit)]
    return {"status": "ok", "items": items, "count": len(items)}


@app.get("/api/chat/runs", response_model=ChatRunListResponse)
def chat_runs(
    limit: int = Query(default=50, ge=1, le=200),
    _: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    authorization: str | None = Header(default=None),
) -> dict:
    require_chat_access(_, auth_header_present=authorization is not None)
    items = [record.model_dump() for record in list_chat_runs(limit=limit)]
    return {"status": "ok", "items": items, "count": len(items)}


@app.post("/api/traces/chat/reset", response_model=ChatTraceResetResponse)
def reset_chat_trace_runs(
    _: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    authorization: str | None = Header(default=None),
) -> dict:
    require_chat_access(_, auth_header_present=authorization is not None)
    removed_count = clear_chat_runs()
    log_event(
        component="frontend.chat.traces",
        event="chat_trace_runs_reset",
        removed_count=removed_count,
    )
    return {"status": "ok", "removed_count": removed_count}


@app.get("/api/evals/chat", response_model=ChatEvalListResponse)
def chat_eval_runs(
    limit: int = Query(default=25),
    _: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    authorization: str | None = Header(default=None),
) -> dict:
    require_chat_access(_, auth_header_present=authorization is not None)
    normalized_limit = max(1, min(int(limit), 100))
    items = [record.model_dump() for record in list_chat_runs(limit=normalized_limit)]
    return {
        "items": items,
        "count": len(items),
        "limit": normalized_limit,
    }


@app.get("/api/evals/runs", response_model=ChatEvalRunsListResponse)
def saved_chat_eval_runs(
    _: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    authorization: str | None = Header(default=None),
) -> dict:
    require_chat_access(_, auth_header_present=authorization is not None)
    return chat_eval_runner.list_saved_eval_runs(out_dir_str=chat_eval_runner.DEFAULT_OUT_DIR)


def _execute_chat_eval_case(payload: dict[str, object]) -> dict[str, object]:
    try:
        request = ChatRequest.model_validate(payload)
    except ValidationError as exc:
        return chat_eval_runner.normalize_chat_result(
            {
                "detail": {
                    "status": "error",
                    "code": "invalid_eval_case_payload",
                    "message": str(exc),
                    "retrieval_status": None,
                    "chunk_ids": [],
                    "document_ids": [],
                    "source_filenames": [],
                }
            },
            http_status=400,
        )

    try:
        response = run_chat_request(request, persist_trace=False)
    except HTTPException as exc:
        detail = exc.detail if isinstance(exc.detail, dict) else {"status": "error", "message": str(exc.detail)}
        return chat_eval_runner.normalize_chat_result({"detail": detail}, http_status=exc.status_code)

    return chat_eval_runner.normalize_chat_result(response.model_dump(), http_status=200)


@app.post("/api/evals/chat/run", response_model=ChatEvalRunResponse)
def run_chat_eval_suite(
    _: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    authorization: str | None = Header(default=None),
) -> dict:
    require_chat_access(_, auth_header_present=authorization is not None)
    try:
        run_payload, output_path, _ = chat_eval_runner.run_chat_evals(
            base_url=settings.backend_base_url(),
            cases_path_str=chat_eval_runner.DEFAULT_CASES_PATH,
            baseline_path_str=chat_eval_runner.DEFAULT_BASELINE_PATH,
            out_dir_str=chat_eval_runner.DEFAULT_OUT_DIR,
            timeout=chat_eval_runner.DEFAULT_TIMEOUT,
            limit=None,
            source="frontend",
            request_case_fn=_execute_chat_eval_case,
        )
    except chat_eval_runner.RunnerConfigError as exc:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "code": "chat_eval_config_error",
                "message": str(exc),
            },
        ) from exc

    try:
        run_path = str(output_path.relative_to(chat_eval_runner.REPO_ROOT))
    except ValueError:
        run_path = str(output_path)

    return {
        "status": "ok",
        "run_id": run_payload["run_id"],
        "run_path": run_path,
        "source": run_payload["source"],
        "cases_file": run_payload["cases_file"],
        "baseline_file": run_payload["baseline_file"],
        "summary": run_payload["summary"],
        "results": run_payload["results"],
    }


@app.on_event("startup")
def log_runtime_configuration() -> None:
    configured = str(bool(settings.jose_dev_token)).lower()
    get_logger().info("JOSE_DEV_TOKEN configured: %s", configured)
    get_logger().info("Chat-only runtime mode enabled for /chat and /health.")


@app.post("/chat", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    _: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    authorization: str | None = Header(default=None),
) -> ChatResponse:
    require_chat_access(_, auth_header_present=authorization is not None)
    return run_chat_request(request)
