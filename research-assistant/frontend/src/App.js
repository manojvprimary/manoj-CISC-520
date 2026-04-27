import React, { useState, useRef, useEffect } from "react";
import Message from "./components/Message";
import { BACKEND_URL, EXAMPLE_PROMPTS } from "./config";
import "./App.css";

const WELCOME_MESSAGE = {
  role: "assistant",
  type: "result",
  response:
    "Hi! I'm your **Animal Rescue Research Assistant**. Here's what I can help you explore:\n\n" +
    "- **National shelter trends** — intake, adoption & euthanasia rates across all US states (2024–25 SAC data)\n" +
    "- **Austin Animal Center** — deep-dive intake/outcome history for one of the largest open-admission US shelters\n" +
    "- **NYC live shelter reports** — real-time Animal Care & Control data via the NYC Open Data API\n" +
    "- **Pet adoption prediction** — explore which animal traits drive adoption outcomes\n" +
    "- **Multi-org welfare benchmarks** — compare welfare scores and care metrics across shelter networks\n" +
    "- **Your own CSV** — upload any dataset for instant AI-powered analysis\n\n" +
    "Pick an area below or ask me anything — I'll tell you what data is available and suggest the most useful analyses.",
  plots: [],
};

function App() {
  const [messages, setMessages] = useState([WELCOME_MESSAGE]);
  const [input, setInput] = useState("");
  const [uploadedCsv, setUploadedCsv] = useState(null);
  const [uploadedFilename, setUploadedFilename] = useState(null);
  const chatEndRef = useRef(null);
  const fileInputRef = useRef(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const buildHistory = (msgs) =>
    msgs
      .filter((m) => m.role === "user" || m.role === "assistant")
      .map((m) => ({
        role: m.role,
        content: m.role === "user" ? m.content : m.response || m.content || "",
      }))
      .filter((m) => m.content);

  const sendMessage = async (text) => {
    const messageText = (text || input).trim();
    if (!messageText || isStreaming) return;

    const history = buildHistory(messages);
    setMessages((prev) => [
      ...prev,
      { role: "user", content: messageText },
      {
        role: "assistant",
        type: "result",
        response: "",
        plots: [],
        toolPills: [],
        streaming: true,
      },
    ]);
    setInput("");

    const payload = { message: messageText, history };
    if (uploadedCsv) payload.csv_context = uploadedCsv;

    try {
      const res = await fetch(`${BACKEND_URL}/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buf = "";

      const applyEvent = (event) => {
        setMessages((prev) => {
          const msgs = [...prev];
          const last = { ...msgs[msgs.length - 1] };

          if (event.type === "text") {
            last.response = (last.response || "") + event.content;
          } else if (event.type === "tool_start") {
            const pills = [...(last.toolPills || [])];
            const existingIdx = pills.findIndex(
              (p) => p.label === event.label
            );
            if (existingIdx >= 0) {
              const p = { ...pills[existingIdx] };
              p.pendingCount = (p.pendingCount || 0) + 1;
              if (event.code !== undefined) p.code = event.code;
              pills[existingIdx] = p;
            } else {
              const p = {
                label: event.label,
                toolName: event.toolName,
                pendingCount: 1,
                doneCount: 0,
              };
              if (event.code !== undefined) p.code = event.code;
              pills.push(p);
            }
            last.toolPills = pills;
          } else if (event.type === "tool_done") {
            const pills = [...(last.toolPills || [])];
            const idx = pills.findIndex((p) => (p.pendingCount || 0) > 0);
            if (idx >= 0) {
              const p = { ...pills[idx] };
              p.pendingCount = Math.max(0, (p.pendingCount || 1) - 1);
              p.doneCount = (p.doneCount || 0) + 1;
              pills[idx] = p;
            }
            last.toolPills = pills;
          } else if (event.type === "dataset_sample") {
            const pills = [...(last.toolPills || [])];
            for (let i = pills.length - 1; i >= 0; i--) {
              const p = pills[i];
              if (
                p.toolName === "analyze_dataset" &&
                (p.pendingCount || 0) === 0 &&
                !p.sample
              ) {
                pills[i] = {
                  ...p,
                  sample: {
                    dataset: event.dataset,
                    columns: event.columns,
                    rows: event.sample,
                  },
                };
                break;
              }
            }
            last.toolPills = pills;
          } else if (event.type === "plot") {
            last.plots = [...(last.plots || []), event.data];
          } else if (event.type === "done") {
            last.streaming = false;
          } else if (event.type === "error") {
            last.type = "error";
            last.content = `Error: ${event.content}`;
            last.response = "";
            last.streaming = false;
          }

          msgs[msgs.length - 1] = last;
          return msgs;
        });
      };

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buf += decoder.decode(value, { stream: true });
        const lines = buf.split("\n");
        buf = lines.pop();
        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          try {
            applyEvent(JSON.parse(line.slice(6)));
          } catch {
            /* skip malformed chunk */
          }
        }
      }
    } catch (err) {
      console.error(err);
      setMessages((prev) => {
        const msgs = [...prev];
        msgs[msgs.length - 1] = {
          role: "assistant",
          type: "error",
          content: "Connection error — make sure the backend is running.",
          streaming: false,
        };
        return msgs;
      });
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const handleFileChange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch(`${BACKEND_URL}/upload`, {
        method: "POST",
        body: formData,
      });
      const data = await res.json();

      if (data.error) {
        alert(`Upload failed: ${data.error}`);
        return;
      }

      setUploadedCsv(data.csv_path);
      setUploadedFilename(file.name);

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          type: "result",
          response: `Uploaded **${file.name}** — ${data.rows.toLocaleString()} rows × ${data.columns.length} columns.\n\n**Columns:** ${data.columns.join(", ")}\n\nAsk me to analyze it!`,
          plots: [],
        },
      ]);
    } catch (err) {
      alert("Upload error: " + err.message);
    }

    e.target.value = "";
  };

  const isStreaming = messages.some((m) => m.streaming);
  const showExamples = messages.length === 1;

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-title">
          <span className="header-icon">🐾</span>
          Animal Rescue Research Assistant
        </div>
        <div className="header-subtitle">
          Powered by Claude AI · Animal shelter &amp; rescue data analysis
        </div>
      </header>

      <div className="chat-container">
        <div className="messages-area">
          {messages.map((msg, i) => (
            <Message key={i} msg={msg} />
          ))}
          <div ref={chatEndRef} />
        </div>

        {showExamples && (
          <div className="example-prompts">
            {EXAMPLE_PROMPTS.map((prompt, i) => (
              <button
                key={i}
                className="example-btn"
                onClick={() => sendMessage(prompt)}
              >
                {prompt}
              </button>
            ))}
          </div>
        )}

        <div className="input-area">
          <input
            type="file"
            accept=".csv"
            ref={fileInputRef}
            style={{ display: "none" }}
            onChange={handleFileChange}
          />
          <button
            className="upload-btn"
            title="Upload CSV"
            onClick={() => fileInputRef.current.click()}
          >
            📎
          </button>
          <textarea
            className="input-field"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about shelter data… (Enter to send, Shift+Enter for newline)"
            rows={1}
            disabled={isStreaming}
          />
          <button
            className="send-btn"
            onClick={() => sendMessage()}
            disabled={isStreaming || !input.trim()}
          >
            Send
          </button>
        </div>

        {uploadedCsv && (
          <div className="csv-badge">
            📄 {uploadedFilename} loaded —{" "}
            <button
              className="clear-csv"
              onClick={() => {
                setUploadedCsv(null);
                setUploadedFilename(null);
              }}
            >
              clear
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
