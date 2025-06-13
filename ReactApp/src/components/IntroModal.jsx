import React, { useRef } from "react";

export default function IntroModal({ onIngested }) {
  const fileRef = useRef(null);

  const handleClick = () => {
    if (fileRef.current) fileRef.current.click();
  };

  const handleChange = async (e) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;
    const form = new FormData();
    for (const f of files) form.append("files", f);
    try {
      const res = await fetch("/ingest_data", {
        method: "POST",
        body: form,
      });
      if (res.ok) {
        if (onIngested) onIngested();
      } else {
        console.error("ingest failed", await res.text());
        alert("Failed to ingest files");
      }
    } catch (err) {
      console.error("ingest error", err);
      alert("Ingest error");
    }
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
          backgroundColor: "#212121",
          padding: "2rem",
          borderRadius: 8,
          color: "#fff",
          maxWidth: "90%",
          width: "400px",
          textAlign: "center",
        }}
      >
        <h2 style={{ marginTop: 0 }}>Welcome to Deb,
          Your Free, Open Source Data Engineer Bot
        </h2>
        <h3>
          Please select your data files to get started.<br>
          Click button below or select from sample datasets in the dropdown.
        </h3>
        <p style={{ fontSize: "0.85rem", opacity: 0.7 }}>
          Your file contents will be ingested (read-only) into a temporary<br> 
          secure database ONLY for this session.
          Files themselves are never stored anywhere at anytime.<br>
          Your data is merely observed and forgotten by Deb.
        </p>
        <input
          ref={fileRef}
          type="file"
          multiple
          style={{ display: "none" }}
          onChange={handleChange}
        />
        <button onClick={handleClick} style={{ marginTop: "1rem" }}>
          Add Data
        </button>
      </div>
    </div>
  );
}
