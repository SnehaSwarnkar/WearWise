import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import "../App.css";
import { login } from "../api/auth";
import { useAuth } from "../context/AuthContext";

function Login() {
  const navigate = useNavigate();
  const { setUser } = useAuth();
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
      setUser(user);
      // Route based on onboarding state
      if (!user.gender) navigate("/select-gender");
      else if (user.gender === "kids") navigate("/kids-shop");
      else if (user.gender === "men")  navigate("/men-shop");
      else                              navigate("/women-shop");
    } catch (err) {
      setError(err.message || "Login failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      {/* DECORATIVE SHAPES */}
      <div className="auth-shape auth-shape-purple" />
      <div className="auth-shape auth-shape-lime" />
      <div className="auth-shape auth-shape-orange" />

      <div className="auth-card">
        {/* LOGO */}
        <Link to="/" className="auth-logo">
          Wear<span>Wise</span>
        </Link>

        <div className="auth-eyebrow">✦ WELCOME BACK</div>

        <h1 className="auth-title">
          LOG
          <br />
          <span>BACK IN.</span>
        </h1>

        <p className="auth-subtitle">
          Your style profile, wardrobe and saved looks are waiting.
        </p>

        <form className="auth-form" onSubmit={handleSubmit} noValidate>
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
              placeholder="Your password"
              required
              autoComplete="current-password"
            />
          </div>

          {error && <p className="auth-error">{error}</p>}

          <button className="auth-submit" type="submit" disabled={loading}>
            {loading ? "Signing in…" : "SIGN IN ✦"}
          </button>
        </form>

        <p className="auth-switch">
          New to WearWise?{" "}
          <Link to="/signup">Create an account →</Link>
        </p>
      </div>
    </div>
  );
}

export default Login;
