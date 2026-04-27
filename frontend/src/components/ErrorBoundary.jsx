import React from "react";
import { logAction } from "../lib/actionLogger";

/**
 * React error boundary — catches rendering errors thrown anywhere in the
 * wrapped component tree, logs them through the existing actionLogger buffer
 * (flushed periodically to /logs/flush), and shows a minimal fallback UI
 * so the user sees a message rather than a blank screen.
 *
 * Usage:
 *   <ErrorBoundary name="MySection">
 *     <MyComponent />
 *   </ErrorBoundary>
 *
 * The optional `name` prop identifies the boundary in logs.
 */
export class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, errorId: null };
  }

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error, info) {
    const errorId = crypto.randomUUID();
    logAction("react_render_error", {
      component: this.props.name ?? "ErrorBoundary",
      error_id: errorId,
      error_message: error.message,
      // componentStack traces where in the tree the error originated
      component_stack: info.componentStack ?? null,
    });
    this.setState({ errorId });
  }

  render() {
    if (this.state.hasError) {
      return (
        <div
          style={{
            padding: "2rem",
            textAlign: "center",
            color: "var(--text, #ccc)",
          }}
        >
          <h2 style={{ color: "#ef4444", marginBottom: "0.5rem" }}>
            Something went wrong.
          </h2>
          <p
            style={{
              fontSize: "0.8rem",
              opacity: 0.55,
              marginBottom: "1.25rem",
            }}
          >
            Error ID: {this.state.errorId}
          </p>
          <button
            style={{
              padding: "0.5rem 1.25rem",
              borderRadius: "6px",
              border: "1px solid var(--border, #444)",
              background: "transparent",
              color: "var(--text, #ccc)",
              cursor: "pointer",
              fontSize: "0.9rem",
            }}
            onClick={() => this.setState({ hasError: false, errorId: null })}
          >
            Try again
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
