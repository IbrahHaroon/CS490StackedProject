import { getActionLogs, markActionLogsFlushed } from "./actionLogger";

const API = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

function generateRequestId() {
  return crypto.randomUUID();
}

function getToken() {
  return localStorage.getItem("token");
}

// In-memory ring buffer for API call logs
const LOG_BUFFER_SIZE = 500;
const logs = [];

export function getLogs() {
  return logs;
}

export function clearLogs() {
  logs.length = 0;
  _lastFlushedApiIndex = 0;
}

function pushLog(entry) {
  logs.push(entry);
  if (logs.length > LOG_BUFFER_SIZE) logs.shift();
  if (import.meta.env.DEV) {
    console.groupCollapsed(
      `[API] ${entry.method} ${entry.path} → ${entry.status ?? "pending"} (${entry.durationMs ?? "?"}ms) [${entry.caller}]`
    );
    console.log(entry);
    console.groupEnd();
  }
}

/**
 * Central fetch wrapper. All components should use this instead of raw fetch().
 *
 * @param {string} path - API path, e.g. "/profile/me"
 * @param {RequestInit} options - Standard fetch options (method, body, headers)
 * @param {Object} context - Logging context
 * @param {string} context.caller - Identifies the call site, e.g. "Profile.saveProfile"
 * @param {string} [context.action] - Describes the action, e.g. "save_profile"
 * @returns {Promise<Response>}
 */
export async function apiRequest(path, options = {}, context = {}) {
  const { caller = "unknown", action = "api_call" } = context;
  const requestId = generateRequestId();
  const url = `${API}${path}`;
  const token = getToken();
  const startTime = performance.now();

  // Build headers — do NOT set Content-Type for FormData (browser sets boundary)
  const headers = { ...(options.headers || {}) };
  headers["X-Request-ID"] = requestId;
  if (token && !headers["Authorization"]) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const fetchOptions = {
    ...options,
    headers,
  };

  const logEntry = {
    requestId,
    method: options.method || "GET",
    url,
    path,
    caller,
    action,
    timestamp: new Date().toISOString(),
    status: null,
    durationMs: null,
    error: null,
  };

  try {
    const response = await fetch(url, fetchOptions);
    const durationMs = Math.round(performance.now() - startTime);

    logEntry.status = response.status;
    logEntry.durationMs = durationMs;

    // Attach requestId to the response for downstream correlation
    response.requestId = requestId;

    pushLog(logEntry);
    return response;
  } catch (error) {
    const durationMs = Math.round(performance.now() - startTime);
    logEntry.status = 0; // network error
    logEntry.durationMs = durationMs;
    logEntry.error = error.message;
    logEntry.stack = error.stack || null;
    pushLog(logEntry);
    throw error;
  }
}

// --- Log persistence: flush logs to backend/logs/frontend.log every 10 seconds ---
let _flushTimer = null;
let _lastFlushedApiIndex = 0;

function startLogFlushing() {
  if (_flushTimer) return;
  _flushTimer = setInterval(() => flushLogs(), 10000);
}

async function flushLogs() {
  const actionLogs = getActionLogs();

  const apiToFlush = logs.slice(_lastFlushedApiIndex);
  const actionsToFlush = actionLogs.slice();

  if (apiToFlush.length === 0 && actionsToFlush.length === 0) return;

  const batch = [...apiToFlush, ...actionsToFlush];
  _lastFlushedApiIndex = logs.length;
  markActionLogsFlushed();

  try {
    // Use raw fetch to avoid logging the log-flush call itself
    await fetch(`${API}/logs/flush`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ logs: batch }),
    });
  } catch {
    // If flush fails, indices stay advanced — logs are still in the in-memory buffer
  }
}

// Also flush when the page is being unloaded
if (typeof window !== "undefined") {
  startLogFlushing();

  window.addEventListener("beforeunload", () => {
    // sendBeacon for reliability on page close
    const apiToFlush = logs.slice(_lastFlushedApiIndex);
    const actionsToFlush = getActionLogs();
    if (apiToFlush.length === 0 && actionsToFlush.length === 0) return;
    const batch = [...apiToFlush, ...actionsToFlush];
    navigator.sendBeacon(
      `${API}/logs/flush`,
      new Blob([JSON.stringify({ logs: batch })], { type: "application/json" })
    );
  });
}

// Convenience wrappers
export const api = {
  get: (path, context) => apiRequest(path, {}, context),

  post: (path, body, context) => {
    const opts = { method: "POST" };
    if (body instanceof FormData) {
      opts.body = body;
      // No Content-Type — browser sets multipart boundary automatically
    } else if (body instanceof URLSearchParams) {
      opts.body = body;
      opts.headers = { "Content-Type": "application/x-www-form-urlencoded" };
    } else {
      opts.headers = { "Content-Type": "application/json" };
      opts.body = JSON.stringify(body);
    }
    return apiRequest(path, opts, context);
  },

  put: (path, body, context) => {
    const opts = {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    };
    return apiRequest(path, opts, context);
  },

  delete: (path, context) =>
    apiRequest(path, { method: "DELETE" }, context),
};
