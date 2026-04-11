import React, { useState } from "react";
import axios from "axios";
import "./App.css";

const API_URL = "https://research-assistant-636745240622.us-central1.run.app/chat";

function App() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState([]);

  const sendMessage = async () => {
    if (!input.trim()) return;

    const updated = [...messages, { role: "user", content: input }];
    setMessages(updated);
    setInput("");

    try {
      const res = await axios.post(API_URL, {
        message: input,
        history: updated
      });

      setMessages([
        ...updated,
        { role: "assistant", content: res.data.response }
      ]);
    } catch (err) {
      setMessages([
        ...updated,
        { role: "assistant", content: "Error contacting backend" }
      ]);
    }
  };

  return (
      <div className="container">
        <h2>🐾 Animal Rescue Assistant</h2>

        <div className="chat-box">
          {messages.map((msg, i) => (
              <div key={i} className={msg.role}>
                <b>{msg.role === "user" ? "You" : "Assistant"}:</b> {msg.content}
              </div>
          ))}
        </div>

        <div className="input-box">
          <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask something..."
          />
          <button onClick={sendMessage}>Send</button>
        </div>
      </div>
  );
}

export default App;