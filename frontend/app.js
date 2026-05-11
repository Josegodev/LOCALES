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
    error.data = data;
    error.latencyMs = latencyMs;
    throw error;
  }
  return { data, latencyMs };
}

function applyTelegramConfig(data) {
  const config = data.config || data;
  if (typeof config.default_model === "string" && config.default_model.trim()) {
    elements.telegramModelInput.value = config.default_model;
  }
  if (typeof config.default_temperature === "number") {
    elements.telegramTemperatureInput.value = String(config.default_temperature);
  }
  if (typeof config.default_rag_enabled === "boolean") {
    elements.telegramRagInput.checked = config.default_rag_enabled;
  }
}

async function callTelegramEndpoint(path, options = {}) {
  updateBackendLinks();
  setStatus(elements.telegramStatus, `Llamando a ${path}...`, "muted");
  elements.telegramRaw.textContent = "-";

  try {
    const { data, latencyMs } = await fetchJsonWithLatency(`${requireBackendBaseUrl()}${path}`, options);
    setStatus(elements.telegramStatus, `OK ${path} (${latencyMs} ms)`, "ok");
    elements.telegramRaw.textContent = prettyJson(data);
    applyTelegramConfig(data);
  } catch (error) {
    setStatus(elements.telegramStatus, `Error ${path}`, "error");
    elements.telegramRaw.textContent = error.data ? prettyJson(error.data) : error.message;
  }
}

function saveTelegramConfig() {
  const temperature = Number(elements.telegramTemperatureInput.value);
  callTelegramEndpoint("/telegram/config", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      default_model: elements.telegramModelInput.value.trim(),
      default_temperature: Number.isFinite(temperature) ? temperature : undefined,
      default_rag_enabled: elements.telegramRagInput.checked,
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
    const { data, latencyMs } = await fetchJsonWithLatency(`${requireBackendBaseUrl()}/health`);
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
    snippet.textContent = valueOrDash(chunks[index]);
    item.append(meta, snippet);
    elements.evidenceList.appendChild(item);
  }
}

async function sendChat() {
  updateBackendLinks();
  const payload = {
    message: elements.messageInput.value.trim(),
    use_rag: elements.useRagInput.checked,
  };

  if (!payload.message) {
    setStatus(elements.chatStatus, "Escribe un mensaje antes de enviar", "error");
    return;
  }

  setStatus(elements.chatStatus, "Enviando a /chat...", "muted");
  elements.chatRaw.textContent = prettyJson({ request: payload });

  try {
    const { data, latencyMs } = await fetchJsonWithLatency(`${requireBackendBaseUrl()}/chat`, {
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
    elements.chatRaw.textContent = prettyJson(data);
    renderEvidence(data);
  } catch (error) {
    setStatus(elements.chatStatus, "Error llamando a /chat", "error");
    elements.chatLatency.textContent = error.latencyMs ? String(error.latencyMs) : "-";
    elements.answerText.textContent = error.message;
    elements.chatRaw.textContent = error.data ? prettyJson(error.data) : error.message;
    renderEvidence({});
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
elements.telegramStatusButton.addEventListener("click", () => callTelegramEndpoint("/telegram/status"));
elements.telegramConfigButton.addEventListener("click", () => callTelegramEndpoint("/telegram/config"));
elements.telegramStartButton.addEventListener("click", () => callTelegramEndpoint("/telegram/start", { method: "POST" }));
elements.telegramStopButton.addEventListener("click", () => callTelegramEndpoint("/telegram/stop", { method: "POST" }));
elements.telegramSaveConfigButton.addEventListener("click", saveTelegramConfig);
