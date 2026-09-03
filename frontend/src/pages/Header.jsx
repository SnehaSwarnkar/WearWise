import { Link } from "react-router-dom";

function Header() {
  return (
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
        My Style ✦
      </Link>
    </nav>
  );
}

export default Header;