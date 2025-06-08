import React from "react";

export default function ImageModal({ src, onClose }) {
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
            textDecoration: "underline",
          }}
        >
          Download
        </a>
        <img
          src={src}
          alt="table"
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
