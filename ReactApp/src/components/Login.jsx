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
      setError(""); // clear any previous error
      if (!validate()) return;

      // 1) Build the payload for both login and register
      let payload = { username, password };

      // 2) If registering, prompt for the secret and add it to payload
      if (path === "/register") {
        if (locked) {
          setError(
            "Too many attempts. Please reach out to kydxbot@support.com to retrieve the SECRET_KEY if you are actively subscribed."
          );
          return;
        }
        const secret = prompt("Enter the secret code to register:");
        if (secret === null) {
          // user hit Cancel on the prompt
          return;
        }
        payload.secret = secret;
      }

      // 3) Fire the register/login request
      const res = await fetch(path, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      // 4) Handle HTTP errors (especially for invalid secret on /register)
      if (!res.ok) {
        // If we're in the register flow and the server returns 401 or 403, count attempts
        if (
          path === "/register" &&
          (res.status === 401 || res.status === 403)
        ) {
          const newAttempts = attempts + 1;
          setAttempts(newAttempts);

          if (newAttempts >= 5 || res.status === 403) {
            setLocked(true);
            setError(
              "Too many attempts. Please reach out to kydxbot@support.com to retrieve the SECRET_KEY if you are actively subscribed."
            );
          } else if (newAttempts >= 3) {
            setError(
              `Invalid secret. You have ${5 - newAttempts} attempts remaining.`
            );
          } else {
            setError("Invalid secret");
          }
          return;
        }

        // Any other non-2xx error is fatal
        throw new Error(`HTTP ${res.status}`);
      }

      // 5) If we reach here, `res.ok === true`. Now decide what to do:
      //    • If this was a login call, the server should have returned { token }
      //    • If it was a register call, we need to immediately call /login to obtain a token

      if (path === "/login") {
        // ___ LOGIN FLOW ___
        const data = await res.json();
        const token = data.token;
        if (token) {
          localStorage.setItem("token", token);
          onAuth(token);
        } else {
          setError("No token returned from login");
        }
      } else {
        // ___ REGISTER FLOW ___
        // The register endpoint succeeded (created user), but it likely did NOT return a token.
        // So now we perform a second request to /login using the same credentials:
        const loginRes = await fetch("/login", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ username, password }),
        });

        if (!loginRes.ok) {
          // Registration succeeded, but login immediately afterward failed
          setError(
            "Registered successfully, but automatic login failed. Please try logging in manually."
          );
          return;
        }

        const loginData = await loginRes.json();
        const token = loginData.token;
        if (token) {
          localStorage.setItem("token", token);
          onAuth(token);
        } else {
          setError("Registered successfully, but no token returned from login.");
        }
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
        padding: "1rem 2rem 2rem 1rem",
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

      {/* ===== Button container: centered, equal‐width buttons ===== */}
      <div
        style={{
          display: "flex",
          justifyContent: "center",
          gap: "0.5rem",
          paddingLeft:"1.2rem"
        }}
      >
        <button
          style={{
            flex: 1,
            maxWidth: "120px",
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
            flex: 1,
            maxWidth: "120px",
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
        <p style={{ color: "#ff7276", marginTop: "0.75rem", paddingLeft:"1.2rem" }}>{error}</p>
      )}
    </div>
  );
}