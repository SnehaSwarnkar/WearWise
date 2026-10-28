import { useState } from "react";
import { useNavigate } from "react-router-dom";
import "../App.css";
import { updateProfile } from "../api/auth";
import { useAuth } from "../context/AuthContext";

const BODY_TYPES = [
  { id: "hourglass",         label: "Hourglass",          desc: "Balanced shoulders & hips, defined waist" },
  { id: "pear",              label: "Pear",               desc: "Hips are naturally more prominent" },
  { id: "rectangle",        label: "Rectangle",          desc: "Straight, balanced silhouette" },
  { id: "apple",            label: "Apple",              desc: "Fuller through the middle" },
  { id: "inverted-triangle", label: "Inverted Triangle",  desc: "Shoulders are naturally more prominent" },
  { id: "plus",             label: "Plus Size",          desc: "Fuller, curvier silhouette" },
];

function WomenSetup() {
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
      navigate("/women-shop");
    } catch {
      setSaving(false);
    }
  };

  return (
    <div className="setup-page">
      <div className="setup-shape setup-shape-pink" />
      <div className="setup-shape setup-shape-lime" />

      <div className="setup-inner">
        <div className="setup-eyebrow">✦ STEP 02 — WOMEN'S BODY PROFILE</div>

        <h1 className="setup-title">
          YOUR BODY.
          <br />
          <span>YOUR FIT.</span>
        </h1>

        <p className="setup-subtitle">
          Choose the silhouette closest to yours. We use this to recommend
          cuts, drapes and fits made for your shape.
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
          {saving ? "Saving…" : "ENTER WOMEN'S SHOP →"}
        </button>
      </div>
    </div>
  );
}

export default WomenSetup;
