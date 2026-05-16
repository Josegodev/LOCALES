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
  chatRunsLoadButton: document.querySelector("#chatRunsLoadButton"),
  chatRunsStatus: document.querySelector("#chatRunsStatus"),
  runsTotal: document.querySelector("#runsTotal"),
  runsOkError: document.querySelector("#runsOkError"),
  runsModels: document.querySelector("#runsModels"),
  runsAvgLatency: document.querySelector("#runsAvgLatency"),
  runsAvgTokens: document.querySelector("#runsAvgTokens"),
  chatRunsTableBody: document.querySelector("#chatRunsTableBody"),
  chatRunsRaw: document.querySelector("#chatRunsRaw"),
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

function formatModels(models) {
  if (!Array.isArray(models) || !models.length) {
    return "-";
  }
  return models
    .map((item) => `${valueOrDash(item.model)}: ${valueOrDash(item.runs)}`)
    .join(", ");
}

function normalizeRunsListPayload(data) {
  if (!data || typeof data !== "object" || !Array.isArray(data.items)) {
    throw new Error("Respuesta JSON invalida del endpoint /api/runs.");
  }

  return {
    runs: data.items,
    count: Number.isFinite(data.count) ? data.count : data.items.length,
  };
}

function normalizeRunsSummaryPayload(data) {
  if (!data || typeof data !== "object" || !Array.isArray(data.models)) {
    throw new Error("Respuesta JSON invalida del endpoint /api/runs/summary.");
  }

  return {
    total_runs: valueOrDash(data.total_runs),
    ok_runs: valueOrDash(data.ok_runs),
    failed_runs: valueOrDash(data.failed_runs),
    models: data.models,
    avg_latency_ms: data.avg_latency_ms ?? null,
    avg_tokens_total: data.avg_tokens_total ?? null,
  };
}

function renderSavedRuns(summaryPayload, runsPayload) {
  elements.runsTotal.textContent = valueOrDash(summaryPayload.total_runs);
  elements.runsOkError.textContent = `${valueOrDash(summaryPayload.ok_runs)} / ${valueOrDash(summaryPayload.failed_runs)}`;
  elements.runsModels.textContent = formatModels(summaryPayload.models);
  elements.runsAvgLatency.textContent = valueOrDash(summaryPayload.avg_latency_ms);
  elements.runsAvgTokens.textContent = valueOrDash(summaryPayload.avg_tokens_total);

  elements.chatRunsTableBody.innerHTML = "";
  if (!runsPayload.runs.length) {
    elements.chatRunsTableBody.innerHTML = '<tr><td colspan="7">No hay runs guardados todavia. Ejecuta una pregunta desde Chat.</td></tr>';
    return;
  }

  for (const item of runsPayload.runs) {
    const row = document.createElement("tr");
    if (String(item.status || "").trim().toLowerCase() === "error") {
      row.classList.add("error-row");
    }

    [
      item.created_at,
      item.model,
      item.status,
      item.retrieval_status,
      item.latency_ms,
      item.tokens_total,
      item.trace_id,
    ].forEach((cellValue) => {
      const cell = document.createElement("td");
      cell.textContent = valueOrDash(cellValue);
      row.appendChild(cell);
    });

    elements.chatRunsTableBody.appendChild(row);
  }
}

async function loadSavedRuns() {
  updateBackendLinks();
  setStatus(elements.chatRunsStatus, "Cargando runs guardados...", "muted");
  elements.chatRunsLoadButton.disabled = true;
  elements.chatRunsTableBody.innerHTML = '<tr><td colspan="7">Cargando...</td></tr>';
  elements.chatRunsRaw.textContent = "-";

  try {
    const [runsResponse, summaryResponse] = await Promise.all([
      backendFetch("/api/runs?limit=100"),
      backendFetch("/api/runs/summary"),
    ]);
    const runsPayload = normalizeRunsListPayload(runsResponse.data);
    const summaryPayload = normalizeRunsSummaryPayload(summaryResponse.data);
    renderSavedRuns(summaryPayload, runsPayload);
    elements.chatRunsRaw.textContent = prettyJson({
      summary: summaryResponse.data,
      runs: runsResponse.data,
    });
    setStatus(
      elements.chatRunsStatus,
      `Runs cargados: ${runsPayload.count} (${Math.max(runsResponse.latencyMs, summaryResponse.latencyMs)} ms)`,
      "ok",
    );
  } catch (error) {
    setStatus(elements.chatRunsStatus, "Error cargando runs guardados", "error");
    elements.chatRunsTableBody.innerHTML = '<tr><td colspan="7">No se pudo cargar el endpoint de runs.</td></tr>';
    elements.chatRunsRaw.textContent = error.data ? prettyJson(error.data) : visibleChatErrorMessage(error);
  } finally {
    elements.chatRunsLoadButton.disabled = false;
  }
}
async function sendChat() {
  updateBackendLinks();
  setChatPending(true);

  const payload = {
    message: elements.messageInput.value.trim(),
    provider: selectedModelProvider(),
    model: elements.modelSelect.value,
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

updateBackendLinks();
setActiveTab("chat");
elements.tabButtons.forEach((button) => {
  button.addEventListener("click", () => setActiveTab(button.dataset.tabTarget));
});
elements.backendUrl.addEventListener("change", () => {
  updateBackendLinks();
  loadChatModels().catch(() => {});
});
elements.backendUrl.addEventListener("input", updateBackendLinks);
elements.modelSelect.addEventListener("change", () => {
  localStorage.setItem("locales.chatModel", elements.modelSelect.value);
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
loadChatModels().catch(() => {});
loadSavedRuns().catch(() => {});
