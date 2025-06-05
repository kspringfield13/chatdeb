import React, { useEffect, useState } from "react";

const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID;

export default function Login({ onAuth }) {
  const [googleToken, setGoogleToken] = useState(null);
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [attempts, setAttempts] = useState(0);
  const [locked, setLocked] = useState(false);
  const [secret, setSecret] = useState("");
  const [showSecret, setShowSecret] = useState(false);

  useEffect(() => {
    if (window.google) {
      window.google.accounts.id.initialize({
        client_id: clientId,
        callback: (res) => setGoogleToken(res.credential),
      });
      window.google.accounts.id.renderButton(
        document.getElementById("gbtn"),
        { theme: "outline", size: "large" }
      );
    }
  }, []);

  const submit = async (path) => {
    try {
      if (!googleToken || !password.trim()) {
        setError("Google sign in and password required.");
        return;
      }
      const payload = { token: googleToken, password };
      if (path === "/register") {
        if (locked) {
          setError(
            "Too many attempts. Please reach out to kydxbot@support.com to retrieve the SECRET_KEY if you are actively subscribed."
          );
          return;
        }
        if (!secret.trim()) {
          setError("Secret code required.");
          return;
        }
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
      const t = data.token;
      if (t) {
        localStorage.setItem("token", t);
        onAuth(t);
        setSecret("");
        setShowSecret(false);
        setAttempts(0);
        setError("");
      } else {
        setError("No token returned");
      }
    } catch (err) {
      console.error(err);
      setError("Authentication failed");
    }
  };

  const handleRegister = () => {
    if (!showSecret) {
      setShowSecret(true);
      setError("");
      return;
    }
    submit("/register");
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
      <div id="gbtn" style={{ marginBottom: "1rem" }}></div>
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
      {showSecret && (
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
          type="text"
          placeholder="Secret code"
          value={secret}
          onChange={(e) => setSecret(e.target.value)}
        />
      )}
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
          onClick={handleRegister}
        >
          Register
        </button>
      </div>
      {error && <p style={{ color: "#ff7276", marginTop: "0.75rem" }}>{error}</p>}
    </div>
  );
}
