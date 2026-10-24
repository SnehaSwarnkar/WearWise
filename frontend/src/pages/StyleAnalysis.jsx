import "./../App.css";
import { Link, useLocation, useNavigate } from "react-router-dom";
import Header from "./Header";

function StyleAnalysis() {
    const location = useLocation();
const navigate = useNavigate();

const selectedLook = location.state?.selectedLook;
const handleBackToChoose = () => {
  navigate("/choose-look");
};
 if (!selectedLook) {

 }
      // fallback screen
  return (
    <div className="app analysis-page">
      {/* ================= NAVBAR ================= */}
      <Header />
      

      {/* ================= MAIN SECTION ================= */}

      <main className="analysis-main">
        {/* LEFT SIDE */}

        <section className="analysis-content">
          <div className="analysis-badge">
            ✦ YOUR STYLE RESULTS
          </div>

          <h1 className="analysis-title">
            YOUR
            <br />
            STYLE
            <br />
            <span>ERA</span> IS
            <br />
            HERE.
          </h1>

          <p className="analysis-description">
            AI Fashion has analyzed your visual style and created a fashion
            direction designed around your colors, personality and aesthetic.
          </p>

          <div className="analysis-buttons">
            <Link to="/explore" className="primary-analysis-btn">
              Explore Your Style →
            </Link>

            <Link to="/try-on" className="secondary-analysis-btn">
              Try Your Look
            </Link>
          </div>

          <div className="style-summary">
            <div className="summary-item">
              <span className="summary-number">01</span>
              <p>COLOR<br />PROFILE</p>
            </div>

            <div className="summary-item">
              <span className="summary-number">02</span>
              <p>STYLE<br />VIBE</p>
            </div>

            <div className="summary-item">
              <span className="summary-number">03</span>
              <p>BODY<br />PROFILE</p>
            </div>
          </div>
        </section>

        {/* RIGHT SIDE */}

        <section className="analysis-visual">
          {/* Main AI style orb */}

          <div className="style-orb">
            <div className="orb-glow"></div>
            <div className="orb-small"></div>

            <div className="style-text">
              <span>AI</span>
              <h2>STYLE</h2>
              <p>ANALYZED</p>
            </div>
          </div>

          {/* PAMPHLET 1 */}

          <div className="fashion-card card-match">
            <span className="card-number">01</span>

            <p>YOUR BEST</p>

            <h3>
              COLOR
              <br />
              MATCH
            </h3>

            <div className="card-line"></div>

            <span className="card-tag">
              PERSONAL PALETTE
            </span>
          </div>

          {/* PAMPHLET 2 */}

          <div className="fashion-card card-vibe">
            <span className="mini-star">✦</span>

            <p>STYLE</p>

            <h3>
              YOUR
              <br />
              VIBE
            </h3>

            <span className="vibe-label">2026</span>
          </div>

          {/* PAMPHLET 3 */}

          <div className="fashion-card card-fit">
            <span className="fit-icon">✦</span>

            <p>BODY</p>

            <h3>PROFILE</h3>

            <span className="fit-sub">
              MADE FOR YOU
            </span>
          </div>

          {/* LOOK GOOD STICKER */}

          <div className="look-sticker">
            <span>YOU</span>
            <strong>LOOK</strong>
            <strong>GOOD</strong>
            <small>✦</small>
          </div>

          {/* Extra floating tag */}

          <div className="style-tag">
            <span>✦</span>
            PERSONAL STYLE
          </div>
        </section>
      </main>
    </div>
  );
}

export default StyleAnalysis;