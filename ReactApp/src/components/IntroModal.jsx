import React, { useRef } from "react";

export default function IntroModal({ onUploaded }) {
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
      const res = await fetch("/upload_data", {
        method: "POST",
        body: form,
      });
      if (res.ok) {
        if (onUploaded) onUploaded();
      } else {
        console.error("upload failed", await res.text());
        alert("Failed to upload files");
      }
    } catch (err) {
      console.error("upload error", err);
      alert("Upload error");
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
        <h2 style={{ marginTop: 0 }}>Welcome to Deb, the ultimate Data Engineer Bot</h2>
        <p>Please add your data files to get started.</p>
        <p style={{ fontSize: "0.85rem", opacity: 0.8 }}>
          Uploaded data is temporary and removed after your session.
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
