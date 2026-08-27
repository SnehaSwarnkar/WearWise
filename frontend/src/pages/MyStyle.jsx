import "../App.css";
import { Link } from "react-router-dom";

function MyStyle() {
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
          My Profile
        </Link>
      </nav>

      <main className="placeholder-page">
        <p className="hero-tag">DISCOVER MY STYLE</p>

        <h1>
          Let's understand
          <br />
          <span>your unique style.</span>
        </h1>

        <p>
          AI Fashion will help you understand your color profile, body shape,
          and the clothing styles that may suit you best.
        </p>

        <div className="style-options">
          <div className="style-option">
            <span>🎨</span>
            <h2>Color Analysis</h2>
            <p>
              Discover your undertone and explore colors that may complement
              your overall appearance.
            </p>
          </div>

          <div className="style-option">
            <span>🧍</span>
            <h2>Body Profile</h2>
            <p>
              Understand your body profile and discover clothing styles that
              may work well for you.
            </p>
          </div>

          <div className="style-option">
            <span>✨</span>
            <h2>Style Recommendations</h2>
            <p>
              Get personalized fashion suggestions based on your preferences
              and profile.
            </p>
          </div>
        </div>

        <Link to="/try-on" className="primary-btn">
          Start My Style Analysis →
        </Link>
      </main>
    </div>
  );
}

export default MyStyle;