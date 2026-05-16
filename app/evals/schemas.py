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
    error_type: str | None = None
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


class OperationalModelStats(BaseModel):
    model: str
    runs: int
    samples_valid_latency: int
    samples_valid_tokens: int
    ok_count: int
    error_count: int
    timeout_count: int
    success_rate: float | None = None
    error_rate: float | None = None
    timeout_rate: float | None = None
    avg_latency_ms: float | None = None
    p50_latency_ms: float | None = None
    p90_latency_ms: float | None = None
    p95_latency_ms: float | None = None
    p99_latency_ms: float | None = None
    min_latency_ms: float | None = None
    max_latency_ms: float | None = None
    std_latency_ms: float | None = None
    avg_tokens_input: float | None = None
    avg_tokens_output: float | None = None
    avg_tokens_total: float | None = None
    min_tokens_total: float | None = None
    max_tokens_total: float | None = None
    p50_tokens_total: float | None = None
    p95_tokens_total: float | None = None
    avg_tokens_per_second: float | None = None
    p50_tokens_per_second: float | None = None
    p95_tokens_per_second: float | None = None


class OperationalStatsResponse(BaseModel):
    status: str = "ok"
    timeout_ms: int
    models: list[OperationalModelStats] = Field(default_factory=list)
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
