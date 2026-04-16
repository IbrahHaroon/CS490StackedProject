import { useState, useEffect, useRef, useCallback } from "react";
import { getLogs, clearLogs } from "../lib/apiClient";

const API = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

const STATUS_COLORS = {
  success: "#4caf50",
  clientError: "#ff9800",
  serverError: "#f44336",
  networkError: "#9e9e9e",
};

function statusColor(status) {
  if (status === 0) return STATUS_COLORS.networkError;
  if (status >= 200 && status < 300) return STATUS_COLORS.success;
  if (status >= 400 && status < 500) return STATUS_COLORS.clientError;
  return STATUS_COLORS.serverError;
}

const TAB_STYLE_BASE = {
  border: "none",
  padding: "4px 10px",
  borderRadius: 4,
  cursor: "pointer",
  fontFamily: "monospace",
  fontSize: 11,
  whiteSpace: "nowrap",
};

function TabButton({ active, label, onClick }) {
  return (
    <button
      onClick={onClick}
      style={{
        ...TAB_STYLE_BASE,
        background: active ? "#333" : "transparent",
        color: active ? "#0f0" : "#888",
      }}
    >
      {label}
    </button>
  );
}

function HeaderButton({ onClick, children, style = {} }) {
  return (
    <button
      onClick={onClick}
      style={{
        background: "transparent",
        color: "#888",
        border: "none",
        cursor: "pointer",
        fontFamily: "monospace",
        fontSize: 12,
        padding: "2px 6px",
        ...style,
      }}
    >
      {children}
    </button>
  );
}

function EmptyState({ message }) {
  return (
    <div style={{ color: "#555", padding: 16, textAlign: "center" }}>
      {message}
    </div>
  );
}

function DevLogViewer() {
  // "closed" = just the button, "minimized" = collapsed bar, "open" = full panel
  const [viewState, setViewState] = useState("closed");
  const [tab, setTab] = useState("frontend"); // "frontend" | "backend"
  const [, setTick] = useState(0);
  const [backendLogs, setBackendLogs] = useState([]);
  const [backendClearedAfter, setBackendClearedAfter] = useState(null);
  const scrollRef = useRef(null);

  // Refresh display every second so log counts stay current in all view states
  useEffect(() => {
    const id = setInterval(() => setTick((t) => t + 1), 1000);
    return () => clearInterval(id);
  }, []);

  // Fetch backend logs when the backend tab is active
  const fetchBackendLogs = useCallback((afterTs) => {
    const params = new URLSearchParams({ tail: "150" });
    if (afterTs) params.set("after", afterTs);
    fetch(`${API}/logs/backend?${params}`)
      .then((r) => (r.ok ? r.json() : []))
      .then(setBackendLogs)
      .catch(() => {});
  }, []);

  const handleTabChange = useCallback((newTab) => {
    setTab(newTab);
  }, []);

  // Poll backend logs so the count stays current in all view states
  useEffect(() => {
    fetchBackendLogs(backendClearedAfter);
    const id = setInterval(() => fetchBackendLogs(backendClearedAfter), 3000);
    return () => clearInterval(id);
  }, [backendClearedAfter, fetchBackendLogs]);

  const apiLogs = getLogs();
  const totalCount = apiLogs.length + backendLogs.length;

  // Auto-scroll to bottom only when new entries arrive
  const prevCountRef = useRef(0);
  useEffect(() => {
    const currentCount =
      tab === "frontend" ? apiLogs.length : backendLogs.length;
    if (currentCount > prevCountRef.current && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
    prevCountRef.current = currentCount;
  }, [tab, apiLogs.length, backendLogs.length]);

  // --- Closed state: small floating button ---
  if (viewState === "closed") {
    return (
      <button
        onClick={() => setViewState("open")}
        style={{
          position: "fixed",
          bottom: 16,
          right: 34,
          zIndex: 99999,
          background: "#1e1e1e",
          color: "#0f0",
          border: "1px solid #444",
          borderRadius: 6,
          padding: "6px 12px",
          fontSize: 12,
          fontFamily: "monospace",
          cursor: "pointer",
          opacity: 0.85,
        }}
      >
        Logs ({totalCount})
      </button>
    );
  }

  // --- Minimized state: slim bar at the bottom ---
  if (viewState === "minimized") {
    return (
      <div
        style={{
          position: "fixed",
          bottom: 0,
          right: 18,
          width: 600,
          maxWidth: "100vw",
          height: 32,
          zIndex: 99999,
          background: "#222",
          color: "#ddd",
          border: "1px solid #444",
          borderRadius: "8px 0 0 0",
          fontFamily: "monospace",
          fontSize: 11,
          display: "flex",
          alignItems: "center",
          padding: "0 10px",
          gap: 8,
        }}
      >
        <span style={{ color: "#0f0" }}>Log Console</span>
        <span style={{ color: "#555" }}>
          {apiLogs.length} frontend / {backendLogs.length} backend
        </span>
        <div style={{ flex: 1 }} />
        <HeaderButton onClick={() => setViewState("open")}>expand</HeaderButton>
        <HeaderButton onClick={() => setViewState("closed")}>x</HeaderButton>
      </div>
    );
  }

  // --- Open state: full panel ---
  const clearAll = () => {
    clearLogs();
    setBackendLogs([]);
    setBackendClearedAfter(new Date().toISOString());
    setTick((t) => t + 1);
  };

  return (
    <div
      style={{
        position: "fixed",
        bottom: 0,
        right: 18,
        width: 700,
        maxWidth: "100vw",
        height: 400,
        zIndex: 99999,
        background: "#1a1a1a",
        color: "#ddd",
        border: "1px solid #444",
        borderRadius: "8px 0 0 0",
        fontFamily: "monospace",
        fontSize: 11,
        display: "flex",
        flexDirection: "column",
      }}
    >
      {/* Header with tabs */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 4,
          padding: "5px 10px",
          borderBottom: "1px solid #333",
          background: "#222",
          flexWrap: "wrap",
        }}
      >
        <span
          style={{
            color: "#0f0",
            fontSize: 11,
            fontWeight: 700,
            marginRight: 4,
          }}
        >
          LOG CONSOLE
        </span>
        <span style={{ color: "#333", marginRight: 2 }}>|</span>
        <TabButton
          active={tab === "frontend"}
          label={`Frontend (${apiLogs.length})`}
          onClick={() => handleTabChange("frontend")}
        />
        <TabButton
          active={tab === "backend"}
          label={`Backend (${backendLogs.length})`}
          onClick={() => handleTabChange("backend")}
        />
        <div style={{ flex: 1 }} />
        <HeaderButton onClick={clearAll}>clear</HeaderButton>
        <HeaderButton
          onClick={() => setViewState("minimized")}
          style={{ fontSize: 14 }}
        >
          _
        </HeaderButton>
        <HeaderButton
          onClick={() => setViewState("closed")}
          style={{ fontSize: 14 }}
        >
          x
        </HeaderButton>
      </div>

      {/* Log entries */}
      <div
        ref={scrollRef}
        style={{ flex: 1, overflow: "auto", padding: "4px 8px" }}
      >
        {/* Frontend tab */}
        {tab === "frontend" &&
          (apiLogs.length === 0 ? (
            <EmptyState message="No frontend API calls logged yet" />
          ) : (
            apiLogs.map((log, i) => (
              <div
                key={i}
                style={{
                  padding: "3px 0",
                  borderBottom: "1px solid #2a2a2a",
                  lineHeight: 1.5,
                }}
              >
                <span style={{ color: "#888" }}>
                  {log.timestamp?.slice(11, 19)}
                </span>{" "}
                <span style={{ color: "#6cf" }}>{log.method}</span>{" "}
                <span style={{ color: "#ccc" }}>{log.path}</span>{" "}
                <span
                  style={{ color: statusColor(log.status), fontWeight: 700 }}
                >
                  {log.status || "ERR"}
                </span>{" "}
                <span style={{ color: "#888" }}>{log.durationMs}ms</span>{" "}
                <span style={{ color: "#a78bfa" }}>[{log.caller}]</span>{" "}
                <span
                  style={{ color: "#555", fontSize: 9, cursor: "pointer" }}
                  title={`Click to copy: ${log.requestId}`}
                  onClick={() => navigator.clipboard.writeText(log.requestId)}
                >
                  {log.requestId?.slice(0, 8)}...
                </span>
                {log.error && (
                  <div
                    style={{ color: "#f44336", marginLeft: 16, fontSize: 10 }}
                  >
                    {log.error}
                    {log.stack && (
                      <pre
                        style={{
                          margin: "2px 0 0",
                          fontSize: 9,
                          color: "#c62828",
                          whiteSpace: "pre-wrap",
                          maxHeight: 60,
                          overflow: "auto",
                        }}
                      >
                        {log.stack}
                      </pre>
                    )}
                  </div>
                )}
              </div>
            ))
          ))}

        {/* Backend tab */}
        {tab === "backend" &&
          (backendLogs.length === 0 ? (
            <EmptyState message="No backend logs yet — logs appear after requests hit the server" />
          ) : (
            backendLogs.map((log, i) => (
              <div
                key={i}
                style={{
                  padding: "3px 0",
                  borderBottom: "1px solid #2a2a2a",
                  lineHeight: 1.5,
                }}
              >
                <span style={{ color: "#888" }}>
                  {log.timestamp?.slice(11, 19)}
                </span>{" "}
                <span
                  style={{
                    color: log.level === "ERROR" ? "#f44336" : "#4caf50",
                    fontWeight: 700,
                    fontSize: 9,
                  }}
                >
                  {log.level}
                </span>{" "}
                <span style={{ color: "#6cf" }}>{log.method}</span>{" "}
                <span style={{ color: "#ccc" }}>{log.path}</span>{" "}
                <span
                  style={{
                    color: statusColor(log.status_code),
                    fontWeight: 700,
                  }}
                >
                  {log.status_code}
                </span>{" "}
                <span style={{ color: "#888" }}>{log.duration_ms}ms</span>{" "}
                <span style={{ color: "#a78bfa" }}>[{log.handler}]</span>{" "}
                <span style={{ color: "#555", fontSize: 9 }}>
                  {log.handler_file
                    ? log.handler_file.split("/").slice(-2).join("/")
                    : ""}
                </span>{" "}
                {log.user_email && (
                  <span style={{ color: "#4dd0e1", fontSize: 9 }}>
                    {log.user_email}
                  </span>
                )}{" "}
                {log.request_id && log.request_id !== "none" && (
                  <span
                    style={{ color: "#555", fontSize: 9, cursor: "pointer" }}
                    title={`Click to copy: ${log.request_id}`}
                    onClick={() =>
                      navigator.clipboard.writeText(log.request_id)
                    }
                  >
                    {log.request_id.slice(0, 8)}...
                  </span>
                )}
                {log.exception && (
                  <div
                    style={{ color: "#f44336", marginLeft: 16, fontSize: 10 }}
                  >
                    {log.exception.type}: {log.exception.message}
                    {log.exception.traceback && (
                      <pre
                        style={{
                          margin: "2px 0 0",
                          fontSize: 9,
                          color: "#c62828",
                          whiteSpace: "pre-wrap",
                          maxHeight: 80,
                          overflow: "auto",
                        }}
                      >
                        {log.exception.traceback.join("")}
                      </pre>
                    )}
                  </div>
                )}
              </div>
            ))
          ))}
      </div>
    </div>
  );
}

export default DevLogViewer;
