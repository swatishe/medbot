import React, { useState, useRef, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import "./App.css";

const API_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";

const SAMPLE_QUESTIONS = [
  "What is the hand hygiene protocol before patient contact?",
  "What are the standard precautions for infection control?",
  "How should needlestick injuries be handled?",
  "What PPE is required for airborne precautions?",
];

function SourceCard({ source }) {
  const [expanded, setExpanded] = useState(false);
  return (
    <div className="source-card" onClick={() => setExpanded(!expanded)}>
      <div className="source-header">
        <span className="source-icon">📄</span>
        <span className="source-name">{source.source}</span>
        <span className="source-page">p.{source.page}</span>
        <span className="source-toggle">{expanded ? "▲" : "▼"}</span>
      </div>
      {expanded && <p className="source-excerpt">{source.excerpt}</p>}
    </div>
  );
}

function Message({ msg }) {
  if (msg.role === "user") {
    return (
      <div className="message user-message">
        <div className="message-bubble user-bubble">
          <p>{msg.content}</p>
        </div>
      </div>
    );
  }

  if (msg.role === "error") {
    return (
      <div className="message bot-message">
        <div className="avatar bot-avatar">🤖</div>
        <div className="message-bubble error-bubble">
          <p>{msg.content}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="message bot-message">
      <div className="avatar bot-avatar">🏥</div>
      <div className="message-content">
        <div className="message-bubble bot-bubble">
          <ReactMarkdown>{msg.content}</ReactMarkdown>
        </div>
        {msg.sources && msg.sources.length > 0 && (
          <div className="sources-section">
            <p className="sources-label">
              📚 Referenced {msg.sources.length} source{msg.sources.length > 1 ? "s" : ""}
              {msg.doc_count && (
                <span className="doc-count"> · {msg.doc_count} docs indexed</span>
              )}
            </p>
            {msg.sources.map((s, i) => (
              <SourceCard key={i} source={s} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function TypingIndicator() {
  return (
    <div className="message bot-message">
      <div className="avatar bot-avatar">🏥</div>
      <div className="message-bubble bot-bubble typing-bubble">
        <span className="dot"></span>
        <span className="dot"></span>
        <span className="dot"></span>
      </div>
    </div>
  );
}

export default function App() {
  const [messages, setMessages] = useState([
    {
      role: "bot",
      content:
        "Hello! I'm **MedBot**, your clinical policy assistant. I answer questions based on your hospital's ingested policy documents and clinical guidelines.\n\nAsk me anything about protocols, procedures, or clinical guidelines.",
      sources: [],
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [health, setHealth] = useState(null);
  const bottomRef = useRef(null);

  useEffect(() => {
    fetch(`${API_URL}/health`)
      .then((r) => r.json())
      .then((d) => setHealth(d))
      .catch(() => setHealth({ status: "offline" }));
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const sendMessage = async (question) => {
    const q = question || input.trim();
    if (!q || loading) return;

    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: q }]);
    setLoading(true);

    try {
      const res = await fetch(`${API_URL}/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: q }),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Server error");
      }

      const data = await res.json();
      setMessages((prev) => [
        ...prev,
        {
          role: "bot",
          content: data.answer,
          sources: data.sources,
          doc_count: data.doc_count,
        },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: "error",
          content: `⚠️ ${err.message}. Make sure the backend is running and documents are ingested.`,
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKey = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="app">
      <header className="header">
        <div className="header-left">
          <span className="logo">🏥</span>
          <div>
            <h1 className="app-title">MedBot</h1>
            <p className="app-subtitle">Clinical Policy Assistant</p>
          </div>
        </div>
        <div className="status-badge">
          <span
            className={`status-dot ${health?.status === "ok" ? "online" : "offline"}`}
          ></span>
          <span className="status-text">
            {health?.status === "ok"
              ? `${health.doc_count} chunks indexed`
              : health?.status === "offline"
              ? "Backend offline"
              : "Connecting…"}
          </span>
        </div>
      </header>

      <div className="chat-container">
        {messages.map((msg, i) => (
          <Message key={i} msg={msg} />
        ))}
        {loading && <TypingIndicator />}
        <div ref={bottomRef} />
      </div>

      {messages.length === 1 && (
        <div className="suggestions">
          <p className="suggestions-label">Try asking:</p>
          <div className="suggestion-chips">
            {SAMPLE_QUESTIONS.map((q, i) => (
              <button key={i} className="chip" onClick={() => sendMessage(q)}>
                {q}
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="input-area">
        <textarea
          className="input-box"
          placeholder="Ask about clinical protocols, guidelines, or procedures…"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKey}
          rows={2}
          disabled={loading}
        />
        <button
          className={`send-btn ${loading ? "loading" : ""}`}
          onClick={() => sendMessage()}
          disabled={loading || !input.trim()}
        >
          {loading ? "…" : "→"}
        </button>
      </div>
      <p className="disclaimer">
        ⚕️ For clinical reference only. Always verify with qualified medical personnel.
      </p>
    </div>
  );
}
