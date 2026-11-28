import { useState, useEffect, useCallback } from "react";
import { Link, NavLink, useNavigate } from "react-router-dom";
import { Menu, X } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { useTheme } from "../context/ThemeContext";
import { getCart } from "../api/cart";

const CUSTOMER_NAV_LINKS = [
  { label: "Home", to: "/home" },
  { label: "Explore", to: "/explore" },
  { label: "Shop", to: "/shop" },
  { label: "Avatar", to: "/avatar" },
  { label: "Wishlist", to: "/wishlist" },
  { label: "Orders", to: "/orders" },
  { label: "Cart", to: "/cart" },
  { label: "Profile", to: "/profile" },
];

function Header() {
  const { user, isSeller, isAdmin, logout } = useAuth();
  const themeContext = useTheme();
  const theme = themeContext?.theme || "light";
  const toggle = themeContext?.toggle || (() => {});
  const navigate = useNavigate();

  const [cartCount, setCartCount] = useState(0);
  const [mobileOpen, setMobileOpen] = useState(false);

  const loadCartCount = useCallback(() => {
    getCart()
      .then((c) => {
        const count = (c?.items || []).reduce((sum, it) => sum + (it.quantity || 1), 0);
        setCartCount(count);
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    loadCartCount();
  }, [loadCartCount]);

  const handleLogout = async () => {
    await logout();
    setMobileOpen(false);
    navigate(isAdmin ? "/admin/login" : isSeller ? "/seller/login" : "/auth");
  };

  return (
    <header className="navbar" data-testid="customer-header" style={{ position: "relative" }}>
      <Link to="/home" className="logo" onClick={() => setMobileOpen(false)}>
        Wear<span>Wise</span>
      </Link>

      {/* Desktop Customer Navigation */}
      <nav className="nav-links" aria-label="Main navigation">
        {!isSeller &&
          !isAdmin &&
          CUSTOMER_NAV_LINKS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              style={({ isActive }) => ({
                fontWeight: isActive ? 900 : 700,
                textDecoration: isActive ? "underline" : "none",
                textUnderlineOffset: "5px",
              })}
            >
              {item.label}
              {item.to === "/cart" && cartCount > 0 ? ` (${cartCount})` : ""}
            </NavLink>
          ))}
        {isSeller && <Link to="/seller/dashboard">Seller Workspace</Link>}
        {isAdmin && <Link to="/admin">Admin Portal</Link>}
      </nav>

      {/* Right Actions */}
      <div className="header-actions">
        {isSeller && (
          <Link
            to="/seller/dashboard"
            className="nav-cta"
            style={{ background: "#8d6bff", color: "#ffffff" }}
          >
            Seller Portal ◆
          </Link>
        )}

        {isAdmin && (
          <Link
            to="/admin"
            className="nav-cta"
            style={{ background: "#ff3d9a", color: "#ffffff" }}
          >
            Admin Console ■
          </Link>
        )}

        <button
          className="theme-toggle"
          onClick={toggle}
          aria-label={`Switch to ${theme === "negative" ? "light" : "dark"} mode`}
          title={theme === "negative" ? "Switch to Light Mode" : "Switch to Dark Mode"}
        >
          <span className="theme-toggle-icon" aria-hidden="true">
            {theme === "negative" ? "☀" : "☾"}
          </span>
        </button>

        {user ? (
          <div className="header-user">
            <Link
              to={isAdmin ? "/admin" : isSeller ? "/seller/dashboard" : "/profile"}
              className="header-user-name"
              title={user.email}
              style={{ textDecoration: "none", color: "inherit" }}
            >
              {(user.name || user.email || "Account").split(" ")[0]}
            </Link>
            <button
              className="header-logout"
              onClick={handleLogout}
              title="Sign out"
              data-testid="shopper-logout-btn"
            >
              ✕
            </button>
          </div>
        ) : (
          <Link to="/auth" className="nav-cta" data-testid="header-signin-cta">
            Sign In ✦
          </Link>
        )}

        {!isSeller && !isAdmin && (
          <button
            type="button"
            className="theme-toggle"
            aria-label={mobileOpen ? "Close menu" : "Open menu"}
            data-testid="mobile-menu-toggle"
            onClick={() => setMobileOpen((o) => !o)}
            style={{ display: "none" }}
            id="mobile-nav-btn"
          >
            {mobileOpen ? <X size={18} /> : <Menu size={18} />}
          </button>
        )}
      </div>

      {/* Responsive Mobile Navigation Drawer */}
      <style>{`
        @media (max-width: 960px) {
          .navbar .nav-links { display: none !important; }
          #mobile-nav-btn { display: inline-flex !important; align-items: center; justify-content: center; }
        }
      `}</style>

      {mobileOpen && !isSeller && !isAdmin && (
        <nav
          data-testid="mobile-nav-drawer"
          aria-label="Mobile navigation"
          style={{
            position: "absolute",
            top: "100%",
            left: 0,
            right: 0,
            background: "#fff8f1",
            borderBottom: "3px solid #151515",
            padding: "14px 20px 18px",
            display: "grid",
            gridTemplateColumns: "repeat(2, 1fr)",
            gap: "10px",
            zIndex: 90,
          }}
        >
          {CUSTOMER_NAV_LINKS.map((item) => (
            <Link
              key={item.to}
              to={item.to}
              onClick={() => setMobileOpen(false)}
              style={{
                padding: "10px 12px",
                border: "2px solid #151515",
                background: "#ffffff",
                color: "#151515",
                fontWeight: 800,
                fontSize: "13px",
                textDecoration: "none",
              }}
            >
              {item.label}
              {item.to === "/cart" && cartCount > 0 ? ` (${cartCount})` : ""}
            </Link>
          ))}
        </nav>
      )}
    </header>
  );
}

export default Header;
