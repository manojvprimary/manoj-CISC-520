import React, { useEffect } from "react";

export default function DataModal({ dataset, columns, rows, onClose }) {
  useEffect(() => {
    const handler = (e) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [onClose]);

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div
        className="modal-panel modal-panel-wide"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="modal-header">
          <div className="modal-title">
            Sample rows —{" "}
            <span className="modal-dataset-name">{dataset}</span>
          </div>
          <button className="modal-close-btn" onClick={onClose}>
            ✕
          </button>
        </div>
        <div className="modal-table-wrap">
          <table className="modal-table">
            <thead>
              <tr>
                {columns.map((col, i) => (
                  <th key={i}>{col}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {(rows || []).map((row, i) => (
                <tr key={i}>
                  {(Array.isArray(row)
                    ? row
                    : columns.map((c) => row[c])
                  ).map((cell, j) => (
                    <td key={j}>
                      {cell === null || cell === undefined
                        ? "—"
                        : String(cell)}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
