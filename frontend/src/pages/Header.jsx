import { Link } from "react-router-dom";

function Header() {
  return (
    <header className="navbar">

      {/* LOGO */}
      <Link to="/" className="logo">
        Wear<span>Wise</span>
      </Link>

      {/* MAIN NAVIGATION */}
      <nav className="nav-links">
        <Link to="/explore">Explore</Link>
        <Link to="/my-style">My Style</Link>
        <Link to="/try-on">Try On</Link>
        <Link to="/build-avatar">Avatar</Link>
      </nav>

      {/* HEADER ACTIONS */}
      <div className="header-actions">

        {/* AI FASHION ASSISTANT */}
        <Link
          to="/fashion-assistant"
          className="ai-assistant-icon"
          aria-label="AI Fashion Assistant"
          title="AI Fashion Assistant"
        >
          <span>✦</span>
        </Link>

        {/* SAVED / WISHLIST */}
        <Link
          to="/saved"
          className="saved-icon"
          aria-label="Saved Looks"
          title="Saved Looks & Wishlist"
        >
          <svg
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <path d="M20.8 8.7c0 5.5-8.8 10.4-8.8 10.4S3.2 14.2 3.2 8.7C3.2 6.1 5.1 4 7.6 4c1.5 0 2.9.8 3.8 2 0.9-1.2 2.3-2 3.8-2 2.5 0 4.4 2.1 4.4 4.7Z" />
          </svg>
        </Link>

        {/* SHOPPING CART */}
        <Link
          to="/cart"
          className="cart-icon"
          aria-label="Shopping Cart"
          title="Shopping Cart"
        >
          <svg
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <path d="M7 8V6.5C7 4.57 8.57 3 10.5 3h3C15.43 3 17 4.57 17 6.5V8" />
            <path d="M4 8h16l1 13H3L4 8Z" />
            <path d="M9 12c.8.8 1.7 1.2 3 1.2s2.2-.4 3-1.2" />
          </svg>
        </Link>

        {/* CTA */}
        <Link
          to="/my-style"
          className="nav-cta"
        >
          Get Styled ✦
        </Link>

      </div>

    </header>
  );
}

export default Header;