/**
 * Lightweight pub/sub bus for toast notifications.
 *
 * Decouples apiClient (plain JS module) from React so toasts can be triggered
 * from anywhere without importing React or using context.
 *
 * Usage:
 *   emitToast({ message: "Something went wrong.", type: "error" });
 *   const unsub = onToast((toast) => { ... });  // returns unsubscribe fn
 */

const _listeners = new Set();

/**
 * Subscribe to toast events. Returns an unsubscribe function.
 * @param {(toast: { id: string, message: string, type: string, durationMs: number }) => void} handler
 */
export function onToast(handler) {
  _listeners.add(handler);
  return () => _listeners.delete(handler);
}

/**
 * Emit a toast notification to all subscribers.
 * @param {{ message: string, type?: "error"|"warning"|"success", durationMs?: number }} opts
 */
export function emitToast({ message, type = "error", durationMs = 4500 }) {
  const toast = { id: crypto.randomUUID(), message, type, durationMs };
  _listeners.forEach((fn) => fn(toast));
}
