const STAGE_STYLES = {
  Interested: { background: "#6c757d" },
  Applied: { background: "#6f42c1" },
  Interview: { background: "#fd7e14" },
  Offer: { background: "#28a745" },
  Rejected: { background: "#dc3545" },
  Archived: { background: "#343a40" },
  Withdrawn: { background: "#adb5bd" },
};

export default function StageBadge({ status }) {
  const style = STAGE_STYLES[status] || { background: "#999" };

  return (
    <span
      style={{
        ...style,
        color: "white",
        padding: "6px 12px",
        borderRadius: "20px",
        fontSize: "0.85rem",
        fontWeight: "600",
      }}
    >
      {status}
    </span>
  );
}
