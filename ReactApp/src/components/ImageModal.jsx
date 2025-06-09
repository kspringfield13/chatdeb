import React from "react";

export default function ImageModal({ src, onClose }) {
  if (!src) return null;

  const handleDownload = () => {
    const dl = (url) => {
      const a = document.createElement("a");
      a.href = url;
      a.download = "";
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
    };

    dl(src);
    const txt = src.replace(/\.[^.]+$/, ".txt");
    dl(txt);
  };

  return (
    <div
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        width: "100%",
        height: "100%",
        backgroundColor: "rgba(0,0,0,0.6)",
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        zIndex: 1000,
      }}
    >
      <div
        style={{
          position: "relative",
          maxWidth: "90%",
          maxHeight: "90%",
          overflow: src.includes("/table_") ? "auto" : "hidden",
        }}
      >
        <button
          onClick={onClose}
          style={{
            position: "absolute",
            top: "0.5rem",
            right: "0.5rem",
            background: "transparent",
            border: "none",
            color: "#fff",
            fontSize: "1.25rem",
            cursor: "pointer",
          }}
          aria-label="Minimize"
        >
          ×
        </button>
        <button
          onClick={handleDownload}
          style={{
            position: "absolute",
            top: "0.5rem",
            left: "0.5rem",
            background: "transparent",
            border: "none",
            color: "#fff",
            fontSize: "1rem",
            display: "flex",
            alignItems: "center",
            }}
          aria-label="Download"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
            <polyline points="7 10 12 15 17 10" />
            <line x1="12" y1="15" x2="12" y2="3" />
          </svg>
        </button>
        <img
          src={src}
          alt="table"
          style={{
            display: "block",
            maxWidth: src.includes("/table_") ? "none" : "100%",
            maxHeight: src.includes("/table_") ? "none" : "80vh",
            borderRadius: 8,
            backgroundColor: "#1f1f1f",
          }}
        />
      </div>
    </div>
  );
}
