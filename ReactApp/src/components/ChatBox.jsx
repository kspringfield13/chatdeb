// src/components/ChatBox.jsx
import React, { useState, useRef, useEffect } from "react";
import VisualModal from "./VisualModal";

export default function ChatBox() {
  const [query, setQuery] = useState("");
  const [chatHistory, setChatHistory] = useState([]);
  const [showVisualize, setShowVisualize] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [contextQuestions, setContextQuestions] = useState([]);
  const [chartUrl, setChartUrl] = useState(null);
  const messagesEndRef = useRef(null);

  const openVisualization = async () => {
    try {
      const res = await fetch("/visualize/questions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ history: chatHistory }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setContextQuestions(data.questions || []);
      setChartUrl(null);
      setShowModal(true);
    } catch (err) {
      console.error("Error fetching context questions", err);
    }
  };

  const openSummarize = () => {
    console.log("Summarize clicked");
  };

  const completeVisualization = async (answers) => {
    try {
      const res = await fetch("/visualize/complete", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ history: chatHistory, answers }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setChartUrl(data.chart_url);
    } catch (err) {
      console.error("Error creating visualization", err);
    }
  };

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
    setShowVisualize(false);

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
      setShowVisualize(true);
    } catch (err) {
      console.error("Error calling API:", err);
      setChatHistory((prev) => [
        ...prev,
        { sender: "bot", text: "Sorry, something went wrong." },
      ]);
      setShowVisualize(true);
    }
  };

  return (
    <>
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
            {msg.text.includes("\n") ? (
              // ── Case B: Any multiline (e.g. numbered list) ────────────────────
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
                  whiteSpace: "pre-wrap", // preserve all newline breaks
                }}
              >
                {msg.text}
              </div>
            ) : (
              // ── Case C: Single‐line text ───────────────────────────────────────
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

      {showVisualize && (
        <div
          style={{
            backgroundColor: "#1f1f1f",
            padding: "0.5rem 0",
            textAlign: "left",
            borderTop: "1px solid #333",
            display: "flex",
            gap: "0.5rem",
          }}
        >
          <button
            onClick={openVisualization}
            style={{
              padding: "0.5rem 1rem",
              borderRadius: 20,
              backgroundColor: "#004080",
              color: "#fff",
              border: "none",
              cursor: "pointer",
              fontSize: "0.95rem",
            }}
          >
            Visualize?
          </button>
          <button
            onClick={openSummarize}
            style={{
              padding: "0.5rem 1rem",
              borderRadius: 20,
              backgroundColor: "#008000",
              color: "#fff",
              border: "none",
              cursor: "pointer",
              fontSize: "0.95rem",
            }}
          >
            Summarize?
          </button>
        </div>
      )}

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
    {showModal && (
      <VisualModal
        onClose={() => setShowModal(false)}
        questions={contextQuestions}
        onSubmit={completeVisualization}
        chartUrl={chartUrl}
      />
    )}
    </>
  );
}
