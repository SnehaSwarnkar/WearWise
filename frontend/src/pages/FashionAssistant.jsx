import { useState } from "react";
import { Link } from "react-router-dom";
import "./FashionAssistant.css";
import Header from "./Header";
import { sendChatMessage } from "../api/assistant";

function FashionAssistant() {
  const [message, setMessage] = useState("");

  const [messages, setMessages] = useState([
    {
      type: "ai",
      text: "Hi! I'm your WearWise fashion assistant. Tell me what you're dressing for and I'll help you put together a look."
    }
  ]);

  const suggestions = [
    "What should I wear tonight?",
    "Style my wardrobe",
    "Find something for a date",
    "Compare these two looks"
  ];

  const sendMessage = async (text = message) => {
    if (!text.trim()) return;

    const userMsg = { type: "user", text };
    setMessages((prev) => [...prev, userMsg]);
    setMessage("");

    try {
      const res = await sendChatMessage(text, messages);
      setMessages((prev) => [
        ...prev,
        { type: "ai", text: res.reply },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          type: "ai",
          text: "I'm checking your style profile and wardrobe to build the best recommendation for you.",
        },
      ]);
    }
  };

  return (
    <>
      <Header />

      <main className="fashion-assistant-page">


      {/* MAIN AREA */}

      <section className="assistant-layout">

        {/* CHAT */}

        <div className="assistant-chat">

          <div className="chat-top">
            <div className="assistant-avatar">
              ✦
            </div>

            <div>
              <strong>WearWise Stylist</strong>
              <small>Personal Fashion Assistant</small>
            </div>
          </div>


          <div className="chat-messages">

            {messages.map((msg, index) => (
              <div
                key={index}
                className={`chat-message ${msg.type}`}
              >
                {msg.text}
              </div>
            ))}

          </div>


          {/* SUGGESTIONS */}

          <div className="suggestions">

            {suggestions.map((suggestion) => (
              <button
                key={suggestion}
                onClick={() => sendMessage(suggestion)}
              >
                {suggestion}
              </button>
            ))}

          </div>


          {/* INPUT */}

          <div className="chat-input">

            <input
              type="text"
              placeholder="Ask me anything about your style..."
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  sendMessage();
                }
              }}
            />

            <button onClick={() => sendMessage()}>
              →
            </button>

          </div>

        </div>


        {/* CONTEXT PANEL */}

        <aside className="assistant-context">

          <div className="context-card avatar-context">

            <span>YOUR PROFILE</span>

            <div className="context-avatar">
              👤
            </div>

            <h2>Your Style Profile</h2>

            <p>
              Your avatar, colors, body profile and style
              preferences guide your recommendations.
            </p>

            <Link to="/build-avatar">
              Edit Avatar →
            </Link>

          </div>


          <div className="context-card">

            <div className="context-heading">
              <span>WARDROBE</span>
              <Link to="/wardrobe">View →</Link>
            </div>

            <div className="wardrobe-mini-grid">

              <div>👕</div>
              <div>👖</div>
              <div>👟</div>
              <div>👜</div>

            </div>

            <strong>
              Your saved pieces
            </strong>

            <p>
              Use your own clothes in future outfit recommendations.
            </p>

          </div>


          <div className="context-card">

            <span>STYLE TOOLS</span>

            <button>
              ✦ Recommendations
            </button>

            <button>
              ⇄ Compare Looks
            </button>

            <button>
              ◇ Build an Outfit
            </button>

          </div>

        </aside>

      </section>

    </main>
    </>
  );
}

export default FashionAssistant;