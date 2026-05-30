from fastapi import APIRouter, Depends, Header, HTTPException, Query
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import ValidationError

from app.api.runtime_bridge import main_module
from app.auth import bearer_scheme, require_chat_access
from app.schemas import (
    ChatEvalListResponse,
    ChatEvalRunResponse,
    ChatEvalRunsListResponse,
    ChatRequest,
)

router = APIRouter()


def _execute_chat_eval_case(payload: dict[str, object]) -> dict[str, object]:
    app_main = main_module()
    try:
        request = ChatRequest.model_validate(payload)
    except ValidationError as exc:
        return app_main.chat_eval_runner.normalize_chat_result(
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
        response = app_main.run_chat_request(request, persist_trace=False)
    except HTTPException as exc:
        detail = (
            exc.detail
            if isinstance(exc.detail, dict)
            else {"status": "error", "message": str(exc.detail)}
        )
        return app_main.chat_eval_runner.normalize_chat_result(
            {"detail": detail},
            http_status=exc.status_code,
        )

    return app_main.chat_eval_runner.normalize_chat_result(
        response.model_dump(),
        http_status=200,
    )


@router.get("/api/evals/chat", response_model=ChatEvalListResponse)
def chat_eval_runs(
    limit: int = Query(default=25),
    _: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    authorization: str | None = Header(default=None),
) -> dict:
    require_chat_access(_, auth_header_present=authorization is not None)
    normalized_limit = max(1, min(int(limit), 100))
    items = [record.model_dump() for record in main_module().list_chat_runs(limit=normalized_limit)]
    return {
        "items": items,
        "count": len(items),
        "limit": normalized_limit,
    }


@router.get("/api/evals/runs", response_model=ChatEvalRunsListResponse)
def saved_chat_eval_runs(
    _: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    authorization: str | None = Header(default=None),
) -> dict:
    require_chat_access(_, auth_header_present=authorization is not None)
    app_main = main_module()
    return app_main.chat_eval_runner.list_saved_eval_runs(
        out_dir_str=app_main.chat_eval_runner.DEFAULT_OUT_DIR
    )


@router.post("/api/evals/chat/run", response_model=ChatEvalRunResponse)
def run_chat_eval_suite(
    _: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    authorization: str | None = Header(default=None),
) -> dict:
    require_chat_access(_, auth_header_present=authorization is not None)
    app_main = main_module()
    try:
        run_payload, output_path, _ = app_main.chat_eval_runner.run_chat_evals(
            base_url=app_main.settings.backend_base_url(),
            cases_path_str=app_main.chat_eval_runner.DEFAULT_CASES_PATH,
            baseline_path_str=app_main.chat_eval_runner.DEFAULT_BASELINE_PATH,
            out_dir_str=app_main.chat_eval_runner.DEFAULT_OUT_DIR,
            timeout=app_main.chat_eval_runner.DEFAULT_TIMEOUT,
            limit=None,
            source="frontend",
            request_case_fn=_execute_chat_eval_case,
        )
    except app_main.chat_eval_runner.RunnerConfigError as exc:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "code": "chat_eval_config_error",
                "message": str(exc),
            },
        ) from exc

    try:
        run_path = str(output_path.relative_to(app_main.chat_eval_runner.REPO_ROOT))
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
