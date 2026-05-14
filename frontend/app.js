const DEFAULT_BACKEND_URL = "http://127.0.0.1:8000";

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
  useRagInput: document.querySelector("#useRagInput"),
  chatButton: document.querySelector("#chatButton"),
  chatStatus: document.querySelector("#chatStatus"),
  retrievalStatus: document.querySelector("#retrievalStatus"),
  evidenceUsed: document.querySelector("#evidenceUsed"),
  fallbackUsed: document.querySelector("#fallbackUsed"),
  chunksFound: document.querySelector("#chunksFound"),
  providerModel: document.querySelector("#providerModel"),
  traceId: document.querySelector("#traceId"),
  chatLatency: document.querySelector("#chatLatency"),
  answerText: document.querySelector("#answerText"),
  warningsText: document.querySelector("#warningsText"),
  chatRaw: document.querySelector("#chatRaw"),
  evidenceList: document.querySelector("#evidenceList"),
  chatEvalsLimit: document.querySelector("#chatEvalsLimit"),
  chatEvalsLoadButton: document.querySelector("#chatEvalsLoadButton"),
  chatEvalsStatus: document.querySelector("#chatEvalsStatus"),
  chatEvalsTableBody: document.querySelector("#chatEvalsTableBody"),
  chatEvalsRaw: document.querySelector("#chatEvalsRaw"),
  telegramStatusButton: document.querySelector("#telegramStatusButton"),
  telegramConfigButton: document.querySelector("#telegramConfigButton"),
  telegramStartButton: document.querySelector("#telegramStartButton"),
  telegramStopButton: document.querySelector("#telegramStopButton"),
  telegramSaveConfigButton: document.querySelector("#telegramSaveConfigButton"),
  telegramStatus: document.querySelector("#telegramStatus"),
  telegramRaw: document.querySelector("#telegramRaw"),
  telegramModelInput: document.querySelector("#telegramModelInput"),
  telegramTemperatureInput: document.querySelector("#telegramTemperatureInput"),
  telegramRagInput: document.querySelector("#telegramRagInput"),
  telegramEvalsLimit: document.querySelector("#telegramEvalsLimit"),
  telegramEvalsLoadButton: document.querySelector("#telegramEvalsLoadButton"),
  telegramEvalsStatus: document.querySelector("#telegramEvalsStatus"),
  telegramEvalsKpis: document.querySelector("#telegramEvalsKpis"),
  telegramKpiTotalRuns: document.querySelector("#telegramKpiTotalRuns"),
  telegramKpiOkRuns: document.querySelector("#telegramKpiOkRuns"),
  telegramKpiErrorRuns: document.querySelector("#telegramKpiErrorRuns"),
  telegramKpiErrorRate: document.querySelector("#telegramKpiErrorRate"),
  telegramKpiAvgLatencyOk: document.querySelector("#telegramKpiAvgLatencyOk"),
  telegramKpiAvgLatencyError: document.querySelector("#telegramKpiAvgLatencyError"),
  telegramKpiEvidenceRate: document.querySelector("#telegramKpiEvidenceRate"),
  telegramEvalsTableBody: document.querySelector("#telegramEvalsTableBody"),
  telegramLatencyTimeline: document.querySelector("#telegramLatencyTimeline"),
  telegramLatencyByModel: document.querySelector("#telegramLatencyByModel"),
  telegramTokensByModel: document.querySelector("#telegramTokensByModel"),
  telegramRetrievalCounts: document.querySelector("#telegramRetrievalCounts"),
  telegramBackendConnectivityErrors: document.querySelector("#telegramBackendConnectivityErrors"),
  telegramModelErrors: document.querySelector("#telegramModelErrors"),
  telegramErrorsByCategory: document.querySelector("#telegramErrorsByCategory"),
  telegramProbableTimeouts: document.querySelector("#telegramProbableTimeouts"),
  telegramEvalsRaw: document.querySelector("#telegramEvalsRaw"),
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

function logAuthState(route, authRequired) {
  console.info("backend_auth", {
    route,
    auth_required: authRequired,
    auth_header_present: false,
    token_configured: false,
  });
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

async function backendFetch(path, options = {}, { authRequired = false } = {}) {
  logAuthState(path, authRequired);
  return fetchJsonWithLatency(`${requireBackendBaseUrl()}${path}`, {
    ...options,
  });
}

function selectedChatEvalsLimit() {
  const limit = Number(elements.chatEvalsLimit.value);
  return [10, 25, 50].includes(limit) ? limit : 25;
}

function normalizeChatTracesPayload(data) {
  if (Array.isArray(data)) {
    return data;
  }
  if (Array.isArray(data?.items)) {
    return data.items;
  }
  if (Array.isArray(data?.evals)) {
    return data.evals;
  }
  return [];
}

function renderChatTraces(items) {
  elements.chatEvalsTableBody.innerHTML = "";
  if (!items.length) {
    elements.chatEvalsTableBody.innerHTML = '<tr><td colspan="12">No hay trazas disponibles.</td></tr>';
    return;
  }

  for (const item of items) {
    const row = document.createElement("tr");
    if (normalizedStatus(item) === "error") {
      row.classList.add("error-row");
    }
    [
      item.created_at,
      item.status,
      item.provider,
      item.model,
      item.trace_id,
      truncateText(item.input, 120),
      truncateText(item.response, 120),
      item.retrieval_status,
      Array.isArray(item.chunk_ids) ? item.chunk_ids.join(", ") : item.chunk_ids,
      item.latency_ms,
      item.error_code,
      truncateText(item.error_message, 120),
    ].forEach((cellValue) => {
      const cell = document.createElement("td");
      cell.textContent = valueOrDash(cellValue);
      row.appendChild(cell);
    });
    elements.chatEvalsTableBody.appendChild(row);
  }
}

async function loadChatTraces() {
  updateBackendLinks();
  const limit = selectedChatEvalsLimit();
  setStatus(elements.chatEvalsStatus, "Cargando trazas /chat...", "muted");
  elements.chatEvalsLoadButton.disabled = true;
  elements.chatEvalsTableBody.innerHTML = '<tr><td colspan="12">Cargando...</td></tr>';
  elements.chatEvalsRaw.textContent = "-";

  try {
    const { data, latencyMs } = await backendFetch(`/api/traces/chat?limit=${limit}`);
    const items = normalizeChatTracesPayload(data);
    renderChatTraces(items);
    elements.chatEvalsRaw.textContent = prettyJson(data);
    setStatus(elements.chatEvalsStatus, `Trazas cargadas: ${items.length} (${latencyMs} ms)`, "ok");
  } catch (error) {
    setStatus(elements.chatEvalsStatus, "Error cargando trazas /chat", "error");
    elements.chatEvalsTableBody.innerHTML = '<tr><td colspan="12">No se pudo cargar el endpoint de trazas.</td></tr>';
    elements.chatEvalsRaw.textContent = error.data ? prettyJson(error.data) : visibleProtectedErrorMessage(error);
  } finally {
    elements.chatEvalsLoadButton.disabled = false;
  }
}

function applyTelegramConfig(data) {
  const config = data.config || data;
  const model = config.model || config.default_model;
  const temperature = config.temperature ?? config.default_temperature;
  const ragEnabled = config.rag_enabled ?? config.default_rag_enabled;

  if (typeof model === "string" && model.trim()) {
    elements.telegramModelInput.value = model;
  }
  if (typeof temperature === "number") {
    elements.telegramTemperatureInput.value = String(temperature);
  }
  if (typeof ragEnabled === "boolean") {
    elements.telegramRagInput.checked = ragEnabled;
  }
}

async function callTelegramEndpoint(path, options = {}) {
  updateBackendLinks();
  setStatus(elements.telegramStatus, `Llamando a ${path}...`, "muted");
  elements.telegramRaw.textContent = "-";

  try {
    const { data, latencyMs } = await backendFetch(path, options, { authRequired: true });
    setStatus(elements.telegramStatus, `OK ${path} (${latencyMs} ms)`, "ok");
    elements.telegramRaw.textContent = prettyJson(data);
    applyTelegramConfig(data);
  } catch (error) {
    setStatus(elements.telegramStatus, `Error ${path}`, "error");
    elements.telegramRaw.textContent = error.data ? prettyJson(error.data) : visibleProtectedErrorMessage(error);
  }
}

function saveTelegramConfig() {
  const temperature = Number(elements.telegramTemperatureInput.value);
  callTelegramEndpoint("/telegram/config", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      model: elements.telegramModelInput.value.trim(),
      temperature: Number.isFinite(temperature) ? temperature : undefined,
      rag_enabled: elements.telegramRagInput.checked,
    }),
  });
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

function valueOrDash(value) {
  if (value === undefined || value === null || value === "") {
    return "-";
  }
  return String(value);
}

function numericValue(value) {
  if (typeof value === "number" && Number.isFinite(value)) {
    return value;
  }
  if (typeof value === "string" && value.trim() !== "") {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : null;
  }
  return null;
}

function average(values) {
  const validValues = values.filter((value) => Number.isFinite(value));
  if (!validValues.length) {
    return null;
  }
  return validValues.reduce((sum, value) => sum + value, 0) / validValues.length;
}

function groupBy(items, keyFn) {
  return items.reduce((groups, item) => {
    const key = keyFn(item) || "-";
    if (!groups[key]) {
      groups[key] = [];
    }
    groups[key].push(item);
    return groups;
  }, {});
}

function formatMetric(value, fractionDigits = 1) {
  if (!Number.isFinite(value)) {
    return "-";
  }
  return Number.isInteger(value) ? String(value) : value.toFixed(fractionDigits);
}

function formatPercent(value) {
  return Number.isFinite(value) ? `${value.toFixed(1)}%` : "-";
}

function formatLatency(value) {
  if (!Number.isFinite(value)) {
    return "-";
  }
  if (value >= 1000) {
    return `${(value / 1000).toFixed(1)} s`;
  }
  return `${Math.round(value)} ms`;
}

function normalizedStatus(item) {
  const status = String(item.status || "").trim().toLowerCase();
  return status || "unknown";
}

function isErrorEval(item) {
  return normalizedStatus(item) === "error";
}

function isBackendConnectivityError(item) {
  return String(item.error_category || "").toLowerCase() === "backend_connectivity";
}

function isModelError(item) {
  const category = String(item.error_category || "").toLowerCase();
  const phase = String(item.failed_phase || "").toLowerCase();
  return category.includes("model") || category.includes("llm") || phase.includes("model") || phase.includes("llm");
}

function isProbableTimeout(item) {
  const latencyMs = numericValue(item.latency_ms);
  return Number.isFinite(latencyMs) && latencyMs > 30000;
}

function selectedTelegramEvalsLimit() {
  const limit = Number(elements.telegramEvalsLimit.value);
  return [25, 50, 100, 250, 500].includes(limit) ? limit : 100;
}

function renderTelegramEvalsKpis(items) {
  const totalRuns = items.length;
  const okRuns = items.filter((item) => normalizedStatus(item) === "ok");
  const errorRuns = items.filter((item) => normalizedStatus(item) === "error");
  const okLatencies = okRuns.map((item) => numericValue(item.latency_ms)).filter((value) => Number.isFinite(value) && value > 0);
  const errorLatencies = errorRuns.map((item) => numericValue(item.latency_ms)).filter((value) => Number.isFinite(value) && value > 0);
  const evidenceFoundRuns = okRuns.filter((item) => item.retrieval_status === "EVIDENCE_FOUND").length;

  elements.telegramKpiTotalRuns.textContent = String(totalRuns);
  elements.telegramKpiOkRuns.textContent = String(okRuns.length);
  elements.telegramKpiErrorRuns.textContent = String(errorRuns.length);
  elements.telegramKpiErrorRate.textContent = totalRuns ? formatPercent((errorRuns.length / totalRuns) * 100) : "-";
  elements.telegramKpiAvgLatencyOk.textContent = formatLatency(average(okLatencies));
  elements.telegramKpiAvgLatencyError.textContent = formatLatency(average(errorLatencies));
  elements.telegramKpiEvidenceRate.textContent = okRuns.length ? formatPercent((evidenceFoundRuns / okRuns.length) * 100) : "-";
  elements.telegramEvalsKpis.classList.toggle("has-errors", errorRuns.length > 0);
}

function renderTelegramEvalsTable(items) {
  elements.telegramEvalsTableBody.innerHTML = "";
  if (!items.length) {
    elements.telegramEvalsTableBody.innerHTML = '<tr><td colspan="11">No hay evals disponibles.</td></tr>';
    return;
  }

  for (const item of items) {
    const row = document.createElement("tr");
    if (isErrorEval(item)) {
      row.classList.add("error-row");
    }
    if (isProbableTimeout(item)) {
      row.classList.add("timeout-row");
    }

    const cells = [
      item.created_at,
      item.model,
      item.status,
      item.retrieval_status,
      item.latency_ms,
      item.tokens_input,
      item.tokens_output,
      item.output_tokens_per_second,
      item.error_category,
      item.failed_phase,
      item.error_code,
    ];

    cells.forEach((cellValue, index) => {
      const cell = document.createElement("td");
      cell.textContent = valueOrDash(cellValue);
      if (index === 4 && isProbableTimeout(item)) {
        const badge = document.createElement("span");
        badge.className = "inline-badge warning";
        badge.textContent = "timeout probable";
        cell.append(" ", badge);
      }
      row.appendChild(cell);
    });
    elements.telegramEvalsTableBody.appendChild(row);
  }
}

function renderBarChart(container, rows, fractionDigits = 1) {
  container.classList.remove("empty");
  container.innerHTML = "";
  const validRows = rows.filter((row) => Number.isFinite(row.value));
  if (!validRows.length) {
    container.classList.add("empty");
    container.textContent = "Sin datos";
    return;
  }

  const maxValue = Math.max(...validRows.map((row) => row.value), 1);
  for (const row of validRows) {
    const item = document.createElement("div");
    item.className = "chart-row";
    const width = Math.max(2, Math.round((row.value / maxValue) * 100));
    item.innerHTML = `
      <span class="chart-label"></span>
      <span class="bar-track"><span class="bar-fill" style="width: ${width}%"></span></span>
      <span class="chart-value"></span>
    `;
    item.querySelector(".chart-label").textContent = row.label;
    item.querySelector(".chart-value").textContent = formatMetric(row.value, fractionDigits);
    container.appendChild(item);
  }
}

function renderLatencyTimeline(items) {
  const points = items
    .map((item) => ({ createdAt: item.created_at, value: numericValue(item.latency_ms) }))
    .filter((point) => point.createdAt && Number.isFinite(point.value))
    .sort((a, b) => String(a.createdAt).localeCompare(String(b.createdAt)));

  elements.telegramLatencyTimeline.classList.remove("empty");
  elements.telegramLatencyTimeline.innerHTML = "";
  if (points.length < 2) {
    elements.telegramLatencyTimeline.classList.add("empty");
    elements.telegramLatencyTimeline.textContent = points.length ? `latency_ms: ${formatMetric(points[0].value)}` : "Sin datos";
    return;
  }

  const width = 520;
  const height = 160;
  const padding = 16;
  const minValue = Math.min(...points.map((point) => point.value));
  const maxValue = Math.max(...points.map((point) => point.value));
  const valueRange = maxValue - minValue || 1;
  const coordinates = points.map((point, index) => {
    const x = padding + (index / (points.length - 1)) * (width - padding * 2);
    const y = height - padding - ((point.value - minValue) / valueRange) * (height - padding * 2);
    return { x, y, value: point.value };
  });

  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.setAttribute("class", "sparkline");
  svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
  const polyline = document.createElementNS("http://www.w3.org/2000/svg", "polyline");
  polyline.setAttribute("points", coordinates.map((point) => `${point.x},${point.y}`).join(" "));
  svg.appendChild(polyline);

  for (const point of coordinates) {
    const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
    circle.setAttribute("cx", String(point.x));
    circle.setAttribute("cy", String(point.y));
    circle.setAttribute("r", "3");
    svg.appendChild(circle);
  }

  const summary = document.createElement("p");
  summary.className = "muted-text";
  summary.textContent = `min ${formatMetric(minValue)} ms / max ${formatMetric(maxValue)} ms`;
  elements.telegramLatencyTimeline.append(svg, summary);
}

function renderTelegramEvalsCharts(items) {
  renderLatencyTimeline(items);

  const byModel = groupBy(items, (item) => item.model);
  const latencyRows = Object.entries(byModel).map(([model, rows]) => ({
    label: model,
    value: average(rows.map((row) => numericValue(row.latency_ms))),
  }));
  renderBarChart(elements.telegramLatencyByModel, latencyRows);

  const tokenSpeedRows = Object.entries(byModel).map(([model, rows]) => ({
    label: model,
    value: average(rows.map((row) => numericValue(row.output_tokens_per_second))),
  }));
  renderBarChart(elements.telegramTokensByModel, tokenSpeedRows);

  const retrievalCounts = Object.entries(groupBy(items, (item) => item.retrieval_status)).map(([status, rows]) => ({
    label: status,
    value: rows.length,
  }));
  renderBarChart(elements.telegramRetrievalCounts, retrievalCounts, 0);
}

function renderTelegramEvalsErrorKpis(items) {
  const errorItems = items.filter(isErrorEval);
  const backendConnectivityErrors = errorItems.filter(isBackendConnectivityError).length;
  const modelErrors = errorItems.filter((item) => !isBackendConnectivityError(item) && isModelError(item)).length;
  const probableTimeouts = items.filter(isProbableTimeout);

  elements.telegramBackendConnectivityErrors.textContent = String(backendConnectivityErrors);
  elements.telegramModelErrors.textContent = String(modelErrors);

  const errorCategoryRows = Object.entries(groupBy(errorItems, (item) => item.error_category)).map(([category, rows]) => ({
    label: category,
    value: rows.length,
  }));
  renderBarChart(elements.telegramErrorsByCategory, errorCategoryRows, 0);

  const timeoutRows = Object.entries(groupBy(probableTimeouts, (item) => item.error_category || item.status)).map(([category, rows]) => ({
    label: category,
    value: rows.length,
  }));
  renderBarChart(elements.telegramProbableTimeouts, timeoutRows, 0);
}

function normalizeTelegramEvalsPayload(data) {
  if (Array.isArray(data)) {
    return data;
  }
  if (Array.isArray(data?.items)) {
    return data.items;
  }
  if (Array.isArray(data?.evals)) {
    return data.evals;
  }
  return [];
}

async function loadTelegramEvals() {
  updateBackendLinks();
  const limit = selectedTelegramEvalsLimit();
  setStatus(elements.telegramEvalsStatus, "Cargando evals...", "muted");
  elements.telegramEvalsLoadButton.disabled = true;
  elements.telegramEvalsTableBody.innerHTML = '<tr><td colspan="11">Cargando...</td></tr>';
  elements.telegramEvalsRaw.textContent = "-";

  try {
    const { data, latencyMs } = await backendFetch(`/api/evals/telegram?limit=${limit}`, {}, { authRequired: true });
    const items = normalizeTelegramEvalsPayload(data);
    renderTelegramEvalsKpis(items);
    renderTelegramEvalsTable(items);
    renderTelegramEvalsCharts(items);
    renderTelegramEvalsErrorKpis(items);
    elements.telegramEvalsRaw.textContent = prettyJson(data);
    setStatus(elements.telegramEvalsStatus, `Evals cargadas: ${items.length} (${latencyMs} ms)`, "ok");
  } catch (error) {
    setStatus(elements.telegramEvalsStatus, "Error cargando evals", "error");
    elements.telegramEvalsTableBody.innerHTML = '<tr><td colspan="11">No se pudo cargar el endpoint de evals.</td></tr>';
    elements.telegramEvalsRaw.textContent = error.data ? prettyJson(error.data) : visibleProtectedErrorMessage(error);
    renderTelegramEvalsKpis([]);
    renderTelegramEvalsCharts([]);
    renderTelegramEvalsErrorKpis([]);
  } finally {
    elements.telegramEvalsLoadButton.disabled = false;
  }
}

function clearChatOutput() {
  elements.retrievalStatus.textContent = "-";
  elements.evidenceUsed.textContent = "-";
  elements.fallbackUsed.textContent = "-";
  elements.chunksFound.textContent = "-";
  elements.providerModel.textContent = "-";
  elements.traceId.textContent = "-";
  elements.chatLatency.textContent = "-";
  elements.warningsText.textContent = "-";
}

function setChatPending(isPending) {
  elements.chatButton.disabled = isPending;
  elements.chatButton.textContent = isPending ? "Sending..." : "Send";
}

function visibleChatErrorMessage(error) {
  const categorized = categorizedBackendErrorMessage(error);
  if (categorized) return categorized;
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
  if (error?.message === "Failed to fetch") {
    return "Failed to fetch. Revisa Backend base URL, CORS y que FastAPI este accesible desde el navegador.";
  }
  return error?.message || "Error inesperado llamando al backend.";
}

function visibleProtectedErrorMessage(error) {
  const categorized = categorizedBackendErrorMessage(error);
  if (categorized) return categorized;
  const detail = error?.data?.detail;
  if (detail && typeof detail === "object" && detail.message) {
    return String(detail.message);
  }
  return error?.message || "Error inesperado llamando al backend.";
}

function isAuthError(error) {
  return error?.code === "missing_dev_token" || error?.status === 401 || error?.status === 403;
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
  if (isAuthError(error)) {
    return "La ruta requiere autenticacion operacional. El navegador no envia tokens del servidor.";
  }
  return null;
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

async function sendChat() {
  updateBackendLinks();
  setChatPending(true);
  const payload = {
    message: elements.messageInput.value.trim(),
    use_rag: elements.useRagInput.checked,
  };

  if (!payload.message) {
    setStatus(elements.chatStatus, "Escribe un mensaje antes de enviar", "error");
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
    loadChatTraces().catch(() => {});
    setChatPending(false);
  }
}

const savedBackendUrl = localStorage.getItem("locales.backendUrl");
if (savedBackendUrl) {
  elements.backendUrl.value = savedBackendUrl;
}

updateBackendLinks();
setActiveTab("principal");
elements.tabButtons.forEach((button) => {
  button.addEventListener("click", () => setActiveTab(button.dataset.tabTarget));
});
elements.backendUrl.addEventListener("change", updateBackendLinks);
elements.backendUrl.addEventListener("input", updateBackendLinks);
elements.docsLink.addEventListener("click", (event) => {
  if (!backendBaseUrl()) {
    event.preventDefault();
    setStatus(elements.healthStatus, "Configura Backend base URL antes de abrir /docs", "error");
  }
});
elements.healthButton.addEventListener("click", checkHealth);
elements.chatButton.addEventListener("click", sendChat);
elements.chatEvalsLoadButton.addEventListener("click", loadChatTraces);
elements.telegramStatusButton.addEventListener("click", () => callTelegramEndpoint("/telegram/status"));
elements.telegramConfigButton.addEventListener("click", () => callTelegramEndpoint("/telegram/config"));
elements.telegramStartButton.addEventListener("click", () => callTelegramEndpoint("/telegram/start", { method: "POST" }));
elements.telegramStopButton.addEventListener("click", () => callTelegramEndpoint("/telegram/stop", { method: "POST" }));
elements.telegramSaveConfigButton.addEventListener("click", saveTelegramConfig);
elements.telegramEvalsLoadButton.addEventListener("click", loadTelegramEvals);
loadChatTraces().catch(() => {});
