// In-memory ring buffer for UI action logs
const ACTION_LOG_SIZE = 200;
const actionLogs = [];

export function getActionLogs() {
  return actionLogs;
}

/**
 * Clear flushed action logs. Called by apiClient after sending logs to the backend.
 */
export function markActionLogsFlushed() {
  actionLogs.length = 0;
}

/**
 * Log a user interaction (click, form submission, navigation, etc.)
 *
 * @param {string} type - "click" | "form_submit" | "navigation" | "modal_open" | "modal_close" | etc.
 * @param {Object} detail - Contextual detail, e.g. { component: "Profile", element: "save_button" }
 */
export function logAction(type, detail = {}) {
  const entry = {
    type,
    ...detail,
    timestamp: new Date().toISOString(),
    page: window.location.pathname,
  };
  actionLogs.push(entry);
  if (actionLogs.length > ACTION_LOG_SIZE) actionLogs.shift();
  if (import.meta.env.DEV) {
    console.log(`[ACTION] ${type}`, detail);
  }
}

/**
 * Log a route navigation event. Call from App.jsx using useLocation.
 */
export function logNavigation(from, to) {
  logAction("navigation", { from, to });
}
