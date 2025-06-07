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
        alignItems: "right",
        position: "relative",
      }}
    >
      <img
        src="/logo.png"
        alt="KYDxBot logo"
        style={{ height: "75px", alignSelf: "left" }}
      />
      <div>
        <ChatBox />
      </div>
    </div>
  );
}
