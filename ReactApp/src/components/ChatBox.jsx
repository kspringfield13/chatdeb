// src/components/ChatBox.jsx
import React, { useState, useRef, useEffect } from "react";
import ImageModal from "./ImageModal";
// Visualization questions are now asked through the chat flow

export default function ChatBox({ token }) {
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
  const [infographQuestions, setInfographQuestions] = useState([]);
  const [infographAnswers, setInfographAnswers] = useState([]);
  const [infographStep, setInfographStep] = useState(0);
  const [collectingInfograph, setCollectingInfograph] = useState(false);
  const [loading, setLoading] = useState(false);
  const [showScrollDown, setShowScrollDown] = useState(false);
  const [imageModalSrc, setImageModalSrc] = useState(null);
  const messagesEndRef = useRef(null);
  const containerRef = useRef(null);

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
    setShowVisualize(true);
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

      const intro = "To create your visualization I'll need a bit more information.";
      if (qs[0] && qs[0].startsWith(intro)) {
        const first = qs[0].slice(intro.length).trim();
        setChatHistory((prev) => [
          ...prev,
          { sender: "bot", text: intro },
          ...(first ? [{ sender: "bot", text: first }] : []),
        ]);
      } else {
        setChatHistory((prev) => [...prev, { sender: "bot", text: qs[0] }]);
      }
      setShowVisualize(false);
      setLoading(false);
    } catch (err) {
      console.error("Error fetching context questions", err);
      setLoading(false);
    }
  };

  const openInfograph = async () => {
    setLoading(true);
    try {
      const res = await fetch("/infograph/questions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ history: chatHistory }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      const qs = data.questions || [];
      if (!qs.length) return;
      setInfographQuestions(qs);
      setInfographAnswers([]);
      setInfographStep(0);
      setCollectingInfograph(true);
      setChatHistory((prev) => [...prev, { sender: "bot", text: qs[0] }]);
      setShowVisualize(false);
      setLoading(false);
    } catch (err) {
      console.error("Error fetching infographic questions", err);
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

  const completeInfograph = async (answers) => {
    setLoading(true);
    try {
      const res = await fetch("/infograph/complete", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ history: chatHistory, answers }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      if (data.image_url) {
        setVisuals((prev) => [...prev, data.image_url]);
        setChatHistory((prev) => [
          ...prev,
          { sender: "bot", text: "Here is your infographic:", image: data.image_url },
        ]);
      } else {
        setChatHistory((prev) => [
          ...prev,
          { sender: "bot", text: "Sorry, I couldn't create the infographic." },
        ]);
      }
      setLoading(false);
    } catch (err) {
      console.error("Error creating infographic", err);
      setChatHistory((prev) => [
        ...prev,
        { sender: "bot", text: "Error creating infographic." },
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
      setChatHistory((prev) => [
        ...prev,
        { sender: "bot", text: "Sorry, I couldn't generate a summary." },
      ]);
    } finally {
      setLoading(false);
      setShowVisualize(true);
    }
  };

  const openMyData = async () => {
    setShowVisualize(false);
    setLoading(true);
    try {
      const res = await fetch("/my_data");
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      if (data.summary) {
        setChatHistory((prev) => [...prev, { sender: "bot", text: data.summary }]);
      }
      if (data.erd_url) {
        setChatHistory((prev) => [
          ...prev,
          { sender: "bot", text: "Here is the ER diagram:", image: data.erd_url },
        ]);
      }
    } catch (err) {
      console.error("Error getting data overview", err);
      setChatHistory((prev) => [
        ...prev,
        { sender: "bot", text: "Sorry, I couldn't summarize the data." },
      ]);
    } finally {
      setLoading(false);
      setShowVisualize(true);
    }
  };

  const handleScroll = () => {
    const container = containerRef.current;
    if (!container) return;
    const { scrollTop, scrollHeight, clientHeight } = container;
    const atBottom = scrollHeight - scrollTop - clientHeight < 50;
    setShowScrollDown(!atBottom);
  };

  // Whenever chatHistory changes, scroll to bottom
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
    handleScroll();
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

    if (collectingInfograph) {
      const newAnswers = [...infographAnswers, trimmed];
      setInfographAnswers(newAnswers);

      const next = infographStep + 1;
      if (next < infographQuestions.length) {
        setInfographStep(next);
        setChatHistory((prev) => [...prev, { sender: "bot", text: infographQuestions[next] }]);
      } else {
        setCollectingInfograph(false);
        await completeInfograph(newAnswers);
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
      if (data.response && data.response.startsWith("TABLE:")) {
        const img = data.response.replace("TABLE:", "");
        setChatHistory((prev) => [
          ...prev,
          { sender: "bot", text: "Here is your table:", image: img },
        ]);
      } else {
        setChatHistory((prev) => [
          ...prev,
          { sender: "bot", text: data.response },
        ]);
      }
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
        position: "relative",
      }}
    >
      {/* ─── 1) Header: title in top‐right, minimal padding ──────────────────────────── */}
      <div
        style={{
          display: "flex",
          justifyContent: "right",
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
        ref={containerRef}
        onScroll={handleScroll}
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
              <div style={{ position: "relative", maxWidth: "80%" }}>
                <img
                  src={msg.image}
                  alt="chart"
                  style={{ maxWidth: "100%", borderRadius: 8, backgroundColor: "#1f1f1f" }}
                />
                <button
                  onClick={() => setImageModalSrc(msg.image)}
                  style={{
                    position: "absolute",
                    top: "0.25rem",
                    right: "0.25rem",
                    background: "rgba(0,0,0,0.6)",
                    border: "none",
                    borderRadius: "50%",
                    color: "#fff",
                    cursor: "pointer",
                    padding: "0.25rem",
                  }}
                  aria-label="Expand"
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    width="14"
                    height="14"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <path d="M15 3h6v6" />
                    <path d="M21 3l-9 9" />
                    <path d="M9 21H3v-6" />
                    <path d="M3 21l9-9" />
                  </svg>
                </button>
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
                  whiteSpace: msg.text.includes("\n") ? "pre-wrap" : "normal",
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

      {showScrollDown && (
        <button
          onClick={() => {
            messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
            handleScroll();
          }}
          style={{
            position: "absolute",
            bottom: "6rem",
            right: "0.75rem",
            backgroundColor: "transparent",
            border: "none",
            borderRadius: "50%",
            padding: "0.5rem",
            cursor: "pointer",
            opacity: 0.6,
          }}
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="#fff"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <polyline points="6 9 12 15 18 9" />
          </svg>
        </button>
      )}

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
            justifyContent: "flex-start",
            gap: "0.5rem",
            paddingLeft: "1rem",
          }}
        >
          <button
            onClick={openMyData}
            style={{
              padding: "0.5rem 1rem",
              borderRadius: 20,
              backgroundColor: "#00FFE1",
              color: "#000",
              border: "none",
              cursor: "pointer",
              fontSize: "0.95rem",
            }}
          >
            My Data?
          </button>
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
            onClick={openInfograph}
            style={{
              padding: "0.5rem 1rem",
              borderRadius: 20,
              backgroundColor: "#800080",
              color: "#fff",
              border: "none",
              cursor: "pointer",
              fontSize: "0.95rem",
            }}
          >
            Infograph It?
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
    {imageModalSrc && (
      <ImageModal src={imageModalSrc} onClose={() => setImageModalSrc(null)} />
    )}
    </>
  );
}
