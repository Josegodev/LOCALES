const DEFAULT_BACKEND_URL = "";

const elements = {
  tabButtons: document.querySelectorAll("[data-tab-target]"),
  tabPanels: document.querySelectorAll("[data-tab-panel]"),
  backendUrl: document.querySelector("#backendUrl"),
  docsLink: document.querySelector("#docsLink"),
  healthButton: document.querySelector("#healthButton"),
  healthStatus: document.querySelector("#healthStatus"),
  healthState: document.querySelector("#healthState"),
  healthLatency: document.querySelector("#healthLatency"),
  healthRaw: document.querySelector("#healthRaw"),
  messageInput: document.querySelector("#messageInput"),
  modelSelect: document.querySelector("#modelSelect"),
  temperatureSelect: document.querySelector("#temperatureSelect"),
  useRagInput: document.querySelector("#useRagInput"),
  chatButton: document.querySelector("#chatButton"),
  chatStatus: document.querySelector("#chatStatus"),
  retrievalStatus: document.querySelector("#retrievalStatus"),
  evidenceUsed: document.querySelector("#evidenceUsed"),
  fallbackUsed: document.querySelector("#fallbackUsed"),
  chunksFound: document.querySelector("#chunksFound"),
  providerModel: document.querySelector("#providerModel"),
  responseTemperature: document.querySelector("#responseTemperature"),
  traceId: document.querySelector("#traceId"),
  chatLatency: document.querySelector("#chatLatency"),
  answerText: document.querySelector("#answerText"),
  warningsText: document.querySelector("#warningsText"),
  chatRaw: document.querySelector("#chatRaw"),
  evidenceList: document.querySelector("#evidenceList"),
  chatRunsLoadButton: document.querySelector("#chatRunsLoadButton"),
  chatRunsStatus: document.querySelector("#chatRunsStatus"),
  benchmarkTotalRuns: document.querySelector("#benchmarkTotalRuns"),
  benchmarkFastestAvgLatency: document.querySelector("#benchmarkFastestAvgLatency"),
  benchmarkBestP95Latency: document.querySelector("#benchmarkBestP95Latency"),
  benchmarkHighestOutputTokens: document.querySelector("#benchmarkHighestOutputTokens"),
  benchmarkHighestErrorRate: document.querySelector("#benchmarkHighestErrorRate"),
  benchmarkTableBody: document.querySelector("#benchmarkTableBody"),
  latencyChart: document.querySelector("#latencyChart"),
  tokensChart: document.querySelector("#tokensChart"),
  throughputChart: document.querySelector("#throughputChart"),
  reliabilityChart: document.querySelector("#reliabilityChart"),
  chatRunsRaw: document.querySelector("#chatRunsRaw"),
  temperatureRunsLoadButton: document.querySelector("#temperatureRunsLoadButton"),
  temperatureRunsStatus: document.querySelector("#temperatureRunsStatus"),
  temperatureTotalRuns: document.querySelector("#temperatureTotalRuns"),
  temperatureFastestAvgLatency: document.querySelector("#temperatureFastestAvgLatency"),
  temperatureBestP95Latency: document.querySelector("#temperatureBestP95Latency"),
  temperatureHighestOutputTokens: document.querySelector("#temperatureHighestOutputTokens"),
  temperatureHighestErrorRate: document.querySelector("#temperatureHighestErrorRate"),
  temperatureBenchmarkTableBody: document.querySelector("#temperatureBenchmarkTableBody"),
  temperatureLatencyChart: document.querySelector("#temperatureLatencyChart"),
  temperatureTokensChart: document.querySelector("#temperatureTokensChart"),
  temperatureThroughputChart: document.querySelector("#temperatureThroughputChart"),
  temperatureReliabilityChart: document.querySelector("#temperatureReliabilityChart"),
  temperatureRunsRaw: document.querySelector("#temperatureRunsRaw"),
};

function setActiveTab(tabName) {
  elements.tabButtons.forEach((button) => {
    const isActive = button.dataset.tabTarget === tabName;
    button.classList.toggle("active", isActive);
    button.setAttribute("aria-selected", String(isActive));
  });

  elements.tabPanels.forEach((panel) => {
    const isActive = panel.dataset.tabPanel === tabName;
    panel.classList.toggle("active", isActive);
    panel.hidden = !isActive;
  });
}

function backendBaseUrl() {
  return (elements.backendUrl.value || DEFAULT_BACKEND_URL).trim().replace(/\/+$/, "");
}

function requireBackendBaseUrl() {
  const baseUrl = backendBaseUrl();
  if (!baseUrl) {
    throw new Error("Configura Backend base URL antes de llamar al backend.");
  }
  return baseUrl;
}

function setStatus(node, text, kind) {
  node.textContent = text;
  node.className = `status ${kind}`;
}

function prettyJson(value) {
  return JSON.stringify(value, null, 2);
}

function valueOrDash(value) {
  if (value === undefined || value === null || value === "") {
    return "-";
  }
  return String(value);
}

function truncateText(value, limit = 1200) {
  if (typeof value !== "string") {
    return valueOrDash(value);
  }
  if (value.length <= limit) {
    return value;
  }
  return `${value.slice(0, limit)}\n...[truncated ${value.length - limit} chars]`;
}

function summarizeChatPayload(data) {
  const payload = { ...data };
  if (Array.isArray(payload.chunks)) {
    payload.chunks = payload.chunks.map((chunk) => truncateText(chunk, 600));
  }
  if (typeof payload.answer === "string") {
    payload.answer = truncateText(payload.answer, 4000);
  }
  return payload;
}

function updateBackendLinks() {
  const baseUrl = backendBaseUrl();
  localStorage.setItem("locales.backendUrl", baseUrl);
  elements.docsLink.href = baseUrl ? `${baseUrl}/docs` : "#";
  elements.docsLink.classList.toggle("disabled", !baseUrl);
}

function inferProviderFromModel(modelName) {
  return String(modelName || "").trim().startsWith("gpt-") ? "openai" : "ollama";
}

function selectedModelOption() {
  return elements.modelSelect.selectedOptions[0] || null;
}

function selectedModelProvider() {
  const option = selectedModelOption();
  const provider = option?.dataset?.provider;
  if (provider === "ollama" || provider === "openai") {
    return provider;
  }
  return inferProviderFromModel(elements.modelSelect.value);
}

function selectPreferredModel(preferredModel) {
  const options = Array.from(elements.modelSelect.options);
  if (!options.length) {
    return;
  }

  const normalizedPreferredModel = String(preferredModel || "").trim().toLowerCase();
  const exactMatch = options.find((option) => option.value === preferredModel);
  if (exactMatch) {
    elements.modelSelect.value = exactMatch.value;
    return;
  }

  if (normalizedPreferredModel) {
    const prefixMatch = options.find((option) => option.value.toLowerCase().startsWith(normalizedPreferredModel));
    if (prefixMatch) {
      elements.modelSelect.value = prefixMatch.value;
      return;
    }
  }

  const defaultOption = options.find((option) => option.dataset.isDefault === "true");
  elements.modelSelect.value = (defaultOption || options[0]).value;
}

function replaceModelOptions(items) {
  const currentValue = elements.modelSelect.value;
  const savedModel = localStorage.getItem("locales.chatModel");
  elements.modelSelect.innerHTML = "";

  for (const item of items) {
    const option = document.createElement("option");
    option.value = item.model;
    option.textContent = item.label;
    option.dataset.provider = item.provider;
    option.dataset.isDefault = item.is_default ? "true" : "false";
    elements.modelSelect.appendChild(option);
  }

  selectPreferredModel(savedModel || currentValue);
  localStorage.setItem("locales.chatModel", elements.modelSelect.value);
}

function replaceTemperatureOptions(temperatureOptions = {}) {
  const currentValue = elements.temperatureSelect.value;
  const savedTemperature = localStorage.getItem("locales.chatTemperature");
  const minTemperature = numberOrNull(temperatureOptions.min) ?? 0;
  const maxTemperature = numberOrNull(temperatureOptions.max) ?? 1.5;
  const defaultTemperature = numberOrNull(temperatureOptions.default) ?? 0.2;
  elements.temperatureSelect.innerHTML = "";

  for (let value = minTemperature; value <= maxTemperature + 0.0001; value += 0.1) {
    const normalizedValue = Math.round(value * 10) / 10;
    const option = document.createElement("option");
    option.value = normalizedValue.toFixed(1);
    option.textContent = normalizedValue === defaultTemperature
      ? `${formatNumber(normalizedValue, 1)} - default`
      : formatNumber(normalizedValue, 1);
    elements.temperatureSelect.appendChild(option);
  }

  if (!elements.temperatureSelect.options.length) {
    const option = document.createElement("option");
    option.value = defaultTemperature.toFixed(1);
    option.textContent = `${formatNumber(defaultTemperature, 1)} - default`;
    elements.temperatureSelect.appendChild(option);
  }

  const preferredNumber = numberOrNull(savedTemperature || currentValue);
  const preferred = preferredNumber !== null ? preferredNumber.toFixed(1) : defaultTemperature.toFixed(1);
  if (Array.from(elements.temperatureSelect.options).some((option) => option.value === preferred)) {
    elements.temperatureSelect.value = preferred;
  } else {
    elements.temperatureSelect.value = defaultTemperature.toFixed(1);
  }
  localStorage.setItem("locales.chatTemperature", elements.temperatureSelect.value);
}

async function fetchJsonWithLatency(url, options = {}) {
  const startedAt = performance.now();
  const response = await fetch(url, options);
  const latencyMs = Math.round(performance.now() - startedAt);
  const text = await response.text();
  let data;

  try {
    data = text ? JSON.parse(text) : {};
  } catch {
    data = { raw_text: text };
  }

  if (!response.ok) {
    const error = new Error(`HTTP ${response.status}`);
    error.status = response.status;
    error.data = data;
    error.latencyMs = latencyMs;
    throw error;
  }

  return { data, latencyMs };
}

async function backendFetch(path, options = {}) {
  return fetchJsonWithLatency(`${requireBackendBaseUrl()}${path}`, options);
}

function validateChatModelsPayload(data) {
  if (!data || typeof data !== "object" || !Array.isArray(data.items)) {
    throw new Error("Respuesta JSON invalida del endpoint de modelos.");
  }

  return data.items.filter((item) => (
    item
    && typeof item.provider === "string"
    && typeof item.model === "string"
    && typeof item.label === "string"
  ));
}

function clearChatOutput() {
  elements.retrievalStatus.textContent = "-";
  elements.evidenceUsed.textContent = "-";
  elements.fallbackUsed.textContent = "-";
  elements.chunksFound.textContent = "-";
  elements.providerModel.textContent = "-";
  elements.responseTemperature.textContent = "-";
  elements.traceId.textContent = "-";
  elements.chatLatency.textContent = "-";
  elements.warningsText.textContent = "-";
}

function setChatPending(isPending) {
  elements.chatButton.disabled = isPending;
  elements.chatButton.textContent = isPending ? "Sending..." : "Send";
}

function categorizedBackendErrorMessage(error) {
  const detail = error?.data?.detail;
  const code = detail && typeof detail === "object" ? detail.code : undefined;

  if (error?.message === "Failed to fetch") {
    return "Backend no accesible. Revisa URL, CORS y que FastAPI este arrancado.";
  }
  if (code === "dev_token_not_configured") {
    return "El token operacional no esta configurado en el servidor.";
  }
  if (code === "chat_disabled") {
    return "/chat esta deshabilitado por configuracion del backend.";
  }
  if (error?.status === 401 || error?.status === 403) {
    return "La ruta requiere autenticacion operacional y el navegador no envia ese token.";
  }
  return null;
}

function visibleChatErrorMessage(error) {
  const categorized = categorizedBackendErrorMessage(error);
  if (categorized) {
    return categorized;
  }

  const detail = error?.data?.detail;
  if (detail && typeof detail === "object") {
    const detailMessage = detail.message || detail.code;
    if (detailMessage) {
      return String(detailMessage);
    }
  }

  if (error?.data?.message) {
    return String(error.data.message);
  }

  return error?.message || "Error inesperado llamando al backend.";
}

function renderEvidence(data) {
  const chunks = Array.isArray(data.chunks) ? data.chunks : [];
  const filenames = Array.isArray(data.source_filenames) ? data.source_filenames : [];
  const chunkIds = Array.isArray(data.chunk_ids) ? data.chunk_ids : [];
  const documentIds = Array.isArray(data.document_ids) ? data.document_ids : [];
  const scores = Array.isArray(data.scores) ? data.scores : [];
  const total = Math.max(chunks.length, filenames.length, chunkIds.length, documentIds.length, scores.length);

  elements.evidenceList.innerHTML = "";
  if (total === 0) {
    elements.evidenceList.innerHTML = '<p class="muted-text">No hay evidencia documental en la respuesta.</p>';
    return;
  }

  for (let index = 0; index < total; index += 1) {
    const item = document.createElement("article");
    item.className = "evidence-item";

    const meta = document.createElement("div");
    meta.className = "evidence-meta";
    meta.innerHTML = `
      <span>filename: ${valueOrDash(filenames[index])}</span>
      <span>chunk_id: ${valueOrDash(chunkIds[index])}</span>
      <span>document_id: ${valueOrDash(documentIds[index])}</span>
      <span>score: ${valueOrDash(scores[index])}</span>
    `;

    const snippet = document.createElement("pre");
    snippet.textContent = truncateText(chunks[index], 900);
    item.append(meta, snippet);
    elements.evidenceList.appendChild(item);
  }
}

async function checkHealth() {
  updateBackendLinks();
  setStatus(elements.healthStatus, "Consultando /health...", "muted");
  elements.healthState.textContent = "-";
  elements.healthLatency.textContent = "-";
  elements.healthRaw.textContent = "-";

  try {
    const { data, latencyMs } = await backendFetch("/health");
    setStatus(elements.healthStatus, "FastAPI responde", "ok");
    elements.healthState.textContent = data.status || "ok";
    elements.healthLatency.textContent = String(latencyMs);
    elements.healthRaw.textContent = prettyJson(data);
  } catch (error) {
    setStatus(elements.healthStatus, "No se pudo conectar", "error");
    elements.healthState.textContent = "ERROR";
    elements.healthLatency.textContent = error.latencyMs ? String(error.latencyMs) : "-";
    elements.healthRaw.textContent = error.data ? prettyJson(error.data) : error.message;
  }
}

async function loadChatModels() {
  if (!backendBaseUrl()) {
    return;
  }

  try {
    const { data } = await backendFetch("/api/models/chat");
    const items = validateChatModelsPayload(data);
    if (items.length) {
      replaceModelOptions(items);
    }
  } catch (error) {
    console.warn("No se pudo cargar /api/models/chat", error);
  }
}

async function loadChatOptions() {
  if (!backendBaseUrl()) {
    return;
  }

  try {
    const { data } = await backendFetch("/api/chat/options");
    if (data && typeof data === "object" && data.temperature) {
      replaceTemperatureOptions(data.temperature);
    }
  } catch (error) {
    console.warn("No se pudo cargar /api/chat/options", error);
  }
}

function numberOrNull(value) {
  const numberValue = Number(value);
  return Number.isFinite(numberValue) ? numberValue : null;
}

function isBenchmarkModelVisible(model) {
  const modelName = String(model?.model || "").trim().toLowerCase();
  if (!modelName || modelName === "unknown" || modelName === "unknow" || modelName.startsWith("unknown:")) {
    return false;
  }
  if (modelName === "qwen-coder-base" || modelName === "qwen2.5-coder:1.5b-base" || modelName.includes("coder-base")) {
    return false;
  }
  return true;
}

function normalizeOperationalBenchmarkPayload(data) {
  if (!data || typeof data !== "object" || !Array.isArray(data.models)) {
    throw new Error("Respuesta JSON invalida del endpoint /api/runs/operational-stats.");
  }

  const models = data.models
    .filter((item) => item && typeof item === "object")
    .filter(isBenchmarkModelVisible);
  const byModelTemperature = Array.isArray(data.by_model_temperature)
    ? data.by_model_temperature.filter((item) => item && typeof item === "object").filter(isBenchmarkModelVisible)
    : [];

  return {
    timeout_ms: data.timeout_ms ?? null,
    count: null,
    models,
    by_model_temperature: byModelTemperature,
  };
}

function formatNumber(value, digits = 0) {
  const numberValue = numberOrNull(value);
  if (numberValue === null) {
    return "-";
  }
  return numberValue.toLocaleString("es-ES", {
    maximumFractionDigits: digits,
    minimumFractionDigits: digits,
  });
}

function formatMs(value) {
  const numberValue = numberOrNull(value);
  if (numberValue === null) {
    return "-";
  }
  return `${Math.round(numberValue).toLocaleString("es-ES")} ms`;
}

function formatRate(value) {
  const numberValue = numberOrNull(value);
  if (numberValue === null) {
    return "-";
  }
  const percent = numberValue <= 1 ? numberValue * 100 : numberValue;
  return `${percent.toLocaleString("es-ES", { maximumFractionDigits: 1, minimumFractionDigits: 1 })}%`;
}

function formatTokensPerSecond(value) {
  const numberValue = numberOrNull(value);
  if (numberValue === null) {
    return "-";
  }
  return `${numberValue.toLocaleString("es-ES", { maximumFractionDigits: 2, minimumFractionDigits: 1 })} tok/s`;
}

function formatTemperature(value) {
  const numberValue = numberOrNull(value);
  if (numberValue === null) {
    return "-";
  }
  return numberValue.toLocaleString("es-ES", { maximumFractionDigits: 2, minimumFractionDigits: 1 });
}

function benchmarkLabel(model) {
  if (Object.prototype.hasOwnProperty.call(model, "temperature")) {
    return `${valueOrDash(model.model)} · T=${formatTemperature(model.temperature)}`;
  }
  return valueOrDash(model.model);
}

function formatModelMetric(model, field, formatter) {
  if (!model) {
    return "-";
  }
  return `${benchmarkLabel(model)} (${formatter(model[field])})`;
}

function pickByMetric(models, field, direction = "min") {
  const candidates = models.filter((model) => numberOrNull(model[field]) !== null);
  if (!candidates.length) {
    return null;
  }
  return candidates.sort((left, right) => {
    const leftValue = numberOrNull(left[field]);
    const rightValue = numberOrNull(right[field]);
    return direction === "max" ? rightValue - leftValue : leftValue - rightValue;
  })[0];
}

function sortedBenchmarkModels(models) {
  return [...models].sort((left, right) => {
    const leftLatency = numberOrNull(left.avg_latency_ms);
    const rightLatency = numberOrNull(right.avg_latency_ms);
    if (leftLatency === null && rightLatency === null) {
      return benchmarkLabel(left).localeCompare(benchmarkLabel(right));
    }
    if (leftLatency === null) return 1;
    if (rightLatency === null) return -1;
    return leftLatency - rightLatency || benchmarkLabel(left).localeCompare(benchmarkLabel(right));
  });
}

function renderBenchmarkSummary(payload) {
  const models = payload.models;
  const totalRuns = payload.count ?? models.reduce((total, model) => total + (numberOrNull(model.runs) || 0), 0);
  elements.benchmarkTotalRuns.textContent = formatNumber(totalRuns);
  elements.benchmarkFastestAvgLatency.textContent = formatModelMetric(
    pickByMetric(models, "avg_latency_ms", "min"),
    "avg_latency_ms",
    formatMs,
  );
  elements.benchmarkBestP95Latency.textContent = formatModelMetric(
    pickByMetric(models, "p95_latency_ms", "min"),
    "p95_latency_ms",
    formatMs,
  );
  elements.benchmarkHighestOutputTokens.textContent = formatModelMetric(
    pickByMetric(models, "avg_tokens_output", "max"),
    "avg_tokens_output",
    (value) => formatNumber(value, 0),
  );
  elements.benchmarkHighestErrorRate.textContent = formatModelMetric(
    pickByMetric(models, "error_rate", "max"),
    "error_rate",
    formatRate,
  );
}

function renderBenchmarkTable(models) {
  elements.benchmarkTableBody.innerHTML = "";
  if (!models.length) {
    elements.benchmarkTableBody.innerHTML = '<tr><td colspan="14">No operational runs found yet.</td></tr>';
    return;
  }

  for (const model of sortedBenchmarkModels(models)) {
    const row = document.createElement("tr");
    if ((numberOrNull(model.error_rate) || 0) > 0) {
      row.classList.add("error-row");
    }
    [
      valueOrDash(model.model),
      formatNumber(model.runs),
      formatRate(model.success_rate),
      formatRate(model.error_rate),
      formatRate(model.timeout_rate),
      formatMs(model.avg_latency_ms),
      formatMs(model.p50_latency_ms),
      formatMs(model.p95_latency_ms),
      formatMs(model.p99_latency_ms),
      formatMs(model.std_latency_ms),
      formatNumber(model.avg_tokens_input),
      formatNumber(model.avg_tokens_output),
      formatNumber(model.avg_tokens_total),
      formatTokensPerSecond(model.avg_tokens_per_second),
    ].forEach((cellValue) => {
      const cell = document.createElement("td");
      cell.textContent = cellValue;
      row.appendChild(cell);
    });
    elements.benchmarkTableBody.appendChild(row);
  }
}

function renderGroupedChart(container, models, series, formatter) {
  container.innerHTML = "";
  const values = models.flatMap((model) => series.map((item) => numberOrNull(model[item.field]))).filter((value) => value !== null && value > 0);
  const maxValue = values.length ? Math.max(...values) : 0;

  if (!models.length || maxValue <= 0) {
    container.className = "grouped-chart empty";
    container.textContent = "No hay datos suficientes.";
    return;
  }

  container.className = "grouped-chart";
  for (const model of sortedBenchmarkModels(models)) {
    const row = document.createElement("div");
    row.className = "grouped-row";
    const label = document.createElement("div");
    label.className = "chart-label";
    label.textContent = benchmarkLabel(model);
    const bars = document.createElement("div");
    bars.className = "grouped-bars";

    for (const item of series) {
      const value = numberOrNull(model[item.field]);
      const line = document.createElement("div");
      line.className = "mini-bar-line";
      const miniLabel = document.createElement("span");
      miniLabel.className = "mini-bar-label";
      miniLabel.textContent = item.label;
      const track = document.createElement("div");
      track.className = "bar-track";
      const fill = document.createElement("div");
      fill.className = `bar-fill ${item.className || ""}`.trim();
      fill.style.width = value !== null && value > 0 ? `${Math.max((value / maxValue) * 100, 2)}%` : "0%";
      track.appendChild(fill);
      const chartValue = document.createElement("span");
      chartValue.className = "chart-value";
      chartValue.textContent = formatter(value);
      line.append(miniLabel, track, chartValue);
      bars.appendChild(line);
    }

    row.append(label, bars);
    container.appendChild(row);
  }
}

function renderBenchmarkCharts(models) {
  renderGroupedChart(elements.latencyChart, models, [
    { field: "avg_latency_ms", label: "avg" },
    { field: "p50_latency_ms", label: "p50", className: "alt" },
    { field: "p95_latency_ms", label: "p95", className: "warn" },
  ], formatMs);
  renderGroupedChart(elements.tokensChart, models, [
    { field: "avg_tokens_input", label: "input" },
    { field: "avg_tokens_output", label: "output", className: "alt" },
    { field: "avg_tokens_total", label: "total", className: "warn" },
  ], (value) => formatNumber(value, 0));
  renderGroupedChart(elements.throughputChart, models, [
    { field: "avg_tokens_per_second", label: "tok/s" },
  ], formatTokensPerSecond);
  renderGroupedChart(elements.reliabilityChart, models, [
    { field: "success_rate", label: "success" },
    { field: "error_rate", label: "error", className: "danger" },
    { field: "timeout_rate", label: "timeout", className: "warn" },
  ], formatRate);
}

function renderOperationalBenchmark(payload) {
  renderBenchmarkSummary(payload);
  renderBenchmarkTable(payload.models);
  renderBenchmarkCharts(payload.models);
}

function renderTemperatureSummary(items) {
  const payload = { models: items, count: null };
  const totalRuns = items.reduce((total, item) => total + (numberOrNull(item.runs) || 0), 0);
  elements.temperatureTotalRuns.textContent = formatNumber(totalRuns);
  elements.temperatureFastestAvgLatency.textContent = formatModelMetric(
    pickByMetric(payload.models, "avg_latency_ms", "min"),
    "avg_latency_ms",
    formatMs,
  );
  elements.temperatureBestP95Latency.textContent = formatModelMetric(
    pickByMetric(payload.models, "p95_latency_ms", "min"),
    "p95_latency_ms",
    formatMs,
  );
  elements.temperatureHighestOutputTokens.textContent = formatModelMetric(
    pickByMetric(payload.models, "avg_tokens_output", "max"),
    "avg_tokens_output",
    (value) => formatNumber(value, 0),
  );
  elements.temperatureHighestErrorRate.textContent = formatModelMetric(
    pickByMetric(payload.models, "error_rate", "max"),
    "error_rate",
    formatRate,
  );
}

function renderTemperatureTable(items) {
  elements.temperatureBenchmarkTableBody.innerHTML = "";
  if (!items.length) {
    elements.temperatureBenchmarkTableBody.innerHTML = '<tr><td colspan="13">No hay runs con temperatura guardada todavia.</td></tr>';
    return;
  }

  for (const item of sortedBenchmarkModels(items)) {
    const row = document.createElement("tr");
    if ((numberOrNull(item.error_rate) || 0) > 0) {
      row.classList.add("error-row");
    }
    [
      valueOrDash(item.model),
      formatTemperature(item.temperature),
      formatNumber(item.runs),
      formatRate(item.success_rate),
      formatRate(item.error_rate),
      formatRate(item.timeout_rate),
      formatMs(item.avg_latency_ms),
      formatMs(item.p50_latency_ms),
      formatMs(item.p95_latency_ms),
      formatMs(item.p99_latency_ms),
      formatNumber(item.avg_tokens_output),
      formatNumber(item.avg_tokens_total),
      formatTokensPerSecond(item.avg_tokens_per_second),
    ].forEach((cellValue) => {
      const cell = document.createElement("td");
      cell.textContent = cellValue;
      row.appendChild(cell);
    });
    elements.temperatureBenchmarkTableBody.appendChild(row);
  }
}

function renderTemperatureCharts(items) {
  renderGroupedChart(elements.temperatureLatencyChart, items, [
    { field: "avg_latency_ms", label: "avg" },
    { field: "p50_latency_ms", label: "p50", className: "alt" },
    { field: "p95_latency_ms", label: "p95", className: "warn" },
  ], formatMs);
  renderGroupedChart(elements.temperatureTokensChart, items, [
    { field: "avg_tokens_output", label: "output", className: "alt" },
    { field: "avg_tokens_total", label: "total", className: "warn" },
  ], (value) => formatNumber(value, 0));
  renderGroupedChart(elements.temperatureThroughputChart, items, [
    { field: "avg_tokens_per_second", label: "tok/s" },
  ], formatTokensPerSecond);
  renderGroupedChart(elements.temperatureReliabilityChart, items, [
    { field: "success_rate", label: "success" },
    { field: "error_rate", label: "error", className: "danger" },
    { field: "timeout_rate", label: "timeout", className: "warn" },
  ], formatRate);
}

function renderTemperatureBenchmark(items) {
  renderTemperatureSummary(items);
  renderTemperatureTable(items);
  renderTemperatureCharts(items);
}

async function loadSavedRuns() {
  updateBackendLinks();
  const benchmarkPath = "/api/runs/operational-stats";
  const benchmarkUrl = `${backendBaseUrl()}${benchmarkPath}`;
  setStatus(elements.chatRunsStatus, "Loading operational benchmark...", "muted");
  elements.chatRunsLoadButton.disabled = true;
  elements.benchmarkTableBody.innerHTML = '<tr><td colspan="14">Loading operational benchmark...</td></tr>';
  [elements.latencyChart, elements.tokensChart, elements.throughputChart, elements.reliabilityChart].forEach((container) => {
    container.className = "grouped-chart empty";
    container.textContent = "Loading operational benchmark...";
  });
  elements.chatRunsRaw.textContent = "-";

  try {
    const { data, latencyMs } = await backendFetch(benchmarkPath);
    const payload = normalizeOperationalBenchmarkPayload(data);
    renderOperationalBenchmark(payload);
    elements.chatRunsRaw.textContent = prettyJson({ ...data, count: payload.models.length, models: payload.models });
    setStatus(
      elements.chatRunsStatus,
      payload.models.length ? `Operational benchmark loaded: ${payload.models.length} modelos (${latencyMs} ms)` : "No operational runs found yet.",
      "ok",
    );
  } catch (error) {
    setStatus(elements.chatRunsStatus, `Error loading operational benchmark from ${benchmarkUrl || "/api/runs/operational-stats"}`, "error");
    elements.benchmarkTableBody.innerHTML = '<tr><td colspan="14">No se pudo cargar el benchmark operacional.</td></tr>';
    [elements.latencyChart, elements.tokensChart, elements.throughputChart, elements.reliabilityChart].forEach((container) => {
      container.className = "grouped-chart empty";
      container.textContent = "No se pudo conectar al backend.";
    });
    elements.chatRunsRaw.textContent = error.data ? prettyJson(error.data) : visibleChatErrorMessage(error);
  } finally {
    elements.chatRunsLoadButton.disabled = false;
  }
}

async function loadTemperatureRuns() {
  updateBackendLinks();
  const benchmarkPath = "/api/runs/operational-stats";
  const benchmarkUrl = `${backendBaseUrl()}${benchmarkPath}`;
  setStatus(elements.temperatureRunsStatus, "Loading temperature benchmark...", "muted");
  elements.temperatureRunsLoadButton.disabled = true;
  elements.temperatureBenchmarkTableBody.innerHTML = '<tr><td colspan="13">Loading temperature benchmark...</td></tr>';
  [
    elements.temperatureLatencyChart,
    elements.temperatureTokensChart,
    elements.temperatureThroughputChart,
    elements.temperatureReliabilityChart,
  ].forEach((container) => {
    container.className = "grouped-chart empty";
    container.textContent = "Loading temperature benchmark...";
  });
  elements.temperatureRunsRaw.textContent = "-";

  try {
    const { data, latencyMs } = await backendFetch(benchmarkPath);
    const payload = normalizeOperationalBenchmarkPayload(data);
    renderTemperatureBenchmark(payload.by_model_temperature);
    elements.temperatureRunsRaw.textContent = prettyJson({
      status: data.status,
      timeout_ms: data.timeout_ms,
      count: payload.by_model_temperature.length,
      by_model_temperature: payload.by_model_temperature,
    });
    setStatus(
      elements.temperatureRunsStatus,
      payload.by_model_temperature.length ? `Temperature benchmark loaded: ${payload.by_model_temperature.length} configuraciones (${latencyMs} ms)` : "No hay runs con temperatura guardada todavia.",
      "ok",
    );
  } catch (error) {
    setStatus(elements.temperatureRunsStatus, `Error loading temperature benchmark from ${benchmarkUrl || "/api/runs/operational-stats"}`, "error");
    elements.temperatureBenchmarkTableBody.innerHTML = '<tr><td colspan="13">No se pudo cargar el benchmark por temperatura.</td></tr>';
    [
      elements.temperatureLatencyChart,
      elements.temperatureTokensChart,
      elements.temperatureThroughputChart,
      elements.temperatureReliabilityChart,
    ].forEach((container) => {
      container.className = "grouped-chart empty";
      container.textContent = "No se pudo conectar al backend.";
    });
    elements.temperatureRunsRaw.textContent = error.data ? prettyJson(error.data) : visibleChatErrorMessage(error);
  } finally {
    elements.temperatureRunsLoadButton.disabled = false;
  }
}

async function sendChat() {
  updateBackendLinks();
  setChatPending(true);

  const payload = {
    message: elements.messageInput.value.trim(),
    provider: selectedModelProvider(),
    model: elements.modelSelect.value,
    temperature: numberOrNull(elements.temperatureSelect.value),
    use_rag: elements.useRagInput.checked,
  };

  if (!payload.message) {
    setStatus(elements.chatStatus, "Escribe un mensaje antes de enviar", "error");
    setChatPending(false);
    return;
  }

  if (!String(payload.model || "").trim()) {
    setStatus(elements.chatStatus, "Selecciona un modelo valido antes de enviar", "error");
    elements.answerText.textContent = "La UI necesita cargar o seleccionar un modelo explicito.";
    setChatPending(false);
    return;
  }

  setStatus(elements.chatStatus, "Enviando a /chat...", "muted");
  elements.chatRaw.textContent = prettyJson({ request: payload });
  elements.answerText.textContent = "Esperando respuesta...";
  clearChatOutput();
  renderEvidence({});

  try {
    const { data, latencyMs } = await backendFetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    setStatus(elements.chatStatus, "Respuesta recibida", "ok");
    elements.retrievalStatus.textContent = valueOrDash(data.retrieval_status);
    elements.evidenceUsed.textContent = valueOrDash(data.evidence_used);
    elements.fallbackUsed.textContent = valueOrDash(data.fallback_used);
    elements.chunksFound.textContent = String(Array.isArray(data.chunks) ? data.chunks.length : 0);
    elements.providerModel.textContent = `${valueOrDash(data.provider)} / ${valueOrDash(data.model)}`;
    elements.responseTemperature.textContent = formatTemperature(data.temperature);
    elements.traceId.textContent = valueOrDash(data.trace_id || data.request_id);
    elements.chatLatency.textContent = String(latencyMs);
    elements.answerText.textContent = valueOrDash(data.answer);
    elements.warningsText.textContent = Array.isArray(data.warnings) && data.warnings.length ? data.warnings.join("\n") : "-";
    elements.chatRaw.textContent = prettyJson(summarizeChatPayload(data));
    renderEvidence(data);
  } catch (error) {
    setStatus(elements.chatStatus, "Error llamando a /chat", "error");
    clearChatOutput();
    elements.chatLatency.textContent = error.latencyMs ? String(error.latencyMs) : "-";
    elements.answerText.textContent = visibleChatErrorMessage(error);
    elements.warningsText.textContent = "La llamada al backend ha fallado.";
    elements.chatRaw.textContent = error.data ? prettyJson(error.data) : error.message;
    renderEvidence({});
  } finally {
    try {
      await loadSavedRuns();
      await loadTemperatureRuns();
    } catch {
      // La UI principal no debe quedarse bloqueada si falla la carga de trazas.
    }
    setChatPending(false);
  }
}

const savedBackendUrl = localStorage.getItem("locales.backendUrl");
if (savedBackendUrl) {
  elements.backendUrl.value = savedBackendUrl;
}

const savedModel = localStorage.getItem("locales.chatModel");
if (savedModel && Array.from(elements.modelSelect.options).some((option) => option.value === savedModel)) {
  elements.modelSelect.value = savedModel;
}

const savedTemperature = localStorage.getItem("locales.chatTemperature");
if (savedTemperature && Array.from(elements.temperatureSelect.options).some((option) => option.value === savedTemperature)) {
  elements.temperatureSelect.value = savedTemperature;
}

updateBackendLinks();
setActiveTab("chat");
elements.tabButtons.forEach((button) => {
  button.addEventListener("click", () => setActiveTab(button.dataset.tabTarget));
});
elements.backendUrl.addEventListener("change", () => {
  updateBackendLinks();
  loadChatModels().catch(() => {});
  loadChatOptions().catch(() => {});
});
elements.backendUrl.addEventListener("input", updateBackendLinks);
elements.modelSelect.addEventListener("change", () => {
  localStorage.setItem("locales.chatModel", elements.modelSelect.value);
});
elements.temperatureSelect.addEventListener("change", () => {
  localStorage.setItem("locales.chatTemperature", elements.temperatureSelect.value);
});
elements.docsLink.addEventListener("click", (event) => {
  if (!backendBaseUrl()) {
    event.preventDefault();
    setStatus(elements.healthStatus, "Configura Backend base URL antes de abrir /docs", "error");
  }
});
elements.healthButton.addEventListener("click", checkHealth);
elements.chatButton.addEventListener("click", sendChat);
elements.chatRunsLoadButton.addEventListener("click", loadSavedRuns);
elements.temperatureRunsLoadButton.addEventListener("click", loadTemperatureRuns);
loadChatModels().catch(() => {});
loadChatOptions().catch(() => {});
loadSavedRuns().catch(() => {});
loadTemperatureRuns().catch(() => {});
