import { useState, useRef, useEffect, useCallback } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useTheme } from "../context/ThemeContext";
import { getCart } from "../api/cart";

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
  const { user, logout, role, switchRole } = useAuth();
  const themeContext = useTheme();
  const theme = themeContext?.theme || 'light';
  const toggle = themeContext?.toggle || (() => {});
  const navigate = useNavigate();

  // Cart item count badge
  const [cartCount, setCartCount] = useState(0);
  useEffect(() => {
    getCart()
      .then((c) => {
        const count = (c?.items || []).reduce((sum, it) => sum + (it.quantity || 1), 0);
        setCartCount(count);
      })
      .catch(() => {});
  }, []);

  // Animate icon on click
  const [switching, setSwitching] = useState(false);
  const switchTimer = useRef(null);

  const handleThemeToggle = useCallback(() => {
    setSwitching(true);
    toggle();
    switchTimer.current = setTimeout(() => setSwitching(false), 480);
  }, [toggle]);

  useEffect(() => () => clearTimeout(switchTimer.current), []);

  // Gender dropdown state
  const [activeGender, setActiveGender] = useState(null);
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const closeTimer = useRef(null);
  const menuRef = useRef(null);

  // My Fit dropdown state
  const [myFitOpen, setMyFitOpen] = useState(false);
  const myFitCloseTimer = useRef(null);
  const myFitRef = useRef(null);

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

  const openMyFit = () => {
    clearTimeout(myFitCloseTimer.current);
    setMyFitOpen(true);
  };

  const closeMyFit = () => {
    myFitCloseTimer.current = setTimeout(() => {
      setMyFitOpen(false);
    }, 180);
  };

  // Close dropdowns on outside click
  useEffect(() => {
    const handler = (e) => {
      if (menuRef.current && !menuRef.current.contains(e.target)) {
        setDropdownOpen(false);
        setActiveGender(null);
      }
      if (myFitRef.current && !myFitRef.current.contains(e.target)) {
        setMyFitOpen(false);
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
    if (!user) return "/explore";
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
        <Link to="/">Home</Link>
        <Link to="/explore">Explore</Link>

        {/* SHOP (GENDER DROPDOWN) */}
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
                  <Link
                    to={gItem.path}
                    className="nav-dropdown-gender"
                    onClick={() => setDropdownOpen(false)}
                  >
                    <span className="nav-dropdown-gender-label">{gItem.label}</span>
                    <span className="nav-dropdown-chevron">›</span>
                  </Link>

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

        {/* MY STYLE */}
        <Link to="/my-style">My Style</Link>

        {/* MY FIT (BODY ENGINE DROPDOWN) */}
        <div
          className="nav-dropdown-root"
          ref={myFitRef}
          onMouseEnter={openMyFit}
          onMouseLeave={closeMyFit}
        >
          <Link
            to="/my-fit"
            className={`nav-dropdown-trigger ${myFitOpen ? "nav-dropdown-trigger-open" : ""}`}
            onClick={(e) => {
              if (myFitOpen) { e.preventDefault(); setMyFitOpen(false); }
            }}
          >
            My Fit
            <span className="nav-dropdown-arrow">{myFitOpen ? "▲" : "▼"}</span>
          </Link>

          {myFitOpen && (
            <div className="nav-dropdown" onMouseEnter={openMyFit} onMouseLeave={closeMyFit} style={{ width: '220px' }}>
              <Link to="/my-fit" className="nav-dropdown-gender" onClick={() => setMyFitOpen(false)}>
                <span className="nav-dropdown-gender-label">Fit Dashboard</span>
                <span className="nav-dropdown-chevron">›</span>
              </Link>
              <Link to="/profile" className="nav-dropdown-gender" onClick={() => setMyFitOpen(false)}>
                <span className="nav-dropdown-gender-label">Body Profile</span>
                <span className="nav-dropdown-chevron">›</span>
              </Link>
              <Link to="/avatar" className="nav-dropdown-gender" onClick={() => setMyFitOpen(false)}>
                <span className="nav-dropdown-gender-label">3D Avatar Studio</span>
                <span className="nav-dropdown-chevron">›</span>
              </Link>
              <Link to="/fit" className="nav-dropdown-gender" onClick={() => setMyFitOpen(false)}>
                <span className="nav-dropdown-gender-label">Honest Fit Studio</span>
                <span className="nav-dropdown-chevron" style={{ color: "var(--pink)" }}>✦</span>
              </Link>
              <Link
                to="/garments"
                className="nav-dropdown-gender"
                onClick={() => setMyFitOpen(false)}
                style={{ borderTop: "1px dashed var(--border-soft)", background: role === 'brand' ? 'rgba(255, 99, 61, 0.1)' : undefined }}
              >
                <span className="nav-dropdown-gender-label">Merchant Garments</span>
                <span className="nav-dropdown-chevron" style={{ color: "var(--orange)", fontSize: "11px" }}>[MERCHANT]</span>
              </Link>
              <Link
                to="/merchant/garment-studio"
                className="nav-dropdown-gender"
                onClick={() => setMyFitOpen(false)}
                style={{ background: 'rgba(255, 61, 154, 0.08)' }}
              >
                <span className="nav-dropdown-gender-label">Digital Garment Studio</span>
                <span className="nav-dropdown-chevron" style={{ color: "var(--pink)", fontSize: "11px" }}>[STUDIO]</span>
              </Link>
            </div>
          )}
        </div>

        <Link to="/wardrobe">Wardrobe</Link>
        <Link to="/try-on">Try On</Link>
        <Link to="/fashion-assistant">AI Stylist</Link>
        {user && <Link to="/orders">Orders</Link>}
      </nav>

      {/* ACTIONS */}
      <div className="header-actions">

        {/* DEV ROLE TOGGLE (SHOPPER / MERCHANT) */}
        <button
          className="header-role-badge"
          onClick={() => switchRole(role === 'user' ? 'brand' : 'user')}
          title={`Active: ${role === 'user' ? 'Shopper Mode' : 'Merchant Mode'}. Click to toggle.`}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '5px',
            padding: '4px 10px',
            borderRadius: '4px',
            fontSize: '11px',
            fontWeight: 800,
            letterSpacing: '0.06em',
            textTransform: 'uppercase',
            background: role === 'brand' ? 'var(--orange)' : 'var(--lime)',
            color: '#151515',
            border: '2px solid var(--border)',
            boxShadow: '2px 2px 0 var(--border)',
            cursor: 'pointer',
          }}
        >
          <span>{role === 'brand' ? 'MERCHANT' : 'SHOPPER'}</span>
        </button>

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
          style={{ position: 'relative' }}
        >
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="M7 8V6.5C7 4.57 8.57 3 10.5 3h3C15.43 3 17 4.57 17 6.5V8" />
            <path d="M4 8h16l1 13H3L4 8Z" />
            <path d="M9 12c.8.8 1.7 1.2 3 1.2s2.2-.4 3-1.2" />
          </svg>
          {cartCount > 0 && (
            <span
              style={{
                position: 'absolute',
                top: '-4px',
                right: '-6px',
                background: 'var(--pink)',
                color: '#ffffff',
                fontSize: '10px',
                fontWeight: 800,
                width: '16px',
                height: '16px',
                borderRadius: '50%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                border: '1.5px solid var(--border)',
              }}
            >
              {cartCount}
            </span>
          )}
        </Link>

        {/* THEME TOGGLE */}
        <button
          className={`theme-toggle${switching ? " is-switching" : ""}`}
          onClick={handleThemeToggle}
          aria-label={`Switch to ${theme === "negative" ? "light" : "dark"} mode`}
          title={theme === "negative" ? "Switch to Light Mode" : "Switch to Dark Mode"}
        >
          <span className="theme-toggle-icon" aria-hidden="true">
            {theme === "negative" ? "☀" : "☾"}
          </span>
        </button>

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
