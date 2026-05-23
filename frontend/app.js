const apiClient = window.LOCALES_API_CLIENT;
const DEFAULT_BACKEND_URL = apiClient?.resolveConfiguredBaseUrl?.() || "";

const elements = {
  backendUrl: document.querySelector("#backendUrl"),
  docsLink: document.querySelector("#docsLink"),
  healthButton: document.querySelector("#healthButton"),
  healthStatus: document.querySelector("#healthStatus"),
  backendStatusDetail: document.querySelector("#backendStatusDetail"),
  mainTabs: document.querySelectorAll("[data-main-tab]"),
  mainPanels: document.querySelectorAll("[data-main-panel]"),
  chatForm: document.querySelector("#chatForm"),
  messageInput: document.querySelector("#messageInput"),
  modelSelect: document.querySelector("#modelSelect"),
  temperatureSelect: document.querySelector("#temperatureSelect"),
  useRagInput: document.querySelector("#useRagInput"),
  createDocumentButton: document.querySelector("#createDocumentButton"),
  chatButton: document.querySelector("#chatButton"),
  chatStatus: document.querySelector("#chatStatus"),
  chatMessages: document.querySelector("#chatMessages"),
  retrievalStatus: document.querySelector("#retrievalStatus"),
  evidenceUsed: document.querySelector("#evidenceUsed"),
  fallbackUsed: document.querySelector("#fallbackUsed"),
  chunksFound: document.querySelector("#chunksFound"),
  providerModel: document.querySelector("#providerModel"),
  responseTemperature: document.querySelector("#responseTemperature"),
  traceId: document.querySelector("#traceId"),
  chatLatency: document.querySelector("#chatLatency"),
  warningsText: document.querySelector("#warningsText"),
  chatRaw: document.querySelector("#chatRaw"),
  evidenceList: document.querySelector("#evidenceList"),
  sideTabs: document.querySelectorAll("[data-side-tab]"),
  sidePanels: document.querySelectorAll("[data-side-panel]"),
  runsStatus: document.querySelector("#runsStatus"),
  runsFilterModel: document.querySelector("#runsFilterModel"),
  runsFilterProvider: document.querySelector("#runsFilterProvider"),
  runsFilterUseRag: document.querySelector("#runsFilterUseRag"),
  runsFilterStatus: document.querySelector("#runsFilterStatus"),
  runsFilterDateFrom: document.querySelector("#runsFilterDateFrom"),
  runsFilterDateTo: document.querySelector("#runsFilterDateTo"),
  runsTotalRuns: document.querySelector("#runsTotalRuns"),
  runsOkRuns: document.querySelector("#runsOkRuns"),
  runsErrorRate: document.querySelector("#runsErrorRate"),
  runsAvgLatency: document.querySelector("#runsAvgLatency"),
  runsP95Latency: document.querySelector("#runsP95Latency"),
  runsAvgTokensPerSecond: document.querySelector("#runsAvgTokensPerSecond"),
  runsRagHitRate: document.querySelector("#runsRagHitRate"),
  runsFallbackRate: document.querySelector("#runsFallbackRate"),
  runsLatencyByModel: document.querySelector("#runsLatencyByModel"),
  runsTokensByModel: document.querySelector("#runsTokensByModel"),
  runsErrorRateByModel: document.querySelector("#runsErrorRateByModel"),
  runsQuickSummary: document.querySelector("#runsQuickSummary"),
  runsTableBody: document.querySelector("#runsTableBody"),
  runDetailModal: document.querySelector("#runDetailModal"),
  runDetailStatus: document.querySelector("#runDetailStatus"),
  runDetailTraceId: document.querySelector("#runDetailTraceId"),
  runDetailProviderModel: document.querySelector("#runDetailProviderModel"),
  runDetailTemperature: document.querySelector("#runDetailTemperature"),
  runDetailUseRag: document.querySelector("#runDetailUseRag"),
  runDetailLatency: document.querySelector("#runDetailLatency"),
  runDetailTokensTotal: document.querySelector("#runDetailTokensTotal"),
  runDetailTokensPerSecond: document.querySelector("#runDetailTokensPerSecond"),
  runDetailRetrievalStatus: document.querySelector("#runDetailRetrievalStatus"),
  runDetailFallbackUsed: document.querySelector("#runDetailFallbackUsed"),
  runDetailErrorCode: document.querySelector("#runDetailErrorCode"),
  runDetailErrorMessage: document.querySelector("#runDetailErrorMessage"),
  runDetailChunkIds: document.querySelector("#runDetailChunkIds"),
  runDetailSourceFilenames: document.querySelector("#runDetailSourceFilenames"),
  runDetailConfig: document.querySelector("#runDetailConfig"),
  runDetailEvidence: document.querySelector("#runDetailEvidence"),
  runDetailError: document.querySelector("#runDetailError"),
  closeRunDetailButtons: document.querySelectorAll("[data-close-run-detail]"),
};

const fallbackModels = [
  { provider: "ollama", model: "granite4.1:8b", label: "Ollama / granite4.1:8b", is_default: true },
  { provider: "ollama", model: "ibm/granite-3.2-8b", label: "Ollama / ibm/granite-3.2-8b" },
  { provider: "openai", model: "gpt-5.5", label: "OpenAI / gpt-5.5" },
  { provider: "openai", model: "gpt-5.4-mini", label: "OpenAI / gpt-5.4-mini" },
  { provider: "openai", model: "gpt-4o-mini", label: "OpenAI / gpt-4o-mini" },
];
const CREATE_DOCUMENT_PREFIX = "/creardoc";

const hiddenModelNames = new Set([
  "qwen2.5-coder:1.5b-base",
]);
const DEFAULT_CHAT_PROVIDER = "ollama";
const DEFAULT_CHAT_MODEL = "granite4.1:8b";
const DEFAULT_CHAT_TEMPERATURE = 0.2;

const chatState = {
  messages: [],
  abortController: null,
};

const runsState = {
  stats: null,
  runs: [],
  filteredRuns: [],
  loaded: false,
};
function modelOptionKey(provider, model) {
  return `${provider || "ollama"}::${model || ""}`;
}

function isOpenAIModel(model) {
  return String(model || "").trim().startsWith("gpt-");
}

function inferProviderFromModel(model) {
  return isOpenAIModel(model) ? "openai" : "ollama";
}

function normalizeProviderModel(provider, model) {
  const normalizedModel = String(model || "").trim();
  const normalizedProvider = String(provider || "").trim().toLowerCase();
  const inferredProvider = inferProviderFromModel(normalizedModel);

  if (normalizedProvider === "openai" && !isOpenAIModel(normalizedModel)) {
    return { provider: inferredProvider, model: normalizedModel };
  }
  if (normalizedProvider === "ollama" && isOpenAIModel(normalizedModel)) {
    return { provider: inferredProvider, model: normalizedModel };
  }
  if (normalizedProvider === "openai" || normalizedProvider === "ollama") {
    return { provider: normalizedProvider, model: normalizedModel };
  }
  return { provider: inferredProvider, model: normalizedModel };
}

function backendBaseUrl() {
  const state = apiClient.normalizeBackendBaseUrl(elements.backendUrl.value || DEFAULT_BACKEND_URL);
  return state.ok ? state.baseUrl : "";
}

function backendBaseUrlState() {
  return apiClient.normalizeBackendBaseUrl(elements.backendUrl.value || DEFAULT_BACKEND_URL);
}

function createBackendBaseUrlError(state) {
  const error = new Error(state?.message || "Backend base URL inválida.");
  error.code = state?.code || "invalid_backend_base_url";
  error.isConfigError = true;
  error.baseUrl = state?.baseUrl || "";
  error.rawValue = state?.rawValue || "";
  error.extractedUrl = state?.extractedUrl || "";
  return error;
}

function endpoint(path) {
  const baseUrlState = backendBaseUrlState();
  if (!baseUrlState.ok) {
    throw createBackendBaseUrlError(baseUrlState);
  }
  return apiClient.buildUrl(path, baseUrlState.baseUrl);
}

function renderBackendStatusDetail(details = {}) {
  const lines = [
    `base_url: ${valueOrDash(details.baseUrl)}`,
    `endpoint: ${valueOrDash(details.endpoint)}`,
    `http_status: ${valueOrDash(details.httpStatus)}`,
    `technical: ${valueOrDash(details.technicalMessage)}`,
  ];

  if (details.warning) {
    lines.push(`warning: ${details.warning}`);
  }
  if (details.extractedUrl) {
    lines.push(`extracted_url: ${details.extractedUrl}`);
  }

  elements.backendStatusDetail.textContent = lines.join("\n");
}

function updateBackendLinks() {
  const rawValue = elements.backendUrl.value || DEFAULT_BACKEND_URL;
  const baseUrlState = backendBaseUrlState();
  const baseUrl = baseUrlState.ok ? baseUrlState.baseUrl : "";
  const docsUrl = baseUrl ? `${baseUrl}/docs` : "";
  const healthUrl = baseUrl ? `${baseUrl}/health` : "";

  localStorage.setItem("locales.backendUrl", String(rawValue).trim());
  console.info("[backend] raw base url", rawValue);
  console.info("[backend] normalized base url", baseUrl);
  console.info("[backend] health url", healthUrl);
  console.info("[backend] docs url", docsUrl);

  if (baseUrl) {
    elements.docsLink.href = `${baseUrl}/docs`;
    elements.docsLink.removeAttribute("aria-disabled");
  } else {
    elements.docsLink.href = "#";
    elements.docsLink.setAttribute("aria-disabled", "true");
  }

  renderBackendStatusDetail({
    baseUrl,
    endpoint: healthUrl || "-",
    technicalMessage: baseUrlState.message || (baseUrl ? "Pendiente de comprobación" : "Backend base URL no configurada"),
    warning: baseUrlState.code === "cloudflared_command_instead_of_public_url" ? baseUrlState.message : "",
    extractedUrl: baseUrlState.extractedUrl || "",
  });
}

function normalizeBackendUrlInputValue() {
  const baseUrlState = backendBaseUrlState();
  if (baseUrlState.ok) {
    elements.backendUrl.value = baseUrlState.baseUrl;
  }
}

function setStatus(node, text, kind) {
  node.textContent = text;
  node.className = `status ${kind}`;
}

function valueOrDash(value) {
  return value === undefined || value === null || value === "" ? "-" : String(value);
}

function metricOrNA(value, formatter = null) {
  if (value === undefined || value === null || Number.isNaN(value)) {
    return "n/a";
  }
  return formatter ? formatter(value) : String(value);
}

function numberOrNull(value) {
  if (value === undefined || value === null || value === "") {
    return null;
  }
  const numberValue = Number(value);
  return Number.isFinite(numberValue) ? numberValue : null;
}

function formatTemperature(value) {
  const numberValue = numberOrNull(value);
  return numberValue === null ? "n/a" : numberValue.toFixed(1).replace(".", ",");
}

function formatPercent(value) {
  const numberValue = numberOrNull(value);
  return numberValue === null ? "n/a" : `${(numberValue * 100).toFixed(1)}%`;
}

function formatMs(value) {
  const numberValue = numberOrNull(value);
  return numberValue === null ? "n/a" : `${Math.round(numberValue)} ms`;
}

function formatFloat(value, digits = 1) {
  const numberValue = numberOrNull(value);
  return numberValue === null ? "n/a" : numberValue.toFixed(digits);
}

function truncateText(value, limit = 1200) {
  if (typeof value !== "string") return valueOrDash(value);
  if (value.length <= limit) return value;
  return `${value.slice(0, limit)}\n...[truncated ${value.length - limit} chars]`;
}

function prettyJson(value) {
  return JSON.stringify(value, null, 2);
}

function summarizeChatPayload(data) {
  const payload = { ...(data || {}) };
  if (Array.isArray(payload.chunks)) {
    payload.chunks = payload.chunks.map((chunk) => truncateText(chunk, 600));
  }
  if (typeof payload.answer === "string") {
    payload.answer = truncateText(payload.answer, 4000);
  }
  return payload;
}

function isCreateDocumentCommand(message) {
  return typeof message === "string" && message.trim().toLowerCase().startsWith(CREATE_DOCUMENT_PREFIX);
}

async function fetchJsonWithLatency(path, options = {}) {
  const url = endpoint(path);
  return apiClient.fetchJson(url, {
    ...options,
  });
}

function visibleChatErrorMessage(error) {
  const detail = error?.data?.detail;
  if (detail && typeof detail === "object") {
    if (detail.code === "model_required") {
      return "El backend requiere un modelo explícito.";
    }
    return String(detail.message || detail.code || error.message);
  }
  if (error?.data?.message) return String(error.data.message);
  if (error?.status === 422) {
    return "Payload incompatible con ChatRequest.";
  }
  if (error?.code === "invalid_backend_base_url") {
    return "Backend base URL inválida. Pega solo la URL pública HTTPS del túnel.";
  }
  if (error?.code === "cloudflared_command_instead_of_public_url") {
    return "Has pegado el comando de cloudflared, no la URL pública del túnel.";
  }
  if (error?.code === "backend_base_url_missing") {
    return "Backend base URL no configurada. Define runtime-config.js o rellena el campo Backend base URL.";
  }
  if (error?.code === "request_timeout") {
    return "El backend ha tardado demasiado en responder.";
  }
  if (error?.status === 401) {
    return "401 Unauthorized. Revisa el Bearer token o la politica de acceso.";
  }
  if (error?.status === 403) {
    return "403 Forbidden. El backend ha rechazado el acceso.";
  }
  if (error?.status === 404 && String(error?.url || "").endsWith("/health")) {
    return "404 en /health. La URL base apunta a un backend incorrecto o incompleto.";
  }
  if (error?.status >= 500) {
    return "El backend ha devuelto un error interno.";
  }
  if (error?.name === "AbortError") return "Solicitud cancelada.";
  if (error?.code === "network_error" || error?.message === "Failed to fetch") {
    return "No se pudo conectar con el backend. Posible CORS, túnel caído o URL inaccesible.";
  }
  return error?.message || "Error inesperado llamando al backend.";
}

function selectedModelProvider() {
  const option = elements.modelSelect.selectedOptions[0];
  return normalizeProviderModel(option?.dataset.provider, option?.dataset.model || DEFAULT_CHAT_MODEL).provider;
}

function selectedProviderModel() {
  const option = elements.modelSelect.selectedOptions[0];
  const rawValue = typeof option?.value === "string" ? option.value : "";
  const explicitModel = option?.dataset.model
    || (rawValue.includes("|") ? rawValue.split("|").slice(1).join("|") : rawValue)
    || DEFAULT_CHAT_MODEL;
  const explicitProvider = option?.dataset.provider
    || (rawValue.includes("|") ? rawValue.split("|")[0] : "")
    || DEFAULT_CHAT_PROVIDER;
  const normalized = normalizeProviderModel(explicitProvider, explicitModel);
  return {
    provider: normalized.provider || DEFAULT_CHAT_PROVIDER,
    model: normalized.model || DEFAULT_CHAT_MODEL,
  };
}

function modelOptionValue(item) {
  return `${item.provider}|${item.model}`;
}

function replaceModelOptions(items) {
  elements.modelSelect.innerHTML = "";
  const models = (Array.isArray(items) && items.length ? items : fallbackModels)
    .filter((item) => item?.model && !hiddenModelNames.has(String(item.model).trim()));
  const seen = new Set();
  for (const item of models) {
    if (!item?.provider || !item?.model) continue;
    const optionValue = modelOptionValue(item);
    if (seen.has(optionValue)) continue;
    seen.add(optionValue);
    const option = document.createElement("option");
    option.value = optionValue;
    option.dataset.provider = item.provider;
    option.dataset.model = item.model;
    option.dataset.modelKey = modelOptionKey(item.provider, item.model);
    option.textContent = item.label || `${item.provider} / ${item.model}`;
    if (item.is_default) option.selected = true;
    elements.modelSelect.appendChild(option);
  }
  const options = Array.from(elements.modelSelect.options);
  const savedModelKey = localStorage.getItem("locales.chatModelKey");
  const savedModel = localStorage.getItem("locales.chatModel");
  const keyMatch = options.find((option) => option.dataset.modelKey === savedModelKey);
  if (keyMatch) {
    elements.modelSelect.selectedIndex = options.indexOf(keyMatch);
    return;
  }
  const modelMatches = savedModel ? options.filter((option) => option.value === savedModel) : [];
  if (modelMatches.length === 1) {
    elements.modelSelect.selectedIndex = options.indexOf(modelMatches[0]);
    localStorage.setItem("locales.chatModelKey", modelMatches[0].dataset.modelKey);
  }
}

function replaceTemperatureOptions(temperature) {
  const currentValue = localStorage.getItem("locales.chatTemperature");
  const presets = Array.isArray(temperature?.presets) && temperature.presets.length
    ? temperature.presets
    : [{ value: temperature?.default ?? 0.2, label: "Default" }];

  elements.temperatureSelect.innerHTML = "";
  for (const preset of presets) {
    const option = document.createElement("option");
    option.value = Number(preset.value).toFixed(1);
    option.textContent = `${formatTemperature(preset.value)} - ${preset.label}`;
    elements.temperatureSelect.appendChild(option);
  }

  const preferred = currentValue || Number(temperature?.default ?? 0.2).toFixed(1);
  if (Array.from(elements.temperatureSelect.options).some((option) => option.value === preferred)) {
    elements.temperatureSelect.value = preferred;
  }
}

async function loadChatModels() {
  if (!backendBaseUrl()) {
    replaceModelOptions(fallbackModels);
    return;
  }
  try {
    const { data } = await fetchJsonWithLatency("/api/models/chat");
    replaceModelOptions(Array.isArray(data?.items) ? data.items : []);
  } catch (error) {
    replaceModelOptions(fallbackModels);
    setStatus(elements.chatStatus, `Modelos fallback: ${visibleChatErrorMessage(error)}`, "muted");
  }
}

async function loadChatOptions() {
  if (!backendBaseUrl()) {
    replaceTemperatureOptions({ default: 0.2 });
    return;
  }
  try {
    const { data } = await fetchJsonWithLatency("/api/chat/options");
    replaceTemperatureOptions(data?.temperature);
  } catch {
    replaceTemperatureOptions({ default: 0.2 });
  }
}

function clearInspection() {
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

function renderChatMessages() {
  elements.chatMessages.innerHTML = "";
  for (const message of chatState.messages) {
    const item = document.createElement("article");
    item.className = `chat-message ${message.role}`;

    const avatar = document.createElement("span");
    avatar.className = "chat-avatar";
    avatar.textContent = message.role === "user" ? "U" : "N";

    const bubble = document.createElement("div");
    bubble.className = "chat-bubble";

    const label = document.createElement("p");
    label.className = "chat-label";
    label.textContent = message.role === "user" ? "User input" : "NucleoChat response";

    const body = document.createElement("p");
    body.textContent = message.text;
    bubble.append(label, body);

    if (message.meta?.length) {
      const meta = document.createElement("div");
      meta.className = "chat-meta";
      for (const [name, value] of message.meta) {
        const pill = document.createElement("span");
        pill.textContent = `${name}: ${valueOrDash(value)}`;
        meta.appendChild(pill);
      }
      bubble.appendChild(meta);
    }

    item.append(avatar, bubble);
    elements.chatMessages.appendChild(item);
  }
  elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
}

function appendChatMessage(message) {
  chatState.messages.push(message);
  renderChatMessages();
}

function renderEvidence(data, useRag) {
  const chunks = Array.isArray(data.chunks) ? data.chunks : [];
  const filenames = Array.isArray(data.source_filenames) ? data.source_filenames : [];
  const chunkIds = Array.isArray(data.chunk_ids) ? data.chunk_ids : [];
  const scores = Array.isArray(data.scores) ? data.scores : [];
  const total = Math.max(chunks.length, filenames.length, chunkIds.length, scores.length);

  elements.evidenceList.innerHTML = "";
  if (!useRag) {
    elements.evidenceList.innerHTML = '<p class="muted-text">RAG desactivado para este mensaje.</p>';
    return;
  }
  if (!total) {
    elements.evidenceList.innerHTML = '<p class="muted-text">No hay evidencia documental en la respuesta.</p>';
    return;
  }

  for (let index = 0; index < total; index += 1) {
    const item = document.createElement("article");
    item.className = "evidence-item";
    item.innerHTML = `
      <div class="evidence-meta">
        <span>filename: ${valueOrDash(filenames[index])}</span>
        <span>chunk_id: ${valueOrDash(chunkIds[index])}</span>
        <span>score: ${valueOrDash(scores[index])}</span>
      </div>
    `;
    const snippet = document.createElement("pre");
    snippet.textContent = truncateText(chunks[index], 800);
    item.appendChild(snippet);
    elements.evidenceList.appendChild(item);
  }
}

function renderChatResponse(data, latencyMs, useRag) {
  const answer = data?.document_path
    ? `Documento creado: ${data.document_path}${data?.document_filename ? ` (${data.document_filename})` : ""}`
    : (data?.answer ?? data?.response ?? "");
  const traceId = data?.trace_id || data?.request_id;
  const chunks = Array.isArray(data?.chunks) ? data.chunks : [];
  const warnings = Array.isArray(data?.warnings) ? data.warnings : [];
  const effectiveUseRag = typeof data?.use_rag === "boolean" ? data.use_rag : useRag;

  elements.retrievalStatus.textContent = valueOrDash(data?.retrieval_status);
  elements.evidenceUsed.textContent = valueOrDash(data?.evidence_used);
  elements.fallbackUsed.textContent = valueOrDash(data?.fallback_used);
  elements.chunksFound.textContent = String(chunks.length);
  elements.providerModel.textContent = `${valueOrDash(data?.provider)} / ${valueOrDash(data?.model)}`;
  elements.responseTemperature.textContent = formatTemperature(data?.temperature);
  elements.traceId.textContent = valueOrDash(traceId);
  elements.chatLatency.textContent = String(data?.latency_ms ?? latencyMs);
  elements.warningsText.textContent = warnings.length ? warnings.map((warning) => typeof warning === "string" ? warning : prettyJson(warning)).join("\n") : "-";
  elements.chatRaw.textContent = prettyJson(summarizeChatPayload(data));
  renderEvidence(data || {}, effectiveUseRag);

  appendChatMessage({
    role: "assistant",
    text: answer || "(respuesta vacia)",
    meta: [
      ["provider", data?.provider],
      ["model", data?.model],
      ["command", data?.command],
      ["tool", data?.tool_called],
      ["retrieval", data?.retrieval_status],
      ["latency_ms", data?.latency_ms ?? latencyMs],
      ["trace_id", traceId ? String(traceId).slice(0, 8) : "-"],
    ],
  });
}

function buildChatPayload(message) {
  const selected = selectedProviderModel();
  const selectedTemperature = numberOrNull(elements.temperatureSelect.value);
  return {
    message,
    provider: selected.provider || DEFAULT_CHAT_PROVIDER,
    model: selected.model || DEFAULT_CHAT_MODEL,
    temperature: selectedTemperature === null ? DEFAULT_CHAT_TEMPERATURE : selectedTemperature,
    use_rag: elements.useRagInput.checked,
  };
}

function prefillCreateDocumentCommand() {
  const currentMessage = elements.messageInput.value.trim();
  if (!currentMessage) {
    elements.messageInput.value = `${CREATE_DOCUMENT_PREFIX} `;
  } else if (!isCreateDocumentCommand(currentMessage)) {
    elements.messageInput.value = `${CREATE_DOCUMENT_PREFIX} ${currentMessage}`;
  }
  elements.useRagInput.checked = false;
  elements.messageInput.focus();
  elements.messageInput.style.height = "";
  elements.messageInput.style.height = `${Math.min(elements.messageInput.scrollHeight, 180)}px`;
}

function setChatPending(isPending) {
  elements.chatButton.disabled = isPending;
  elements.chatButton.textContent = isPending ? "Enviando..." : "Enviar";
}

async function sendChat(event) {
  event?.preventDefault();
  updateBackendLinks();
  const message = elements.messageInput.value.trim();
  if (!message) {
    setStatus(elements.chatStatus, "Escribe un mensaje antes de enviar", "error");
    return;
  }

  const payload = buildChatPayload(message);
  if (!payload.model) {
    setStatus(elements.chatStatus, "Selecciona un modelo valido antes de enviar", "error");
    return;
  }

  if (chatState.abortController) chatState.abortController.abort();
  chatState.abortController = new AbortController();
  setChatPending(true);
  setStatus(elements.chatStatus, "Enviando a /chat...", "muted");
  clearInspection();
  elements.chatRaw.textContent = prettyJson({ request: payload });
  appendChatMessage({ role: "user", text: payload.message });
  elements.messageInput.value = "";
  elements.messageInput.style.height = "";

  try {
    console.info("[api] POST /chat url", endpoint("/chat"));
    console.info("[api] POST /chat payload", payload);
    const { data, latencyMs } = await fetchJsonWithLatency("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      signal: chatState.abortController.signal,
      body: JSON.stringify(payload),
    });
    setStatus(elements.chatStatus, "Respuesta recibida", "ok");
    renderChatResponse(data, latencyMs, payload.use_rag);
  } catch (error) {
    const messageText = visibleChatErrorMessage(error);
    setStatus(elements.chatStatus, "Error llamando a /chat", "error");
    elements.chatLatency.textContent = error.latencyMs ? String(error.latencyMs) : "-";
    elements.warningsText.textContent = "La llamada al backend ha fallado.";
    elements.chatRaw.textContent = error.data ? prettyJson(error.data) : messageText;
    renderEvidence({}, payload.use_rag);
    appendChatMessage({
      role: "assistant",
      text: messageText,
      meta: [["provider", "fastapi"], ["retrieval", "error"], ["latency_ms", error.latencyMs || "-"]],
    });
  } finally {
    chatState.abortController = null;
    setChatPending(false);
  }
}

async function checkHealth() {
  updateBackendLinks();
  setStatus(elements.healthStatus, "Consultando /health...", "muted");
  const baseUrlState = backendBaseUrlState();
  if (!baseUrlState.ok) {
    const error = createBackendBaseUrlError(baseUrlState);
    console.error("[backend] health failed", error);
    renderBackendStatusDetail({
      baseUrl: baseUrlState.baseUrl || "-",
      endpoint: "-",
      technicalMessage: error.message,
      warning: baseUrlState.code === "cloudflared_command_instead_of_public_url" ? baseUrlState.message : "",
      extractedUrl: baseUrlState.extractedUrl || "",
    });
    setStatus(elements.healthStatus, visibleChatErrorMessage(error), "error");
    return;
  }

  const healthUrl = `${baseUrlState.baseUrl}/health`;
  try {
    const { data, latencyMs } = await fetchJsonWithLatency("/health");
    renderBackendStatusDetail({
      baseUrl: baseUrlState.baseUrl,
      endpoint: healthUrl,
      httpStatus: 200,
      technicalMessage: valueOrDash(data.status || "ok"),
    });
    setStatus(elements.healthStatus, `${valueOrDash(data.status || "ok")} (${latencyMs} ms)`, "ok");
  } catch (error) {
    console.error("[backend] health failed", error);
    renderBackendStatusDetail({
      baseUrl: baseUrlState.baseUrl,
      endpoint: healthUrl,
      httpStatus: error?.status ?? "-",
      technicalMessage: error?.data?.detail?.message || error?.message || "unknown_error",
    });
    setStatus(elements.healthStatus, visibleChatErrorMessage(error), "error");
  }
}

function setActiveSidePanel(panelName) {
  elements.sideTabs.forEach((button) => {
    const isActive = button.dataset.sideTab === panelName;
    button.classList.toggle("active", isActive);
    button.setAttribute("aria-selected", String(isActive));
  });

  elements.sidePanels.forEach((panel) => {
    const isActive = panel.dataset.sidePanel === panelName;
    panel.classList.toggle("active", isActive);
    panel.hidden = !isActive;
  });
}

function setActiveMainPanel(panelName) {
  elements.mainTabs.forEach((button) => {
    const isActive = button.dataset.mainTab === panelName;
    button.classList.toggle("active", isActive);
    button.setAttribute("aria-selected", String(isActive));
  });

  elements.mainPanels.forEach((panel) => {
    const isActive = panel.dataset.mainPanel === panelName;
    panel.classList.toggle("active", isActive);
    panel.hidden = !isActive;
  });
}

function percentile(values, percentileValue) {
  const filtered = values.filter((value) => typeof value === "number" && Number.isFinite(value)).sort((a, b) => a - b);
  if (!filtered.length) {
    return null;
  }
  if (filtered.length === 1) {
    return filtered[0];
  }
  const position = (percentileValue / 100) * (filtered.length - 1);
  const lowerIndex = Math.floor(position);
  const upperIndex = Math.ceil(position);
  if (lowerIndex === upperIndex) {
    return filtered[lowerIndex];
  }
  const weight = position - lowerIndex;
  return filtered[lowerIndex] + (filtered[upperIndex] - filtered[lowerIndex]) * weight;
}

function mean(values) {
  const filtered = values.filter((value) => typeof value === "number" && Number.isFinite(value));
  if (!filtered.length) {
    return null;
  }
  return filtered.reduce((sum, value) => sum + value, 0) / filtered.length;
}

function rate(count, total) {
  if (!total) {
    return null;
  }
  return count / total;
}

function parseRunDate(run) {
  const rawValue = run?.created_at || run?.timestamp;
  if (typeof rawValue !== "string" || !rawValue.trim()) {
    return null;
  }
  const parsed = new Date(rawValue);
  if (Number.isNaN(parsed.getTime())) {
    return null;
  }
  return parsed;
}

function matchesRunFilters(run) {
  if (elements.runsFilterModel.value !== "all" && (run.model || "") !== elements.runsFilterModel.value) {
    return false;
  }
  if (elements.runsFilterProvider.value !== "all" && (run.provider || "") !== elements.runsFilterProvider.value) {
    return false;
  }
  if (elements.runsFilterStatus.value !== "all" && (run.status || "") !== elements.runsFilterStatus.value) {
    return false;
  }
  if (elements.runsFilterUseRag.value !== "all") {
    const wanted = elements.runsFilterUseRag.value === "true";
    if (run.use_rag !== wanted) {
      return false;
    }
  }
  const runDate = parseRunDate(run);
  if (elements.runsFilterDateFrom.value) {
    if (runDate === null) {
      return false;
    }
    const fromDate = new Date(`${elements.runsFilterDateFrom.value}T00:00:00`);
    if (runDate < fromDate) {
      return false;
    }
  }
  if (elements.runsFilterDateTo.value) {
    if (runDate === null) {
      return false;
    }
    const toDate = new Date(`${elements.runsFilterDateTo.value}T23:59:59.999`);
    if (runDate > toDate) {
      return false;
    }
  }
  return true;
}

function filteredRuns() {
  return runsState.runs.filter(matchesRunFilters);
}

function setSelectOptions(select, values, placeholder = "All") {
  const current = select.value || "all";
  select.innerHTML = "";
  const allOption = document.createElement("option");
  allOption.value = "all";
  allOption.textContent = placeholder;
  select.appendChild(allOption);
  values.forEach((value) => {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = value;
    select.appendChild(option);
  });
  if (Array.from(select.options).some((option) => option.value === current)) {
    select.value = current;
  } else {
    select.value = "all";
  }
}

function resetRunsFiltersToDefault() {
  elements.runsFilterModel.value = "all";
  elements.runsFilterProvider.value = "all";
  elements.runsFilterUseRag.value = "all";
  elements.runsFilterStatus.value = "all";
  elements.runsFilterDateFrom.value = "";
  elements.runsFilterDateTo.value = "";
}

function renderRunsFilters() {
  const modelValues = [...new Set(runsState.runs.map((run) => run.model).filter(Boolean))].sort((a, b) => a.localeCompare(b));
  const providerValues = [...new Set(runsState.runs.map((run) => run.provider).filter(Boolean))].sort((a, b) => a.localeCompare(b));
  setSelectOptions(elements.runsFilterModel, modelValues, "All");
  setSelectOptions(elements.runsFilterProvider, providerValues, "All");
}

function renderRunsMetricCards(runs) {
  const totalRuns = runs.length;
  const okRuns = runs.filter((run) => String(run.status || "").toLowerCase() === "ok").length;
  const errorRuns = runs.filter((run) => String(run.status || "").toLowerCase() === "error").length;
  const avgLatency = mean(runs.map((run) => numberOrNull(run.latency_ms)));
  const p95Latency = percentile(runs.map((run) => numberOrNull(run.latency_ms)), 95);
  const avgTokensPerSecond = mean(runs.map((run) => numberOrNull(run.output_tokens_per_second)));
  const ragRuns = runs.filter((run) => run.use_rag === true);
  const ragHitRate = rate(ragRuns.filter((run) => run.retrieval_status === "EVIDENCE_FOUND").length, ragRuns.length);
  const fallbackRate = rate(runs.filter((run) => run.fallback_used === true).length, totalRuns);

  elements.runsTotalRuns.textContent = metricOrNA(totalRuns, String);
  elements.runsOkRuns.textContent = metricOrNA(okRuns, String);
  elements.runsErrorRate.textContent = metricOrNA(rate(errorRuns, totalRuns), formatPercent);
  elements.runsAvgLatency.textContent = metricOrNA(avgLatency, formatMs);
  elements.runsP95Latency.textContent = metricOrNA(p95Latency, formatMs);
  elements.runsAvgTokensPerSecond.textContent = metricOrNA(avgTokensPerSecond, (value) => `${value.toFixed(1)} tok/s`);
  elements.runsRagHitRate.textContent = metricOrNA(ragHitRate, formatPercent);
  elements.runsFallbackRate.textContent = metricOrNA(fallbackRate, formatPercent);
}

function renderBarChart(container, rows, formatter) {
  container.innerHTML = "";
  if (!rows.length) {
    container.className = "chart-list empty-state";
    container.textContent = "Sin datos";
    return;
  }

  container.className = "chart-list";
  const maxValue = Math.max(...rows.map((row) => row.value), 0);
  rows.forEach((row) => {
    const item = document.createElement("div");
    item.className = "chart-row";
    const width = maxValue > 0 ? Math.max(4, Math.round((row.value / maxValue) * 100)) : 4;
    item.innerHTML = `
      <span class="chart-label"></span>
      <span class="chart-track"><span class="chart-fill" style="width:${width}%"></span></span>
      <span class="chart-value"></span>
    `;
    item.querySelector(".chart-label").textContent = row.label;
    item.querySelector(".chart-value").textContent = formatter(row.value);
    container.appendChild(item);
  });
}

function buildModelRows(runs, valueSelector) {
  const grouped = new Map();
  runs.forEach((run) => {
    const key = `${run.provider || "n/a"} / ${run.model || "n/a"}`;
    if (!grouped.has(key)) {
      grouped.set(key, []);
    }
    grouped.get(key).push(run);
  });
  return [...grouped.entries()]
    .map(([label, modelRuns]) => ({ label, value: valueSelector(modelRuns) }))
    .filter((row) => row.value !== null && row.value !== undefined && !Number.isNaN(row.value))
    .sort((a, b) => b.value - a.value);
}

function renderRunsCharts(runs) {
  renderBarChart(
    elements.runsLatencyByModel,
    buildModelRows(runs, (modelRuns) => mean(modelRuns.map((run) => numberOrNull(run.latency_ms)))),
    formatMs
  );
  renderBarChart(
    elements.runsTokensByModel,
    buildModelRows(runs, (modelRuns) => mean(modelRuns.map((run) => numberOrNull(run.output_tokens_per_second)))),
    (value) => `${value.toFixed(1)} tok/s`
  );
  renderBarChart(
    elements.runsErrorRateByModel,
    buildModelRows(
      runs,
      (modelRuns) => rate(modelRuns.filter((run) => String(run.status || "").toLowerCase() === "error").length, modelRuns.length)
    ),
    formatPercent
  );
}

function renderRunsQuickSummary(runs) {
  if (!runs.length) {
    elements.runsQuickSummary.className = "empty-state";
    elements.runsQuickSummary.textContent = "Sin runs para resumir.";
    return;
  }
  elements.runsQuickSummary.className = "summary-list";
  elements.runsQuickSummary.innerHTML = "";
  runs.slice(0, 5).forEach((run) => {
    const row = document.createElement("div");
    row.className = "summary-row";
    row.innerHTML = `
      <span>${valueOrDash(run.created_at || run.timestamp)}</span>
      <span>${valueOrDash(run.provider)} / ${valueOrDash(run.model)}</span>
      <span>${valueOrDash(run.status)}</span>
    `;
    elements.runsQuickSummary.appendChild(row);
  });
}

function statusClassName(run) {
  const classes = [];
  if (String(run.status || "").toLowerCase() === "error") {
    classes.push("is-error");
  }
  if (run.fallback_used === true) {
    classes.push("is-fallback");
  }
  if (String(run.retrieval_status || "").toUpperCase() === "NO_EVIDENCE") {
    classes.push("is-no-evidence");
  }
  if (String(run.retrieval_status || "").toUpperCase() === "NO_EVIDENCE_FOR_ANSWER") {
    classes.push("is-no-evidence");
  }
  return classes.join(" ");
}

function runCellText(value, formatter = null) {
  if (value === null || value === undefined || value === "") {
    return "n/a";
  }
  return formatter ? formatter(value) : String(value);
}

function renderRunsTable(runs) {
  elements.runsTableBody.innerHTML = "";
  if (!runs.length) {
    elements.runsTableBody.innerHTML = '<tr><td colspan="11">No hay runs para los filtros actuales.</td></tr>';
    return;
  }

  runs.forEach((run) => {
    const row = document.createElement("tr");
    row.className = statusClassName(run);
    row.dataset.traceId = run.trace_id || "";
    row.innerHTML = `
      <td>${runCellText(run.created_at || run.timestamp)}</td>
      <td>${runCellText(run.trace_id)}</td>
      <td>${runCellText(run.model)}</td>
      <td>${runCellText(run.provider)}</td>
      <td>${runCellText(run.use_rag)}</td>
      <td>${runCellText(run.retrieval_status)}</td>
      <td>${runCellText(run.latency_ms, (value) => Math.round(value))}</td>
      <td>${runCellText(run.tokens_total, (value) => Number(value).toFixed(0))}</td>
      <td>${runCellText(run.output_tokens_per_second, (value) => Number(value).toFixed(1))}</td>
      <td>${runCellText(run.fallback_used)}</td>
      <td>${runCellText(run.status)}</td>
    `;
    row.addEventListener("click", () => openRunDetail(run.trace_id));
    elements.runsTableBody.appendChild(row);
  });
}

function applyRunsFilters() {
  runsState.filteredRuns = filteredRuns();
  renderRunsMetricCards(runsState.filteredRuns);
  renderRunsCharts(runsState.filteredRuns);
  renderRunsQuickSummary(runsState.filteredRuns);
  renderRunsTable(runsState.filteredRuns);
}

async function loadRunsDashboard() {
  if (!backendBaseUrl()) {
    runsState.stats = null;
    runsState.runs = [];
    runsState.filteredRuns = [];
    renderRunsFilters();
    applyRunsFilters();
    setStatus(elements.runsStatus, "Backend base URL no configurada", "error");
    return;
  }

  setStatus(elements.runsStatus, "Cargando runs guardados...", "muted");
  try {
    const [{ data: statsData }, { data: runsData }] = await Promise.all([
      fetchJsonWithLatency("/api/chat-runs/stats"),
      fetchJsonWithLatency("/api/chat-runs?limit=1000"),
    ]);
    runsState.stats = statsData;
    runsState.runs = Array.isArray(runsData?.items) ? runsData.items : [];
    if (!runsState.loaded) {
      resetRunsFiltersToDefault();
    }
    runsState.loaded = true;
    renderRunsFilters();
    applyRunsFilters();
    setStatus(elements.runsStatus, runsState.runs.length ? "Runs cargados" : "No hay runs guardados", "ok");
  } catch (error) {
    runsState.stats = null;
    runsState.runs = [];
    runsState.filteredRuns = [];
    if (!runsState.loaded) {
      resetRunsFiltersToDefault();
    }
    renderRunsFilters();
    applyRunsFilters();
    setStatus(elements.runsStatus, visibleChatErrorMessage(error), "error");
  }
}

function closeRunDetail() {
  elements.runDetailModal.hidden = true;
}

function renderRunDetail(detail) {
  elements.runDetailTraceId.textContent = valueOrDash(detail.trace_id);
  elements.runDetailProviderModel.textContent = `${valueOrDash(detail.provider)} / ${valueOrDash(detail.model)}`;
  elements.runDetailTemperature.textContent = formatTemperature(detail.temperature);
  elements.runDetailUseRag.textContent = valueOrDash(detail.use_rag);
  elements.runDetailLatency.textContent = metricOrNA(detail.latency_ms, formatMs);
  elements.runDetailTokensTotal.textContent = metricOrNA(detail.tokens_total, (value) => Number(value).toFixed(0));
  elements.runDetailTokensPerSecond.textContent = metricOrNA(detail.output_tokens_per_second, (value) => `${Number(value).toFixed(1)} tok/s`);
  elements.runDetailRetrievalStatus.textContent = valueOrDash(detail.retrieval_status);
  elements.runDetailFallbackUsed.textContent = valueOrDash(detail.fallback_used);
  elements.runDetailErrorCode.textContent = valueOrDash(detail.error_code);
  elements.runDetailErrorMessage.textContent = valueOrDash(detail.error_message);
  elements.runDetailChunkIds.textContent = Array.isArray(detail.chunk_ids) && detail.chunk_ids.length ? detail.chunk_ids.join(", ") : "n/a";
  elements.runDetailSourceFilenames.textContent = Array.isArray(detail.source_filenames) && detail.source_filenames.length ? detail.source_filenames.join(", ") : "n/a";
  elements.runDetailConfig.textContent = prettyJson({
    requested_model: detail.requested_model,
    temperature: detail.temperature,
    max_tokens: detail.max_tokens,
    top_p: detail.top_p,
    generation_config: detail.generation_config,
    answer_mode: detail.answer_mode,
    warnings: detail.warnings || [],
  });
  elements.runDetailEvidence.textContent = prettyJson({
    retrieval_status: detail.retrieval_status,
    chunk_ids: detail.chunk_ids || [],
    document_ids: detail.document_ids || [],
    source_filenames: detail.source_filenames || [],
    evidence_used: detail.evidence_used,
    fallback_used: detail.fallback_used,
    fallback_reason: detail.fallback_reason,
  });
  elements.runDetailError.textContent = prettyJson({
    status: detail.status,
    error_code: detail.error_code,
    error_message: detail.error_message,
  });
}

async function openRunDetail(traceId) {
  if (!traceId) {
    return;
  }
  elements.runDetailModal.hidden = false;
  setStatus(elements.runDetailStatus, "Cargando detalle...", "muted");
  try {
    const { data } = await fetchJsonWithLatency(`/api/chat-runs/${encodeURIComponent(traceId)}`);
    renderRunDetail(data);
    setStatus(elements.runDetailStatus, "Detalle cargado", "ok");
  } catch (error) {
    setStatus(elements.runDetailStatus, visibleChatErrorMessage(error), "error");
    elements.runDetailConfig.textContent = "n/a";
    elements.runDetailEvidence.textContent = "n/a";
    elements.runDetailError.textContent = error.data ? prettyJson(error.data) : visibleChatErrorMessage(error);
  }
}

function init() {
  const savedBackendUrl = localStorage.getItem("locales.backendUrl");
  if (savedBackendUrl) elements.backendUrl.value = savedBackendUrl;
  if (!elements.backendUrl.value && DEFAULT_BACKEND_URL) elements.backendUrl.value = DEFAULT_BACKEND_URL;

  updateBackendLinks();
  replaceModelOptions(fallbackModels);
  renderChatMessages();
  if (!backendBaseUrl()) {
    const backendError = createBackendBaseUrlError(backendBaseUrlState());
    setStatus(elements.healthStatus, visibleChatErrorMessage(backendError), "error");
    setStatus(elements.chatStatus, visibleChatErrorMessage(backendError), "error");
    setStatus(elements.runsStatus, visibleChatErrorMessage(backendError), "error");
  }
  loadChatModels();
  loadChatOptions();
  loadRunsDashboard();

  elements.backendUrl.addEventListener("change", () => {
    normalizeBackendUrlInputValue();
    updateBackendLinks();
    loadChatModels();
    loadChatOptions();
    loadRunsDashboard();
  });
  elements.backendUrl.addEventListener("input", updateBackendLinks);
  elements.modelSelect.addEventListener("change", () => {
    const selected = selectedProviderModel();
    localStorage.setItem("locales.chatModel", modelOptionValue(selected));
    localStorage.setItem("locales.chatModelKey", modelOptionKey(selected.provider, selected.model));
  });
  elements.temperatureSelect.addEventListener("change", () => localStorage.setItem("locales.chatTemperature", elements.temperatureSelect.value));
  elements.healthButton.addEventListener("click", checkHealth);
  elements.chatForm.addEventListener("submit", sendChat);
  elements.createDocumentButton.addEventListener("click", prefillCreateDocumentCommand);
  elements.sideTabs.forEach((button) => {
    button.addEventListener("click", () => setActiveSidePanel(button.dataset.sideTab));
  });
  elements.mainTabs.forEach((button) => {
    button.addEventListener("click", () => setActiveMainPanel(button.dataset.mainTab));
  });
  [
    elements.runsFilterModel,
    elements.runsFilterProvider,
    elements.runsFilterUseRag,
    elements.runsFilterStatus,
    elements.runsFilterDateFrom,
    elements.runsFilterDateTo,
  ].forEach((select) => {
    select.addEventListener("change", applyRunsFilters);
  });
  elements.closeRunDetailButtons.forEach((button) => {
    button.addEventListener("click", closeRunDetail);
  });
  elements.messageInput.addEventListener("input", () => {
    elements.messageInput.style.height = "";
    elements.messageInput.style.height = `${Math.min(elements.messageInput.scrollHeight, 180)}px`;
  });
  elements.messageInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      elements.chatForm.requestSubmit();
    }
  });
}

init();
