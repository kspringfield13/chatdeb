// src/components/ChatBox.jsx
import React, { useState, useRef, useEffect } from "react";
import ImageModal from "./ImageModal";
import VideoModal from "./VideoModal";
import IntroModal from "./IntroModal";
// Visualization questions are now asked through the chat flow

export default function ChatBox() {
  const [query, setQuery] = useState("");
  const [chatHistory, setChatHistory] = useState([]);
  const [showVisualize, setShowVisualize] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [contextQuestions] = useState([]);
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
  const [erdModalSrc, setErdModalSrc] = useState(null);
  const [isErdOpen, setIsErdOpen] = useState(false);
  const [myDataClicked, setMyDataClicked] = useState(false);
  const [showDirectorsCut, setShowDirectorsCut] = useState(false);
  const [directorsCutUrl, setDirectorsCutUrl] = useState(null);
  const [isDirectorsCutOpen, setIsDirectorsCutOpen] = useState(false);
  const [lastTablePath, setLastTablePath] = useState(null);
  const [showIntro, setShowIntro] = useState(true);
  const [windowWidth, setWindowWidth] = useState(window.innerWidth);
  const messagesEndRef = useRef(null);
  const containerRef = useRef(null);
  const hasUserPrompt = chatHistory.some((m) => m.sender === "user");

  const wait = (ms) => new Promise((res) => setTimeout(res, ms));
  const loadImage = (url) =>
    new Promise((resolve, reject) => {
      const img = new Image();
      img.onload = () => resolve();
      img.onerror = reject;
      img.src = url;
    });

  // Track window width for responsive pill buttons
  useEffect(() => {
    const handleResize = () => setWindowWidth(window.innerWidth);
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  // Derived styles for pill buttons based on screen width
  const BASE_WIDTH = 1024; // reference width for responsive sizing
  const hidePillText = windowWidth < BASE_WIDTH * 0.25;
  const pillFontSize =
    windowWidth < BASE_WIDTH * 0.75
      ? "0.6rem"
      : windowWidth < BASE_WIDTH * 0.5
      ? "0.55rem"
      : "0.90rem";
  const pillPadding = hidePillText
    ? "0.25rem"
    : windowWidth < BASE_WIDTH * 0.35
    ? "0.4rem 0.75rem"
    : "0.5rem 1rem";
  const basePillStyle = {
    padding: pillPadding,
    borderRadius: 20,
    border: "none",
    cursor: "pointer",
    fontSize: pillFontSize,
    whiteSpace: "nowrap",
    flexShrink: 0,
  };

  const DB_SIZE_LIMIT = 20 * 1024 * 1024; // ~20MB

  // Start a fresh session on mount
  useEffect(() => {
    fetch("/clear_history", { method: "POST" }).catch((err) =>
      console.error("clear history error", err)
    );
  }, []);

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
      setVizAnswers(lastTablePath ? [lastTablePath] : []);
      setVizStep(0);
      setCollectingViz(true);

      const intro = "To create a visualization for you, I need some more details:";
      let firstMsg = qs[0] || "";

      setChatHistory((prev) => [...prev, { sender: "bot", text: intro }]);

      if (firstMsg.startsWith(intro)) {
        firstMsg = firstMsg.slice(intro.length).trim();
      }

      if (firstMsg) {
        setTimeout(() => {
          setChatHistory((prev) => [...prev, { sender: "bot", text: firstMsg }]);
        }, 300);
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
      let data = await res.json().catch(() => ({}));
      if (!res.ok) {
        const msg = data.detail || `HTTP ${res.status}`;
        throw new Error(msg);
      }
      data = data || {};
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
        { sender: "bot", text: err.message || "Error creating visualization." },
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
      if (data.summary && data.summary.startsWith("TABLE:")) {
        const parts = data.summary.replace("TABLE:", "").split("\n");
        const img = parts[0].trim();
        const txt = img.replace(/\.png$/, ".txt");
        setLastTablePath(txt);
        setChatHistory((prev) => {
          const msgs = [
            ...prev,
            { sender: "bot", text: "Here is your table:", image: img, data: txt },
          ];
          const extra = parts.slice(1).join("\n").trim();
          if (extra) msgs.push({ sender: "bot", text: extra });
          return msgs;
        });
      } else {
        setChatHistory((prev) => [...prev, { sender: "bot", text: data.summary }]);
      }
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
      const newMsgs = [];
      if (data.summary) {
        if (data.summary.startsWith("TABLE:")) {
          // "TABLE:/charts/foo.png\nExtra text" → ["/charts/foo.png", "Extra text"]
          const parts = data.summary.replace("TABLE:", "").split("\n");
          const img = parts[0].trim();
          const txt = img.replace(/\.png$/, ".txt");
          setLastTablePath(txt);
          newMsgs.push({ sender: "bot", text: "Here is your table:", image: img, data: txt });
          const extra = parts.slice(1).join("\n").trim();
          if (extra) newMsgs.push({ sender: "bot", text: extra });
        } else {
          newMsgs.push({ sender: "bot", text: data.summary });
        }
      }
      if (data.erd_url) {
        await loadImage(data.erd_url);
        await wait(1000);
        setVisuals((prev) => [...prev, data.erd_url]);
        newMsgs.push({ sender: "bot", text: "Here is the ER diagram:", image: data.erd_url });
        setErdModalSrc(data.erd_url);
        setIsErdOpen(true);
      }
      if (data.erd_desc) {
        newMsgs.push({ sender: "bot", text: `Vision summary: ${data.erd_desc}.` });
      }


      setChatHistory((prev) => [...prev, ...newMsgs]);
    } catch (err) {
      console.error("Error getting data overview", err);
      setChatHistory((prev) => [
        ...prev,
        { sender: "bot", text: "Sorry, I couldn't load your data." },
      ]);
    } finally {
      setLoading(false);
      setShowVisualize(true);
    }
  };

  const openDirectorsCut = async () => {
    setLoading(true);
    try {
      const res = await fetch("/directors_cut", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ history: chatHistory }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      if (data.video_url) {
        setDirectorsCutUrl(data.video_url);
        setIsDirectorsCutOpen(true);
      }
    } catch (err) {
      console.error("Error creating directors cut", err);
      setChatHistory((prev) => [
        ...prev,
        { sender: "bot", text: "Error creating video." },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleDirectorsCutClick = async () => {
    if (directorsCutUrl) {
      setIsDirectorsCutOpen(true);
    } else {
      await openDirectorsCut();
    }
  };

  const handleMyDataClick = async () => {
    if (!myDataClicked) {
      setMyDataClicked(true);
      let timeoutId = null;
      try {
        const infoRes = await fetch("/db_info");
        if (infoRes.ok) {
          const info = await infoRes.json();
          if (info.size > DB_SIZE_LIMIT) {
            timeoutId = setTimeout(() => {
              setChatHistory((prev) => [
                ...prev,
                {
                  sender: "bot",
                  text: "Hang tight, you have a lot of data here. This will only take a second!",
                },
              ]);
            }, 1000);
          }
        }
      } catch (e) {
        console.error("Error fetching db info", e);
      }
      await openMyData();
      if (timeoutId) clearTimeout(timeoutId);
    } else {
      if (erdModalSrc) {
        setIsErdOpen(true);
      } else {
        await openMyData();
      }
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
        const parts = data.response.replace("TABLE:", "").split("\n");
        const img = parts[0].trim();
        const txt = img.replace(/\.png$/, ".txt");
        setLastTablePath(txt);
        setChatHistory((prev) => {
          const msgs = [
            ...prev,
            { sender: "bot", text: "Here is your table:", image: img, data: txt },
          ];
          const extra = parts.slice(1).join("\n").trim();
          if (extra) msgs.push({ sender: "bot", text: extra });
          return msgs;
        });
        setShowDirectorsCut(true);
        setDirectorsCutUrl(null);
      } else {
        setChatHistory((prev) => [
          ...prev,
          { sender: "bot", text: data.response },
        ]);
        setShowDirectorsCut(false);
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
        <img
          src="/logo.png"
          alt="KYDxBot logo"
          style={{ height: "45px" }}
        />
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
              <div
                style={{
                  position: "relative",
                  maxWidth: "100%",
                  overflowX: "auto",
                }}
              >
                <img
                  src={msg.image}
                  alt={msg.image.includes("/table_") ? "table" : "chart"}
                  style={{
                    display: "block",
                    maxWidth: "100%",
                    height: "auto",
                    objectFit: "contain",
                    borderRadius: 8,
                    backgroundColor: "#1f1f1f",
                  }}
                  onLoad={() => {
                    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
                    handleScroll();
                  }}
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
            paddingRight: "1rem",
            overflowX: "auto",
          }}
        >
          <button
            onClick={handleMyDataClick}
            style={{
              ...basePillStyle,
              backgroundColor: "#00FFE1",
              color: "#000",
              opacity: myDataClicked ? 0.6 : 1,
              fontWeight: "bold",
            }}
            title="My Data"
          >
            {!hidePillText && (myDataClicked ? "View My Data" : "My Data")}
          </button>
          {hasUserPrompt && (
            <>
              <button
                onClick={openVisualization}
                style={{
                  ...basePillStyle,
                  backgroundColor: "#004080",
                  color: "#fff",
                }}
                title="Visualize?"
              >
                {!hidePillText && "Visualize?"}
              </button>
              <button
                onClick={openInfograph}
                style={{
                  ...basePillStyle,
                  backgroundColor: "#800080",
                  color: "#fff",
                }}
                title="Infograph It?"
              >
                {!hidePillText && "Infograph It?"}
              </button>
              <button
                onClick={openSummary}
                style={{
                  ...basePillStyle,
                  backgroundColor: "#008000",
                  color: "#fff",
                }}
                title="Summarize?"
              >
                {!hidePillText && "Summarize?"}
              </button>
              {showDirectorsCut && (
                <button
                  onClick={handleDirectorsCutClick}
                  style={{
                    ...basePillStyle,
                    backgroundColor: "#000",
                    color: "#fff",
                    border: "2px solid gold",
                    boxShadow: "0 0 6px gold",
                  }}
                  title="Director's Cut"
                >
                  {!hidePillText && "Director's Cut"}
                </button>
              )}
            </>
          )}
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
    {erdModalSrc && isErdOpen && (
      <ImageModal src={erdModalSrc} onClose={() => setIsErdOpen(false)} />
    )}
    {directorsCutUrl && isDirectorsCutOpen && (
      <VideoModal src={directorsCutUrl} onClose={() => setIsDirectorsCutOpen(false)} />
    )}
    {showIntro && (
      <IntroModal onIngested={() => setShowIntro(false)} />
    )}
    </>
  );
}
