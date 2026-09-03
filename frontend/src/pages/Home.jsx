import "../App.css";
import { Link } from "react-router-dom";

function Home() {
  return (
    <div className="app">

      {/* NAVBAR */}
      <nav className="navbar">
        <Link to="/" className="logo">
          Wear<span>Wise</span>
        </Link>

        <div className="nav-links">
          <Link to="/explore">Explore</Link>
          <Link to="/my-style">My Style</Link>
          <Link to="/try-on">Try On</Link>
        </div>

        <Link to="/my-style" className="nav-cta">
          Get Styled ✦
        </Link>
      </nav>


      {/* FASHION TICKER */}
      <div className="fashion-ticker">
        <div className="ticker-content">
          <span>STYLE SMARTER</span>
          <span>✦</span>
          <span>WEAR WITH CONFIDENCE</span>
          <span>✦</span>
          <span>DISCOVER YOUR COLORS</span>
          <span>✦</span>
          <span>TRY BEFORE YOU BUY</span>
          <span>✦</span>
          <span>STYLE SMARTER</span>
          <span>✦</span>
          <span>WEAR WITH CONFIDENCE</span>
        </div>
      </div>


      {/* HERO */}
      <section className="fashion-hero">

        <div className="hero-left">

          <div className="hero-pill">
            <span className="live-dot"></span>
            YOUR PERSONAL AI STYLIST
          </div>

          <h1>
            DRESS LIKE
            <br />
            <span>THE MAIN</span>
            <br />
            CHARACTER.
          </h1>

          <p className="hero-description">
            AI Fashion helps you discover your colors, understand your body
            profile and try clothes virtually before making a decision.
          </p>

          <div className="hero-actions">
            <Link to="/style-analysis" className="main-btn">
              Discover My Style →
            </Link>

            <Link to="/explore" className="outline-btn">
              Explore Fashion
            </Link>
          </div>

          <div className="mini-stats">
            <div>
              <strong>AI</strong>
              <span>Powered styling</span>
            </div>

            <div>
              <strong>4+</strong>
              <span>Style tools</span>
            </div>

            <div>
              <strong>∞</strong>
              <span>Fashion choices</span>
            </div>
          </div>

        </div>


        {/* HERO RIGHT */}
        <div className="hero-right">

          <div className="hero-card main-fashion-card">

            <div className="card-top">
              <span>YOUR STYLE ERA</span>
              <span>2026</span>
            </div>

            <div className="fashion-word">
              <span>Wear</span>
              <h2>Wise</h2>
            </div>

            <div className="card-bottom">
              <span>PERSONAL STYLE,</span>
              <span>REIMAGINED.</span>
            </div>

          </div>


          <div className="floating-tag pink-tag">
            <span>✦</span>
            COLOR MATCH
          </div>

          <div className="floating-tag orange-tag">
            <span>◉</span>
            BODY FIT
          </div>

          <div className="floating-tag purple-tag">
            <span>♧</span>
            VIRTUAL TRY ON
          </div>

          <div className="fashion-sticker">
            <span>YOU</span>
            <strong>LOOK</strong>
            <span>GOOD</span>
          </div>

        </div>

      </section>


      {/* STYLE JOURNEY */}
      <section className="journey-section">

        <div className="journey-heading">
          <p>YOUR FASHION JOURNEY</p>
          <h2>
            Less guessing.
            <br />
            <span>More you.</span>
          </h2>
        </div>


        <div className="journey-grid">

          <Link to="/style-analysis" className="journey-card card-pink">
            <span className="card-number">01</span>
            <div className="big-icon">🎨</div>
            <h3>Discover Your Colors</h3>
            <p>
              Find colors that complement your natural features.
            </p>
            <span className="card-arrow">↗</span>
          </Link>


          <Link to="/style-analysis" className="journey-card card-lime">
            <span className="card-number">02</span>
            <div className="big-icon">✦</div>
            <h3>Understand Your Body</h3>
            <p>
              Discover your body profile and better clothing fits.
            </p>
            <span className="card-arrow">↗</span>
          </Link>


          <Link to="/try-on" className="journey-card card-purple">
            <span className="card-number">03</span>
            <div className="big-icon">🪞</div>
            <h3>Try It On</h3>
            <p>
              Upload your image and visualize fashion choices.
            </p>
            <span className="card-arrow">↗</span>
          </Link>


          <Link to="/explore" className="journey-card card-orange">
            <span className="card-number">04</span>
            <div className="big-icon">↔</div>
            <h3>Compare Looks</h3>
            <p>
              Compare colors and styles to find your favorite look.
            </p>
            <span className="card-arrow">↗</span>
          </Link>

        </div>

      </section>


      {/* EXPLORE */}
      <section className="explore-section">

        <div className="explore-title">
          <p>EXPLORE THE MOOD</p>
          <h2>What are we wearing today?</h2>
        </div>


        <div className="fashion-category-grid">

          <Link to="/explore" className="fashion-category category-one">
            <span className="category-label">01</span>
            <h3>Tops</h3>
            <p>Make a statement.</p>
          </Link>

          <Link to="/explore" className="fashion-category category-two">
            <span className="category-label">02</span>
            <h3>Denim</h3>
            <p>Find your perfect fit.</p>
          </Link>

          <Link to="/explore" className="fashion-category category-three">
            <span className="category-label">03</span>
            <h3>Dresses</h3>
            <p>One piece. Full look.</p>
          </Link>

        </div>

      </section>


      {/* BIG CTA */}
      <section className="big-cta">

        <div className="cta-bubble one"></div>
        <div className="cta-bubble two"></div>

        <p>READY TO MEET YOUR STYLE?</p>

        <h2>
          Before you buy it,
          <br />
          <span>try it on.</span>
        </h2>

        <Link to="/try-on" className="cta-btn">
          Start Virtual Try-On ✦
        </Link>

      </section>


      {/* FOOTER */}
      <footer className="footer">

        <div className="footer-logo">
          Wear<span>Wise</span>
        </div>

        <p>
          Your personal AI fashion companion.
        </p>

        <p>
          Made to help you feel more confident in what you wear.
        </p>

      </footer>

    </div>
  );
}

export default Home;