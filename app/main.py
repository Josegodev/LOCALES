from DB.chunks.document_context import build_document_prompt
import app.chat_eval_runner as chat_eval_runner
from app.api import (
    chat_router,
    chat_runs_router as api_chat_runs_router,
    evals_router,
    health_router,
    models_router,
    traces_router,
)
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
from app.schemas import ChatRequest, ChatResponse
from app.testclient_compat import apply_blocking_portal_compat_patch
from app.tools.create_document import create_document_tool
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

apply_blocking_portal_compat_patch()

app = FastAPI(title="Local LLM Gateway")

LOCAL_FRONTEND_FALLBACK_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5500",
    "http://127.0.0.1:5500",
]


def _merge_origins(*origin_lists: list[str]) -> list[str]:
    merged: list[str] = []
    for origin_list in origin_lists:
        for origin in origin_list:
            if origin not in merged:
                merged.append(origin)
    return merged


def _resolve_cors_allowed_origins() -> list[str]:
    configured_origins = settings.frontend_allowed_origins()
    if configured_origins:
        if configured_origins == ["*"]:
            return ["*"]
        app_env = settings.app_env.strip().lower()
        if app_env in {"local", "dev"}:
            return _merge_origins(configured_origins, LOCAL_FRONTEND_FALLBACK_ORIGINS)
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
app.include_router(health_router)
app.include_router(models_router)
app.include_router(traces_router)
app.include_router(api_chat_runs_router)
app.include_router(evals_router)
app.include_router(chat_router)


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
        list_chat_runs=list_chat_runs,
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


@app.on_event("startup")
def log_runtime_configuration() -> None:
    configured = str(bool(settings.jose_dev_token)).lower()
    get_logger().info("JOSE_DEV_TOKEN configured: %s", configured)
    get_logger().info("Chat-only runtime mode enabled for /chat and /health.")
