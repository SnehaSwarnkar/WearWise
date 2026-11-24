import { useState } from "react";
import { useNavigate } from "react-router-dom";
import "./BuildAvatar.css";
import Header from "./Header";
import { saveAvatarProfile, analyzeAvatarPhoto } from "../api/avatar";

/* ─── Decoration SVGs ──────────────────────────────────────── */
function StarDeco({ size = 16, color = "#FF3294", style = {} }) {
  return (
    <svg width={size} height={size} viewBox="0 0 20 20" fill={color} style={style} aria-hidden="true">
      <path d="M10 0 L11.5 8.5 L20 10 L11.5 11.5 L10 20 L8.5 11.5 L0 10 L8.5 8.5Z" />
    </svg>
  );
}

/* ─── Progress bar ─────────────────────────────────────────── */
function ProgressBar({ step, total = 3 }) {
  const pct = (step / total) * 100;
  return (
    <div className="ba-progress-wrap">
      <span className="ba-progress-label">STEP {step} / {total}</span>
      <div className="ba-progress-track">
        <div className="ba-progress-fill" style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

/* ─── Body shape SVGs for body-type cards ──────────────────── */
function BodyShapeSVG({ type, selected }) {
  const fill = selected ? "#FF3294" : "#C4A0E8";
  const stroke = selected ? "#E8007F" : "#9450D8";

  const shapes = {
    hourglass: (
      <svg viewBox="0 0 50 90" fill="none" className="ba-body-svg">
        <ellipse cx="25" cy="12" rx="12" ry="12" fill={fill} stroke={stroke} strokeWidth="1.5"/>
        <path d="M14 24 Q8 40 10 55 Q16 65 25 65 Q34 65 40 55 Q42 40 36 24 Q30 30 25 30 Q20 30 14 24Z" fill={fill} stroke={stroke} strokeWidth="1.5"/>
        <path d="M12 65 Q8 78 10 88 L20 88 L22 70Z" fill={fill} stroke={stroke} strokeWidth="1" opacity=".8"/>
        <path d="M38 65 Q42 78 40 88 L30 88 L28 70Z" fill={fill} stroke={stroke} strokeWidth="1" opacity=".8"/>
      </svg>
    ),
    pear: (
      <svg viewBox="0 0 50 90" fill="none" className="ba-body-svg">
        <ellipse cx="25" cy="12" rx="11" ry="12" fill={fill} stroke={stroke} strokeWidth="1.5"/>
        <path d="M17 24 Q14 36 15 48 Q12 58 10 68 Q16 72 25 72 Q34 72 40 68 Q38 58 35 48 Q36 36 33 24 Q29 28 25 28 Q21 28 17 24Z" fill={fill} stroke={stroke} strokeWidth="1.5"/>
        <path d="M12 70 Q10 80 12 88 L20 88 L22 72Z" fill={fill} stroke={stroke} strokeWidth="1" opacity=".8"/>
        <path d="M38 70 Q40 80 38 88 L30 88 L28 72Z" fill={fill} stroke={stroke} strokeWidth="1" opacity=".8"/>
      </svg>
    ),
    rectangle: (
      <svg viewBox="0 0 50 90" fill="none" className="ba-body-svg">
        <ellipse cx="25" cy="12" rx="11" ry="12" fill={fill} stroke={stroke} strokeWidth="1.5"/>
        <rect x="14" y="24" width="22" height="42" rx="6" fill={fill} stroke={stroke} strokeWidth="1.5"/>
        <rect x="14" y="66" width="8" height="22" rx="4" fill={fill} stroke={stroke} strokeWidth="1" opacity=".8"/>
        <rect x="28" y="66" width="8" height="22" rx="4" fill={fill} stroke={stroke} strokeWidth="1" opacity=".8"/>
      </svg>
    ),
    apple: (
      <svg viewBox="0 0 50 90" fill="none" className="ba-body-svg">
        <ellipse cx="25" cy="12" rx="11" ry="12" fill={fill} stroke={stroke} strokeWidth="1.5"/>
        <path d="M16 24 Q8 36 8 50 Q8 62 25 64 Q42 62 42 50 Q42 36 34 24 Q30 32 25 32 Q20 32 16 24Z" fill={fill} stroke={stroke} strokeWidth="1.5"/>
        <path d="M14 62 Q12 74 14 88 L22 88 L23 64Z" fill={fill} stroke={stroke} strokeWidth="1" opacity=".8"/>
        <path d="M36 62 Q38 74 36 88 L28 88 L27 64Z" fill={fill} stroke={stroke} strokeWidth="1" opacity=".8"/>
      </svg>
    ),
    "inverted-triangle": (
      <svg viewBox="0 0 50 90" fill="none" className="ba-body-svg">
        <ellipse cx="25" cy="12" rx="11" ry="12" fill={fill} stroke={stroke} strokeWidth="1.5"/>
        <path d="M10 24 Q8 36 12 50 Q16 60 25 62 Q34 60 38 50 Q42 36 40 24 Q32 30 25 30 Q18 30 10 24Z" fill={fill} stroke={stroke} strokeWidth="1.5"/>
        <path d="M14 60 Q12 72 14 88 L22 88 L24 62Z" fill={fill} stroke={stroke} strokeWidth="1" opacity=".8"/>
        <path d="M36 60 Q38 72 36 88 L28 88 L26 62Z" fill={fill} stroke={stroke} strokeWidth="1" opacity=".8"/>
      </svg>
    ),
    athletic: (
      <svg viewBox="0 0 50 90" fill="none" className="ba-body-svg">
        <ellipse cx="25" cy="11" rx="10" ry="11" fill={fill} stroke={stroke} strokeWidth="1.5"/>
        <path d="M12 22 Q7 34 9 48 Q12 60 25 62 Q38 60 41 48 Q43 34 38 22 Q32 28 25 28 Q18 28 12 22Z" fill={fill} stroke={stroke} strokeWidth="1.5"/>
        <path d="M12 60 Q10 73 12 88 L21 88 L23 62Z" fill={fill} stroke={stroke} strokeWidth="1" opacity=".8"/>
        <path d="M38 60 Q40 73 38 88 L29 88 L27 62Z" fill={fill} stroke={stroke} strokeWidth="1" opacity=".8"/>
      </svg>
    ),
    plus: (
      <svg viewBox="0 0 50 90" fill="none" className="ba-body-svg">
        <ellipse cx="25" cy="12" rx="12" ry="12" fill={fill} stroke={stroke} strokeWidth="1.5"/>
        <path d="M10 24 Q4 38 6 54 Q8 68 25 70 Q42 68 44 54 Q46 38 40 24 Q32 32 25 32 Q18 32 10 24Z" fill={fill} stroke={stroke} strokeWidth="1.5"/>
        <path d="M10 68 Q8 79 10 88 L20 88 L22 70Z" fill={fill} stroke={stroke} strokeWidth="1" opacity=".8"/>
        <path d="M40 68 Q42 79 40 88 L30 88 L28 70Z" fill={fill} stroke={stroke} strokeWidth="1" opacity=".8"/>
      </svg>
    ),
  };
  return shapes[type] || shapes.rectangle;
}

/* ─── Live avatar figure in sidebar ───────────────────────── */
function AvatarFigure({ profile, bodyTypes }) {
  const bodyName = profile.bodyType
    ? bodyTypes.find((b) => b.id === profile.bodyType)?.name
    : null;

  const colourMap = {
    warm:    ["#FFAD7D", "#FF7A5A"],
    cool:    ["#C4A0E8", "#FF3294"],
    neutral: ["#C8C8C8", "#A0A0A0"],
    bold:    ["#D2F34B", "#FF3294"],
  };
  const [c1, c2] = colourMap[profile.colour] || ["#E8D5FF", "#C4A0E8"];

  return (
    <svg viewBox="0 0 120 220" fill="none" className="ba-avatar-figure" aria-label="Style avatar">
      {/* glow */}
      <ellipse cx="60" cy="180" rx="52" ry="20" fill="rgba(148,80,216,0.1)"/>
      {/* head */}
      <ellipse cx="60" cy="34" rx="22" ry="24" fill="#F5DDD8" stroke="#C4906A" strokeWidth="1.5"/>
      {/* hair */}
      <path d="M38 24 Q38 10 60 8 Q82 10 82 24 Q76 20 60 18 Q44 20 38 24Z" fill="#8B4513"/>
      {/* outfit */}
      <path d="M38 56 Q28 72 30 100 L90 100 Q92 72 82 56 Q72 64 60 64 Q48 64 38 56Z"
        fill={`url(#bodyGrad-${profile.colour || "default"})`} stroke={c2} strokeWidth="1.2"/>
      {/* skirt / trousers */}
      <path d="M30 100 Q24 130 26 160 L48 160 L50 108Z" fill={c2} opacity=".85"/>
      <path d="M90 100 Q96 130 94 160 L72 160 L70 108Z" fill={c2} opacity=".85"/>
      {/* shoes */}
      <ellipse cx="37" cy="162" rx="12" ry="5" fill="#9450D8"/>
      <ellipse cx="83" cy="162" rx="12" ry="5" fill="#9450D8"/>
      {/* arms */}
      <path d="M38 60 Q22 76 24 95" stroke={c1} strokeWidth="10" strokeLinecap="round"/>
      <path d="M82 60 Q98 76 96 95" stroke={c1} strokeWidth="10" strokeLinecap="round"/>
      {/* gradient def */}
      <defs>
        <linearGradient id={`bodyGrad-${profile.colour || "default"}`} x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor={c1}/>
          <stop offset="100%" stopColor={c2}/>
        </linearGradient>
      </defs>
      {/* style vibe chips */}
      {profile.styles.slice(0, 2).map((s, i) => (
        <g key={s} transform={`translate(${i === 0 ? -10 : 70}, ${170 + i * 22})`}>
          <rect x="0" y="0" width="60" height="18" rx="9" fill="white" stroke="#EEDCFF" strokeWidth="1"/>
          <text x="30" y="12.5" fontSize="7" fontWeight="700" fill="#9450D8" textAnchor="middle">{s}</text>
        </g>
      ))}
      {/* name label */}
      {bodyName && (
        <text x="60" y="210" fontSize="8" fontWeight="800" fill="#9450D8" textAnchor="middle" letterSpacing="1">{bodyName.toUpperCase()}</text>
      )}
    </svg>
  );
}

/* ═══════════════════════════════════════════════════════════
   MAIN COMPONENT
═══════════════════════════════════════════════════════════ */
function BuildAvatar() {
  const navigate = useNavigate();

  const [mode, setMode] = useState(null);   // null | "manual" | "ai"
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [profile, setProfile] = useState({
    colour: "",
    bodyType: "",
    fit: "",
    styles: [],
    selectedColour: "#FF3294",
    photo: null,
  });

  const bodyTypes = [
    { id: "hourglass",         name: "Hourglass",          description: "Balanced shoulders and hips" },
    { id: "pear",              name: "Pear",               description: "Hips are naturally more prominent" },
    { id: "rectangle",        name: "Rectangle",          description: "A straighter, balanced silhouette" },
    { id: "apple",            name: "Apple",              description: "More fullness through the middle" },
    { id: "inverted-triangle", name: "Inverted Triangle",  description: "Shoulders are naturally more prominent" },
    { id: "athletic",         name: "Athletic",           description: "Defined, sporty silhouette" },
    { id: "plus",             name: "Plus Size",          description: "Fuller, curvier silhouette" },
  ];

  const styleOptions = ["Minimal", "Streetwear", "Casual", "Elegant", "Vintage", "Sporty", "Edgy", "Boho"];

  const handleStyleToggle = (style) =>
    setProfile((prev) => ({
      ...prev,
      styles: prev.styles.includes(style)
        ? prev.styles.filter((s) => s !== style)
        : [...prev.styles, style],
    }));

  const handlePhotoUpload = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setProfile((prev) => ({ ...prev, photo: file }));
    setError("");
  };

  const handleFinish = async () => {
    setLoading(true);
    setError("");
    try {
      await saveAvatarProfile({ mode: mode || "manual", ...profile });
    } catch {
      /* non-blocking */
    }
    setLoading(false);
    navigate("/style-analysis", { state: { avatarProfile: profile } });
  };

  const handleAiAnalyze = async () => {
    setLoading(true);
    setError("");
    if (!profile.photo) {
      await handleFinish();
      return;
    }
    try {
      const result = await analyzeAvatarPhoto(profile.photo, profile.selectedColour);
      const merged = { ...profile, ...result };
      await saveAvatarProfile({ mode: "ai", ...merged });
      setLoading(false);
      navigate("/style-analysis", { state: { avatarProfile: merged } });
    } catch {
      setLoading(false);
      await handleFinish();
    }
  };

  /* ───────────────────────────────────────────
     MODE SELECTION SCREEN
  ─────────────────────────────────────────── */
  if (!mode) {
    return (
      <div className="ba-page">
        <Header />

        {/* Background blobs */}
        <div className="ba-blob ba-blob-1" />
        <div className="ba-blob ba-blob-2" />
        <div className="ba-blob ba-blob-3" />

        <div className="ba-main">
          {/* Hero text */}
          <div className="ba-intro">
            <span className="ba-eyebrow">✦ YOUR STYLE IDENTITY</span>
            <h1 className="ba-intro-h1">
              BUILD YOUR<br />
              <em>WearWise</em><br />
              AVATAR.
            </h1>
            <p className="ba-intro-p">
              Create a style profile that feels like you.
              Choose everything yourself or let AI help
              discover your starting point.
            </p>
          </div>

          {/* Mode cards */}
          <div className="ba-mode-grid">
            <button className="ba-mode-card ba-mode-manual" onClick={() => setMode("manual")}>
              <div className="ba-mode-num">01</div>
              <div className="ba-mode-icon">
                <svg viewBox="0 0 48 48" fill="none" width="44" height="44">
                  <circle cx="24" cy="24" r="22" fill="#FFF3F5" stroke="#EEDCFF" strokeWidth="1.5"/>
                  <path d="M24 10 L25.8 22.2 L38 24 L25.8 25.8 L24 38 L22.2 25.8 L10 24 L22.2 22.2Z" fill="#FF3294"/>
                </svg>
              </div>
              <h2>BUILD MANUALLY</h2>
              <p>I know my style. Let me choose my colours, body profile and fashion preferences.</p>
              <span className="ba-mode-arrow">START BUILDING →</span>
            </button>

            <button className="ba-mode-card ba-mode-ai" onClick={() => setMode("ai")}>
              <div className="ba-mode-num">02</div>
              <div className="ba-mode-icon">
                <svg viewBox="0 0 48 48" fill="none" width="44" height="44">
                  <circle cx="24" cy="24" r="22" fill="#F7EFFF" stroke="#EEDCFF" strokeWidth="1.5"/>
                  <text x="24" y="30" fontSize="14" fontWeight="900" fill="#9450D8" textAnchor="middle">AI</text>
                </svg>
              </div>
              <h2>AI ASSISTED</h2>
              <p>Upload a photo and let WearWise create a personalised starting profile for you.</p>
              <span className="ba-mode-arrow">LET AI HELP →</span>
            </button>
          </div>

          {/* Floating labels */}
          <div className="ba-float-label ba-fl-1">
            <StarDeco size={10} color="#9450D8"/> COLOUR
          </div>
          <div className="ba-float-label ba-fl-2">
            <StarDeco size={10} color="#FF3294"/> BODY FIT
          </div>
          <div className="ba-float-label ba-fl-3">
            <StarDeco size={10} color="#9450D8"/> YOUR VIBE
          </div>

          {/* Sketch deco */}
          <svg className="ba-deco-sketch ba-deco-top" viewBox="0 0 80 80" fill="none">
            <path d="M20 60 Q20 20 60 20" stroke="#EEDCFF" strokeWidth="1.5" strokeDasharray="4 5"/>
            <path d="M55 15 Q62 15 62 22" stroke="#EEDCFF" strokeWidth="1.5" fill="none"/>
          </svg>
          <svg className="ba-deco-sketch ba-deco-bottom" viewBox="0 0 60 40" fill="none">
            <path d="M4 36 Q30 4 56 20" stroke="#FFD6EC" strokeWidth="1.4" strokeDasharray="3 4"/>
          </svg>
        </div>
      </div>
    );
  }

  /* ───────────────────────────────────────────
     MANUAL BUILDER
  ─────────────────────────────────────────── */
  if (mode === "manual") {
    return (
      <div className="ba-page">
        {/* Minimal header */}
        <header className="ba-builder-header">
          <button className="ba-builder-logo" onClick={() => navigate("/")}>
            Wear<span>Wise</span>
          </button>
          <ProgressBar step={step} />
          <button className="ba-builder-exit" onClick={() => setMode(null)} title="Back to mode selection">✕</button>
        </header>

        <div className="ba-builder-layout">
          {/* ── Left content panel ── */}
          <section className="ba-builder-content">

            {/* STEP 1 — COLOUR */}
            {step === 1 && (
              <>
                <span className="ba-eyebrow">✦ STEP 01 — COLOUR PROFILE</span>
                <h1 className="ba-step-h1">
                  WHAT <em>COLOURS</em><br />FEEL LIKE YOU?
                </h1>
                <p className="ba-step-desc">
                  Pick the colour direction that feels most natural to you.
                  You don't need to know your exact colour season.
                </p>

                <div className="ba-colour-grid">
                  {[
                    { id: "warm",    label: "WARM",    desc: "Peach, coral, gold & earthy tones",  colors: ["#FFAD7D","#FF7A5A","#D4A05A"] },
                    { id: "cool",    label: "COOL",    desc: "Pink, blue, lavender & icy tones",   colors: ["#C4A0E8","#FF3294","#8FCFFF"] },
                    { id: "neutral", label: "NEUTRAL", desc: "Balanced shades across the spectrum", colors: ["#D4C8C4","#B0A8A4","#8C8495"] },
                    { id: "bold",    label: "BOLD",    desc: "I love colour. Give me everything.",  colors: ["#FF3294","#D2F34B","#9450D8"] },
                  ].map(({ id, label, desc, colors }) => (
                    <button
                      key={id}
                      className={`ba-colour-card${profile.colour === id ? " ba-selected" : ""}`}
                      onClick={() => setProfile({ ...profile, colour: id })}
                    >
                      <div className="ba-colour-swatches">
                        {colors.map((c) => (
                          <span key={c} className="ba-swatch" style={{ background: c }} />
                        ))}
                      </div>
                      <strong>{label}</strong>
                      <small>{desc}</small>
                      {profile.colour === id && (
                        <span className="ba-check">✓</span>
                      )}
                    </button>
                  ))}
                </div>
              </>
            )}

            {/* STEP 2 — BODY */}
            {step === 2 && (
              <>
                <span className="ba-eyebrow">✦ STEP 02 — BODY PROFILE</span>
                <h1 className="ba-step-h1">
                  YOUR BODY.<br /><em>YOUR FIT.</em>
                </h1>
                <p className="ba-step-desc">
                  Choose the silhouette that feels closest to you. This helps
                  WearWise recommend proportions and fits — it doesn't define
                  what you should wear.
                </p>

                <div className="ba-body-grid">
                  {bodyTypes.map((body) => (
                    <button
                      key={body.id}
                      className={`ba-body-card${profile.bodyType === body.id ? " ba-selected" : ""}`}
                      onClick={() => setProfile({ ...profile, bodyType: body.id })}
                    >
                      <div className="ba-body-figure">
                        <BodyShapeSVG type={body.id} selected={profile.bodyType === body.id} />
                      </div>
                      <strong>{body.name}</strong>
                      <small>{body.description}</small>
                    </button>
                  ))}
                </div>

                <div className="ba-fit-section">
                  <h3 className="ba-fit-label">HOW DO YOU LIKE YOUR CLOTHES TO FIT?</h3>
                  <div className="ba-fit-row">
                    {["Fitted", "Relaxed", "Oversized", "Mixed"].map((fit) => (
                      <button
                        key={fit}
                        className={`ba-fit-btn${profile.fit === fit ? " ba-selected" : ""}`}
                        onClick={() => setProfile({ ...profile, fit })}
                      >
                        {fit}
                      </button>
                    ))}
                  </div>
                </div>
              </>
            )}

            {/* STEP 3 — STYLE */}
            {step === 3 && (
              <>
                <span className="ba-eyebrow">✦ STEP 03 — YOUR STYLE</span>
                <h1 className="ba-step-h1">
                  WHAT'S<br /><em>YOUR VIBE?</em>
                </h1>
                <p className="ba-step-desc">
                  Pick as many as you want. Your style doesn't have to fit into one box.
                </p>

                <div className="ba-style-grid">
                  {styleOptions.map((style) => (
                    <button
                      key={style}
                      className={`ba-style-chip${profile.styles.includes(style) ? " ba-selected" : ""}`}
                      onClick={() => handleStyleToggle(style)}
                    >
                      <span className="ba-chip-star">✦</span>
                      {style}
                    </button>
                  ))}
                </div>

                {/* Identity preview */}
                <div className="ba-identity-card">
                  <div className="ba-identity-avatar">
                    <div className="ba-id-head"/>
                    <div className="ba-id-body"/>
                  </div>
                  <div>
                    <span className="ba-identity-label">YOUR WEARWISE ID</span>
                    <strong className="ba-identity-value">
                      {profile.styles.length
                        ? profile.styles.join(" × ")
                        : "STYLE IN PROGRESS…"}
                    </strong>
                  </div>
                </div>
              </>
            )}

            {/* Navigation */}
            <div className="ba-nav-row">
              {step > 1 && (
                <button className="ba-btn-back" onClick={() => setStep(step - 1)}>
                  ← BACK
                </button>
              )}
              {step < 3 ? (
                <button className="ba-btn-next" onClick={() => setStep(step + 1)}>
                  CONTINUE →
                </button>
              ) : (
                <button
                  className="ba-btn-next ba-btn-finish"
                  onClick={handleFinish}
                  disabled={loading}
                >
                  {loading ? (
                    <span className="ba-spinner"/>
                  ) : (
                    "CREATE MY AVATAR ✦"
                  )}
                </button>
              )}
            </div>

            {error && <p className="ba-error">{error}</p>}
          </section>

          {/* ── Right preview panel ── */}
          <aside className="ba-preview-panel">
            <div className="ba-preview-glow"/>

            <span className="ba-preview-label">✦ LIVE PREVIEW</span>

            <div className="ba-avatar-stage">
              <div className="ba-stage-ring ba-ring-1"/>
              <div className="ba-stage-ring ba-ring-2"/>
              <AvatarFigure profile={profile} bodyTypes={bodyTypes} />

              {/* You look good bubble */}
              <div className="ba-bubble">
                YOU<br/>LOOK<br/>GOOD ✦
              </div>
            </div>

            <div className="ba-preview-info">
              <span>WEARWISE AVATAR</span>
              <strong>
                {profile.bodyType
                  ? bodyTypes.find((b) => b.id === profile.bodyType)?.name
                  : "YOUR BODY PROFILE"}
              </strong>
            </div>

            {/* Sketch decorations */}
            <StarDeco size={14} color="#FF3294" style={{ position:"absolute", top:60, right:24, opacity:0.6 }}/>
            <StarDeco size={10} color="#9450D8" style={{ position:"absolute", bottom:120, left:20, opacity:0.5 }}/>
          </aside>
        </div>
      </div>
    );
  }

  /* ───────────────────────────────────────────
     AI ASSISTED BUILDER
  ─────────────────────────────────────────── */
  return (
    <div className="ba-page">
      <header className="ba-builder-header">
        <button className="ba-builder-logo" onClick={() => navigate("/")}>
          Wear<span>Wise</span>
        </button>
        <div className="ba-ai-badge">
          <span className="ba-ai-dot"/>
          AI ASSISTED ✦
        </div>
        <button className="ba-builder-exit" onClick={() => setMode(null)} title="Back to mode selection">✕</button>
      </header>

      <div className="ba-ai-layout">
        {/* ── Left ── */}
        <section className="ba-ai-content">
          <span className="ba-eyebrow">✦ AI STYLE STARTER</span>
          <h1 className="ba-step-h1">
            LET AI<br /><em>GET TO KNOW</em><br />YOUR STYLE.
          </h1>
          <p className="ba-step-desc">
            Upload a clear photo and WearWise can use it as a starting point
            for your colour, body-profile and style recommendations.
          </p>

          {/* Photo upload */}
          <label className={`ba-upload-zone${profile.photo ? " ba-upload-ready" : ""}`}>
            {profile.photo ? (
              <div className="ba-upload-preview">
                <div className="ba-upload-preview-img">
                  <img
                    src={URL.createObjectURL(profile.photo)}
                    alt="Uploaded"
                    className="ba-upload-img"
                  />
                </div>
                <div className="ba-upload-preview-info">
                  <span className="ba-upload-ready-badge">✦ PHOTO READY</span>
                  <strong>{profile.photo.name}</strong>
                  <small>{(profile.photo.size / 1024).toFixed(0)} KB</small>
                </div>
              </div>
            ) : (
              <>
                <div className="ba-upload-icon">
                  <svg viewBox="0 0 40 40" fill="none" width="36" height="36">
                    <circle cx="20" cy="20" r="19" fill="#F7EFFF" stroke="#EEDCFF" strokeWidth="1.5"/>
                    <path d="M20 12 L20 28 M12 20 L28 20" stroke="#9450D8" strokeWidth="2.5" strokeLinecap="round"/>
                  </svg>
                </div>
                <strong>DROP YOUR PHOTO</strong>
                <span>JPG / PNG · Clear full-body photo works best</span>
              </>
            )}
            <input type="file" accept="image/*" onChange={handlePhotoUpload}/>
          </label>

          {/* Colour picker */}
          <div className="ba-colour-picker-section">
            <div className="ba-cp-header">
              <div>
                <span className="ba-cp-label">YOUR COLOUR STARTING POINT</span>
                <strong className="ba-cp-value">{profile.selectedColour}</strong>
              </div>
              <div className="ba-cp-swatch" style={{ background: profile.selectedColour }}/>
            </div>
            <input
              type="color"
              className="ba-native-color"
              value={profile.selectedColour}
              onChange={(e) => setProfile({ ...profile, selectedColour: e.target.value })}
            />
            <p className="ba-cp-hint">
              Choose a colour that already feels like you — it helps AI calibrate your palette.
            </p>
          </div>

          {error && <p className="ba-error">{error}</p>}

          <button
            className="ba-btn-next ba-btn-ai-analyse"
            onClick={handleAiAnalyze}
            disabled={loading}
          >
            {loading ? (
              <><span className="ba-spinner"/> ANALYSING…</>
            ) : (
              "ANALYSE MY STYLE ✦"
            )}
          </button>

          <p className="ba-privacy-note">
            🔒 Your photo is processed privately and never stored.
          </p>
        </section>

        {/* ── Right ── */}
        <aside className="ba-ai-preview">
          <div className="ba-ai-glow"/>

          <span className="ba-preview-label">✦ YOUR STARTING AVATAR</span>

          <div className="ba-ai-stage">
            <div className="ba-ai-orb"/>
            <AvatarFigure profile={profile} bodyTypes={bodyTypes} />
            <div className="ba-ai-card">
              <span>AI READY</span>
              <strong>LET'S<br/>STYLE YOU.</strong>
            </div>
          </div>

          {/* Benefits */}
          <div className="ba-ai-benefits">
            <span>✦ COLOUR PROFILE</span>
            <span>✦ BODY ANALYSIS</span>
            <span>✦ STYLE MATCH</span>
          </div>

          {/* Sketch deco */}
          <StarDeco size={14} color="#FF3294" style={{ position:"absolute", top:60, right:28, opacity:0.6 }}/>
          <StarDeco size={10} color="#9450D8" style={{ position:"absolute", bottom:140, left:24, opacity:0.5 }}/>
        </aside>
      </div>
    </div>
  );
}

export default BuildAvatar;
