import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import "../App.css";
import Header from "./Header";

function ChooseLook() {
  const navigate = useNavigate();

  const [selectedLook, setSelectedLook] = useState(null);

  const looks = [
    {
      id: 1,
      name: "STREET EDIT",
      mood: "BOLD • URBAN",
      image:
        "https://images.unsplash.com/photo-1539109136881-3be0616acf4b?auto=format&fit=crop&w=800&q=80",
    },
    {
      id: 2,
      name: "QUIET LUXURY",
      mood: "MINIMAL • ELEVATED",
      image:
        "https://images.unsplash.com/photo-1496747611176-843222e1e57c?auto=format&fit=crop&w=800&q=80",
    },
    {
      id: 3,
      name: "POWER LOOK",
      mood: "SHARP • CONFIDENT",
      image:
        "https://images.unsplash.com/photo-1485968579580-b6d095142e6e?auto=format&fit=crop&w=800&q=80",
    },
    {
      id: 4,
      name: "NIGHT OUT",
      mood: "DARK • GLAM",
      image:
        "https://images.unsplash.com/photo-1539109136881-3be0616acf4b?auto=format&fit=crop&w=800&q=80",
    },
  ];

  const handleContinue = () => {
    if (!selectedLook) {
      alert("Please choose a look first.");
      return;
    }

    navigate("/style-analysis", {
      state: {
        selectedLook,
      },
    });
  };

  return (
    <div className="choose-look-page">
      <Header />

      <main className="choose-editorial">
        <div className="choose-editorial-top">
          <span>✦ AI VIRTUAL TRY ON</span>
          <span>STEP 02 / 03</span>
        </div>

        <section className="choose-hero">
          <div className="choose-copy">
            <div className="choose-side-label">
              YOUR DIGITAL
              <br />
              WARDROBE
            </div>

            <h1>
              CHOOSE
              <br />
              <span>YOUR</span>
              <br />
              LOOK.
            </h1>

            <p>
              Pick a style that feels like you.
              <br />
              AI Fashion will transform your
              <br />
              photo into your next look.
            </p>
          </div>

          <div className="look-selection-stage">
            <div className="choose-purple-shape"></div>
            <div className="choose-orange-shape"></div>

            <div className="look-selection-card">
              <div className="look-card-top">
                <span>✦ STYLE SELECTOR</span>
                <span>02 / 03</span>
              </div>

              <div className="look-grid">
                {looks.map((look) => (
                  <button
                    type="button"
                    key={look.id}
                    className={`look-option ${
                      selectedLook?.id === look.id ? "selected" : ""
                    }`}
                    onClick={() => setSelectedLook(look)}
                  >
                    <img src={look.image} alt={look.name} />

                    <div className="look-option-overlay">
                      <span>{look.mood}</span>
                      <h3>{look.name}</h3>
                    </div>

                    {selectedLook?.id === look.id && (
                      <div className="selected-look-mark">✦ SELECTED</div>
                    )}
                  </button>
                ))}
              </div>

              <div className="look-card-bottom">
                <span>
                  {selectedLook
                    ? `SELECTED: ${selectedLook.name}`
                    : "SELECT YOUR STYLE"}
                </span>

                <button
                  type="button"
                  className="continue-look-btn"
                  onClick={handleContinue}
                >
                  CONTINUE →
                </button>
              </div>
            </div>
          </div>

          <div className="choose-right-details">
            <div className="right-detail-number">2026</div>

            <div className="right-detail-text">
              STYLE
              <br />
              STARTS
              <br />
              WITH
              <br />
              YOU
            </div>

            <div className="choose-star">✦</div>
          </div>
        </section>

        <section className="choose-bottom">
          <div className="choose-privacy">
            <span>✦</span>
            YOUR STYLE • YOUR CHOICE
          </div>

          <div className="choose-flow">
            <div className="flow-item complete">
              <span>01</span>
              <div>
                <strong>UPLOAD</strong>
                <small>Photo ready</small>
              </div>
            </div>

            <div className="flow-line complete-line"></div>

            <div className="flow-item active">
              <span>02</span>
              <div>
                <strong>CHOOSE</strong>
                <small>Your outfit</small>
              </div>
            </div>

            <div className="flow-line"></div>

            <div className="flow-item">
              <span>03</span>
              <div>
                <strong>TRY ON</strong>
                <small>Your AI look</small>
              </div>
            </div>
          </div>

          <div className="choose-bottom-tag">
            AI FASHION
            <span>✦</span>
          </div>
        </section>
      </main>
    </div>
  );
}

export default ChooseLook;