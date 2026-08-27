import "../App.css";
import { Link } from "react-router-dom";

function Explore() {
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

        <Link to="/my-style" className="profile-btn">
          Get Started
        </Link>
      </nav>

      <main className="placeholder-page">
        <p className="hero-tag">EXPLORE FASHION</p>

        <h1>Find something you love.</h1>

        <p>
          Browse different clothing styles and discover outfits that could
          match your personal fashion profile.
        </p>

        <div className="coming-soon-box">
          <span>🛍️</span>
          <h2>Your AI-powered fashion catalogue is coming here.</h2>
          <p>
            Soon you'll be able to explore clothing, filter styles, and
            virtually try outfits before making a decision.
          </p>
        </div>

        <Link to="/my-style" className="primary-btn">
          ✨ Discover My Style First
        </Link>
      </main>
    </div>
  );
}

export default Explore;