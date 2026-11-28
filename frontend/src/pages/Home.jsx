import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import "../App.css";
import Header from "./Header";
import { fetchProducts, fetchRecommendations } from "../api/products";

const SECTIONS = [
  {
    key: "women",
    title: "Women",
    subtitle: "Tailored layers, everyday tops, denim & dresses",
    to: "/shop/women",
    accent: "#ff3d9a",
  },
  {
    key: "men",
    title: "Men",
    subtitle: "Structured shirts, knit tees, chinos & outerwear",
    to: "/shop/men",
    accent: "#8d6bff",
  },
  {
    key: "kids",
    title: "Kids",
    subtitle: "Durable cotton essentials, sets & easy layers",
    to: "/shop/kids",
    accent: "#d8ff3f",
  },
];

function ProductTile({ item }) {
  const linkTo = item.sku ? `/product/${encodeURIComponent(item.sku)}` : `/shop`;
  const price = Number(item.price || 0);
  const colors = Array.isArray(item.colors) ? item.colors.slice(0, 4) : [];

  return (
    <Link
      to={linkTo}
      style={{
        textDecoration: "none",
        color: "#151515",
        background: "#ffffff",
        border: "2.5px solid #151515",
        boxShadow: "5px 5px 0 #151515",
        display: "flex",
        flexDirection: "column",
        overflow: "hidden",
      }}
    >
      <div style={{ position: "relative", aspectRatio: "4 / 5", background: "#f3ece4", overflow: "hidden" }}>
        {item.image ? (
          <img
            src={item.image}
            alt={item.name}
            style={{ width: "100%", height: "100%", objectFit: "cover", display: "block" }}
          />
        ) : (
          <div style={{ padding: "24px", fontSize: "13px", color: "#6b7280" }}>Product preview</div>
        )}
        {item.gender && (
          <span
            style={{
              position: "absolute",
              top: "10px",
              left: "10px",
              background: "#151515",
              color: "#fff8f1",
              padding: "3px 8px",
              fontSize: "10px",
              fontWeight: 900,
              textTransform: "uppercase",
              letterSpacing: "0.06em",
            }}
          >
            {item.gender}
          </span>
        )}
      </div>
      <div style={{ padding: "14px 14px 16px", display: "flex", flexDirection: "column", gap: "6px", flex: 1 }}>
        <div style={{ fontSize: "11px", fontWeight: 800, color: "#6b7280", textTransform: "uppercase" }}>
          {item.seller_name || item.brand || "WearWise Edit"} · {item.category}
        </div>
        <div style={{ fontSize: "15px", fontWeight: 900, lineHeight: 1.25 }}>{item.name}</div>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginTop: "auto", paddingTop: "6px" }}>
          <strong style={{ fontSize: "15px" }}>₹{price.toLocaleString()}</strong>
          {colors.length > 0 && (
            <div style={{ display: "flex", gap: "4px" }}>
              {colors.map((c, idx) => (
                <span
                  key={`${c}-${idx}`}
                  style={{
                    width: "12px",
                    height: "12px",
                    borderRadius: "50%",
                    background: c.startsWith("#") ? c : "#d6d3d1",
                    border: "1px solid #151515",
                  }}
                />
              ))}
            </div>
          )}
        </div>
      </div>
    </Link>
  );
}

function Home() {
  const [newArrivals, setNewArrivals] = useState([]);
  const [popular, setPopular] = useState([]);
  const [recommended, setRecommended] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let alive = true;
    Promise.all([
      fetchProducts(null, false, { sort: "newest" }).catch(() => []),
      fetchProducts(null, false, { sort: "popular" }).catch(() => []),
      fetchRecommendations(null, 4).catch(() => ({ items: [] })),
    ]).then(([newest, pop, rec]) => {
      if (!alive) return;
      setNewArrivals(Array.isArray(newest) ? newest.slice(0, 4) : []);
      setPopular(Array.isArray(pop) ? pop.slice(0, 4) : []);
      setRecommended(Array.isArray(rec?.items) ? rec.items.slice(0, 4) : []);
      setLoading(false);
    });
    return () => {
      alive = false;
    };
  }, []);

  return (
    <div className="app" style={{ background: "#fff8f1", color: "#151515", minHeight: "100vh" }}>
      <Header />

      {/* HERO SECTION */}
      <section
        style={{
          maxWidth: "1280px",
          margin: "0 auto",
          padding: "42px 24px 36px",
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))",
          gap: "28px",
          alignItems: "center",
        }}
      >
        <div>
          <span
            style={{
              display: "inline-block",
              background: "#d8ff3f",
              border: "2px solid #151515",
              padding: "4px 12px",
              fontSize: "11px",
              fontWeight: 900,
              letterSpacing: "0.08em",
              marginBottom: "16px",
            }}
          >
            WEARWISE PERSONAL FIT MARKETPLACE
          </span>
          <h1
            style={{
              fontFamily: '"Archivo Black", sans-serif',
              fontSize: "clamp(38px, 5vw, 62px)",
              lineHeight: 0.96,
              letterSpacing: "-2px",
              margin: "0 0 16px",
            }}
          >
            SHOP CLOTHES
            <br />
            <span style={{ color: "#ff3d9a" }}>TAILORED TO YOU.</span>
          </h1>
          <p style={{ fontSize: "16px", lineHeight: 1.6, color: "#3b3e49", maxWidth: "520px", margin: "0 0 24px" }}>
            Browse curated collections across Men, Women, and Kids, build your personal 3D avatar in minutes, and preview how your size fits before checking out.
          </p>
          <div style={{ display: "flex", gap: "12px", flexWrap: "wrap" }}>
            <Link
              to="/avatar/create"
              data-testid="home-create-avatar-cta"
              className="main-btn"
              style={{ textDecoration: "none" }}
            >
              Create My Avatar →
            </Link>
            <Link
              to="/shop"
              data-testid="home-shop-cta"
              className="outline-btn"
              style={{ textDecoration: "none" }}
            >
              Explore Clothing
            </Link>
          </div>
        </div>

        {/* Visual Editorial Feature Card */}
        <div
          style={{
            background: "#151515",
            color: "#fff8f1",
            border: "3px solid #151515",
            boxShadow: "12px 12px 0 #d8ff3f",
            padding: "28px",
            display: "flex",
            flexDirection: "column",
            gap: "18px",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", fontSize: "11px", fontWeight: 800, letterSpacing: "0.08em", color: "#d8ff3f" }}>
            <span>VIRTUAL FITTING ROOM</span>
            <span>NEW SEASON</span>
          </div>
          <h2 style={{ fontFamily: '"Playfair Display", serif', fontSize: "32px", fontStyle: "italic", margin: 0, lineHeight: 1.15 }}>
            Your body, your proportions, less guesswork at checkout.
          </h2>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "10px" }}>
            {[
              { step: "01", title: "Build Avatar", desc: "Simple height & shape guide" },
              { step: "02", title: "Check Fit", desc: "Clear S / M / L size comfort" },
              { step: "03", title: "Shop Confidently", desc: "Save favorites or order" },
            ].map((s) => (
              <div key={s.step} style={{ border: "1.5px solid rgba(255,248,241,0.3)", padding: "12px" }}>
                <div style={{ fontSize: "11px", fontWeight: 900, color: "#ff3d9a" }}>{s.step}</div>
                <div style={{ fontSize: "13px", fontWeight: 800, marginTop: "4px" }}>{s.title}</div>
                <div style={{ fontSize: "11px", color: "#d1d5db", marginTop: "3px" }}>{s.desc}</div>
              </div>
            ))}
          </div>
          <Link
            to="/try-on"
            style={{
              alignSelf: "flex-start",
              background: "#ff3d9a",
              color: "#ffffff",
              padding: "10px 18px",
              fontWeight: 900,
              fontSize: "13px",
              textDecoration: "none",
              border: "2px solid #fff8f1",
            }}
          >
            Try 3D Fitting Room →
          </Link>
        </div>
      </section>

      {/* SHOP BY DEPARTMENT */}
      <section style={{ maxWidth: "1280px", margin: "0 auto", padding: "12px 24px 36px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: "18px", flexWrap: "wrap", gap: "8px" }}>
          <h2 style={{ fontFamily: '"Archivo Black", sans-serif', fontSize: "24px", margin: 0 }}>SHOP BY COLLECTION</h2>
          <Link to="/shop" style={{ fontWeight: 800, fontSize: "13px", color: "#151515" }}>
            View full catalog →
          </Link>
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))", gap: "18px" }}>
          {SECTIONS.map((sec) => (
            <Link
              key={sec.key}
              to={sec.to}
              data-testid={`home-section-${sec.key}`}
              style={{
                textDecoration: "none",
                color: "#151515",
                background: "#ffffff",
                border: "2.5px solid #151515",
                boxShadow: `6px 6px 0 ${sec.accent}`,
                padding: "24px",
                display: "flex",
                flexDirection: "column",
                gap: "8px",
              }}
            >
              <span style={{ fontSize: "11px", fontWeight: 900, letterSpacing: "0.08em", textTransform: "uppercase", color: "#6b7280" }}>
                DEPARTMENT
              </span>
              <strong style={{ fontFamily: '"Archivo Black", sans-serif', fontSize: "28px" }}>{sec.title}</strong>
              <span style={{ fontSize: "13px", color: "#454854", lineHeight: 1.5 }}>{sec.subtitle}</span>
              <span style={{ marginTop: "8px", fontWeight: 900, fontSize: "13px" }}>Shop {sec.title} →</span>
            </Link>
          ))}
        </div>
      </section>

      {/* NEW ARRIVALS */}
      <section style={{ maxWidth: "1280px", margin: "0 auto", padding: "8px 24px 36px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: "18px" }}>
          <h2 style={{ fontFamily: '"Archivo Black", sans-serif', fontSize: "24px", margin: 0 }}>NEW ARRIVALS</h2>
          <Link to="/shop?sort=newest" style={{ fontWeight: 800, fontSize: "13px", color: "#151515" }}>
            See all new →
          </Link>
        </div>
        {loading ? (
          <p style={{ fontSize: "14px", color: "#6b7280" }}>Loading collection…</p>
        ) : (
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(240px, 1fr))", gap: "18px" }}>
            {newArrivals.map((p) => (
              <ProductTile key={`new-${p.id}`} item={p} />
            ))}
          </div>
        )}
      </section>

      {/* POPULAR PRODUCTS */}
      <section style={{ maxWidth: "1280px", margin: "0 auto", padding: "8px 24px 36px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: "18px" }}>
          <h2 style={{ fontFamily: '"Archivo Black", sans-serif', fontSize: "24px", margin: 0 }}>POPULAR RIGHT NOW</h2>
          <Link to="/explore" style={{ fontWeight: 800, fontSize: "13px", color: "#151515" }}>
            Discover more →
          </Link>
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(240px, 1fr))", gap: "18px" }}>
          {popular.map((p) => (
            <ProductTile key={`pop-${p.id}`} item={p} />
          ))}
        </div>
      </section>

      {/* CATALOG RECOMMENDATIONS */}
      {recommended.length > 0 && (
        <section style={{ maxWidth: "1280px", margin: "0 auto", padding: "8px 24px 56px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: "18px", flexWrap: "wrap", gap: "8px" }}>
            <div>
              <h2 style={{ fontFamily: '"Archivo Black", sans-serif', fontSize: "24px", margin: 0 }}>CURATED PICKS</h2>
              <span style={{ fontSize: "12px", color: "#6b7280" }}>Selected from active WearWise catalog items</span>
            </div>
            <Link to="/explore" style={{ fontWeight: 800, fontSize: "13px", color: "#151515" }}>
              Explore all →
            </Link>
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(240px, 1fr))", gap: "18px" }}>
            {recommended.map((p) => (
              <ProductTile key={`rec-${p.id}`} item={p} />
            ))}
          </div>
        </section>
      )}
    </div>
  );
}

export default Home;
