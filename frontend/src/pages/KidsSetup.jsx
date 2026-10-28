import { useState } from "react";
import { useNavigate } from "react-router-dom";
import "../App.css";
import { updateProfile } from "../api/auth";
import { useAuth } from "../context/AuthContext";

const AGE_GROUPS = [
  { id: "2-5",   label: "2 – 5 yrs",  desc: "Toddler & early childhood" },
  { id: "6-10",  label: "6 – 10 yrs", desc: "Primary school age" },
  { id: "11-14", label: "11 – 14 yrs", desc: "Pre-teen & teen" },
];

function KidsSetup() {
  const navigate = useNavigate();
  const { setUser } = useAuth();
  const [kidsGender, setKidsGender] = useState(null);
  const [ageGroup, setAgeGroup] = useState(null);
  const [saving, setSaving] = useState(false);

  const handleContinue = async () => {
    if (!kidsGender || !ageGroup) return;
    setSaving(true);
    try {
      const updated = await updateProfile({ kidsGender, ageGroup, onboardingDone: true });
      setUser(updated);
      navigate("/kids-shop");
    } catch {
      setSaving(false);
    }
  };

  return (
    <div className="setup-page">
      <div className="setup-shape setup-shape-lime" />
      <div className="setup-shape setup-shape-orange" />

      <div className="setup-inner">
        <div className="setup-eyebrow">✦ STEP 02 — KIDS SECTION</div>

        <h1 className="setup-title">
          LET'S SET UP
          <br />
          <span>THE KIDS.</span>
        </h1>

        <p className="setup-subtitle">
          Tell us who you're shopping for and their age group so we can
          show the right sizes and styles.
        </p>

        {/* GENDER */}
        <div className="setup-section-label">SHOPPING FOR</div>
        <div className="kids-gender-row">
          {[
            { id: "boys",  label: "BOYS",  icon: "◉", color: "var(--purple)" },
            { id: "girls", label: "GIRLS", icon: "✦", color: "var(--pink)" },
          ].map((opt) => (
            <button
              key={opt.id}
              className={`kids-gender-btn ${kidsGender === opt.id ? "kids-gender-active" : ""}`}
              onClick={() => setKidsGender(opt.id)}
              style={kidsGender === opt.id ? {
                background: opt.color,
                color: "white",
                borderColor: opt.color,
              } : {}}
            >
              <span>{opt.icon}</span>
              {opt.label}
            </button>
          ))}
        </div>

        {/* AGE */}
        <div className="setup-section-label" style={{ marginTop: 36 }}>AGE GROUP</div>
        <div className="age-grid">
          {AGE_GROUPS.map((ag) => (
            <button
              key={ag.id}
              className={`age-card ${ageGroup === ag.id ? "age-card-active" : ""}`}
              onClick={() => setAgeGroup(ag.id)}
            >
              <strong>{ag.label}</strong>
              <small>{ag.desc}</small>
            </button>
          ))}
        </div>

        <button
          className="setup-continue"
          disabled={!kidsGender || !ageGroup || saving}
          onClick={handleContinue}
        >
          {saving ? "Saving…" : "ENTER KIDS' SHOP →"}
        </button>
      </div>
    </div>
  );
}

export default KidsSetup;
