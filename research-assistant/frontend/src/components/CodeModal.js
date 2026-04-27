import React, { useState, useEffect } from "react";

export default function CodeModal({ code, onClose }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(code).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  useEffect(() => {
    const handler = (e) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [onClose]);

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-panel" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div className="modal-title">
            <span className="modal-lang-badge">python</span>
            Generated Code
          </div>
          <div className="modal-header-actions">
            <button className="modal-copy-btn" onClick={handleCopy}>
              {copied ? "Copied!" : "Copy"}
            </button>
            <button className="modal-close-btn" onClick={onClose}>
              ✕
            </button>
          </div>
        </div>
        <pre className="modal-code">
          <code>{code}</code>
        </pre>
      </div>
    </div>
  );
}
