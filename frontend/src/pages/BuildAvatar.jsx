import { useState } from "react";
import { useNavigate } from "react-router-dom";
import "../App.css";
import Header from "./Header";
import { saveAvatarProfile, analyzeAvatarPhoto } from "../api/avatar";

function BuildAvatar() {
    
  const navigate = useNavigate();

  const [mode, setMode] = useState(null);
  const [step, setStep] = useState(1);

  const [profile, setProfile] = useState({
    colour: "",
    bodyType: "",
    fit: "",
    styles: [],
    selectedColour: "#ff3b91",
    photo: null,
  });

  const bodyTypes = [
    {
      id: "hourglass",
      name: "Hourglass",
      description: "Balanced shoulders and hips",
    },
    {
      id: "pear",
      name: "Pear",
      description: "Hips are naturally more prominent",
    },
    {
      id: "rectangle",
      name: "Rectangle",
      description: "A straighter, balanced silhouette",
    },
    {
      id: "apple",
      name: "Apple",
      description: "More fullness through the middle",
    },
    {
      id: "inverted-triangle",
      name: "Inverted Triangle",
      description: "Shoulders are naturally more prominent",
    },
    {
      id: "athletic",
      name: "Athletic",
      description: "Defined, sporty silhouette",
    },
  ];

  const styles = [
    "Minimal",
    "Streetwear",
    "Casual",
    "Elegant",
    "Vintage",
    "Sporty",
    "Edgy",
    "Boho",
  ];

  const handleStyleToggle = (style) => {
    setProfile((prev) => ({
      ...prev,
      styles: prev.styles.includes(style)
        ? prev.styles.filter((item) => item !== style)
        : [...prev.styles, style],
    }));
  };

  const handlePhotoUpload = (event) => {
    const file = event.target.files?.[0];

    if (!file) return;

    setProfile((prev) => ({
      ...prev,
      photo: file,
    }));
  };

  const handleFinish = async () => {
    try {
      await saveAvatarProfile({ mode: mode || "manual", ...profile });
    } catch {
      // Non-blocking — still navigate
    }
    navigate("/style-analysis", {
      state: { avatarProfile: profile },
    });
  };

  const handleAiAnalyze = async () => {
    if (!profile.photo) {
      handleFinish();
      return;
    }
    try {
      const result = await analyzeAvatarPhoto(profile.photo, profile.selectedColour);
      const mergedProfile = { ...profile, ...result };
      await saveAvatarProfile({ mode: "ai", ...mergedProfile });
      navigate("/style-analysis", { state: { avatarProfile: mergedProfile } });
    } catch {
      handleFinish();
    }
  };

  /* --------------------------------
     MODE SELECTION
  -------------------------------- */

  if (!mode) {
    return (
      <main className="avatar-builder-page">
        <Header />
        <div className="avatar-bg-shape avatar-bg-pink"></div>
        <div className="avatar-bg-shape avatar-bg-purple"></div>
        <div className="avatar-bg-shape avatar-bg-orange"></div>
        <div className="avatar-bg-shape avatar-bg-lime"></div>

        

        <section className="avatar-intro">
          <div className="avatar-eyebrow">
            ✦ YOUR STYLE IDENTITY
          </div>

          <h1>
            BUILD YOUR
            <br />
            <span>WEARWISE</span>
            <br />
            AVATAR.
          </h1>

          <p>
            Create a style profile that feels like you.
            Choose everything yourself or let AI help
            discover your starting point.
          </p>
        </section>

        <section className="avatar-mode-grid">
          <button
            className="avatar-mode-card manual-card"
            onClick={() => setMode("manual")}
          >
            <div className="mode-number">01</div>

            <div className="mode-icon">
              ✦
            </div>

            <h2>BUILD MANUALLY</h2>

            <p>
              I know my style. Let me choose my
              colours, body profile and fashion
              preferences.
            </p>

            <span className="mode-arrow">
              START BUILDING →
            </span>
          </button>

          <button
            className="avatar-mode-card ai-card"
            onClick={() => setMode("ai")}
          >
            <div className="mode-number">02</div>

            <div className="mode-icon">
              AI
            </div>

            <h2>AI ASSISTED</h2>

            <p>
              Upload a photo and let WearWise
              create a personalised starting
              profile for you.
            </p>

            <span className="mode-arrow">
              LET AI HELP →
            </span>
          </button>
        </section>

        <div className="avatar-floating-label label-one">
          ✦ COLOUR
        </div>

        <div className="avatar-floating-label label-two">
          BODY FIT
        </div>

        <div className="avatar-floating-label label-three">
          YOUR VIBE
        </div>
      </main>
    );
  }

  /* --------------------------------
     MANUAL BUILDER
  -------------------------------- */

  if (mode === "manual") {
    return (
      <main className="avatar-builder-page manual-builder">

        <header className="avatar-builder-header">
          <button
            className="avatar-logo"
            onClick={() => navigate("/")}
          >
            Wear<span>Wise</span>
          </button>

          <div className="avatar-progress">
            STEP {step} / 03
          </div>
        </header>

        <div className="builder-layout">

          <section className="builder-content">

            {step === 1 && (
              <>
                <div className="avatar-eyebrow">
                  ✦ STEP 01 — COLOUR PROFILE
                </div>

                <h1>
                  WHAT
                  <br />
                  <span>COLOURS</span>
                  <br />
                  FEEL LIKE YOU?
                </h1>

                <p className="builder-description">
                  Pick the colour direction that feels
                  most natural to you. You don't need
                  to know your exact colour season.
                </p>

                <div className="choice-grid">
                  {[
                    ["warm", "WARM", "Peach, coral, gold & earthy tones"],
                    ["cool", "COOL", "Pink, blue, lavender & icy tones"],
                    ["neutral", "NEUTRAL", "Balanced shades across the spectrum"],
                    ["bold", "BOLD", "I love colour. Give me everything."],
                  ].map(([id, title, description]) => (
                    <button
                      key={id}
                      className={`choice-card ${
                        profile.colour === id ? "selected" : ""
                      }`}
                      onClick={() =>
                        setProfile({
                          ...profile,
                          colour: id,
                        })
                      }
                    >
                      <div className={`colour-dot ${id}`}></div>

                      <strong>{title}</strong>

                      <small>{description}</small>
                    </button>
                  ))}
                </div>
              </>
            )}

            {step === 2 && (
              <>
                <div className="avatar-eyebrow">
                  ✦ STEP 02 — BODY PROFILE
                </div>

                <h1>
                  YOUR BODY.
                  <br />
                  <span>YOUR FIT.</span>
                </h1>

                <p className="builder-description">
                  Choose the silhouette that feels closest
                  to you. This helps WearWise recommend
                  proportions and fits — it doesn't define
                  what you should wear.
                </p>

                <div className="body-type-grid">
                  {bodyTypes.map((body) => (
                    <button
                      key={body.id}
                      className={`body-type-card ${
                        profile.bodyType === body.id
                          ? "selected"
                          : ""
                      }`}
                      onClick={() =>
                        setProfile({
                          ...profile,
                          bodyType: body.id,
                        })
                      }
                    >
                      <div className={`body-avatar ${body.id}`}>
                        <div className="body-avatar-head"></div>
                        <div className="body-avatar-body"></div>
                      </div>

                      <div>
                        <strong>{body.name}</strong>
                        <small>{body.description}</small>
                      </div>
                    </button>
                  ))}
                </div>

                <div className="fit-selection">
                  <h3>HOW DO YOU LIKE YOUR CLOTHES TO FIT?</h3>

                  <div className="fit-buttons">
                    {["Fitted", "Relaxed", "Oversized", "Mixed"].map(
                      (fit) => (
                        <button
                          key={fit}
                          className={
                            profile.fit === fit
                              ? "selected"
                              : ""
                          }
                          onClick={() =>
                            setProfile({
                              ...profile,
                              fit,
                            })
                          }
                        >
                          {fit}
                        </button>
                      )
                    )}
                  </div>
                </div>
              </>
            )}

            {step === 3 && (
              <>
                <div className="avatar-eyebrow">
                  ✦ STEP 03 — YOUR STYLE
                </div>

                <h1>
                  WHAT'S
                  <br />
                  <span>YOUR VIBE?</span>
                </h1>

                <p className="builder-description">
                  Pick as many as you want. Your style
                  doesn't have to fit into one box.
                </p>

                <div className="style-chip-grid">
                  {styles.map((style) => (
                    <button
                      key={style}
                      className={
                        profile.styles.includes(style)
                          ? "selected"
                          : ""
                      }
                      onClick={() =>
                        handleStyleToggle(style)
                      }
                    >
                      ✦ {style}
                    </button>
                  ))}
                </div>

                <div className="avatar-final-preview">
                  <div className="mini-avatar">
                    <div className="mini-head"></div>
                    <div className="mini-body"></div>
                  </div>

                  <div>
                    <span>YOUR WEARWISE ID</span>
                    <strong>
                      {profile.styles.length
                        ? profile.styles.join(" × ")
                        : "STYLE IN PROGRESS"}
                    </strong>
                  </div>
                </div>
              </>
            )}

            <div className="builder-navigation">
              {step > 1 && (
                <button
                  className="back-button"
                  onClick={() => setStep(step - 1)}
                >
                  ← BACK
                </button>
              )}

              {step < 3 ? (
                <button
                  className="next-button"
                  onClick={() => setStep(step + 1)}
                >
                  CONTINUE →
                </button>
              ) : (
                <button
                  className="next-button"
                  onClick={handleFinish}
                >
                  CREATE MY AVATAR ✦
                </button>
              )}
            </div>
          </section>

          <aside className="avatar-preview-panel">

            <div className="preview-label">
              ✦ LIVE AVATAR
            </div>

            <div className="avatar-stage">

              <div className="avatar-stage-circle"></div>

              <div className="large-avatar">
                <div className="large-avatar-head"></div>
                <div className="large-avatar-hair"></div>
                <div className="large-avatar-body"></div>
                <div className="large-avatar-legs"></div>
              </div>

              <div className="preview-bubble">
                YOU
                <br />
                LOOK
                <br />
                GOOD ✦
              </div>
            </div>

            <div className="preview-info">
              <span>WEARWISE AVATAR</span>
              <strong>
                {profile.bodyType
                  ? bodyTypes.find(
                      (item) =>
                        item.id === profile.bodyType
                    )?.name
                  : "YOUR BODY PROFILE"}
              </strong>
            </div>

          </aside>
        </div>
      </main>
    );
  }

  /* --------------------------------
     AI ASSISTED BUILDER
  -------------------------------- */

  return (
    <main className="avatar-builder-page ai-builder">

      <header className="avatar-builder-header">
        <button
          className="avatar-logo"
          onClick={() => navigate("/")}
        >
          Wear<span>Wise</span>
        </button>

        <div className="avatar-progress">
          AI ASSISTED ✦
        </div>
      </header>

      <div className="ai-builder-layout">

        <section className="ai-builder-content">

          <div className="avatar-eyebrow">
            ✦ AI STYLE STARTER
          </div>

          <h1>
            LET AI
            <br />
            <span>GET TO KNOW</span>
            <br />
            YOUR STYLE.
          </h1>

          <p className="builder-description">
            Upload a clear photo and WearWise can use
            it as a starting point for your colour,
            body-profile and style recommendations.
          </p>

          <label className="ai-upload-box">

            {profile.photo ? (
              <div className="uploaded-photo-name">
                ✦ {profile.photo.name}
              </div>
            ) : (
              <>
                <div className="upload-plus">+</div>

                <strong>
                  DROP YOUR PHOTO
                </strong>

                <span>
                  JPG / PNG · Clear full-body photo works best
                </span>
              </>
            )}

            <input
              type="file"
              accept="image/*"
              onChange={handlePhotoUpload}
            />
          </label>

          <div className="ai-colour-section">
            
            

            <div className="section-heading">
              <span>YOUR COLOUR STARTING POINT</span>
              <strong>
                {profile.selectedColour}
              </strong>
            </div>

            <div className="colour-picker">
              <div className="picker-cursor"></div>
            </div>

            <input
              type="color"
              value={profile.selectedColour}
              onChange={(e) =>
                setProfile({
                  ...profile,
                  selectedColour: e.target.value,
                })
              }
            />

            <p>
              Drag through the palette or choose a
              colour that already feels like you.
            </p>
          </div>

          <button
            className="next-button ai-analyze-button"
            onClick={handleAiAnalyze}
          >
            ANALYSE MY STYLE ✦
          </button>

        </section>

        <aside className="ai-avatar-preview">

          <div className="preview-label">
            ✦ YOUR STARTING AVATAR
          </div>

          <div className="ai-avatar-stage">

            <div className="neon-orb"></div>

            <div className="large-avatar">
              <div className="large-avatar-head"></div>
              <div className="large-avatar-hair"></div>
              <div className="large-avatar-body"></div>
              <div className="large-avatar-legs"></div>
            </div>

            <div className="ai-floating-card">
              <span>AI READY</span>
              <strong>
                LET'S
                <br />
                STYLE YOU.
              </strong>
            </div>

          </div>

        </aside>

      </div>
    </main>
  );
}

export default BuildAvatar;