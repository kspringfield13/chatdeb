// src/App.jsx
import React from "react";
import ChatBox from "./components/ChatBox";
import "./App.css"; // keep if you have any global styles

export default function App() {
  return (
    <div style={{ padding: "2rem", textAlign: "center" }}>
      <ChatBox />
    </div>
  );
}
