import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import "../App.css";
import { useAuth } from "../context/AuthContext";

function Login() {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [form, setForm] = useState({ email: "", password: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const update = (e) =>
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const user = await login(form.email, form.password);
      if (!user.gender) navigate("/explore");
      else if (user.gender === "kids") navigate("/kids-shop");
      else if (user.gender === "men") navigate("/men-shop");
      else navigate("/women-shop");
    } catch (err) {
      setError(err.message || "Shopper login failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-shape auth-shape-purple" />
      <div className="auth-shape auth-shape-lime" />
      <div className="auth-shape auth-shape-orange" />

      <div className="auth-card" data-testid="shopper-login-card">
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
            SHOPPER PORTAL
          </span>
        </div>

        <div className="auth-eyebrow">✦ SHOPPER LOGIN</div>

        <h1 className="auth-title">
          LOG
          <br />
          <span>BACK IN.</span>
        </h1>

        <p className="auth-subtitle">
          Discover fashion, find your fit and shop with WearWise.
        </p>

        <form className="auth-form" onSubmit={handleSubmit} noValidate>
          <div className="auth-field">
            <label>EMAIL</label>
            <input
              type="email"
              name="email"
              value={form.email}
              onChange={update}
              placeholder="shopper@example.com"
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
              placeholder="Your password"
              required
              autoComplete="current-password"
            />
          </div>

          {error && <p className="auth-error" data-testid="shopper-login-error">{error}</p>}

          <button className="auth-submit" type="submit" disabled={loading} data-testid="shopper-login-submit">
            {loading ? "Signing in…" : "SIGN IN AS SHOPPER ✦"}
          </button>
        </form>

        <p className="auth-switch">
          New to WearWise?{" "}
          <Link to="/register">Create a shopper account →</Link>
        </p>
        <p className="auth-switch" style={{ marginTop: "8px", fontSize: "12px" }}>
          Are you a merchant?{" "}
          <Link to="/seller/login" style={{ color: "#8d6bff" }}>Switch to Seller Login →</Link>
        </p>
      </div>
    </div>
  );
}

export default Login;
