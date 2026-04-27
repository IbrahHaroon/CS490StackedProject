/**
 * Client-side centralized error capture.
 *
 * Two responsibilities:
 *
 *  1. initGlobalErrorCapture() — attaches window-level handlers for unhandled
 *     JS errors and promise rejections, routing them through the existing
 *     actionLogger buffer so they are included in the periodic /logs/flush call.
 *     Call once from main.jsx before ReactDOM.render.
 *
 *  2. parseApiError(response) — async helper that extracts a structured error
 *     description from a failed API Response. Handles both the new normalized
 *     format ({ detail, error_code, request_id, timestamp }) and the legacy
 *     FastAPI default ({ detail: "..." } or { detail: [{loc, msg, type}] }).
 *     New components should use this instead of manually calling res.json().
 */

import { logAction } from "./actionLogger";

let _initialized = false;

/**
 * Attach global error capture handlers.
 * Safe to call multiple times — only installs once per page load.
 */
export function initGlobalErrorCapture() {
  if (_initialized || typeof window === "undefined") return;
  _initialized = true;

  // Uncaught synchronous errors (e.g. TypeError in event handlers)
  window.onerror = (message, source, lineno, colno, error) => {
    logAction("js_error", {
      component: "window",
      error_message: String(message),
      source: source ?? null,
      lineno: lineno ?? null,
      colno: colno ?? null,
      stack: error?.stack ?? null,
    });
    return false; // let browser still log to console
  };

  // Unhandled promise rejections (e.g. async function that throws without a catch)
  window.addEventListener("unhandledrejection", (event) => {
    const reason = event.reason;
    logAction("unhandled_rejection", {
      component: "window",
      error_message:
        reason instanceof Error ? reason.message : String(reason ?? "unknown"),
      stack: reason instanceof Error ? (reason.stack ?? null) : null,
    });
  });
}

/**
 * Extract a structured error description from a failed API Response.
 *
 * @param {Response} response - The fetch Response object from apiClient
 * @returns {Promise<{ message: string, errorCode: string|null, requestId: string|null, status: number }>}
 *
 * @example
 *   const res = await api.put("/jobs/1", payload, ctx);
 *   if (!res.ok) {
 *     const { message } = await parseApiError(res);
 *     setError(message);
 *   }
 */
export async function parseApiError(response) {
  let body = {};
  try {
    body = await response.json();
  } catch {
    // response body is empty or not JSON — fall through to status-based defaults
  }

  const {
    detail,
    message: serverMessage = null,
    error_code: errorCode = null,
    request_id: requestId = null,
  } = body;

  let message;
  if (serverMessage) {
    // Prefer the pre-formatted message field (set by our validation handler)
    message = serverMessage;
  } else if (typeof detail === "string" && detail.length > 0) {
    message = detail;
  } else if (Array.isArray(detail) && detail.length > 0) {
    // Fallback: parse raw Pydantic error array
    message = detail
      .map((e) => {
        const field = (e.loc ?? []).slice(1).join(".");
        return field ? `${field}: ${e.msg}` : e.msg;
      })
      .join("; ");
  } else {
    message = `Request failed (${response.status})`;
  }

  return {
    message,
    errorCode,
    // Prefer server-echoed request_id; fall back to the id apiClient attached
    requestId: requestId ?? response.requestId ?? null,
    status: response.status,
  };
}
