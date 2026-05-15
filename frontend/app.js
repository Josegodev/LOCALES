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
  chatRunsResetButton: document.querySelector("#chatRunsResetButton"),
  chatEvalsStatus: document.querySelector("#chatEvalsStatus"),
  chatEvalsTableBody: document.querySelector("#chatEvalsTableBody"),
  chatEvalsRaw: document.querySelector("#chatEvalsRaw"),
  chatRunsKpis: document.querySelector("#chatRunsKpis"),
  chatRunTotal: document.querySelector("#chatRunTotal"),
  chatRunOk: document.querySelector("#chatRunOk"),
  chatRunError: document.querySelector("#chatRunError"),
  chatRunErrorRate: document.querySelector("#chatRunErrorRate"),
  chatRunAvgLatency: document.querySelector("#chatRunAvgLatency"),
  chatRunEvidenceRate: document.querySelector("#chatRunEvidenceRate"),
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
  return [10, 25, 50, 100].includes(limit) ? limit : 100;
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
    elements.chatEvalsTableBody.innerHTML = '<tr><td colspan="15">No hay runs disponibles.</td></tr>';
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
      item.tokens_input,
      item.tokens_output,
      item.tokens_total,
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

function renderChatRunKpis(items) {
  const totalRuns = items.length;
  const okRuns = items.filter((item) => normalizedStatus(item) === "ok");
  const errorRuns = items.filter((item) => normalizedStatus(item) === "error");
  const latencies = items.map((item) => numericValue(item.latency_ms)).filter((value) => Number.isFinite(value) && value > 0);
  const evidenceFoundRuns = okRuns.filter((item) => item.retrieval_status === "EVIDENCE_FOUND").length;

  elements.chatRunTotal.textContent = String(totalRuns);
  elements.chatRunOk.textContent = String(okRuns.length);
  elements.chatRunError.textContent = String(errorRuns.length);
  elements.chatRunErrorRate.textContent = totalRuns ? formatPercent((errorRuns.length / totalRuns) * 100) : "-";
  elements.chatRunAvgLatency.textContent = formatLatency(average(latencies));
  elements.chatRunEvidenceRate.textContent = okRuns.length ? formatPercent((evidenceFoundRuns / okRuns.length) * 100) : "-";
  elements.chatRunsKpis.classList.toggle("has-errors", errorRuns.length > 0);
}

async function loadChatTraces() {
  updateBackendLinks();
  const limit = selectedChatEvalsLimit();
  setStatus(elements.chatEvalsStatus, "Cargando runs /chat...", "muted");
  elements.chatEvalsLoadButton.disabled = true;
  elements.chatEvalsTableBody.innerHTML = '<tr><td colspan="15">Cargando...</td></tr>';
  elements.chatEvalsRaw.textContent = "-";

  try {
    const { data, latencyMs } = await backendFetch(`/api/traces/chat?limit=${limit}`);
    const items = normalizeChatTracesPayload(data);
    renderChatRunKpis(items);
    renderChatTraces(items);
    elements.chatEvalsRaw.textContent = prettyJson(data);
    setStatus(elements.chatEvalsStatus, `Runs cargados: ${items.length} (${latencyMs} ms)`, "ok");
  } catch (error) {
    setStatus(elements.chatEvalsStatus, "Error cargando runs /chat", "error");
    elements.chatEvalsTableBody.innerHTML = '<tr><td colspan="15">No se pudo cargar el endpoint de runs.</td></tr>';
    elements.chatEvalsRaw.textContent = error.data ? prettyJson(error.data) : visibleProtectedErrorMessage(error);
    renderChatRunKpis([]);
  } finally {
    elements.chatEvalsLoadButton.disabled = false;
  }
}

async function resetChatRuns() {
  const confirmed = window.confirm("Vas a borrar los runs /chat guardados en el backend. ¿Continuar?");
  if (!confirmed) {
    return;
  }

  updateBackendLinks();
  setStatus(elements.chatEvalsStatus, "Reseteando runs /chat...", "muted");
  elements.chatRunsResetButton.disabled = true;

  try {
    const { data, latencyMs } = await backendFetch("/api/traces/chat/reset", {
      method: "POST",
    });
    renderChatRunKpis([]);
    renderChatTraces([]);
    elements.chatEvalsRaw.textContent = prettyJson(data);
    setStatus(
      elements.chatEvalsStatus,
      `Runs reseteados: ${valueOrDash(data.removed_count)} (${latencyMs} ms)`,
      "ok",
    );
  } catch (error) {
    setStatus(elements.chatEvalsStatus, "Error reseteando runs /chat", "error");
    elements.chatEvalsRaw.textContent = error.data ? prettyJson(error.data) : visibleProtectedErrorMessage(error);
  } finally {
    elements.chatRunsResetButton.disabled = false;
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
elements.chatRunsResetButton.addEventListener("click", resetChatRuns);
loadChatTraces().catch(() => {});
