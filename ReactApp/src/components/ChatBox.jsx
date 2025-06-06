// src/components/ChatBox.jsx
import React, { useState, useRef, useEffect } from "react";

function renderMarkdownTable(text, sender) {
  const lines = text
    .split("\n")
    .map((l) => l.trim())
    .filter((l) => l.includes("|") && l.startsWith("|"));
  if (lines.length === 0) return null;
  const rows = lines.map((line) =>
    line
      .split("|")
      .filter((c) => c.trim() !== "")
      .map((c) => c.trim())
  );
  const rowCount = rows.length;
  const colCount = rows[0] ? rows[0].length : 0;
  if (rowCount === 1 && colCount === 1) return null;
  const bg = sender === "user" ? "#004080" : "#3a3a3a";
  return (
    <div
      style={{
        backgroundColor: bg,
        padding: "0.75rem 1rem",
        borderRadius: 20,
        maxWidth: "80%",
        overflowX: "auto",
      }}
    >
      <table
        style={{
          borderCollapse: "collapse",
          width: "100%",
          color: "#fff",
          fontSize: "0.9rem",
        }}
      >
        <tbody>
          {rows.map((cells, i) => (
            <tr key={i}>
              {cells.map((cell, j) => (
                <td
                  key={j}
                  style={{
                    border: "1px solid #555",
                    padding: "0.35rem 0.6rem",
                    textAlign: "left",
                  }}
                >
                  {cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function ChatBox({ token }) {
  const [query, setQuery] = useState("");
  const [chatHistory, setChatHistory] = useState([]);
  const messagesEndRef = useRef(null);

  // Whenever chatHistory changes, scroll to bottom
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [chatHistory]);

  const sendQuery = async () => {
    const trimmed = query.trim();
    if (!trimmed) return;

    // 1) Add user message
    setChatHistory((prev) => [
      ...prev,
      { sender: "user", text: trimmed },
    ]);

    // 2) Clear input immediately
    setQuery("");

    try {
      // 3) Send to backend with auth token
      const res = await fetch("/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ query: trimmed }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);

      const data = await res.json();
      // 4) Add bot response
      setChatHistory((prev) => [
        ...prev,
        { sender: "bot", text: data.response },
      ]);
    } catch (err) {
      console.error("Error calling API:", err);
      setChatHistory((prev) => [
        ...prev,
        { sender: "bot", text: "Sorry, something went wrong." },
      ]);
    }
  };

  const fetchSummary = async () => {
    try {
      const res = await fetch("/summarize", { method: "GET" });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setChatHistory((prev) => [
        ...prev,
        { sender: "bot", text: data.summary },
      ]);
    } catch (err) {
      console.error("Error fetching summary:", err);
    }
  };

  return (
    <div
      style={{
        height: "85vh",
        width: "70vw",
        minWidth: "325px",
        maxWidth: "800px",
        margin: "0 auto 10px",
        display: "flex",
        flexDirection: "column",
        backgroundColor: "#1f1f1f",
        borderRadius: "8px",
        boxShadow: "0 2px 8px rgba(0, 0, 0, 0.5)",
        overflow: "hidden",
      }}
    >
      {/* ─── 1) Header: title in top‐right, minimal padding ──────────────────────────── */}
      <div
        style={{
          display: "flex",
          justifyContent: "flex-end", // push title to the right
          alignItems: "center",
          padding: "0.25rem 1rem", // very small vertical padding
          backgroundColor: "#212121",
          borderBottom: "1px solid #333",
        }}
      >
        <h2
          style={{
            margin: 0,
            color: "#ffffff",
            fontFamily: "'Montserrat', sans-serif", // use Montserrat
            fontSize: "1rem", // smaller, modern size
            fontWeight: 600, // semi‐bold
          }}
        >
          KYDxBot
        </h2>
      </div>

      {/* === 2) Message list: flex:1, scrollable === */}
      <div
        style={{
          flex: 1,
          overflowY: "auto",
          padding: "1rem",
          backgroundColor: "#1f1f1f",
        }}
      >
        {chatHistory.map((msg, idx) => (
          <div
            key={idx}
            style={{
              display: "flex",
              justifyContent:
                msg.sender === "user" ? "flex-end" : "flex-start",
              marginBottom: "0.75rem",
            }}
          >
            {/**
             * Case A: if the text contains BOTH "\n" and "|", treat it as a table
             *         and render inside a <pre> with monospace.
             * Case B: if the text contains just "\n" (but no "|"), treat it as
             *         a general multiline block (e.g. numbered list) and render
             *         inside a <div> with white-space: pre-wrap.
             * Case C: otherwise, render as a normal single-line bubble.
             */}
            {renderMarkdownTable(msg.text, msg.sender) ||
              (msg.text.includes("\n") ? (
                // --- Case B: Any multiline (e.g. numbered list) ---
                <div
                  style={{
                    backgroundColor:
                      msg.sender === "user" ? "#004080" : "#3a3a3a",
                    color: "#fff",
                    padding: "0.75rem 1rem",
                    borderRadius: 20,
                    maxWidth: "80%",
                    lineHeight: 1.4,
                    fontSize: "0.95rem",
                    textAlign: "left",
                    whiteSpace: "pre-wrap",
                  }}
                >
                  {msg.text}
                </div>
              ) : (
                // --- Case C: Single-line text ---
                <div
                  style={{
                    backgroundColor:
                      msg.sender === "user" ? "#004080" : "#3a3a3a",
                    color: "#fff",
                    padding: "0.75rem 1rem",
                    borderRadius: 20,
                    maxWidth: "80%",
                    lineHeight: 1.4,
                    fontSize: "0.95rem",
                    textAlign: "left",
                  }}
                >
                  {msg.text}
                </div>
              ))}
          </div>
        ))}

        {/* Dummy div to scroll into view */}
        <div ref={messagesEndRef} />
      </div>

      {/* === 3) Input bar pinned at bottom === */}
      <div
        style={{
          padding: "0.5rem 1rem",
          borderTop: "1px solid #333",
          backgroundColor: "#212121",
          display: "flex",
          alignItems: "center",
          gap: "0.5rem",
        }}
      >
        {/* — Query input field */}
        <input
          style={{
            flexGrow: 1,
            padding: "0.75rem 1rem",
            borderRadius: 25,
            border: "none",
            outline: "none",
            backgroundColor: "#2a2a2a",
            color: "#fff",
            fontSize: "1rem",
          }}
          type="text"
          value={query}
          placeholder="Type your question..."
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") sendQuery();
          }}
        />

        {/* — Summarize */}
        <button
          onClick={fetchSummary}
          style={{
            backgroundColor: "#4caf50",
            border: "none",
            padding: "0.75rem 1rem",
            borderRadius: 20,
            color: "#fff",
            fontSize: "0.9rem",
            cursor: "pointer",
          }}
        >
          Summarize?
        </button>

        {/* — Send */}
        <button
          onClick={sendQuery}
          style={{
            backgroundColor: "#f2f3f5",
            border: "none",
            padding: "1rem 1rem",
            borderRadius: "34%",
            color: "#fff",
            fontSize: "1 rem",
            cursor: "pointer",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
          >
            {/* Inline SVG for a paper-plane icon */}
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="18"
            height="18"
            viewBox="0 0 24 24"
            fill="none"
            stroke="#000"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <line x1="22" y1="2" x2="11" y2="13"></line>
            <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
          </svg>
        </button>
      </div>
    </div>
  );
}
