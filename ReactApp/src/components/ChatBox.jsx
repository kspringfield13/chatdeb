// src/components/ChatBox.jsx
import React, { useState, useRef, useEffect } from "react";

// Parse a simple pipe separated table ("| a | b |\n| c | d |") into
// an array of rows, each being an array of strings.
// Used to convert plain text tables from the backend into real HTML.
function parsePipeTable(text) {
  const lines = text
    .trim()
    .split("\n")
    .map((l) => l.trim())
    .filter((l) => l.includes("|"));

  const rows = lines.map((line) =>
    line
      .replace(/^\||\|$/g, "")
      .split("|")
      .map((c) => c.trim())
  );

  return rows;
}

// Component to render a table with optional expand/collapse capability.
function TableMessage({ text }) {
  const [expanded, setExpanded] = useState(false);
  const rows = parsePipeTable(text);

  // Only treat it as a table if we have more than one row or cell
  const valid = rows.length > 0 && rows[0].length > 1;
  if (!valid) {
    return <div>{text}</div>;
  }

  return (
    <div
      onClick={() => setExpanded((v) => !v)}
      style={{
        backgroundColor: "#3a3a3a",
        color: "#fff",
        padding: "0.75rem 1rem",
        borderRadius: 6,
        maxWidth: expanded ? "100%" : "80%",
        overflowX: "auto",
        fontSize: "0.9rem",
        cursor: "pointer",
      }}
    >
      <table
        style={{
          borderCollapse: "collapse",
          width: "100%",
          tableLayout: "auto",
        }}
      >
        <tbody>
          {rows.map((row, i) => (
            <tr key={i}>
              {row.map((cell, j) => (
                <td
                  key={j}
                  style={{
                    border: "1px solid #666",
                    padding: "4px 8px",
                    maxWidth: "200px",
                    whiteSpace: "nowrap",
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                  }}
                  title={cell}
                >
                  {cell.length > 50 ? cell.slice(0, 50) + "…" : cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      <div
        style={{
          textAlign: "right",
          fontSize: "0.75rem",
          marginTop: "0.25rem",
          color: "#bbb",
        }}
      >
        {expanded ? "Click to collapse" : "Click to expand"}
      </div>
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
            {msg.text.includes("|") && msg.text.includes("\n") ? (
              <TableMessage text={msg.text} />
            ) : msg.text.includes("\n") ? (
              // ── Case B: Any multiline (e.g. numbered list) ──────
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
              // ── Case C: Single‐line text ────────────
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
            )}
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
