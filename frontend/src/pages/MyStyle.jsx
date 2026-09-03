import "../App.css";
import Header from "./Header";
import { useNavigate } from "react-router-dom";

function MyStyle() {
  const navigate = useNavigate();

  return (
    <main className="my-style-page">
      <Header />

      <div className="style-container">
        {/* LEFT CONTENT */}
        <section className="style-left">
          <div className="style-badge">
            ✦ YOUR PERSONAL STYLE
          </div>

          <h1 className="style-title">
            DISCOVER
            <br />
            WHAT
            <br />
            <span>SUITS YOU.</span>
          </h1>

          <p className="style-description">
            Upload your photo and let AI Fashion discover your personal
            colors, body profile and fashion choices designed especially
            for you.
          </p>

          <div className="style-actions">
            <label className="upload-photo-btn">
              ✦ Upload Photo

              <input
                type="file"
                accept="image/*"
                className="hidden-file-input"
                onChange={(e) => {
                  if (e.target.files && e.target.files[0]) {
                    navigate("/try-on");
                  }
                }}
              />
            </label>

            <button
              className="analyze-btn"
              onClick={() => navigate("/style-analysis")}
            >
              Analyze My Style →
            </button>
          </div>

          <div className="style-stats">
            <div className="style-stat">
              <h3>AI</h3>
              <p>Powered styling</p>
            </div>

            <div className="style-stat">
              <h3>4+</h3>
              <p>Style insights</p>
            </div>

            <div className="style-stat">
              <h3>∞</h3>
              <p>Fashion choices</p>
            </div>
          </div>
        </section>

        {/* RIGHT VISUAL */}
        <section className="style-visual">
          <div className="style-orange-shape"></div>

          <div className="style-yellow-shape"></div>

          <div className="visual-year">
            2026
          </div>

          <div className="visual-era">
            YOUR STYLE ERA
          </div>

          <div className="color-match">
            ✦ COLOR MATCH
          </div>

          <div className="body-profile-tag">
            ✦ BODY FIT
          </div>

          {/* PROFILE CARD */}
          <div className="style-profile-card">
            <div className="profile-icon">
              ✦
            </div>

            <h2>Your Style Profile</h2>

            <p>
              Upload a clear photo and let AI Fashion discover your
              unique style direction.
            </p>

            <label className="choose-photo-btn">
              Choose Photo

              <input
                type="file"
                accept="image/*"
                className="hidden-file-input"
                onChange={(e) => {
                  if (e.target.files && e.target.files[0]) {
                    navigate("/try-on");
                  }
                }}
              />
            </label>
          </div>

          <div className="visual-ai">
            Wear
          </div>

          <div className="visual-fashion">
            Wise
          </div>

          <div className="visual-bottom-label">
            PERSONAL STYLE
          </div>

          <div className="look-good">
            <span>YOU</span>
            <strong>LOOK</strong>
            <small>GOOD</small>
          </div>
        </section>
      </div>
    </main>
  );
}

export default MyStyle;