import React, { useState } from "react";

export default function VisualModal({ onClose, questions = [], onSubmit, chartUrl }) {
  const [answers, setAnswers] = useState(() => questions.map(() => ""));

  const handleChange = (idx, value) => {
    setAnswers((prev) => prev.map((a, i) => (i === idx ? value : a)));
  };

  const submit = () => {
    if (onSubmit) onSubmit(answers);
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
        {!chartUrl ? (
          <>
            <h3 style={{ marginTop: 0 }}>Confirm Details</h3>
            {questions.map((q, idx) => (
              <div key={idx} style={{ margin: "0.5rem 0" }}>
                <div style={{ marginBottom: "0.25rem" }}>{q}</div>
                <input
                  type="text"
                  value={answers[idx]}
                  onChange={(e) => handleChange(idx, e.target.value)}
                  style={{ width: "100%", padding: "0.5rem" }}
                />
              </div>
            ))}
            <button
              onClick={submit}
              style={{
                marginTop: "1rem",
                padding: "0.5rem 1rem",
                borderRadius: 20,
                backgroundColor: "#004080",
                color: "#fff",
                border: "none",
                cursor: "pointer",
                fontSize: "0.95rem",
              }}
            >
              Submit
            </button>
          </>
        ) : (
          <iframe
            title="Superset"
            src={chartUrl}
            style={{ width: "100%", height: "400px", border: "none" }}
          />
        )}
      </div>
    </div>
  );
}
