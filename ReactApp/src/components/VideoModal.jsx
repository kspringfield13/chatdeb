import React from "react";

export default function VideoModal({ src, onClose }) {
  if (!src) return null;
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
      <div style={{ position: "relative", maxWidth: "90%", maxHeight: "90%" }}>
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
        <a
          href={src}
          download
          style={{
            position: "absolute",
            top: "0.5rem",
            left: "0.5rem",
            background: "transparent",
            border: "none",
            color: "#fff",
            fontSize: "1rem",
            textDecoration: "none",
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
        </a>
        <video
          src={src}
          controls
          style={{
            maxWidth: "100%",
            maxHeight: "80vh",
            borderRadius: 8,
            backgroundColor: "#1f1f1f",
          }}
        />
      </div>
    </div>
  );
}
