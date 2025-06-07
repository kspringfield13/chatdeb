// src/App.jsx
import ChatBox from "./components/ChatBox";
import "./App.css"; // keep if you have any global styles

export default function App() {

  return (
    <div 
      style={{
        position: "relative" 
      }}
    >
      <img
        src="/logo.png"
        alt="KYDxBot logo"
        style={{
          height: "60px",
          position: "absolute",
          top: "1rem",
          left: "1rem"
        }}
      />
      <div style={{ display: "flex", flexDirection: "row" }}>
        {/* other flex items */}
      </div>
          <ChatBox />
    </div>
  );
}
