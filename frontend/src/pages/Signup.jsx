import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import "../App.css";
import { useAuth } from "../context/AuthContext";

function Signup() {
  const navigate = useNavigate();
  const { signup } = useAuth();
  const [form, setForm] = useState({ name: "", email: "", password: "", confirm: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const update = (e) =>
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    if (form.password !== form.confirm) {
      setError("Passwords do not match.");
      return;
    }
    if (form.password.length < 6) {
      setError("Password must be at least 6 characters.");
      return;
    }
    setLoading(true);
    try {
      await signup(form.name, form.email, form.password);
      navigate("/select-gender");
    } catch (err) {
      setError(err.message || "Signup failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-shape auth-shape-pink" />
      <div className="auth-shape auth-shape-lime" />
      <div className="auth-shape auth-shape-purple" />

      <div className="auth-card" data-testid="shopper-register-card">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "22px" }}>
          <Link to="/" className="auth-logo" style={{ marginBottom: 0 }}>
            Wear<span>Wise</span>
          </Link>
          <span
            style={{
              background: "#d8ff3f",
              color: "#151515",
              border: "2px solid #151515",
              padding: "4px 10px",
              fontSize: "11px",
              fontWeight: 900,
              letterSpacing: "0.08em",
            }}
          >
            SHOPPER REGISTRATION
          </span>
        </div>

        <div className="auth-eyebrow">✦ JOIN WEARWISE</div>

        <h1 className="auth-title">
          START
          <br />
          <span>YOUR STYLE.</span>
        </h1>

        <p className="auth-subtitle">
          Create a shopper account and discover fashion that actually fits who you are.
        </p>

        <form className="auth-form" onSubmit={handleSubmit} noValidate>
          <div className="auth-field">
            <label>YOUR NAME</label>
            <input
              type="text"
              name="name"
              value={form.name}
              onChange={update}
              placeholder="First name"
              required
              autoComplete="given-name"
            />
          </div>

          <div className="auth-field">
            <label>EMAIL</label>
            <input
              type="email"
              name="email"
              value={form.email}
              onChange={update}
              placeholder="you@example.com"
              required
              autoComplete="email"
            />
          </div>

          <div className="auth-field">
            <label>PASSWORD</label>
            <input
              type="password"
              name="password"
              value={form.password}
              onChange={update}
              placeholder="Min. 6 characters"
              required
              autoComplete="new-password"
            />
          </div>

          <div className="auth-field">
            <label>CONFIRM PASSWORD</label>
            <input
              type="password"
              name="confirm"
              value={form.confirm}
              onChange={update}
              placeholder="Repeat your password"
              required
              autoComplete="new-password"
            />
          </div>

          {error && <p className="auth-error">{error}</p>}

          <button className="auth-submit" type="submit" disabled={loading}>
            {loading ? "Creating account…" : "CREATE SHOPPER ACCOUNT ✦"}
          </button>
        </form>

        <p className="auth-switch">
          Already have a shopper account?{" "}
          <Link to="/login">Sign in →</Link>
        </p>
        <p className="auth-switch" style={{ marginTop: "8px", fontSize: "12px" }}>
          Selling on WearWise?{" "}
          <Link to="/seller/login" style={{ color: "#8d6bff" }}>Seller Portal →</Link>
        </p>
      </div>
    </div>
  );
}

export default Signup;
