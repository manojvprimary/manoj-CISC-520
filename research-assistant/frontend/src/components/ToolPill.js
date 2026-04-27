import React from "react";

export default function ToolPill({ pill, onViewCode, onViewData }) {
  const { label, pendingCount, doneCount, code, sample } = pill;
  const total = (pendingCount || 0) + (doneCount || 0);
  const isDone = (pendingCount || 0) === 0;

  return (
    <div className={`tool-pill ${isDone ? "done" : "running"}`}>
      <span className="pill-icon">
        {isDone ? (
          <span className="pill-check">✓</span>
        ) : (
          <span className="pill-spinner" />
        )}
      </span>
      <span className="pill-label">{label}</span>
      {total > 1 && <span className="pill-count">×{total}</span>}
      {isDone && (code || sample) && (
        <span className="pill-actions">
          {code && (
            <button
              className="pill-action-btn"
              onClick={() => onViewCode(code)}
            >
              View Code
            </button>
          )}
          {sample && (
            <button
              className="pill-action-btn"
              onClick={() => onViewData(sample)}
            >
              View Data
            </button>
          )}
        </span>
      )}
    </div>
  );
}
