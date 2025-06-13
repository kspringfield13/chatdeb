import React, { useRef, useState } from "react";

export default function IntroModal({ onIngested }) {
  const fileRef = useRef(null);
  const [sample, setSample] = useState("");
  const [digest, setDigest] = useState(false);

  const SAMPLE_OPTIONS = [
    "Orders Snapshot",
    "dataset2",
    "dataset3",
    "dataset4",
    "dataset5",
  ];

  const handleClick = () => {
    if (fileRef.current) fileRef.current.click();
  };

  const handleChange = async (e) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;
    const form = new FormData();
    for (const f of files) form.append("files", f);
    form.append("digest", digest);
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

  const handleSample = async (e) => {
    const name = e.target.value;
    setSample(name);
    if (!name) return;
    const form = new FormData();
    form.append("dataset", name);
    form.append("digest", digest);
    try {
      const res = await fetch("/ingest_sample", {
        method: "POST",
        body: form,
      });
      if (res.ok) {
        if (onIngested) onIngested();
      } else {
        console.error("ingest failed", await res.text());
        alert("Failed to ingest sample");
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
        <h2 style={{ marginTop: 0 }}>
          Welcome to Deb,<br />
          Your Free, Open Source<br />
          Data Engineer Bot
        </h2>
        <h3>
          Please select your data files to get started.<br />
          Click button below or select from sample datasets in the dropdown.
        </h3>
    
        <input
          ref={fileRef}
          type="file"
          multiple
          style={{ display: "none" }}
          onChange={handleChange}
        />
    
        <div
          style={{
            display: "flex",
            justifyContent: "left",
            alignItems: "left",
            gap: "0.5rem",
            marginTop: "0.5rem",
          }}
        >
          <button
            onClick={handleClick}
            style={{
              padding: "0.5rem 1rem",
              backgroundColor: "#007BFF",
              color: "#004080",
              border: "none",
              borderRadius: "5px",
              fontSize: "1rem",
              cursor: "pointer",
              boxShadow: "0 2px 4px rgba(0,0,0,0.2)",
              transition: "background-color 0.3s ease",
            }}
            onMouseOver={(e) => (e.currentTarget.style.backgroundColor = "#0056b3")}
            onMouseOut={(e) => (e.currentTarget.style.backgroundColor = "#007BFF")}
          >
            Add Data
          </button>
          <select
            value={sample}
            onChange={handleSample}
            style={{
              padding: "0.5rem 1rem",
              backgroundColor: "#007BFF",
              color: "#004080",
              border: "none",
              borderRadius: "5px",
              fontSize: "1rem",
              cursor: "pointer",
              marginLeft: "2rem",
            }}
          >
            <option value="">Select Sample Dataset</option>
            {SAMPLE_OPTIONS.map((opt) => (
              <option key={opt} value={opt} >
                {opt}
              </option>
            ))}
          </select>
        </div>
    
        <div
          style={{
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            marginTop: "1rem",
            gap: "0.5rem",
          }}
        >
          <input
            id="digestCheckbox"
            type="checkbox"
            checked={digest}
            onChange={(e) => setDigest(e.target.checked)}
            style={{
              width: "30px",
              height: "30px",
              accentColor: "#007BFF",
              cursor: "pointer",
              marginRight: "0.5rem",
            }}
          />
          <label
            htmlFor="digestCheckbox"
            style={{
              fontSize: "0.85rem",
              cursor: "pointer",
            }}
          >
            Digest My Data
          </label>
          <span style={{ fontSize: "0.7rem", opacity: 0.4 }}>
            Deeper data analysis & improved results.
          </span>
        </div>
        <p style={{ fontSize: "0.85rem", opacity: 0.7, marginTop: "1rem" }}>
          Your file contents will be ingested (read-only) into a temporary<br />
          secure database ONLY for this session.<br />
          Files themselves are never stored anywhere at anytime.<br />
          Your data is merely observed and forgotten by Deb.
        </p>
      </div>
    </div>
  );
}
