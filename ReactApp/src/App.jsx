// src/App.jsx
import ChatBox from "./components/ChatBox";
import "./App.css"; // keep if you have any global styles

export default function App() {

  return (
    <div
      style={{
        padding: "2rem",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        position: "relative",
      }}
    >
      <img
        src="/logo.png"
        alt="KYDxBot logo"
        style={{ padding: "2rem", height: "66px", alignSelf: "flex-start" }}
      />
      <div>
        <ChatBox />
      </div>
    </div>
  );
}
