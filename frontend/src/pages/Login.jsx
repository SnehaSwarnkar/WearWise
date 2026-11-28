import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import "../App.css";
import { useAuth } from "../context/AuthContext";

function Login({ initialRole = "customer" }) {
  const navigate = useNavigate();
  const { login, sellerLogin, adminLogin } = useAuth();
  const [roleTab, setRoleTab] = useState(initialRole);
  const [form, setForm] = useState({ email: "", password: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const update = (e) =>
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));

  const switchTab = (next) => {
    setRoleTab(next);
    setError("");
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      if (roleTab === "seller") {
        await sellerLogin(form.email, form.password);
        navigate("/seller/dashboard");
      } else if (roleTab === "admin") {
        await adminLogin(form.email, form.password);
        navigate("/admin");
      } else {
        const user = await login(form.email, form.password);
        if (!user.gender) navigate("/home");
        else if (user.gender === "kids") navigate("/shop/kids");
        else if (user.gender === "men") navigate("/shop/men");
        else navigate("/shop/women");
      }
    } catch (err) {
      setError(
        err.message ||
          (roleTab === "seller"
            ? "Seller sign-in failed. Please try again."
            : roleTab === "admin"
              ? "Administrator sign-in failed. Please try again."
              : "Customer login failed. Please try again.")
      );
    } finally {
      setLoading(false);
    }
  };

  const tabMeta = {
    customer: {
      badge: "CUSTOMER PORTAL",
      badgeBg: "#d8ff3f",
      badgeColor: "#151515",
      eyebrow: "✦ CUSTOMER SIGN IN",
      subtitle: "Discover fashion, build your personal body profile, and try outfits virtually.",
      placeholder: "shopper@example.com",
      passPlaceholder: "Your password",
      cardTestId: "shopper-login-card",
      errTestId: "shopper-login-error",
      submitTestId: "shopper-login-submit",
      cta: "SIGN IN AS CUSTOMER ✦",
    },
    seller: {
      badge: "SELLER PORTAL",
      badgeBg: "#8d6bff",
      badgeColor: "#ffffff",
      eyebrow: "◆ MERCHANT WORKSPACE",
      subtitle: "Manage your products, prepare 3D & photo try-on items, and fulfill customer orders.",
      placeholder: "seller@yourbrand.studio",
      passPlaceholder: "Seller password",
      cardTestId: "seller-login-card",
      errTestId: "seller-login-error",
      submitTestId: "seller-login-submit",
      cta: "ENTER SELLER WORKSPACE ◆",
    },
    admin: {
      badge: "ADMIN CONSOLE",
      badgeBg: "#ff3d9a",
      badgeColor: "#ffffff",
      eyebrow: "■ PLATFORM GOVERNANCE",
      subtitle: "Review seller applications, moderate listings, and inspect platform operations.",
      placeholder: "admin@wearwise.com",
      passPlaceholder: "Admin password",
      cardTestId: "admin-login-card",
      errTestId: "admin-login-error",
      submitTestId: "admin-login-submit",
      cta: "SIGN IN TO ADMIN PORTAL →",
    },
  }[roleTab];

  return (
    <div className="auth-page" style={roleTab === "customer" ? undefined : { background: "#151515" }}>
      <div className="auth-shape auth-shape-purple" />
      <div className="auth-shape auth-shape-lime" />
      <div className="auth-shape auth-shape-orange" />

      <div className="auth-card" data-testid={tabMeta.cardTestId}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "18px" }}>
          <Link to="/" className="auth-logo" style={{ marginBottom: 0 }}>
            Wear<span>Wise</span>
          </Link>
          <span
            style={{
              background: tabMeta.badgeBg,
              color: tabMeta.badgeColor,
              border: "2px solid #151515",
              padding: "4px 10px",
              fontSize: "11px",
              fontWeight: 900,
              letterSpacing: "0.08em",
            }}
          >
            {tabMeta.badge}
          </span>
        </div>

        {/* Role Selector Tabs */}
        <div
          role="tablist"
          aria-label="Account role sign-in"
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(3, 1fr)",
            gap: "6px",
            marginBottom: "20px",
          }}
        >
          {[
            { id: "customer", label: "Customer" },
            { id: "seller", label: "Seller" },
            { id: "admin", label: "Admin" },
          ].map((t) => {
            const active = roleTab === t.id;
            return (
              <button
                key={t.id}
                type="button"
                role="tab"
                aria-selected={active}
                data-testid={`login-tab-${t.id}`}
                onClick={() => switchTab(t.id)}
                style={{
                  padding: "9px 8px",
                  border: "2px solid #151515",
                  background: active ? "#151515" : "#ffffff",
                  color: active ? "#d8ff3f" : "#151515",
                  fontWeight: 900,
                  fontSize: "12px",
                  letterSpacing: "0.06em",
                  textTransform: "uppercase",
                  cursor: "pointer",
                }}
              >
                {t.label}
              </button>
            );
          })}
        </div>

        <div className="auth-eyebrow">{tabMeta.eyebrow}</div>

        <h1 className="auth-title">
          LOG
          <br />
          <span>BACK IN.</span>
        </h1>

        <p className="auth-subtitle">{tabMeta.subtitle}</p>

        <form className="auth-form" onSubmit={handleSubmit} noValidate>
          <div className="auth-field">
            <label>EMAIL</label>
            <input
              type="email"
              name="email"
              value={form.email}
              onChange={update}
              placeholder={tabMeta.placeholder}
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
              placeholder={tabMeta.passPlaceholder}
              required
              autoComplete="current-password"
            />
          </div>

          {error && (
            <p className="auth-error" data-testid={tabMeta.errTestId}>
              {error}
            </p>
          )}

          <button className="auth-submit" type="submit" disabled={loading} data-testid={tabMeta.submitTestId}>
            {loading ? "Signing in…" : tabMeta.cta}
          </button>
        </form>

        {roleTab === "customer" && (
          <p className="auth-switch">
            New to WearWise? <Link to="/register">Create a customer account →</Link>
          </p>
        )}
        {roleTab === "seller" && (
          <p className="auth-switch">
            Want to sell on WearWise? <Link to="/seller/register">Submit seller application →</Link>
          </p>
        )}
      </div>
    </div>
  );
}

export default Login;
