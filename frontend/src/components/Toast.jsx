import { useEffect, useState } from "react";
import { onToast } from "../lib/toastBus";
import "./Toast.css";

const TYPE_ICON = {
  error: "✕",
  warning: "⚠",
  success: "✓",
};

export default function Toast() {
  const [toasts, setToasts] = useState([]);

  useEffect(() => {
    return onToast((toast) => {
      setToasts((prev) => [...prev, toast]);
      setTimeout(() => {
        setToasts((prev) => prev.filter((t) => t.id !== toast.id));
      }, toast.durationMs);
    });
  }, []);

  if (toasts.length === 0) return null;

  return (
    <div className="toast-container" role="region" aria-live="polite">
      {toasts.map((toast) => (
        <div key={toast.id} className={`toast toast--${toast.type}`}>
          <span className="toast-icon" aria-hidden="true">
            {TYPE_ICON[toast.type] ?? "•"}
          </span>
          <span className="toast-message">{toast.message}</span>
          <button
            className="toast-close"
            aria-label="Dismiss"
            onClick={() =>
              setToasts((prev) => prev.filter((t) => t.id !== toast.id))
            }
          >
            ×
          </button>
        </div>
      ))}
    </div>
  );
}
