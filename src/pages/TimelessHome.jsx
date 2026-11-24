import { useState, useRef, useEffect, useCallback } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useTheme } from "../context/ThemeContext";
import "./TimelessHome.css";

/* ════════════════════════════════════════════════════════════
   NAVBAR
════════════════════════════════════════════════════════════ */
const GENDER_MENU = [
  {
    id: "men", label: "Men", path: "/men-shop",
    occasions: [
      { label: "Casual",  path: "/men-shop?occasion=casual" },
      { label: "Work",    path: "/men-shop?occasion=work" },
      { label: "Festive", path: "/men-shop?occasion=festive" },
      { label: "Wedding", path: "/men-shop?occasion=wedding" },
      { label: "Party",   path: "/men-shop?occasion=party" },
    ],
  },
  {
    id: "women", label: "Women", path: "/women-shop",
    occasions: [
      { label: "Casual",  path: "/women-shop?occasion=casual" },
      { label: "Work",    path: "/women-shop?occasion=work" },
      { label: "Festive", path: "/women-shop?occasion=festive" },
      { label: "Wedding", path: "/women-shop?occasion=wedding" },
      { label: "Party",   path: "/women-shop?occasion=party" },
    ],
  },
  {
    id: "kids", label: "Kids", path: "/kids-shop",
    occasions: [
      { label: "Casual",  path: "/kids-shop?occasion=casual" },
      { label: "Festive", path: "/kids-shop?occasion=festive" },
      { label: "Wedding", path: "/kids-shop?occasion=wedding" },
      { label: "Party",   path: "/kids-shop?occasion=party" },
    ],
  },
];

function HomeHeader() {
  const { user, logout } = useAuth();
  const { theme, toggle } = useTheme();
  const navigate = useNavigate();
  const [switching, setSwitching] = useState(false);
  const switchTimer = useRef(null);
  const [activeGender, setActiveGender] = useState(null);
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const closeTimer = useRef(null);
  const menuRef = useRef(null);

  const handleThemeToggle = useCallback(() => {
    setSwitching(true); toggle();
    switchTimer.current = setTimeout(() => setSwitching(false), 480);
  }, [toggle]);
  useEffect(() => () => clearTimeout(switchTimer.current), []);

  const openMenu = () => { clearTimeout(closeTimer.current); setDropdownOpen(true); };
  const closeMenu = () => { closeTimer.current = setTimeout(() => { setDropdownOpen(false); setActiveGender(null); }, 180); };

  useEffect(() => {
    const h = (e) => { if (menuRef.current && !menuRef.current.contains(e.target)) { setDropdownOpen(false); setActiveGender(null); } };
    document.addEventListener("mousedown", h);
    return () => document.removeEventListener("mousedown", h);
  }, []);

  const shopLink = () => {
    if (!user) return "/login";
    if (user.gender === "men")   return "/men-shop";
    if (user.gender === "women") return "/women-shop";
    if (user.gender === "kids")  return "/kids-shop";
    return "/select-gender";
  };

  return (
    <header className="ww-header">
      <Link to="/" className="ww-logo">Wear<span>Wise</span></Link>

      <nav className="ww-nav">
        <Link to="/" className="ww-nav-link ww-nav-active">Home</Link>
        <Link to="/explore" className="ww-nav-link">Explore</Link>
        <div className="ww-nav-dropdown-root" ref={menuRef} onMouseEnter={openMenu} onMouseLeave={closeMenu}>
          <Link to={shopLink()} className={`ww-nav-link ww-nav-dropdown-trigger${dropdownOpen ? " ww-nav-trigger-open" : ""}`}
            onClick={(e) => { if (dropdownOpen) { e.preventDefault(); setDropdownOpen(false); } }}>
            Shop <span className="ww-dropdown-arrow">{dropdownOpen ? "▲" : "▼"}</span>
          </Link>
          {dropdownOpen && (
            <div className="ww-nav-dropdown" onMouseEnter={openMenu} onMouseLeave={closeMenu}>
              {GENDER_MENU.map((g) => (
                <div key={g.id}
                  className={`ww-dropdown-item${activeGender === g.id ? " ww-dropdown-item-open" : ""}`}
                  onMouseEnter={() => { clearTimeout(closeTimer.current); setActiveGender(g.id); }}
                  onMouseLeave={() => setActiveGender(null)}>
                  <Link to={g.path} className="ww-dropdown-gender" onClick={() => setDropdownOpen(false)}>
                    <span>{g.label}</span><span className="ww-dropdown-chevron">›</span>
                  </Link>
                  {activeGender === g.id && (
                    <div className="ww-occasion-flyout">
                      <div className="ww-occasion-header">OCCASION</div>
                      {g.occasions.map((o) => (
                        <Link key={o.label} to={o.path} className="ww-occasion-item"
                          onClick={() => { setDropdownOpen(false); setActiveGender(null); }}>{o.label}</Link>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
        <Link to="/try-on" className="ww-nav-link">Try On</Link>
        <Link to="/build-avatar" className="ww-nav-link">Avatar</Link>
        {user && <Link to="/orders" className="ww-nav-link">Orders</Link>}
      </nav>

      <div className="ww-header-actions">
        <Link to="/fashion-assistant" className="ww-action-btn ww-ai-btn" title="AI Fashion Assistant">✦</Link>
        <Link to="/saved" className="ww-action-btn ww-heart-btn" title="Saved Looks">
          <svg viewBox="0 0 24 24" fill="#FF3294" stroke="#151515" strokeWidth="1.5" width="16" height="16">
            <path d="M20.8 8.7c0 5.5-8.8 10.4-8.8 10.4S3.2 14.2 3.2 8.7C3.2 6.1 5.1 4 7.6 4c1.5 0 2.9.8 3.8 2 0.9-1.2 2.3-2 3.8-2 2.5 0 4.4 2.1 4.4 4.7Z"/>
          </svg>
        </Link>
        <Link to="/cart" className="ww-action-btn ww-cart-btn" title="Cart">
          <svg viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" width="16" height="16">
            <path d="M6 2 3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z"/><line x1="3" y1="6" x2="21" y2="6"/>
            <path d="M16 10a4 4 0 0 1-8 0"/>
          </svg>
        </Link>
        <button className={`ww-action-btn ww-theme-btn${switching ? " ww-theme-switching" : ""}`} onClick={handleThemeToggle} title="Toggle theme">
          <span className="ww-theme-icon">{theme === "negative" ? "☀" : "☾"}</span>
        </button>
        {user ? (
          <div className="ww-user-row">
            <span className="ww-user-name">{user.name.split(" ")[0]}</span>
            <button className="ww-logout-btn" onClick={() => { logout(); navigate("/login"); }}>✕</button>
          </div>
        ) : (
          <Link to="/login" className="ww-signin-btn">Sign In →</Link>
        )}
      </div>
    </header>
  );
}

/* ════════════════════════════════════════════════════════════
   TICKER
════════════════════════════════════════════════════════════ */
function Ticker() {
  const items = [
    "STYLE SMARTER","✦","WEAR WITH CONFIDENCE","✦","DISCOVER YOUR COLORS","✦",
    "TRY BEFORE YOU BUY","✦","STYLE SMARTER","✦","WEAR WITH CONFIDENCE","✦",
    "STYLE SMARTER","✦","WEAR WITH CONFIDENCE","✦","DISCOVER YOUR COLORS","✦",
    "TRY BEFORE YOU BUY","✦","STYLE SMARTER","✦","WEAR WITH CONFIDENCE","✦",
  ];
  return (
    <div className="ww-ticker">
      <div className="ww-ticker-track">
        {items.map((item, i) => (
          <span key={i} className={item === "✦" ? "ww-ticker-star" : "ww-ticker-text"}>{item}</span>
        ))}
      </div>
    </div>
  );
}

/* ════════════════════════════════════════════════════════════
   HAND-DRAWN SVG ILLUSTRATIONS
════════════════════════════════════════════════════════════ */

/* Central lavender ball gown - detailed hand-drawn SVG */
function GownIllustration() {
  return (
    <svg viewBox="0 0 320 520" fill="none" xmlns="http://www.w3.org/2000/svg" className="ww-gown-svg">
      {/* Gown background glow */}
      <ellipse cx="160" cy="380" rx="140" ry="100" fill="#EEDCFF" opacity="0.5"/>
      <ellipse cx="160" cy="260" rx="80" ry="120" fill="#F0E5FF" opacity="0.4"/>

      {/* Full skirt - large flowing shape */}
      <path d="M 110 220 Q 60 280 30 360 Q 10 420 20 480 Q 80 510 160 510 Q 240 510 300 480 Q 310 420 290 360 Q 260 280 210 220 Z"
        fill="#E8D5FF" stroke="#9450D8" strokeWidth="1.8" strokeLinejoin="round"
        style={{filter:"drop-shadow(2px 4px 8px rgba(148,80,216,0.15))"}}/>

      {/* Skirt inner fold shading lines */}
      <path d="M 110 220 Q 100 300 80 380 Q 65 440 60 490" stroke="#C4A0E8" strokeWidth="1" fill="none" strokeDasharray="2 3" opacity="0.7"/>
      <path d="M 140 230 Q 135 320 130 400 Q 125 450 122 490" stroke="#C4A0E8" strokeWidth="0.8" fill="none" opacity="0.5"/>
      <path d="M 165 228 Q 165 320 165 410 Q 165 455 165 495" stroke="#C4A0E8" strokeWidth="0.8" fill="none" opacity="0.5"/>
      <path d="M 190 230 Q 195 320 200 400 Q 205 450 207 490" stroke="#C4A0E8" strokeWidth="0.8" fill="none" opacity="0.5"/>
      <path d="M 210 220 Q 220 300 240 380 Q 255 440 260 490" stroke="#C4A0E8" strokeWidth="1" fill="none" strokeDasharray="2 3" opacity="0.7"/>

      {/* Skirt cross-hatching for texture */}
      <path d="M 70 320 Q 90 310 110 320 Q 130 330 150 320" stroke="#B890D8" strokeWidth="0.6" fill="none" opacity="0.4"/>
      <path d="M 60 350 Q 85 338 115 348 Q 140 358 170 348" stroke="#B890D8" strokeWidth="0.6" fill="none" opacity="0.4"/>
      <path d="M 55 380 Q 85 368 120 376 Q 155 384 185 376" stroke="#B890D8" strokeWidth="0.6" fill="none" opacity="0.4"/>
      <path d="M 200 320 Q 220 310 240 320 Q 255 330 270 320" stroke="#B890D8" strokeWidth="0.6" fill="none" opacity="0.4"/>
      <path d="M 195 350 Q 218 340 245 348 Q 262 356 278 348" stroke="#B890D8" strokeWidth="0.6" fill="none" opacity="0.4"/>

      {/* Bodice */}
      <path d="M 120 150 Q 118 180 110 220 L 210 220 Q 202 180 200 150 Q 180 135 160 134 Q 140 135 120 150 Z"
        fill="#D8C4F5" stroke="#8840C8" strokeWidth="1.6" strokeLinejoin="round"/>

      {/* Bodice seam lines */}
      <path d="M 160 134 L 160 220" stroke="#9450D8" strokeWidth="0.8" fill="none" opacity="0.5"/>
      <path d="M 140 142 Q 148 175 148 220" stroke="#9450D8" strokeWidth="0.6" fill="none" opacity="0.4"/>
      <path d="M 180 142 Q 172 175 172 220" stroke="#9450D8" strokeWidth="0.6" fill="none" opacity="0.4"/>

      {/* Neckline / décolletage */}
      <path d="M 120 150 Q 140 142 160 138 Q 180 142 200 150" fill="none" stroke="#8840C8" strokeWidth="1.4"/>
      <path d="M 132 148 Q 148 162 160 160 Q 172 162 188 148" fill="none" stroke="#C4A0E8" strokeWidth="0.8"/>

      {/* Shoulders and arms */}
      <path d="M 120 150 Q 100 148 92 158 Q 86 168 90 182 Q 96 190 108 192 Q 118 190 122 180" stroke="#8840C8" strokeWidth="1.4" fill="#E0CCFF"/>
      <path d="M 200 150 Q 220 148 228 158 Q 234 168 230 182 Q 224 190 212 192 Q 202 190 198 180" stroke="#8840C8" strokeWidth="1.4" fill="#E0CCFF"/>

      {/* Neck */}
      <path d="M 148 110 Q 148 130 148 138 L 172 138 Q 172 130 172 110" stroke="#D4A8A8" strokeWidth="1.2" fill="#F5DDD8"/>

      {/* Head */}
      <ellipse cx="160" cy="90" rx="30" ry="34" fill="#F5DDD8" stroke="#C4906A" strokeWidth="1.4"/>

      {/* Hair - flowing updo/bun style */}
      <path d="M 132 70 Q 128 50 140 42 Q 155 36 168 42 Q 180 48 185 58 Q 188 66 190 72"
        fill="#8B4513" stroke="#6B3410" strokeWidth="1.2"/>
      <path d="M 132 70 Q 135 56 148 52 Q 160 48 172 54 Q 182 60 182 72"
        fill="#A0522D" stroke="#6B3410" strokeWidth="1" opacity="0.8"/>
      {/* Hair strand lines */}
      <path d="M 136 68 Q 142 55 155 50" stroke="#6B3410" strokeWidth="0.7" fill="none" opacity="0.6"/>
      <path d="M 148 52 Q 155 44 165 46" stroke="#6B3410" strokeWidth="0.7" fill="none" opacity="0.6"/>

      {/* Face details */}
      <ellipse cx="150" cy="88" rx="3" ry="4" fill="#6B3A2A" opacity="0.7"/> {/* left eye */}
      <ellipse cx="170" cy="88" rx="3" ry="4" fill="#6B3A2A" opacity="0.7"/> {/* right eye */}
      <path d="M 148 88 Q 150 86 152 88" stroke="#2A1810" strokeWidth="0.8" fill="none"/> {/* eye lash */}
      <path d="M 168 88 Q 170 86 172 88" stroke="#2A1810" strokeWidth="0.8" fill="none"/>
      <path d="M 155 96 Q 160 100 165 96" stroke="#C4706A" strokeWidth="1" fill="none"/> {/* smile */}
      <ellipse cx="153" cy="93" rx="4" ry="2" fill="#F5A898" opacity="0.5"/> {/* blush L */}
      <ellipse cx="167" cy="93" rx="4" ry="2" fill="#F5A898" opacity="0.5"/> {/* blush R */}

      {/* Waist detail / belt */}
      <path d="M 115 215 Q 160 208 205 215" stroke="#7820B8" strokeWidth="2" fill="none"/>
      <path d="M 118 218 Q 160 212 202 218" stroke="#C4A0E8" strokeWidth="1" fill="none" opacity="0.7"/>

      {/* Skirt ruffle at hem */}
      <path d="M 25 490 Q 50 480 75 492 Q 100 504 125 490 Q 150 476 175 490 Q 200 504 225 490 Q 250 476 275 490 Q 295 500 300 490"
        stroke="#9450D8" strokeWidth="1.4" fill="none"/>

      {/* Skirt tiered layers */}
      <path d="M 45 440 Q 100 428 160 435 Q 220 442 275 428" stroke="#B890D8" strokeWidth="1" fill="none" opacity="0.6"/>
      <path d="M 32 462 Q 95 448 160 455 Q 225 462 288 448" stroke="#B890D8" strokeWidth="1" fill="none" opacity="0.5"/>

      {/* Decorative embroidery dots on bodice */}
      <circle cx="152" cy="172" r="1.5" fill="#FF3294" opacity="0.8"/>
      <circle cx="160" cy="168" r="1.5" fill="#9450D8" opacity="0.8"/>
      <circle cx="168" cy="172" r="1.5" fill="#FF3294" opacity="0.8"/>
      <circle cx="156" cy="180" r="1.5" fill="#9450D8" opacity="0.8"/>
      <circle cx="164" cy="180" r="1.5" fill="#FF3294" opacity="0.8"/>

      {/* Pink highlights on skirt */}
      <path d="M 95 320 Q 110 310 125 320" stroke="#FF3294" strokeWidth="0.8" fill="none" opacity="0.5"/>
      <path d="M 230 340 Q 245 330 258 340" stroke="#FF3294" strokeWidth="0.8" fill="none" opacity="0.5"/>

      {/* Sketch annotation lines */}
      <line x1="30" y1="220" x2="22" y2="220" stroke="#9450D8" strokeWidth="0.6" opacity="0.4"/>
      <line x1="290" y1="220" x2="298" y2="220" stroke="#9450D8" strokeWidth="0.6" opacity="0.4"/>
      <line x1="22" y1="150" x2="22" y2="490" stroke="#9450D8" strokeWidth="0.5" strokeDasharray="3 4" opacity="0.25"/>
    </svg>
  );
}

/* Sunglasses — cat-eye hand-drawn */
function SunglassesIllustration() {
  return (
    <svg viewBox="0 0 160 70" fill="none" xmlns="http://www.w3.org/2000/svg" className="ww-acc-svg">
      {/* Left lens */}
      <path d="M 8 30 Q 10 18 22 16 Q 34 14 44 20 Q 54 26 52 36 Q 50 46 38 48 Q 26 50 16 44 Q 6 38 8 30 Z"
        fill="#C8ACEE" stroke="#2A1A3A" strokeWidth="2" strokeLinejoin="round"/>
      {/* Left lens cat-eye uptick */}
      <path d="M 44 20 Q 52 12 60 14 Q 54 18 52 24" stroke="#2A1A3A" strokeWidth="1.8" fill="#D4B8F4"/>
      {/* Right lens */}
      <path d="M 108 30 Q 110 18 122 16 Q 134 14 144 20 Q 154 26 152 36 Q 150 46 138 48 Q 126 50 116 44 Q 106 38 108 30 Z"
        fill="#C8ACEE" stroke="#2A1A3A" strokeWidth="2" strokeLinejoin="round"/>
      {/* Right lens cat-eye uptick */}
      <path d="M 144 20 Q 152 12 160 14 Q 154 18 152 24" stroke="#2A1A3A" strokeWidth="1.8" fill="#D4B8F4"/>
      {/* Bridge */}
      <path d="M 52 32 Q 72 26 108 32" stroke="#2A1A3A" strokeWidth="1.8" fill="none"/>
      {/* Left arm */}
      <path d="M 8 30 Q 2 28 1 24" stroke="#2A1A3A" strokeWidth="1.8" strokeLinecap="round" fill="none"/>
      {/* Right arm */}
      <path d="M 152 30 Q 158 28 159 24" stroke="#2A1A3A" strokeWidth="1.8" strokeLinecap="round" fill="none"/>
      {/* Lens reflection glints */}
      <path d="M 18 24 Q 22 20 28 22" stroke="white" strokeWidth="1.2" fill="none" opacity="0.7"/>
      <path d="M 118 24 Q 122 20 128 22" stroke="white" strokeWidth="1.2" fill="none" opacity="0.7"/>
      {/* Sketch lines */}
      <path d="M 15 36 Q 18 38 22 36" stroke="#9450D8" strokeWidth="0.6" fill="none" opacity="0.5"/>
      <path d="M 115 36 Q 118 38 122 36" stroke="#9450D8" strokeWidth="0.6" fill="none" opacity="0.5"/>
      {/* Small scribble marks */}
      <path d="M 36 42 Q 38 44 40 42" stroke="#2A1A3A" strokeWidth="0.7" fill="none" opacity="0.4"/>
    </svg>
  );
}

/* Headphones — elegant over-ear hand-drawn */
function HeadphonesIllustration() {
  return (
    <svg viewBox="0 0 130 150" fill="none" xmlns="http://www.w3.org/2000/svg" className="ww-acc-svg">
      {/* Headband arc */}
      <path d="M 25 72 Q 20 30 65 20 Q 110 10 108 72"
        stroke="#2A1A3A" strokeWidth="2.2" fill="none" strokeLinecap="round"/>
      {/* Headband shading */}
      <path d="M 28 72 Q 24 34 65 24 Q 106 14 105 72"
        stroke="#9450D8" strokeWidth="1" fill="none" opacity="0.4"/>
      {/* Left ear cup */}
      <ellipse cx="22" cy="82" rx="18" ry="22" fill="#D8C4F8" stroke="#2A1A3A" strokeWidth="2"/>
      <ellipse cx="22" cy="82" rx="12" ry="15" fill="#C4A8F0" stroke="#9450D8" strokeWidth="1"/>
      <ellipse cx="22" cy="82" rx="6" ry="8" fill="#B090E8" opacity="0.7"/>
      {/* Left cup detail lines */}
      <path d="M 10 82 Q 16 76 22 78" stroke="#8840C8" strokeWidth="0.7" fill="none" opacity="0.5"/>
      {/* Right ear cup */}
      <ellipse cx="108" cy="82" rx="18" ry="22" fill="#D8C4F8" stroke="#2A1A3A" strokeWidth="2"/>
      <ellipse cx="108" cy="82" rx="12" ry="15" fill="#C4A8F0" stroke="#9450D8" strokeWidth="1"/>
      <ellipse cx="108" cy="82" rx="6" ry="8" fill="#B090E8" opacity="0.7"/>
      {/* Right cup detail */}
      <path d="M 96 82 Q 102 76 108 78" stroke="#8840C8" strokeWidth="0.7" fill="none" opacity="0.5"/>
      {/* Pink accent strip on headband */}
      <path d="M 42 25 Q 65 18 90 24" stroke="#FF3294" strokeWidth="1.6" fill="none" opacity="0.7" strokeLinecap="round"/>
      {/* Cushion details */}
      <path d="M 8 76 Q 10 70 16 72" stroke="#9450D8" strokeWidth="0.8" fill="none" opacity="0.5"/>
      <path d="M 96 76 Q 98 70 104 72" stroke="#9450D8" strokeWidth="0.8" fill="none" opacity="0.5"/>
      {/* Cord hint */}
      <path d="M 22 104 Q 22 118 26 128 Q 30 136 28 142" stroke="#2A1A3A" strokeWidth="1.2" fill="none" strokeLinecap="round" opacity="0.6"/>
    </svg>
  );
}

/* Handbag — structured elegant hand-drawn */
function HandbagIllustration() {
  return (
    <svg viewBox="0 0 170 150" fill="none" xmlns="http://www.w3.org/2000/svg" className="ww-acc-svg">
      {/* Handle left */}
      <path d="M 52 55 Q 52 28 72 24 Q 85 20 85 24" stroke="#2A1A3A" strokeWidth="2" fill="none" strokeLinecap="round"/>
      {/* Handle right */}
      <path d="M 118 55 Q 118 28 98 24 Q 85 20 85 24" stroke="#2A1A3A" strokeWidth="2" fill="none" strokeLinecap="round"/>
      {/* Main bag body */}
      <rect x="28" y="55" width="114" height="85" rx="10" fill="#E8D5FF" stroke="#2A1A3A" strokeWidth="2"/>
      {/* Bag flap */}
      <path d="M 28 85 Q 30 70 42 65 L 128 65 Q 140 70 142 85 Q 100 90 85 88 Q 70 90 28 85 Z"
        fill="#D4BCFA" stroke="#2A1A3A" strokeWidth="1.6"/>
      {/* Flap curve detail */}
      <path d="M 32 83 Q 85 94 138 83" stroke="#9450D8" strokeWidth="1" fill="none" opacity="0.5"/>
      {/* Clasp */}
      <ellipse cx="85" cy="84" rx="10" ry="7" fill="#C8A8F0" stroke="#2A1A3A" strokeWidth="1.6"/>
      <ellipse cx="85" cy="84" rx="5" ry="3.5" fill="#9450D8" opacity="0.8"/>
      {/* Bag stitching lines */}
      <rect x="34" y="61" width="102" height="73" rx="8" stroke="#B890D8" strokeWidth="0.8" strokeDasharray="4 3" fill="none" opacity="0.5"/>
      {/* Pocket detail on front */}
      <rect x="62" y="98" width="46" height="30" rx="5" stroke="#9450D8" strokeWidth="1" fill="none" opacity="0.6"/>
      {/* Pocket stitching */}
      <path d="M 68 112 Q 85 108 102 112" stroke="#B890D8" strokeWidth="0.7" fill="none" opacity="0.5"/>
      {/* Lavender shading on body */}
      <path d="M 36 72 Q 38 80 36 92 Q 36 110 38 128" stroke="#C4A0E8" strokeWidth="0.8" fill="none" opacity="0.4"/>
      <path d="M 134 72 Q 132 80 134 92 Q 134 110 132 128" stroke="#C4A0E8" strokeWidth="0.8" fill="none" opacity="0.4"/>
      {/* Pink accent seam */}
      <path d="M 48 60 Q 85 56 122 60" stroke="#FF3294" strokeWidth="0.8" fill="none" opacity="0.5"/>
      {/* Handle shadow lines */}
      <path d="M 55 50 Q 55 36 70 30" stroke="#9450D8" strokeWidth="0.7" fill="none" opacity="0.4"/>
      <path d="M 115 50 Q 115 36 100 30" stroke="#9450D8" strokeWidth="0.7" fill="none" opacity="0.4"/>
    </svg>
  );
}

/* Perfume bottle — luxury hand-drawn */
function PerfumeIllustration() {
  return (
    <svg viewBox="0 0 100 160" fill="none" xmlns="http://www.w3.org/2000/svg" className="ww-acc-svg">
      {/* Bottle body */}
      <rect x="22" y="68" width="56" height="80" rx="8" fill="#FFD6EC" stroke="#2A1A3A" strokeWidth="1.8"/>
      {/* Bottle shading */}
      <rect x="28" y="74" width="12" height="68" rx="4" fill="white" opacity="0.4"/>
      <rect x="60" y="74" width="8" height="68" rx="3" fill="#FF3294" opacity="0.15"/>
      {/* Bottle neck */}
      <rect x="34" y="48" width="32" height="22" rx="4" fill="#FFB8D8" stroke="#2A1A3A" strokeWidth="1.6"/>
      {/* Neck shading */}
      <path d="M 40 52 Q 42 58 40 68" stroke="white" strokeWidth="1" fill="none" opacity="0.5"/>
      {/* Cap */}
      <rect x="30" y="38" width="40" height="12" rx="3" fill="#FF3294" stroke="#2A1A3A" strokeWidth="1.6"/>
      <rect x="34" y="34" width="32" height="6" rx="2" fill="#D82A80" stroke="#2A1A3A" strokeWidth="1.4"/>
      {/* Spray nozzle */}
      <rect x="62" y="30" width="20" height="8" rx="2" fill="#C4A0E8" stroke="#2A1A3A" strokeWidth="1.4"/>
      <circle cx="84" cy="34" r="4" fill="#9450D8" stroke="#2A1A3A" strokeWidth="1.2"/>
      {/* Label on bottle */}
      <rect x="30" y="80" width="40" height="30" rx="3" fill="white" stroke="#FFB8D8" strokeWidth="1" opacity="0.9"/>
      <path d="M 36 90 Q 50 86 64 90" stroke="#FF3294" strokeWidth="0.8" fill="none" opacity="0.7"/>
      <path d="M 38 96 Q 50 92 62 96" stroke="#C4A0E8" strokeWidth="0.6" fill="none" opacity="0.6"/>
      <path d="M 40 102 Q 50 100 60 102" stroke="#C4A0E8" strokeWidth="0.6" fill="none" opacity="0.5"/>
      {/* WW text on label */}
      <text x="42" y="88" fontSize="8" fontFamily="serif" fill="#9450D8" opacity="0.8" fontStyle="italic">WW</text>
      {/* Perfume spray mist */}
      <path d="M 86 28 Q 92 22 90 16" stroke="#C4A0E8" strokeWidth="0.8" fill="none" opacity="0.5" strokeDasharray="1 2"/>
      <path d="M 88 30 Q 96 26 96 20" stroke="#C4A0E8" strokeWidth="0.6" fill="none" opacity="0.4" strokeDasharray="1 2"/>
      <path d="M 84 26 Q 90 18 88 12" stroke="#FFB8D8" strokeWidth="0.6" fill="none" opacity="0.4" strokeDasharray="1 2"/>
      {/* Bottle highlight line */}
      <path d="M 28 76 Q 28 110 28 140" stroke="white" strokeWidth="1.5" fill="none" opacity="0.5"/>
    </svg>
  );
}

/* High heel — elegant hand-drawn */
function HighHeelIllustration() {
  return (
    <svg viewBox="0 0 160 130" fill="none" xmlns="http://www.w3.org/2000/svg" className="ww-acc-svg">
      {/* Shoe upper/vamp */}
      <path d="M 20 70 Q 24 50 50 42 Q 80 36 110 44 Q 130 50 138 62 Q 140 68 136 72 Q 100 68 60 70 Z"
        fill="#F0D8FF" stroke="#2A1A3A" strokeWidth="1.8" strokeLinejoin="round"/>
      {/* Toe cap */}
      <path d="M 20 70 Q 16 76 18 82 Q 24 88 50 90 Q 70 90 85 86 Q 60 80 42 76 Q 28 72 20 70 Z"
        fill="#E4C8F8" stroke="#2A1A3A" strokeWidth="1.6"/>
      {/* Heel */}
      <path d="M 136 72 Q 148 74 155 90 Q 158 100 155 110 Q 152 118 148 118 Q 144 118 142 110 Q 140 100 136 92 Q 132 82 136 72 Z"
        fill="#D4B8F0" stroke="#2A1A3A" strokeWidth="1.8" strokeLinejoin="round"/>
      {/* Heel inner shading */}
      <path d="M 140 80 Q 148 90 150 108" stroke="#9450D8" strokeWidth="0.8" fill="none" opacity="0.5"/>
      {/* Sole */}
      <path d="M 18 82 Q 60 92 85 88 Q 100 86 118 85 Q 128 84 136 92 L 148 118 Q 140 122 130 118 Q 110 108 90 110 Q 50 112 24 108 Q 14 104 18 82 Z"
        fill="#C8A8F0" stroke="#2A1A3A" strokeWidth="1.6" strokeLinejoin="round"/>
      {/* Sole highlight */}
      <path d="M 25 102 Q 60 108 95 106 Q 115 105 128 108" stroke="white" strokeWidth="1" fill="none" opacity="0.4"/>
      {/* Strap detail */}
      <path d="M 70 42 Q 72 36 76 34 Q 80 32 84 34 Q 88 36 90 42" stroke="#2A1A3A" strokeWidth="1.6" fill="#FFB8D8"/>
      {/* Shoe shading lines */}
      <path d="M 36 54 Q 42 50 50 52" stroke="#9450D8" strokeWidth="0.7" fill="none" opacity="0.5"/>
      <path d="M 60 46 Q 70 44 80 46" stroke="#9450D8" strokeWidth="0.7" fill="none" opacity="0.5"/>
      {/* Pink accent on vamp */}
      <path d="M 32 62 Q 60 56 90 60" stroke="#FF3294" strokeWidth="0.8" fill="none" opacity="0.5"/>
      {/* Cross-hatch on toe */}
      <path d="M 22 76 Q 26 72 32 74" stroke="#C4A0E8" strokeWidth="0.6" fill="none" opacity="0.4"/>
      <path d="M 24 80 Q 30 76 38 78" stroke="#C4A0E8" strokeWidth="0.6" fill="none" opacity="0.4"/>
    </svg>
  );
}

/* Fashion sketch paper */
function SketchPaperIllustration() {
  return (
    <svg viewBox="0 0 110 140" fill="none" xmlns="http://www.w3.org/2000/svg" className="ww-acc-svg">
      {/* Paper body */}
      <rect x="4" y="4" width="102" height="132" rx="4" fill="#FEFAF8" stroke="#D0C0B0" strokeWidth="1.2"/>
      {/* Fold corner */}
      <path d="M 90 4 L 106 20 L 90 20 Z" fill="#EDE0D0" stroke="#D0C0B0" strokeWidth="1"/>
      {/* Ruled lines */}
      <line x1="14" y1="24" x2="96" y2="24" stroke="#E0D0C8" strokeWidth="0.6"/>
      <line x1="14" y1="34" x2="96" y2="34" stroke="#E0D0C8" strokeWidth="0.6"/>
      {/* Rough figure sketch on paper */}
      {/* Head */}
      <ellipse cx="55" cy="48" rx="10" ry="12" stroke="#6B4A3A" strokeWidth="1.2" fill="none"/>
      {/* Neck */}
      <line x1="52" y1="60" x2="52" y2="66" stroke="#6B4A3A" strokeWidth="1"/>
      <line x1="58" y1="60" x2="58" y2="66" stroke="#6B4A3A" strokeWidth="1"/>
      {/* Shoulders */}
      <path d="M 36 68 Q 42 64 55 65 Q 68 64 74 68" stroke="#6B4A3A" strokeWidth="1.2" fill="none"/>
      {/* Arms */}
      <path d="M 36 68 Q 32 78 34 90" stroke="#6B4A3A" strokeWidth="1" fill="none"/>
      <path d="M 74 68 Q 78 78 76 90" stroke="#6B4A3A" strokeWidth="1" fill="none"/>
      {/* Bodice */}
      <path d="M 36 68 Q 36 82 38 90 L 72 90 Q 74 82 74 68" stroke="#6B4A3A" strokeWidth="1" fill="none"/>
      {/* Skirt rough sketch */}
      <path d="M 38 90 Q 28 108 22 128 L 88 128 Q 82 108 72 90" stroke="#6B4A3A" strokeWidth="1" fill="none"/>
      {/* Cross-hatching on skirt */}
      <path d="M 32 100 Q 40 97 48 100" stroke="#6B4A3A" strokeWidth="0.6" opacity="0.5"/>
      <path d="M 28 110 Q 38 106 48 110" stroke="#6B4A3A" strokeWidth="0.6" opacity="0.5"/>
      <path d="M 62 100 Q 70 97 78 100" stroke="#6B4A3A" strokeWidth="0.6" opacity="0.5"/>
      <path d="M 60 110 Q 70 106 80 110" stroke="#6B4A3A" strokeWidth="0.6" opacity="0.5"/>
      {/* Lavender wash on skirt */}
      <path d="M 38 90 Q 28 108 22 128 L 88 128 Q 82 108 72 90" fill="#EEDCFF" fillOpacity="0.3"/>
      {/* Notes on paper */}
      <text x="12" y="20" fontSize="7" fontFamily="serif" fill="#8B6A5A" fontStyle="italic">sketch 01</text>
      {/* Underline */}
      <line x1="12" y1="22" x2="58" y2="22" stroke="#C4A898" strokeWidth="0.5"/>
    </svg>
  );
}

/* ════════════════════════════════════════════════════════════
   FASHION ILLUSTRATION CLUSTER (right side)
════════════════════════════════════════════════════════════ */
function FashionIllustrationCluster() {
  return (
    <div className="ww-illus-cluster">
      {/* Background decorative circles */}
      <div className="ww-bg-circle ww-bg-c1"/>
      <div className="ww-bg-circle ww-bg-c2"/>
      <div className="ww-bg-circle ww-bg-c3"/>

      {/* Soft glow behind gown */}
      <div className="ww-illus-glow-pink"/>
      <div className="ww-illus-glow-lavender"/>

      {/* ── Central gown ── */}
      <div className="ww-illus-item ww-gown">
        <GownIllustration/>
      </div>

      {/* ── Sketch paper behind gown ── */}
      <div className="ww-illus-item ww-sketch-paper">
        <SketchPaperIllustration/>
      </div>

      {/* ── Sunglasses upper-left ── */}
      <div className="ww-illus-item ww-acc-sunglasses">
        <SunglassesIllustration/>
      </div>

      {/* ── Headphones upper-right ── */}
      <div className="ww-illus-item ww-acc-headphones">
        <HeadphonesIllustration/>
      </div>

      {/* ── Handbag lower-left ── */}
      <div className="ww-illus-item ww-acc-handbag">
        <HandbagIllustration/>
      </div>

      {/* ── Perfume right ── */}
      <div className="ww-illus-item ww-acc-perfume">
        <PerfumeIllustration/>
      </div>

      {/* ── High heel lower-right ── */}
      <div className="ww-illus-item ww-acc-heel">
        <HighHeelIllustration/>
      </div>

      {/* ── Floating labels ── */}
      <div className="ww-float-label ww-label-effortless">
        <span className="ww-label-star">✦</span> Effortless
      </div>
      <div className="ww-float-label ww-label-trendy">
        <span className="ww-label-star">✦</span> Trendy
      </div>
      <div className="ww-float-label ww-label-versatile">
        <span className="ww-label-star">✦</span> Versatile
      </div>
      <div className="ww-float-label ww-label-comfortable">
        <span className="ww-label-star">✦</span> Comfortable
      </div>

      {/* ── Sketch decorative elements ── */}
      {/* Pink outlined heart */}
      <svg className="ww-deco ww-deco-heart" viewBox="0 0 48 44" fill="none">
        <path d="M24 40 C24 40 2 27 2 14 C2 8 7 4 13 4 C17.5 4 21.3 6.5 24 10 C26.7 6.5 30.5 4 35 4 C41 4 46 8 46 14 C46 27 24 40 24 40Z"
          stroke="#FF3294" strokeWidth="1.8" fill="none"/>
        {/* heart sketch marks */}
        <path d="M 10 12 Q 12 10 15 12" stroke="#FF3294" strokeWidth="0.7" fill="none" opacity="0.6"/>
      </svg>

      {/* Stars */}
      <svg className="ww-deco ww-deco-star-1" viewBox="0 0 20 20" fill="#9450D8">
        <path d="M10 0 L11.5 8.5 L20 10 L11.5 11.5 L10 20 L8.5 11.5 L0 10 L8.5 8.5Z"/>
      </svg>
      <svg className="ww-deco ww-deco-star-2" viewBox="0 0 14 14" fill="#FF3294">
        <path d="M7 0 L8 5.5 L14 7 L8 8.5 L7 14 L6 8.5 L0 7 L6 5.5Z"/>
      </svg>
      <svg className="ww-deco ww-deco-star-3" viewBox="0 0 12 12" fill="#9450D8" opacity="0.6">
        <path d="M6 0 L7 4.5 L12 6 L7 7.5 L6 12 L5 7.5 L0 6 L5 4.5Z"/>
      </svg>

      {/* Pink hand-drawn arrow */}
      <svg className="ww-deco ww-deco-arrow" viewBox="0 0 60 30" fill="none">
        <path d="M 4 20 Q 20 10 40 16 Q 50 18 54 14" stroke="#FF3294" strokeWidth="1.6" strokeLinecap="round" fill="none"/>
        <path d="M 50 10 L 56 14 L 50 20" stroke="#FF3294" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" fill="none"/>
      </svg>

      {/* Sketch marks near sunglasses */}
      <svg className="ww-deco ww-deco-scribble" viewBox="0 0 40 20" fill="none">
        <path d="M 2 10 Q 8 4 14 10 Q 20 16 26 10 Q 32 4 38 10" stroke="#C4A0E8" strokeWidth="1.2" fill="none" opacity="0.7"/>
        <path d="M 4 14 Q 10 8 18 14" stroke="#C4A0E8" strokeWidth="0.8" fill="none" opacity="0.5"/>
      </svg>

      {/* Thin curved lines */}
      <svg className="ww-deco ww-deco-curve-1" viewBox="0 0 120 60" fill="none">
        <path d="M 4 50 Q 60 10 116 40" stroke="#E8C8F8" strokeWidth="1.4" fill="none" strokeDasharray="4 5"/>
      </svg>
      <svg className="ww-deco ww-deco-curve-2" viewBox="0 0 80 40" fill="none">
        <path d="M 4 30 Q 40 4 76 24" stroke="#FFB8D8" strokeWidth="1.2" fill="none" strokeDasharray="3 4" opacity="0.6"/>
      </svg>

      {/* Handwritten signature bottom-right */}
      <div className="ww-signature">
        <span className="ww-sig-1">Your Style</span>
        <span className="ww-sig-2">E<em>ra</em></span>
      </div>
    </div>
  );
}

/* ════════════════════════════════════════════════════════════
   HERO SECTION
════════════════════════════════════════════════════════════ */
function Hero() {
  return (
    <section className="ww-hero">
      {/* LEFT */}
      <div className="ww-hero-left">
        <div className="ww-hero-badge">
          <span className="ww-badge-dot"/>
          YOUR PERSONAL AI STYLIST
        </div>

        <h1 className="ww-hero-headline">
          <span className="ww-h1-black">DRESS LIKE</span>
          <span className="ww-h1-pink">THE MAIN</span>
          <span className="ww-h1-black">CHARACTER.</span>
        </h1>

        <p className="ww-hero-desc">
          AI Fashion helps you discover your colors, understand your body
          profile and try clothes virtually before making a decision.
        </p>

        <div className="ww-hero-ctas">
          <Link to="/my-style" className="ww-cta-primary">Discover My Style →</Link>
          <Link to="/explore"  className="ww-cta-secondary">Explore Fashion</Link>
        </div>

        <div className="ww-hero-stats">
          <div className="ww-stat"><strong>AI</strong><span>Powered styling</span></div>
          <div className="ww-stat-divider"/>
          <div className="ww-stat"><strong>4+</strong><span>Style tools</span></div>
          <div className="ww-stat-divider"/>
          <div className="ww-stat"><strong>∞</strong><span>Fashion choices</span></div>
        </div>
      </div>

      {/* RIGHT — illustration cluster */}
      <div className="ww-hero-right">
        <FashionIllustrationCluster/>
      </div>
    </section>
  );
}

/* ════════════════════════════════════════════════════════════
   JOURNEY SECTION
════════════════════════════════════════════════════════════ */
function JourneySection() {
  const cards = [
    { num:"01", icon:"🎨", title:"Discover Colors",  desc:"Find the palette that elevates your natural beauty.", cls:"card-pink",   link:"/my-style" },
    { num:"02", icon:"👗", title:"Build Your Style", desc:"Create a fashion profile tailored exactly to you.",  cls:"card-lime",   link:"/build-avatar" },
    { num:"03", icon:"🪄", title:"Virtual Try-On",   desc:"See how any outfit looks on you before buying.",    cls:"card-purple", link:"/try-on" },
    { num:"04", icon:"✦",  title:"AI Stylist Chat",  desc:"Chat with your personal AI fashion assistant 24/7.",cls:"card-orange", link:"/fashion-assistant" },
  ];
  return (
    <section className="ww-journey">
      <div className="ww-journey-heading">
        <p>YOUR FASHION JOURNEY</p>
        <h2>Everything you need<br/><span>to dress better.</span></h2>
      </div>
      <div className="ww-journey-grid">
        {cards.map((c) => (
          <Link key={c.num} to={c.link} className={`ww-journey-card ${c.cls}`}>
            <span className="ww-card-num">{c.num}</span>
            <div className="ww-card-icon">{c.icon}</div>
            <h3>{c.title}</h3>
            <p>{c.desc}</p>
            <span className="ww-card-arrow">→</span>
          </Link>
        ))}
      </div>
    </section>
  );
}

/* ════════════════════════════════════════════════════════════
   EXPLORE CATEGORIES
════════════════════════════════════════════════════════════ */
function ExploreSection() {
  return (
    <section className="ww-explore-section">
      <div className="ww-explore-title">
        <p>EXPLORE THE COLLECTION</p>
        <h2>Find your next<br/><span>obsession.</span></h2>
      </div>
      <div className="ww-category-grid">
        <Link to="/women-shop" className="ww-cat ww-cat-one"><h3>Women</h3><p>Sarees, lehengas & western</p><span>Shop →</span></Link>
        <Link to="/men-shop"   className="ww-cat ww-cat-two"><h3>Men</h3><p>Kurtas, suits & western</p><span>Shop →</span></Link>
        <Link to="/kids-shop"  className="ww-cat ww-cat-three"><h3>Kids</h3><p>Fun styles ages 2–14</p><span>Shop →</span></Link>
      </div>
    </section>
  );
}

/* ════════════════════════════════════════════════════════════
   BIG CTA
════════════════════════════════════════════════════════════ */
function BigCTA() {
  return (
    <section className="ww-big-cta">
      <div className="ww-cta-bubble one"/><div className="ww-cta-bubble two"/>
      <div className="ww-cta-inner">
        <p>READY TO LEVEL UP?</p>
        <h2>Your next look is<br/><span>one click away.</span></h2>
        <Link to="/my-style" className="ww-cta-btn">Start Styling ✦</Link>
      </div>
    </section>
  );
}

/* ════════════════════════════════════════════════════════════
   FOOTER
════════════════════════════════════════════════════════════ */
function Footer() {
  return (
    <footer className="ww-footer">
      <div className="ww-footer-inner">
        <div className="ww-footer-logo">Wear<span>Wise</span></div>
        <p>AI-powered personal fashion styling. Discover your colors, build your avatar, and try on clothes virtually.</p>
        <div className="ww-footer-links">
          <Link to="/explore">Explore</Link>
          <Link to="/try-on">Try On</Link>
          <Link to="/build-avatar">Build Avatar</Link>
          <Link to="/fashion-assistant">AI Stylist</Link>
          <Link to="/cart">Cart</Link>
        </div>
      </div>
      <div className="ww-footer-copy">© 2026 WearWise. All rights reserved.</div>
    </footer>
  );
}

/* ════════════════════════════════════════════════════════════
   PAGE EXPORT
════════════════════════════════════════════════════════════ */
export default function TimelessHome() {
  return (
    <div className="ww-page">
      <HomeHeader/>
      <Ticker/>
      <Hero/>
      <JourneySection/>
      <ExploreSection/>
      <BigCTA/>
      <Footer/>
    </div>
  );
}
