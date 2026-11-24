import { useState } from "react";
import { useNavigate } from "react-router-dom";
import "../App.css";
import { updateProfile } from "../api/auth";
import { useAuth } from "../context/AuthContext";

const OPTIONS = [
  {
    id: "men",
    label: "MEN",
    sub: "Menswear, suits, kurtas & more",
    icon: "◉",
    color: "var(--purple)",
    bg: "var(--black)",
    dest: "/men-setup",
  },
  {
    id: "women",
    label: "WOMEN",
    sub: "Dresses, sarees, western & ethnic",
    icon: "✦",
    color: "var(--pink)",
    bg: "var(--cream)",
    dest: "/women-setup",
  },
  {
    id: "kids",
    label: "KIDS",
    sub: "Boys & girls, ages 2–14",
    icon: "♧",
    color: "var(--lime)",
    bg: "var(--black)",
    dest: "/kids-setup",
  },
];

function GenderSelect() {
  const navigate = useNavigate();
  const { setUser } = useAuth();
  const [selected, setSelected] = useState(null);
  const [saving, setSaving] = useState(false);

  const handleContinue = async () => {
    if (!selected) return;
    setSaving(true);
    try {
      const updated = await updateProfile({ gender: selected });
      setUser(updated);
      navigate(OPTIONS.find((o) => o.id === selected).dest);
    } catch {
      setSaving(false);
    }
  };

  return (
    <div className="gender-page">
      {/* BG SHAPES */}
      <div className="gender-shape gender-shape-1" />
      <div className="gender-shape gender-shape-2" />

      <div className="gender-inner">
        <div className="gender-eyebrow">✦ STEP 01 — WHO ARE YOU SHOPPING FOR?</div>

        <h1 className="gender-title">
          CHOOSE
          <br />
          <span>YOUR</span>
          <br />
          SECTION.
        </h1>

        <p className="gender-subtitle">
          We'll personalise your experience — styles, sizing and
          recommendations — based on your selection.
        </p>

        <div className="gender-grid">
          {OPTIONS.map((opt) => (
            <button
              key={opt.id}
              className={`gender-card ${selected === opt.id ? "gender-card-selected" : ""}`}
              onClick={() => setSelected(opt.id)}
              style={selected === opt.id ? { borderColor: opt.color, boxShadow: `8px 8px 0 ${opt.color}` } : {}}
            >
              <div className="gender-card-icon" style={{ color: opt.color }}>
                {opt.icon}
              </div>
              <h2>{opt.label}</h2>
              <p>{opt.sub}</p>
              {selected === opt.id && (
                <div className="gender-selected-mark" style={{ background: opt.color }}>
                  SELECTED ✦
                </div>
              )}
            </button>
          ))}
        </div>

        <button
          className="gender-continue"
          disabled={!selected || saving}
          onClick={handleContinue}
        >
          {saving ? "Saving…" : "CONTINUE →"}
        </button>
      </div>
    </div>
  );
}

export default GenderSelect;
