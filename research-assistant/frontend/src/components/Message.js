import React, { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import CodeBlock from "./CodeBlock";
import CodeModal from "./CodeModal";
import DataModal from "./DataModal";
import ToolPill from "./ToolPill";

const markdownComponents = {
  code({ node, inline, className, children, ...props }) {
    const match = /language-(\w+)/.exec(className || "");
    const code = String(children).replace(/\n$/, "");
    if (!inline) {
      return <CodeBlock code={code} language={match ? match[1] : ""} />;
    }
    return (
      <code className="inline-code" {...props}>
        {children}
      </code>
    );
  },
  table({ children }) {
    return (
      <div className="table-wrap">
        <table>{children}</table>
      </div>
    );
  },
};

export default function Message({ msg }) {
  const [modal, setModal] = useState(null);

  if (msg.role === "user") {
    return <div className="message user-message">{msg.content}</div>;
  }

  if (msg.type === "error") {
    return (
      <div className="message assistant-message error-message">
        {msg.content}
      </div>
    );
  }

  const isEmpty =
    !msg.response && (!msg.toolPills || msg.toolPills.length === 0);

  return (
    <div className="message assistant-message">
      {modal && modal.type === "code" && (
        <CodeModal code={modal.data} onClose={() => setModal(null)} />
      )}
      {modal && modal.type === "data" && (
        <DataModal
          dataset={modal.data.dataset}
          columns={modal.data.columns}
          rows={modal.data.rows}
          onClose={() => setModal(null)}
        />
      )}

      {msg.toolPills && msg.toolPills.length > 0 && (
        <div className="tool-pills">
          {msg.toolPills.map((pill, i) => (
            <ToolPill
              key={i}
              pill={pill}
              onViewCode={(code) => setModal({ type: "code", data: code })}
              onViewData={(sample) => setModal({ type: "data", data: sample })}
            />
          ))}
        </div>
      )}

      {msg.response && (
        <div className="response-text">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={markdownComponents}
          >
            {msg.response}
          </ReactMarkdown>
          {msg.streaming && <span className="stream-cursor" />}
        </div>
      )}
      {isEmpty && msg.streaming && <span className="stream-cursor" />}
      {msg.plots && msg.plots.length > 0 && (
        <div className="plots-container">
          {msg.plots.map((plot, i) => (
            <img
              key={i}
              src={`data:image/png;base64,${plot}`}
              alt={`Chart ${i + 1}`}
              className="chart-img"
            />
          ))}
        </div>
      )}
    </div>
  );
}
