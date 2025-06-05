// src/App.jsx
import React, { useState } from "react";
import ChatBox from "./components/ChatBox";
import Login from "./components/Login";
import "./App.css"; // keep if you have any global styles

export default function App() {
  const [token, setToken] = useState(() => localStorage.getItem("token"));

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
