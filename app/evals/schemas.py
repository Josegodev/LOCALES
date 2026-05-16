from pydantic import BaseModel, Field


class RunRecord(BaseModel):
    trace_id: str | None = None
    created_at: str | None = None
    model: str | None = None
    latency_ms: float | None = None
    tokens_input: int | None = None
    tokens_output: int | None = None
    tokens_total: int | None = None
    output_tokens_per_second: float | None = None
    status: str | None = None
    error_code: str | None = None
    error_message: str | None = None
    retrieval_status: str | None = None
    fallback_used: bool | None = None
    source: str | None = None
    raw_filename: str | None = None


class RunsListResponse(BaseModel):
    status: str = "ok"
    count: int
    items: list[RunRecord] = Field(default_factory=list)
    corrupt_files_count: int = 0
    skipped_files_count: int = 0
    runs_dir: str


class ModelMetrics(BaseModel):
    model: str
    runs: int
    ok_runs: int
    failed_runs: int
    error_rate: float | None = None
    avg_latency_ms: float | None = None
    p50_latency_ms: float | None = None
    p95_latency_ms: float | None = None
    max_latency_ms: float | None = None
    min_latency_ms: float | None = None
    std_latency_ms: float | None = None
    avg_tokens_input: float | None = None
    avg_tokens_output: float | None = None
    avg_tokens_total: float | None = None
    avg_tokens_per_second: float | None = None
    fallback_rate: float | None = None
    no_evidence_rate: float | None = None


class MetricsSummaryResponse(BaseModel):
    status: str = "ok"
    total_runs: int
    ok_runs: int
    failed_runs: int
    error_rate: float | None = None
    avg_latency_ms: float | None = None
    avg_tokens_total: float | None = None
    models_count: int
    models: list[ModelMetrics] = Field(default_factory=list)
    corrupt_files_count: int = 0
    skipped_files_count: int = 0
    runs_dir: str


class TimeSeriesPoint(BaseModel):
    created_at: str | None = None
    model: str | None = None
    latency_ms: float | None = None
    tokens_input: int | None = None
    tokens_output: int | None = None
    tokens_total: int | None = None
    output_tokens_per_second: float | None = None
    status: str | None = None
    retrieval_status: str | None = None
    fallback_used: bool | None = None
    trace_id: str | None = None


class TimeSeriesResponse(BaseModel):
    status: str = "ok"
    count: int
    items: list[TimeSeriesPoint] = Field(default_factory=list)
    corrupt_files_count: int = 0
    skipped_files_count: int = 0
    runs_dir: str


class RunsByModelResponse(BaseModel):
    status: str = "ok"
    model: str
    count: int
    items: list[RunRecord] = Field(default_factory=list)
    metrics: ModelMetrics
    corrupt_files_count: int = 0
    skipped_files_count: int = 0
    runs_dir: str
