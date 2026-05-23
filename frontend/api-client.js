(function initializeLocalesApiClient() {
  const DEFAULT_TIMEOUT_MS = 15000;
  const CONFIG_KEY = "__LOCALES_RUNTIME_CONFIG__";

  function runtimeConfig() {
    const value = window[CONFIG_KEY];
    return value && typeof value === "object" ? value : {};
  }

  function normalizeUrlCandidate(value) {
    if (typeof value !== "string") {
      return "";
    }

    const trimmed = value.trim();
    if (!trimmed) {
      return "";
    }

    const withProtocol = /^https?:\/\//i.test(trimmed) ? trimmed : `https://${trimmed}`;
    const withoutTrailingSlash = withProtocol.replace(/\/+$/, "");

    try {
      const parsed = new URL(withoutTrailingSlash);
      if (!/^https?:$/i.test(parsed.protocol)) {
        return "";
      }
      return parsed.toString().replace(/\/+$/, "");
    } catch {
      return "";
    }
  }

  function normalizeBackendBaseUrl(value) {
    const rawValue = typeof value === "string" ? value : "";
    const trimmed = rawValue.trim();

    if (!trimmed) {
      return {
        ok: false,
        rawValue,
        baseUrl: "",
        code: "backend_base_url_missing",
        message: "Backend base URL vacía. Pega la URL pública https://xxxxx.trycloudflare.com.",
      };
    }

    if (/^cloudflared\s+tunnel\b/i.test(trimmed)) {
      const extractedMatch = trimmed.match(/--url\s+([^\s]+)/i);
      const extractedUrl = extractedMatch ? normalizeUrlCandidate(extractedMatch[1]) : "";
      return {
        ok: false,
        rawValue,
        baseUrl: "",
        extractedUrl,
        code: "cloudflared_command_instead_of_public_url",
        message: "Ese comando se ejecuta en terminal. Aquí debes pegar la URL https://xxxxx.trycloudflare.com generada por Cloudflare.",
      };
    }

    if (/\s/.test(trimmed)) {
      return {
        ok: false,
        rawValue,
        baseUrl: "",
        code: "invalid_backend_base_url",
        message: "Backend base URL inválida. Usa una URL HTTPS sin espacios ni comandos shell.",
      };
    }

    const normalizedUrl = normalizeUrlCandidate(trimmed);
    if (!normalizedUrl) {
      return {
        ok: false,
        rawValue,
        baseUrl: "",
        code: "invalid_backend_base_url",
        message: "Backend base URL inválida. Usa una URL HTTPS tipo https://xxxxx.trycloudflare.com.",
      };
    }

    return {
      ok: true,
      rawValue,
      baseUrl: normalizedUrl,
      code: null,
      message: "",
    };
  }

  function normalizeBaseUrl(value) {
    const normalized = normalizeBackendBaseUrl(value);
    return normalized.ok ? normalized.baseUrl : "";
  }

  function resolveConfiguredBaseUrl(overrideValue) {
    const config = runtimeConfig();
    return normalizeBaseUrl(
      overrideValue
      ?? config.BACKEND_BASE_URL
      ?? config.backendBaseUrl
      ?? ""
    );
  }

  function resolveAuthToken(overrideValue) {
    if (typeof overrideValue === "string" && overrideValue.trim()) {
      return overrideValue.trim();
    }

    try {
      const localToken = window.localStorage.getItem("locales.authToken");
      if (typeof localToken === "string" && localToken.trim()) {
        return localToken.trim();
      }
    } catch {}

    const config = runtimeConfig();
    if (typeof config.AUTH_TOKEN === "string" && config.AUTH_TOKEN.trim()) {
      return config.AUTH_TOKEN.trim();
    }

    return "";
  }

  function resolveTimeoutMs(overrideValue) {
    if (Number.isFinite(overrideValue) && overrideValue > 0) {
      return Number(overrideValue);
    }

    const configuredValue = Number(runtimeConfig().API_TIMEOUT_MS);
    if (Number.isFinite(configuredValue) && configuredValue > 0) {
      return configuredValue;
    }

    return DEFAULT_TIMEOUT_MS;
  }

  function createApiError(message, extras) {
    const error = new Error(message);
    Object.assign(error, extras || {});
    return error;
  }

  function buildUrl(path, baseUrl) {
    const resolvedBaseUrl = resolveConfiguredBaseUrl(baseUrl);
    if (!resolvedBaseUrl) {
      const message = "BACKEND_BASE_URL no configurada. Define runtime-config.js o usa Backend base URL.";
      console.error(message);
      throw createApiError(message, {
        code: "backend_base_url_missing",
        isConfigError: true,
      });
    }

    if (/^https?:\/\//i.test(path)) {
      return path;
    }

    const normalizedPath = String(path || "").startsWith("/") ? String(path) : `/${String(path || "")}`;
    return `${resolvedBaseUrl}${normalizedPath}`;
  }

  function buildHeaders(initialHeaders, authToken) {
    const headers = new Headers(initialHeaders || {});
    if (!headers.has("Accept")) {
      headers.set("Accept", "application/json");
    }
    if (authToken && !headers.has("Authorization")) {
      headers.set("Authorization", `Bearer ${authToken}`);
    }
    return headers;
  }

  async function fetchJson(path, options) {
    const requestOptions = options || {};
    const url = buildUrl(path, requestOptions.baseUrl);
    const timeoutMs = resolveTimeoutMs(requestOptions.timeoutMs);
    const headers = buildHeaders(requestOptions.headers, resolveAuthToken(requestOptions.authToken));
    const controller = new AbortController();
    const externalSignal = requestOptions.signal;
    const startedAt = performance.now();
    let timeoutId = null;
    let abortedByTimeout = false;

    const onExternalAbort = () => controller.abort(externalSignal.reason);
    if (externalSignal) {
      if (externalSignal.aborted) {
        controller.abort(externalSignal.reason);
      } else {
        externalSignal.addEventListener("abort", onExternalAbort, { once: true });
      }
    }

    if (timeoutMs > 0) {
      timeoutId = window.setTimeout(() => {
        abortedByTimeout = true;
        controller.abort(new DOMException("Request timeout", "TimeoutError"));
      }, timeoutMs);
    }

    try {
      const response = await fetch(url, {
        ...requestOptions,
        headers,
        signal: controller.signal,
      });
      const latencyMs = Math.round(performance.now() - startedAt);
      const text = await response.text();
      let data;

      try {
        data = text ? JSON.parse(text) : {};
      } catch {
        data = { raw_text: text };
      }

      if (!response.ok) {
        throw createApiError(`HTTP ${response.status}`, {
          code: "http_error",
          status: response.status,
          data,
          latencyMs,
          url,
        });
      }

      return { data, latencyMs, url };
    } catch (error) {
      const latencyMs = Math.round(performance.now() - startedAt);
      if (error?.name === "AbortError") {
        if (abortedByTimeout) {
          throw createApiError("Tiempo de espera agotado al contactar el backend.", {
            code: "request_timeout",
            latencyMs,
            url,
          });
        }
        throw createApiError("Solicitud cancelada.", {
          code: "request_aborted",
          latencyMs,
          url,
          name: "AbortError",
        });
      }

      if (error?.code === "http_error" || error?.isConfigError) {
        throw error;
      }

      throw createApiError("No se pudo conectar con el backend.", {
        code: "network_error",
        latencyMs,
        url,
        cause: error,
      });
    } finally {
      if (timeoutId !== null) {
        window.clearTimeout(timeoutId);
      }
      if (externalSignal) {
        externalSignal.removeEventListener("abort", onExternalAbort);
      }
    }
  }

  window.LOCALES_API_CLIENT = {
    DEFAULT_TIMEOUT_MS,
    normalizeBackendBaseUrl,
    normalizeBaseUrl,
    resolveConfiguredBaseUrl,
    resolveAuthToken,
    resolveTimeoutMs,
    buildUrl,
    fetchJson,
  };
}());
