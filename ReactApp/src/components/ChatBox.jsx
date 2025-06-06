// src/components/ChatBox.jsx
import React, { useState, useRef, useEffect } from "react";
// Visualization questions are now asked through the chat flow

export default function ChatBox() {
  const [query, setQuery] = useState("");
  const [chatHistory, setChatHistory] = useState([]);
  const [showVisualize, setShowVisualize] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [contextQuestions, setContextQuestions] = useState([]);
  const [chartUrl, setChartUrl] = useState(null);
  const [visuals, setVisuals] = useState([]);
  const [vizQuestions, setVizQuestions] = useState([]);
  const [vizAnswers, setVizAnswers] = useState([]);
  const [vizStep, setVizStep] = useState(0);
  const [collectingViz, setCollectingViz] = useState(false);
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  // Fetch intro message on mount
  useEffect(() => {
    const fetchIntro = async () => {
      try {
        const res = await fetch("/intro");
        if (!res.ok) return;
        const data = await res.json();
        if (data.message) {
          setChatHistory((prev) => [...prev, { sender: "bot", text: data.message }]);
        }
      } catch (e) {
        console.error("intro fetch error", e);
      }
    };
    fetchIntro();
  }, []);

  const openVisualization = async () => {
    setLoading(true);
    try {
      const res = await fetch("/visualize/questions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ history: chatHistory }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      const qs = data.questions || [];
      if (!qs.length) return;
      setVizQuestions(qs);
      setVizAnswers([]);
      setVizStep(0);
      setCollectingViz(true);
      setChatHistory((prev) => [...prev, { sender: "bot", text: qs[0] }]);
      setShowVisualize(false);
      setLoading(false);
    } catch (err) {
      console.error("Error fetching context questions", err);
      setLoading(false);
    }
  };
  

  const completeVisualization = async (answers) => {
    setLoading(true);
    try {
      const res = await fetch("/visualize/complete", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ history: chatHistory, answers }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setChartUrl(data.chart_url);
      if (data.chart_url) {
        setVisuals((prev) => [...prev, data.chart_url]);
        setChatHistory((prev) => [
          ...prev,
          { sender: "bot", text: "Here is your chart:", image: data.chart_url },
        ]);
      } else {
        setChatHistory((prev) => [
          ...prev,
          { sender: "bot", text: "Sorry, I couldn't create the chart." },
        ]);
      }
      setLoading(false);
    } catch (err) {
      console.error("Error creating visualization", err);
      setChatHistory((prev) => [
        ...prev,
        { sender: "bot", text: "Error creating visualization." },
      ]);
      setLoading(false);
    }
  };

  const openSummary = async () => {
    setShowVisualize(false);
    setLoading(true);
    try {
      const res = await fetch("/summarize", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ history: chatHistory, visuals }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setChatHistory((prev) => [...prev, { sender: "bot", text: data.summary }]);
    } catch (err) {
      console.error("Error generating summary", err);
    } finally {
      setLoading(false);
      setShowVisualize(true);
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
    setChatHistory((prev) => [...prev, { sender: "user", text: trimmed }]);

    // 2) Clear input immediately
    setQuery("");

    if (collectingViz) {
      const newAnswers = [...vizAnswers, trimmed];
      setVizAnswers(newAnswers);

      const next = vizStep + 1;
      if (next < vizQuestions.length) {
        setVizStep(next);
        setChatHistory((prev) => [...prev, { sender: "bot", text: vizQuestions[next] }]);
      } else {
        setCollectingViz(false);
        await completeVisualization(newAnswers);
        setShowVisualize(true);
      }
      setLoading(false);
      return;
    }

    setShowVisualize(false);
    setLoading(true);

    try {
      const res = await fetch("/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: trimmed }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);

      const data = await res.json();
      setChatHistory((prev) => [...prev, { sender: "bot", text: data.response }]);
      setShowVisualize(true);
      setLoading(false);
    } catch (err) {
      console.error("Error calling API:", err);
      setChatHistory((prev) => [...prev, { sender: "bot", text: "Sorry, something went wrong." }]);
      setShowVisualize(true);
      setLoading(false);
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
              justifyContent: msg.sender === "user" ? "flex-end" : "flex-start",
              marginBottom: "0.75rem",
            }}
          >
            {msg.image ? (
              <img src={msg.image} alt="chart" style={{ maxWidth: "80%", borderRadius: 8 }} />
            ) : msg.text.includes("\n") ? (
              <div
                style={{
                  backgroundColor: msg.sender === "user" ? "#004080" : "#3a3a3a",
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
              <div
                style={{
                  backgroundColor: msg.sender === "user" ? "#004080" : "#3a3a3a",
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

      {loading && (
        <div style={{ color: "#888", textAlign: "center", padding: "0.25rem" }}>
          Processing...
        </div>
      )}

      {showVisualize && (
        <div
          style={{
            backgroundColor: "#1f1f1f",
            padding: "0.5rem 0",
            textAlign: "left",
            borderTop: "1px solid #333",
            display: "flex",
            justifyContent: "center",
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
            onClick={openSummary}
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
