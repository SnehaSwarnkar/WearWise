import { useEffect, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import Header from "./Header";
import "./StyleAnalysis.css";

/* ─────────────────────────────────────────
   HELPER — derive style profile from selectedLook
   (pure front-end analysis mirroring the original result cards)
───────────────────────────────────────── */
const LOOK_PROFILES = {
  1: {
    // STREET EDIT
    identity: "Urban Edge",
    tagline: "Bold. Expressive. Unapologetic.",
    description:
      "Your style gravitates toward statement pieces, oversized silhouettes and graphic prints. You dress to make an impression.",
    colourSeason: "Deep Autumn",
    palette: [
      { hex: "#1A1A2E", name: "Midnight" },
      { hex: "#E94560", name: "Bold Red" },
      { hex: "#F5A623", name: "Amber" },
      { hex: "#16213E", name: "Deep Navy" },
      { hex: "#F5F5F5", name: "Clean White" },
    ],
    colourTip: "Contrast is your best friend. Dark bases + a single pop of colour.",
    bodyInsight: "Oversized on top, tapered below — your silhouette is built for impact.",
    recommendations: [
      { label: "Silhouette", value: "Oversized & Relaxed" },
      { label: "Fabrics", value: "Denim, cotton twill, leather" },
      { label: "Patterns", value: "Graphic prints, colour-blocks" },
      { label: "Accessories", value: "Chunky sneakers, bucket hats, crossbodies" },
      { label: "Avoid", value: "Over-tailored or overly feminine cuts" },
    ],
    styleScore: 91,
    vibe: "STREET",
    vibeYear: "2026",
  },
  2: {
    // QUIET LUXURY
    identity: "Quiet Luxury",
    tagline: "Effortless. Refined. Understated.",
    description:
      "Your aesthetic is defined by quality over quantity — clean lines, neutral palettes and pieces that whisper rather than shout.",
    colourSeason: "Light Spring",
    palette: [
      { hex: "#F5EFE6", name: "Ecru" },
      { hex: "#C8B89A", name: "Warm Camel" },
      { hex: "#8B7355", name: "Cognac" },
      { hex: "#3D3028", name: "Rich Brown" },
      { hex: "#FFFFFF", name: "Pure White" },
    ],
    colourTip: "Build a capsule wardrobe in 3-4 neutrals. Texture is your statement.",
    bodyInsight: "Tailored fits that follow your natural silhouette. Quality speaks.",
    recommendations: [
      { label: "Silhouette", value: "Tailored & streamlined" },
      { label: "Fabrics", value: "Cashmere, silk, fine wool, linen" },
      { label: "Patterns", value: "Minimal — solid, fine stripe or subtle check" },
      { label: "Accessories", value: "Gold jewellery, structured bags, loafers" },
      { label: "Avoid", value: "Loud logos, synthetic fabrics, busy prints" },
    ],
    styleScore: 94,
    vibe: "MINIMAL",
    vibeYear: "2026",
  },
  3: {
    // POWER LOOK
    identity: "Power Dressing",
    tagline: "Sharp. Confident. Authoritative.",
    description:
      "You communicate strength through your wardrobe. Structured blazers, clean silhouettes and a commanding presence are your signature.",
    colourSeason: "True Winter",
    palette: [
      { hex: "#151515", name: "True Black" },
      { hex: "#2C2C5E", name: "Deep Indigo" },
      { hex: "#FFFFFF", name: "Crisp White" },
      { hex: "#8B0000", name: "Deep Red" },
      { hex: "#4A4A4A", name: "Charcoal" },
    ],
    colourTip: "High contrast is your power move. Black + white + one bold accent.",
    bodyInsight: "Structured shoulders, defined waist — power dressing amplifies your presence.",
    recommendations: [
      { label: "Silhouette", value: "Sharp, tailored & structured" },
      { label: "Fabrics", value: "Wool suiting, poplin, leather" },
      { label: "Patterns", value: "Classic pinstripe, houndstooth, solid" },
      { label: "Accessories", value: "Minimal gold, structured briefcase, block heels" },
      { label: "Avoid", value: "Flowy or unstructured silhouettes" },
    ],
    styleScore: 89,
    vibe: "POWER",
    vibeYear: "2026",
  },
  4: {
    // NIGHT OUT
    identity: "Glam Noir",
    tagline: "Dark. Luminous. Magnetic.",
    description:
      "After dark is where your style truly shines. Luxe fabrics, body-conscious silhouettes and strategic detail make every entrance count.",
    colourSeason: "Deep Winter",
    palette: [
      { hex: "#0D0D0D", name: "Carbon Black" },
      { hex: "#6B2D6B", name: "Deep Plum" },
      { hex: "#C0A060", name: "Champagne Gold" },
      { hex: "#2C1654", name: "Midnight Violet" },
      { hex: "#E8C4D8", name: "Blush Rose" },
    ],
    colourTip: "Rich jewel tones and metallics are your night-time palette.",
    bodyInsight: "Body-conscious silhouettes with strategic cut-outs or draping.",
    recommendations: [
      { label: "Silhouette", value: "Body-conscious, draped, or slit" },
      { label: "Fabrics", value: "Satin, velvet, sequins, chiffon" },
      { label: "Patterns", value: "Abstract print, metallic, solid deep tones" },
      { label: "Accessories", value: "Statement earrings, clutch, heeled boots" },
      { label: "Avoid", value: "Overly casual or overly covered-up looks" },
    ],
    styleScore: 88,
    vibe: "GLAM",
    vibeYear: "2026",
  },
};

/* ─────────────────────────────────────────
   DECORATION SVGs
───────────────────────────────────────── */
function Star({ size = 14, color = "#FF3294", style = {} }) {
  return (
    <svg width={size} height={size} viewBox="0 0 20 20" fill={color} style={style} aria-hidden="true">
      <path d="M10 0L11.8 8.2L20 10L11.8 11.8L10 20L8.2 11.8L0 10L8.2 8.2Z" />
    </svg>
  );
}

function SketchDress({ style = {} }) {
  return (
    <svg viewBox="0 0 80 160" fill="none" xmlns="http://www.w3.org/2000/svg" style={{ width: 60, height: "auto", ...style }} aria-hidden="true">
      <ellipse cx="40" cy="20" rx="15" ry="16" fill="#F5DDD8" stroke="#C4906A" strokeWidth="1.2" />
      <path d="M28 36Q22 50 24 80Q32 90 40 90Q48 90 56 80Q58 50 52 36Q46 42 40 42Q34 42 28 36Z"
        fill="#FFD6EC" stroke="#FF3294" strokeWidth="1.2" />
      <path d="M24 80Q16 110 18 148Q28 155 40 155Q52 155 62 148Q64 110 56 80Q48 88 40 88Q32 88 24 80Z"
        fill="#EEDCFF" stroke="#9450D8" strokeWidth="1.2" />
      <path d="M28 100Q34 95 40 97Q46 95 52 100" stroke="#C4A0E8" strokeWidth="0.7" fill="none" />
      <path d="M25 115Q33 108 40 111Q47 108 55 115" stroke="#C4A0E8" strokeWidth="0.7" fill="none" />
      <circle cx="36" cy="62" r="1.5" fill="#FF3294" opacity="0.8" />
      <circle cx="40" cy="58" r="1.5" fill="#9450D8" opacity="0.8" />
      <circle cx="44" cy="62" r="1.5" fill="#FF3294" opacity="0.8" />
    </svg>
  );
}

function SketchHandbag({ style = {} }) {
  return (
    <svg viewBox="0 0 80 70" fill="none" xmlns="http://www.w3.org/2000/svg" style={{ width: 56, height: "auto", ...style }} aria-hidden="true">
      <path d="M24 26Q24 14 32 11Q40 9 40 11" stroke="#9450D8" strokeWidth="1.4" fill="none" strokeLinecap="round" />
      <path d="M56 26Q56 14 48 11Q40 9 40 11" stroke="#9450D8" strokeWidth="1.4" fill="none" strokeLinecap="round" />
      <rect x="10" y="26" width="60" height="40" rx="8" fill="#F7EFFF" stroke="#9450D8" strokeWidth="1.4" />
      <path d="M10 42Q20 48 40 44Q60 48 70 42" stroke="#C4A0E8" strokeWidth="0.8" fill="none" />
      <ellipse cx="40" cy="40" rx="7" ry="5" fill="#EEDCFF" stroke="#9450D8" strokeWidth="1.2" />
      <path d="M20 30Q40 27 60 30" stroke="#FFD6EC" strokeWidth="0.7" fill="none" />
    </svg>
  );
}

/* ─────────────────────────────────────────
   SCORE RING component
───────────────────────────────────────── */
function ScoreRing({ score }) {
  const r = 44;
  const circ = 2 * Math.PI * r;
  const filled = (score / 100) * circ;
  return (
    <div className="sa-score-ring-wrap">
      <svg viewBox="0 0 110 110" width="110" height="110">
        <circle cx="55" cy="55" r={r} fill="none" stroke="#EEDCFF" strokeWidth="10" />
        <circle
          cx="55" cy="55" r={r}
          fill="none"
          stroke="url(#scoreGrad)"
          strokeWidth="10"
          strokeLinecap="round"
          strokeDasharray={`${filled} ${circ - filled}`}
          strokeDashoffset={circ * 0.25}
          transform="rotate(-90 55 55)"
        />
        <defs>
          <linearGradient id="scoreGrad" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stopColor="#FF3294" />
            <stop offset="100%" stopColor="#9450D8" />
          </linearGradient>
        </defs>
        <text x="55" y="50" textAnchor="middle" fontSize="24" fontWeight="900" fill="#151515" fontFamily="Archivo Black, sans-serif">{score}</text>
        <text x="55" y="66" textAnchor="middle" fontSize="10" fontWeight="700" fill="#89838A" letterSpacing="1">/ 100</text>
      </svg>
      <span className="sa-score-label">STYLE SCORE</span>
    </div>
  );
}

/* ─────────────────────────────────────────
   COLOUR PALETTE component
───────────────────────────────────────── */
function ColourPalette({ palette, tip }) {
  return (
    <div className="sa-palette-wrap">
      <div className="sa-palette-swatches">
        {palette.map((c) => (
          <div key={c.hex} className="sa-swatch-item">
            <div className="sa-swatch" style={{ background: c.hex }} />
            <span>{c.name}</span>
          </div>
        ))}
      </div>
      {tip && (
        <p className="sa-palette-tip">
          <Star size={10} color="#FF3294" style={{ display: "inline", marginRight: 5 }} />
          {tip}
        </p>
      )}
    </div>
  );
}

/* ─────────────────────────────────────────
   RECOMMENDATION ROW component
───────────────────────────────────────── */
function RecRow({ label, value }) {
  return (
    <div className="sa-rec-row">
      <span className="sa-rec-label">{label}</span>
      <span className="sa-rec-value">{value}</span>
    </div>
  );
}

/* ─────────────────────────────────────────
   MAIN PAGE
───────────────────────────────────────── */
function StyleAnalysis() {
  const location = useLocation();
  const navigate = useNavigate();

  const selectedLook = location.state?.selectedLook;
  const avatarProfile = location.state?.avatarProfile;

  // ── Guard: redirect if no look selected ──
  useEffect(() => {
    if (!selectedLook && !avatarProfile) {
      navigate("/try-on", { replace: true });
    }
  }, [selectedLook, avatarProfile, navigate]);

  // ── Derive profile from selectedLook or avatarProfile ──
  const profile = selectedLook
    ? LOOK_PROFILES[selectedLook.id] || LOOK_PROFILES[2]
    : {
        identity: avatarProfile?.styles?.length
          ? avatarProfile.styles.slice(0, 2).join(" × ")
          : "Personal Style",
        tagline: "Curated just for you.",
        description:
          "Your WearWise avatar profile has been analyzed. Your style identity is built around your colour preferences, body profile and fashion choices.",
        colourSeason: avatarProfile?.colour
          ? { warm: "Warm Autumn", cool: "True Summer", neutral: "Soft Spring", bold: "True Winter" }[avatarProfile.colour] || "Personalised"
          : "Personalised",
        palette: [
          { hex: avatarProfile?.selectedColour || "#FF3294", name: "Your Colour" },
          { hex: "#EEDCFF", name: "Lavender" },
          { hex: "#D2F34B", name: "Lime Pop" },
          { hex: "#C4A0E8", name: "Soft Purple" },
          { hex: "#F5DDD8", name: "Blush" },
        ],
        colourTip: "Your personalised palette reflects your unique colour season.",
        bodyInsight: avatarProfile?.bodyType
          ? `Your ${avatarProfile.bodyType} silhouette works beautifully with ${avatarProfile.fit || "versatile"} fits.`
          : "Your body profile guides our fit recommendations.",
        recommendations: [
          { label: "Style", value: avatarProfile?.styles?.join(", ") || "Personalised" },
          { label: "Fit", value: avatarProfile?.fit || "To be personalised" },
          { label: "Body Type", value: avatarProfile?.bodyType || "To be personalised" },
          { label: "Colour Family", value: avatarProfile?.colour || "To be personalised" },
          { label: "Next Step", value: "Explore your curated collection" },
        ],
        styleScore: 86,
        vibe: avatarProfile?.styles?.[0]?.toUpperCase() || "PERSONAL",
        vibeYear: "2026",
      };

  if (!selectedLook && !avatarProfile) return null;

  const lookImage = selectedLook?.image || null;
  const lookName  = selectedLook?.name  || "YOUR STYLE";
  const lookMood  = selectedLook?.mood  || "";

  return (
    <div className="sa-page">
      <Header />

      {/* ── Page hero ── */}
      <header className="sa-hero">
        <div className="sa-hero-blob sa-blob-1" />
        <div className="sa-hero-blob sa-blob-2" />

        <div className="sa-hero-inner">
          <span className="sa-eyebrow">✦ YOUR PERSONAL AI CONSULTANT</span>
          <h1 className="sa-hero-h1">
            Discover Your<br />
            <em>Personal Style.</em>
          </h1>
          <p className="sa-hero-desc">
            Let AI understand your unique features, discover your best colors,
            and help you build a style that feels completely you.
          </p>
        </div>

        {/* Sketch decoration */}
        <div className="sa-hero-deco" aria-hidden="true">
          <SketchDress />
          <Star size={12} color="#FF3294" style={{ position: "absolute", top: 20, right: 20, opacity: 0.7 }} />
          <Star size={8}  color="#9450D8" style={{ position: "absolute", bottom: 30, left: 10, opacity: 0.5 }} />
        </div>

        {/* Step flow */}
        <div className="sa-step-flow">
          <div className="sa-step-item sa-step-done">
            <span>01</span><div><strong>UPLOAD</strong><small>Photo ready</small></div>
          </div>
          <div className="sa-step-line sa-line-done" />
          <div className="sa-step-item sa-step-done">
            <span>02</span><div><strong>CHOOSE</strong><small>Look selected</small></div>
          </div>
          <div className="sa-step-line sa-line-done" />
          <div className="sa-step-item sa-step-active">
            <span>03</span><div><strong>RESULTS</strong><small>Style analyzed</small></div>
          </div>
        </div>
      </header>

      {/* ── Analysis results ── */}
      <main className="sa-results">

        {/* ══════════════════════════════════
            ROW 1 — Identity card + Score
        ══════════════════════════════════ */}
        <section className="sa-top-row">

          {/* Identity */}
          <div className="sa-identity-card">
            {lookImage && (
              <div className="sa-look-preview">
                <img src={lookImage} alt={lookName} className="sa-look-img" />
                <div className="sa-look-badge">
                  <span className="sa-look-name">{lookName}</span>
                  {lookMood && <span className="sa-look-mood">{lookMood}</span>}
                </div>
              </div>
            )}

            <div className="sa-identity-content">
              <span className="sa-section-eyebrow">✦ YOUR STYLE IDENTITY</span>
              <h2 className="sa-identity-name">{profile.identity}</h2>
              <p className="sa-identity-tagline"><em>{profile.tagline}</em></p>
              <p className="sa-identity-desc">{profile.description}</p>

              <div className="sa-vibe-tag">
                <span className="sa-vibe-year">{profile.vibeYear}</span>
                <div className="sa-vibe-inner">
                  <span>YOUR VIBE</span>
                  <strong>{profile.vibe}</strong>
                </div>
              </div>
            </div>
          </div>

          {/* Score + colour season */}
          <div className="sa-score-card">
            <span className="sa-section-eyebrow">✦ AI ANALYSIS</span>
            <ScoreRing score={profile.styleScore} />
            <div className="sa-colour-season">
              <span className="sa-cs-label">COLOUR SEASON</span>
              <strong className="sa-cs-value">{profile.colourSeason}</strong>
            </div>

            <div className="sa-sticker">
              <span>YOU</span>
              <strong>LOOK</strong>
              <strong>GOOD</strong>
              <small>✦</small>
            </div>
          </div>

        </section>

        {/* ══════════════════════════════════
            ROW 2 — Colour palette
        ══════════════════════════════════ */}
        <section className="sa-section sa-colour-section">
          <div className="sa-section-header">
            <div>
              <span className="sa-section-eyebrow">✦ COLOR ANALYSIS</span>
              <h2 className="sa-section-title">Your Personal <em>Palette.</em></h2>
            </div>
            <SketchHandbag style={{ opacity: 0.6 }} />
          </div>
          <ColourPalette palette={profile.palette} tip={profile.colourTip} />
        </section>

        {/* ══════════════════════════════════
            ROW 3 — Body insight + Recommendations
        ══════════════════════════════════ */}
        <div className="sa-dual-row">

          {/* Body insight */}
          <section className="sa-section sa-body-section">
            <span className="sa-section-eyebrow">✦ BODY PROFILE</span>
            <h2 className="sa-section-title">Fit <em>Intelligence.</em></h2>
            <p className="sa-body-insight">{profile.bodyInsight}</p>
            <div className="sa-body-figure" aria-hidden="true">
              <svg viewBox="0 0 80 160" fill="none" width="60" height="auto">
                <ellipse cx="40" cy="20" rx="14" ry="15" fill="#FFD6EC" stroke="#FF3294" strokeWidth="1.2" />
                <path d="M28 34Q22 48 24 76Q32 86 40 86Q48 86 56 76Q58 48 52 34Q46 40 40 40Q34 40 28 34Z"
                  fill="#F7EFFF" stroke="#9450D8" strokeWidth="1.2" />
                <path d="M24 76Q18 106 20 144Q28 150 40 150Q52 150 60 144Q62 106 56 76Q48 84 40 84Q32 84 24 76Z"
                  fill="#EEDCFF" stroke="#9450D8" strokeWidth="1.2" />
              </svg>
            </div>
          </section>

          {/* Recommendations */}
          <section className="sa-section sa-recs-section">
            <span className="sa-section-eyebrow">✦ FASHION RECOMMENDATIONS</span>
            <h2 className="sa-section-title">Style <em>Playbook.</em></h2>
            <div className="sa-rec-list">
              {profile.recommendations.map((r) => (
                <RecRow key={r.label} label={r.label} value={r.value} />
              ))}
            </div>
          </section>

        </div>

        {/* ══════════════════════════════════
            CTA ROW
        ══════════════════════════════════ */}
        <section className="sa-cta-row">
          <div className="sa-cta-inner">
            <div className="sa-cta-text">
              <span className="sa-section-eyebrow">✦ WHAT'S NEXT</span>
              <h2 className="sa-cta-h2">
                Your style era<br /><em>starts now.</em>
              </h2>
              <p className="sa-cta-p">
                Explore your curated wardrobe, try clothes on virtually,
                or build a deeper style profile with your avatar.
              </p>
            </div>

            <div className="sa-cta-buttons">
              <Link to="/explore" className="sa-btn-primary">
                Explore My Style →
              </Link>
              <Link to="/try-on" className="sa-btn-secondary">
                Virtual Try-On
              </Link>
              <Link to="/build-avatar" className="sa-btn-ghost">
                Build My Avatar
              </Link>
            </div>
          </div>

          {/* Decorative stars */}
          <Star size={18} color="#FF3294" style={{ position: "absolute", top: 32, right: 80, opacity: 0.5 }} />
          <Star size={12} color="#9450D8" style={{ position: "absolute", bottom: 32, right: 160, opacity: 0.4 }} />
          <Star size={10} color="#D2F34B" style={{ position: "absolute", top: 60, right: 40, opacity: 0.6 }} />
        </section>

      </main>
    </div>
  );
}

export default StyleAnalysis;
