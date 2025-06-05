// src/App.jsx
import React, { useState, useEffect } from "react";
import ChatBox from "./components/ChatBox";
import Login from "./components/Login";
import "./App.css"; // keep if you have any global styles

export default function App() {
  const [token, setToken] = useState(() => localStorage.getItem("token"));

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const verifyToken = params.get("token");
    if (verifyToken) {
      fetch(`/verify?token=${verifyToken}`)
        .then((r) => r.json())
        .then((d) => {
          if (d.token) {
            localStorage.setItem("token", d.token);
            setToken(d.token);
            window.history.replaceState({}, "", "/");
          }
        })
        .catch(() => {});
    }
  }, []);

  const logout = () => {
    localStorage.removeItem("token");
    setToken(null);
  };

  return (
    <div style={{ padding: "2rem", textAlign: "center" }}>
      {token ? (
        <div>
          <ChatBox token={token} />
          <button
            onClick={logout}
            style={{ marginTop: "1rem", padding: "0.5rem 1rem" }}
          >
            Logout
          </button>
        </div>
      ) : (
        <Login onAuth={setToken} />
      )}
    </div>
  );
}
