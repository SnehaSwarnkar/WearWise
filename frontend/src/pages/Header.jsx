import { useState, useRef, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const GENDER_MENU = [
  {
    id: "men",
    label: "Men",
    path: "/men-shop",
    occasions: [
      { label: "Casual",  path: "/men-shop?occasion=casual" },
      { label: "Work",    path: "/men-shop?occasion=work" },
      { label: "Festive", path: "/men-shop?occasion=festive" },
      { label: "Wedding", path: "/men-shop?occasion=wedding" },
      { label: "Party",   path: "/men-shop?occasion=party" },
    ],
  },
  {
    id: "women",
    label: "Women",
    path: "/women-shop",
    occasions: [
      { label: "Casual",  path: "/women-shop?occasion=casual" },
      { label: "Work",    path: "/women-shop?occasion=work" },
      { label: "Festive", path: "/women-shop?occasion=festive" },
      { label: "Wedding", path: "/women-shop?occasion=wedding" },
      { label: "Party",   path: "/women-shop?occasion=party" },
    ],
  },
  {
    id: "kids",
    label: "Kids",
    path: "/kids-shop",
    occasions: [
      { label: "Casual",  path: "/kids-shop?occasion=casual" },
      { label: "Festive", path: "/kids-shop?occasion=festive" },
      { label: "Wedding", path: "/kids-shop?occasion=wedding" },
      { label: "Party",   path: "/kids-shop?occasion=party" },
    ],
  },
];

function Header() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  // Which gender item is hovered (shows occasion fly-out)
  const [activeGender, setActiveGender] = useState(null);
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const closeTimer = useRef(null);
  const menuRef = useRef(null);

  const openMenu = () => {
    clearTimeout(closeTimer.current);
    setDropdownOpen(true);
  };

  const closeMenu = () => {
    closeTimer.current = setTimeout(() => {
      setDropdownOpen(false);
      setActiveGender(null);
    }, 180);
  };

  // Close on outside click
  useEffect(() => {
    const handler = (e) => {
      if (menuRef.current && !menuRef.current.contains(e.target)) {
        setDropdownOpen(false);
        setActiveGender(null);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const shopLink = () => {
    if (!user) return "/login";
    if (user.gender === "men")   return "/men-shop";
    if (user.gender === "women") return "/women-shop";
    if (user.gender === "kids")  return "/kids-shop";
    return "/select-gender";
  };

  return (
    <header className="navbar">

      {/* LOGO */}
      <Link to="/" className="logo">
        Wear<span>Wise</span>
      </Link>

      {/* NAVIGATION */}
      <nav className="nav-links">
        <Link to="/explore">Explore</Link>

        {/* GENDER DROPDOWN */}
        <div
          className="nav-dropdown-root"
          ref={menuRef}
          onMouseEnter={openMenu}
          onMouseLeave={closeMenu}
        >
          <Link
            to={shopLink()}
            className={`nav-dropdown-trigger ${dropdownOpen ? "nav-dropdown-trigger-open" : ""}`}
            onClick={(e) => {
              // On mobile tap: toggle instead of navigate
              if (dropdownOpen) { e.preventDefault(); setDropdownOpen(false); }
            }}
          >
            Shop
            <span className="nav-dropdown-arrow">{dropdownOpen ? "▲" : "▼"}</span>
          </Link>

          {dropdownOpen && (
            <div className="nav-dropdown" onMouseEnter={openMenu} onMouseLeave={closeMenu}>
              {GENDER_MENU.map((gItem) => (
                <div
                  key={gItem.id}
                  className={`nav-dropdown-item ${activeGender === gItem.id ? "nav-dropdown-item-open" : ""}`}
                  onMouseEnter={() => { clearTimeout(closeTimer.current); setActiveGender(gItem.id); }}
                  onMouseLeave={() => setActiveGender(null)}
                >
                  {/* Gender row */}
                  <Link
                    to={gItem.path}
                    className="nav-dropdown-gender"
                    onClick={() => setDropdownOpen(false)}
                  >
                    <span className="nav-dropdown-gender-label">{gItem.label}</span>
                    <span className="nav-dropdown-chevron">›</span>
                  </Link>

                  {/* Occasion fly-out */}
                  {activeGender === gItem.id && (
                    <div className="nav-occasion-flyout">
                      <div className="nav-occasion-header">OCCASION</div>
                      {gItem.occasions.map((occ) => (
                        <Link
                          key={occ.label}
                          to={occ.path}
                          className="nav-occasion-item"
                          onClick={() => { setDropdownOpen(false); setActiveGender(null); }}
                        >
                          {occ.label}
                        </Link>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        <Link to="/try-on">Try On</Link>
        <Link to="/build-avatar">Avatar</Link>
      </nav>

      {/* ACTIONS */}
      <div className="header-actions">

        <Link
          to="/fashion-assistant"
          className="ai-assistant-icon"
          aria-label="AI Fashion Assistant"
          title="AI Fashion Assistant"
        >
          <span>✦</span>
        </Link>

        <Link
          to="/saved"
          className="saved-icon"
          aria-label="Saved Looks"
          title="Saved Looks & Wishlist"
        >
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="M20.8 8.7c0 5.5-8.8 10.4-8.8 10.4S3.2 14.2 3.2 8.7C3.2 6.1 5.1 4 7.6 4c1.5 0 2.9.8 3.8 2 0.9-1.2 2.3-2 3.8-2 2.5 0 4.4 2.1 4.4 4.7Z" />
          </svg>
        </Link>

        <Link
          to="/cart"
          className="cart-icon"
          aria-label="Shopping Cart"
          title="Shopping Cart"
        >
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="M7 8V6.5C7 4.57 8.57 3 10.5 3h3C15.43 3 17 4.57 17 6.5V8" />
            <path d="M4 8h16l1 13H3L4 8Z" />
            <path d="M9 12c.8.8 1.7 1.2 3 1.2s2.2-.4 3-1.2" />
          </svg>
        </Link>

        {user ? (
          <div className="header-user">
            <span className="header-user-name" title={user.email}>
              {user.name.split(" ")[0]}
            </span>
            <button className="header-logout" onClick={handleLogout} title="Sign out">
              ✕
            </button>
          </div>
        ) : (
          <Link to="/login" className="nav-cta">
            Sign In ✦
          </Link>
        )}

      </div>
    </header>
  );
}

export default Header;
