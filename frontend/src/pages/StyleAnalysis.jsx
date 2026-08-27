import { useState } from "react";
import { Link } from "react-router-dom";
import "../App.css";

function StyleAnalysis() {
  const [step, setStep] = useState(1);
  const [image, setImage] = useState(null);
  const [undertone, setUndertone] = useState("");
  const [bodyType, setBodyType] = useState("");

  const handleImageChange = (event) => {
    const file = event.target.files[0];

    if (file) {
      setImage(URL.createObjectURL(file));
    }
  };

  return (
    <div className="app">
      <nav className="navbar">
        <Link to="/" className="logo">
          AI <span>FASHION</span>
        </Link>

        <div className="nav-links">
          <Link to="/explore">Explore</Link>
          <Link to="/my-style">My Style</Link>
          <Link to="/try-on">Try On</Link>
        </div>
      </nav>

      <main className="analysis-page">
        <div className="analysis-progress">
          <div className={step >= 1 ? "active-step" : ""}>1</div>
          <div className={step >= 2 ? "active-step" : ""}>2</div>
          <div className={step >= 3 ? "active-step" : ""}>3</div>
          <div className={step >= 4 ? "active-step" : ""}>4</div>
        </div>

        {/* STEP 1 */}

        {step === 1 && (
          <div className="analysis-content">
            <p className="hero-tag">STEP 1 OF 4</p>

            <h1>
              Let's see
              <br />
              <span>your style.</span>
            </h1>

            <p>
              Upload a clear front-facing photo to begin creating your
              personal fashion profile.
            </p>

            {!image ? (
              <div className="tryon-upload-box">
                <div className="upload-icon">📸</div>

                <h2>Upload Your Photo</h2>

                <label
                  htmlFor="style-image-upload"
                  className="primary-btn upload-btn"
                >
                  Choose Photo
                </label>

                <input
                  id="style-image-upload"
                  type="file"
                  accept="image/*"
                  onChange={handleImageChange}
                  hidden
                />
              </div>
            ) : (
              <div className="image-preview-box">
                <img
                  src={image}
                  alt="Style analysis"
                  className="image-preview"
                />

                <button
                  className="primary-btn continue-btn"
                  onClick={() => setStep(2)}
                >
                  Continue →
                </button>
              </div>
            )}
          </div>
        )}

        {/* STEP 2 */}

        {step === 2 && (
          <div className="analysis-content">
            <p className="hero-tag">STEP 2 OF 4</p>

            <h1>
              Discover your
              <br />
              <span>color profile.</span>
            </h1>

            <p>
              Select the undertone that feels closest to your skin.
              Later, our AI will automatically analyze this from your photo.
            </p>

            <div className="selection-grid">
              <button
                className={
                  undertone === "warm"
                    ? "selection-card selected"
                    : "selection-card"
                }
                onClick={() => setUndertone("warm")}
              >
                <span>☀️</span>
                <h2>Warm</h2>
                <p>Golden, peachy or yellow undertones.</p>
              </button>

              <button
                className={
                  undertone === "cool"
                    ? "selection-card selected"
                    : "selection-card"
                }
                onClick={() => setUndertone("cool")}
              >
                <span>❄️</span>
                <h2>Cool</h2>
                <p>Pink, rosy or bluish undertones.</p>
              </button>

              <button
                className={
                  undertone === "neutral"
                    ? "selection-card selected"
                    : "selection-card"
                }
                onClick={() => setUndertone("neutral")}
              >
                <span>⚖️</span>
                <h2>Neutral</h2>
                <p>A balanced mix of warm and cool tones.</p>
              </button>
            </div>

            <button
              className="primary-btn continue-btn"
              disabled={!undertone}
              onClick={() => setStep(3)}
            >
              Continue →
            </button>
          </div>
        )}

        {/* STEP 3 */}

        {step === 3 && (
          <div className="analysis-content">
            <p className="hero-tag">STEP 3 OF 4</p>

            <h1>
              Understand your
              <br />
              <span>body profile.</span>
            </h1>

            <p>
              Choose the body profile that feels closest to you.
            </p>

            <div className="selection-grid body-grid">
              {[
                "Rectangle",
                "Hourglass",
                "Pear",
                "Inverted Triangle",
                "Apple",
              ].map((type) => (
                <button
                  key={type}
                  className={
                    bodyType === type
                      ? "selection-card selected"
                      : "selection-card"
                  }
                  onClick={() => setBodyType(type)}
                >
                  <span>🧍</span>
                  <h2>{type}</h2>
                </button>
              ))}
            </div>

            <button
              className="primary-btn continue-btn"
              disabled={!bodyType}
              onClick={() => setStep(4)}
            >
              Generate My Profile →
            </button>
          </div>
        )}

        {/* STEP 4 */}

        {step === 4 && (
          <div className="analysis-content style-result">
            <p className="hero-tag">YOUR AI FASHION PROFILE</p>

            <h1>
              Your style is
              <br />
              <span>taking shape.</span>
            </h1>

            <div className="profile-result">
              <div className="profile-image">
                {image && <img src={image} alt="Your profile" />}
              </div>

              <div className="profile-details">
                <h2>Your Color Profile</h2>
                <p className="result-value">
                  {undertone.charAt(0).toUpperCase() +
                    undertone.slice(1)}{" "}
                  Undertone
                </p>

                <h2>Your Body Profile</h2>
                <p className="result-value">{bodyType}</p>

                <h2>Next Step</h2>
                <p>
                  Explore personalized clothing recommendations or try outfits
                  virtually.
                </p>

                <div className="result-buttons">
                  <Link to="/explore" className="primary-btn">
                    Explore Fashion
                  </Link>

                  <Link to="/try-on" className="secondary-btn">
                    Try On Clothes
                  </Link>
                </div>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default StyleAnalysis;