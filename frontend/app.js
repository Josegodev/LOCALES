const DEFAULT_BACKEND_URL = "http://127.0.0.1:8001";

const elements = {
  backendUrl: document.querySelector("#backendUrl"),
  docsLink: document.querySelector("#docsLink"),
  healthButton: document.querySelector("#healthButton"),
  healthStatus: document.querySelector("#healthStatus"),
  chatForm: document.querySelector("#chatForm"),
  messageInput: document.querySelector("#messageInput"),
  modelSelect: document.querySelector("#modelSelect"),
  temperatureSelect: document.querySelector("#temperatureSelect"),
  useRagInput: document.querySelector("#useRagInput"),
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
};

const fallbackModels = [
  { provider: "ollama", model: "granite4.1:8b", label: "Ollama / granite4.1:8b", is_default: true },
  { provider: "ollama", model: "ibm/granite-3.2-8b", label: "Ollama / ibm/granite-3.2-8b" },
  { provider: "openai", model: "gpt-5.5", label: "OpenAI / gpt-5.5" },
  { provider: "openai", model: "gpt-5.4-mini", label: "OpenAI / gpt-5.4-mini" },
  { provider: "openai", model: "gpt-4o-mini", label: "OpenAI / gpt-4o-mini" },
];

const chatState = {
  messages: [],
  abortController: null,
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
  return (elements.backendUrl.value || DEFAULT_BACKEND_URL).trim().replace(/\/+$/, "");
}

function endpoint(path) {
  return `${backendBaseUrl()}${path}`;
}

function updateBackendLinks() {
  const baseUrl = backendBaseUrl();
  localStorage.setItem("locales.backendUrl", baseUrl);
  elements.docsLink.href = `${baseUrl}/docs`;
}

function setStatus(node, text, kind) {
  node.textContent = text;
  node.className = `status ${kind}`;
}

function valueOrDash(value) {
  return value === undefined || value === null || value === "" ? "-" : String(value);
}

function numberOrNull(value) {
  const numberValue = Number(value);
  return Number.isFinite(numberValue) ? numberValue : null;
}

function formatTemperature(value) {
  const numberValue = numberOrNull(value);
  return numberValue === null ? "-" : numberValue.toFixed(1).replace(".", ",");
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
    error.data = data;
    error.latencyMs = latencyMs;
    throw error;
  }
  return { data, latencyMs };
}

function visibleChatErrorMessage(error) {
  const detail = error?.data?.detail;
  if (detail && typeof detail === "object") {
    return String(detail.message || detail.code || error.message);
  }
  if (error?.data?.message) return String(error.data.message);
  if (error?.name === "AbortError") return "Solicitud cancelada.";
  if (error?.message === "Failed to fetch") {
    return "Failed to fetch. Revisa Backend base URL, CORS y que FastAPI este accesible.";
  }
  return error?.message || "Error inesperado llamando al backend.";
}

function selectedModelProvider() {
  const option = elements.modelSelect.selectedOptions[0];
  return normalizeProviderModel(option?.dataset.provider, elements.modelSelect.value).provider;
}

function selectedProviderModel() {
  const option = elements.modelSelect.selectedOptions[0];
  return normalizeProviderModel(option?.dataset.provider, elements.modelSelect.value);
}

function replaceModelOptions(items) {
  elements.modelSelect.innerHTML = "";
  const models = Array.isArray(items) && items.length ? items : fallbackModels;
  for (const item of models) {
    const option = document.createElement("option");
    option.value = item.model;
    option.dataset.provider = item.provider;
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
  try {
    const { data } = await fetchJsonWithLatency(endpoint("/api/models/chat"));
    replaceModelOptions(Array.isArray(data?.items) ? data.items : []);
  } catch (error) {
    replaceModelOptions(fallbackModels);
    setStatus(elements.chatStatus, `Modelos fallback: ${visibleChatErrorMessage(error)}`, "muted");
  }
}

async function loadChatOptions() {
  try {
    const { data } = await fetchJsonWithLatency(endpoint("/api/chat/options"));
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
  const answer = data?.answer ?? data?.response ?? "";
  const traceId = data?.trace_id || data?.request_id;
  const chunks = Array.isArray(data?.chunks) ? data.chunks : [];
  const warnings = Array.isArray(data?.warnings) ? data.warnings : [];

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
  renderEvidence(data || {}, useRag);

  appendChatMessage({
    role: "assistant",
    text: answer || "(respuesta vacia)",
    meta: [
      ["provider", data?.provider],
      ["model", data?.model],
      ["retrieval", data?.retrieval_status],
      ["latency_ms", data?.latency_ms ?? latencyMs],
      ["trace_id", traceId ? String(traceId).slice(0, 8) : "-"],
    ],
  });
}

function buildChatPayload(message) {
  const selected = selectedProviderModel();
  return {
    message,
    provider: selected.provider,
    model: selected.model,
    temperature: numberOrNull(elements.temperatureSelect.value),
    use_rag: elements.useRagInput.checked,
  };
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
    const { data, latencyMs } = await fetchJsonWithLatency(endpoint("/chat"), {
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
  try {
    const { data, latencyMs } = await fetchJsonWithLatency(endpoint("/health"));
    setStatus(elements.healthStatus, `${valueOrDash(data.status || "ok")} (${latencyMs} ms)`, "ok");
  } catch (error) {
    setStatus(elements.healthStatus, visibleChatErrorMessage(error), "error");
  }
}

function init() {
  const savedBackendUrl = localStorage.getItem("locales.backendUrl");
  if (savedBackendUrl) elements.backendUrl.value = savedBackendUrl;
  if (!elements.backendUrl.value) elements.backendUrl.value = DEFAULT_BACKEND_URL;

  updateBackendLinks();
  replaceModelOptions(fallbackModels);
  renderChatMessages();
  loadChatModels();
  loadChatOptions();

  elements.backendUrl.addEventListener("change", () => {
    updateBackendLinks();
    loadChatModels();
    loadChatOptions();
  });
  elements.backendUrl.addEventListener("input", updateBackendLinks);
  elements.modelSelect.addEventListener("change", () => {
    const selected = selectedProviderModel();
    localStorage.setItem("locales.chatModel", selected.model);
    localStorage.setItem("locales.chatModelKey", modelOptionKey(selected.provider, selected.model));
  });
  elements.temperatureSelect.addEventListener("change", () => localStorage.setItem("locales.chatTemperature", elements.temperatureSelect.value));
  elements.healthButton.addEventListener("click", checkHealth);
  elements.chatForm.addEventListener("submit", sendChat);
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
