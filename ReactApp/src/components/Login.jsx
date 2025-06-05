import React, { useState } from "react";

export default function Login({ onAuth }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [attempts, setAttempts] = useState(0);
  const [locked, setLocked] = useState(false);

  const validate = () => {
    if (!username.trim() || !password.trim()) {
      setError("Please provide a username and password.");
      return false;
    }
    return true;
  };

  const submit = async (path) => {
    try {
      if (!validate()) return;
      let payload = { username, password };
      if (path === "/register") {
        if (locked) {
          setError(
            "Too many attempts. Please reach out to kydxbot@support.com to retrieve the SECRET_KEY if you are actively subscribed."
          );
          return;
        }
        const secret = prompt("Enter the secret code to register:");
        if (secret === null) return;
        payload.secret = secret;
      }

      const res = await fetch(path, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        if (path === "/register" && (res.status === 401 || res.status === 403)) {
          const newAttempts = attempts + 1;
          setAttempts(newAttempts);
          if (newAttempts >= 5 || res.status === 403) {
            setLocked(true);
            setError(
              "Too many attempts. Please reach out to kydxbot@support.com to retrieve the SECRET_KEY if you are actively subscribed."
            );
          } else if (newAttempts >= 3) {
            setError(`Invalid secret. You have ${5 - newAttempts} attempts remaining.`);
          } else {
            setError("Invalid secret");
          }
          return;
        }
        throw new Error(`HTTP ${res.status}`);
      }

      const data = await res.json();
      const token = data.token;
      if (token) {
        localStorage.setItem("token", token);
        onAuth(token);
      } else {
        setError("No token returned");
      }
    } catch (err) {
      console.error(err);
      setError("Authentication failed");
    }
  };

  return (
    <div
      style={{
        maxWidth: "380px",
        margin: "2rem auto",
        textAlign: "center",
        background: "#1f1f1f",
        padding: "2rem",
        borderRadius: "8px",
        boxShadow: "0 2px 8px rgba(0,0,0,0.5)",
        color: "#fff",
      }}
    >
      <h2 style={{ marginBottom: "1rem" }}>Login</h2>
      <input
        style={{
          width: "100%",
          padding: "0.5rem",
          marginBottom: "0.5rem",
          borderRadius: "4px",
          border: "1px solid #555",
          background: "#2a2a2a",
          color: "#fff",
        }}
        placeholder="Username"
        value={username}
        onChange={(e) => setUsername(e.target.value)}
      />
      <input
        style={{
          width: "100%",
          padding: "0.5rem",
          marginBottom: "0.5rem",
          borderRadius: "4px",
          border: "1px solid #555",
          background: "#2a2a2a",
          color: "#fff",
        }}
        type="password"
        placeholder="Password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
      />
      <div style={{ display: "flex", justifyContent: "space-between" }}>
        <button
          style={{
            padding: "0.5rem 1.5rem",
            backgroundColor: "#4caf50",
            color: "#fff",
            border: "none",
            borderRadius: "4px",
            cursor: "pointer",
          }}
          onClick={() => submit("/login")}
        >
          Login
        </button>
        <button
          style={{
            padding: "0.5rem 1.5rem",
            backgroundColor: "#2196f3",
            color: "#fff",
            border: "none",
            borderRadius: "4px",
            cursor: "pointer",
          }}
          onClick={() => submit("/register")}
        >
          Register
        </button>
      </div>
      {error && (
        <p style={{ color: "#ff7276", marginTop: "0.75rem" }}>{error}</p>
      )}
    </div>
  );
}
