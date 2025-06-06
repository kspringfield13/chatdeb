import React from "react";

export default function VisualModal({ onClose }) {
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
          backgroundColor: "#212121",
          padding: "1.5rem",
          borderRadius: "8px",
          color: "#fff",
          width: "80%",
          maxWidth: "500px",
          textAlign: "center",
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
          aria-label="Close"
        >
          ×
        </button>
        <h3 style={{ marginTop: 0 }}>Visualization</h3>
        <svg width="200" height="200" viewBox="0 0 32 32" style={{ margin: "0 auto" }}>
          <circle r="16" cx="16" cy="16" fill="#555" />
          <path d="M16 16 L16 0 A16 16 0 0 1 31.9 18 z" fill="#4e79a7" />
          <path d="M16 16 L31.9 18 A16 16 0 0 1 14 32 z" fill="#f28e2b" />
          <path d="M16 16 L14 32 A16 16 0 0 1 0 16 z" fill="#76b7b2" />
        </svg>
        <p style={{ fontSize: "0.9rem", marginTop: "0.5rem" }}>Pie Chart Placeholder</p>
      </div>
    </div>
  );
}
