import { useState } from "react";
import { useNavigate } from "react-router-dom";
import "../App.css";
import { updateProfile } from "../api/auth";
import { useAuth } from "../context/AuthContext";

const BODY_TYPES = [
  { id: "athletic",   label: "Athletic",          desc: "Defined, muscular build" },
  { id: "slim",       label: "Slim",               desc: "Lean, narrow frame" },
  { id: "regular",   label: "Regular",            desc: "Average balanced build" },
  { id: "broad",     label: "Broad / Stocky",     desc: "Wide shoulders, solid frame" },
  { id: "tall",      label: "Tall & Lean",        desc: "Height above average, slim" },
  { id: "plus",      label: "Plus Size",          desc: "Fuller, broader silhouette" },
];

function MenSetup() {
  const navigate = useNavigate();
  const { setUser } = useAuth();
  const [bodyType, setBodyType] = useState(null);
  const [saving, setSaving] = useState(false);

  const handleContinue = async () => {
    if (!bodyType) return;
    setSaving(true);
    try {
      const updated = await updateProfile({ bodyType, onboardingDone: true });
      setUser(updated);
      navigate("/men-shop");
    } catch {
      setSaving(false);
    }
  };

  return (
    <div className="setup-page">
      <div className="setup-shape setup-shape-purple" />
      <div className="setup-shape setup-shape-lime" />

      <div className="setup-inner">
        <div className="setup-eyebrow">✦ STEP 02 — MEN'S BODY PROFILE</div>

        <h1 className="setup-title">
          YOUR BODY.
          <br />
          <span>YOUR FIT.</span>
        </h1>

        <p className="setup-subtitle">
          Choose the silhouette closest to yours. This helps us recommend
          better cuts and fits — not define what you should wear.
        </p>

        <div className="setup-grid">
          {BODY_TYPES.map((bt) => (
            <button
              key={bt.id}
              className={`setup-card ${bodyType === bt.id ? "setup-card-active" : ""}`}
              onClick={() => setBodyType(bt.id)}
            >
              <div className="setup-avatar-icon">
                <div className="setup-avatar-head" />
                <div className={`setup-avatar-body setup-body-${bt.id}`} />
              </div>
              <strong>{bt.label}</strong>
              <small>{bt.desc}</small>
            </button>
          ))}
        </div>

        <button
          className="setup-continue"
          disabled={!bodyType || saving}
          onClick={handleContinue}
        >
          {saving ? "Saving…" : "ENTER MEN'S SHOP →"}
        </button>
      </div>
    </div>
  );
}

export default MenSetup;
