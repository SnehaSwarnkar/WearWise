import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import Header from "./Header";
import { fetchCatalogue } from "../api/catalogue";
import { addToCart } from "../api/cart";
import { useAuth } from "../context/AuthContext";
import "../App.css";

const CATEGORIES = ["All", "western", "traditional", "indo-western", "occasion"];
const CATEGORY_LABELS = {
  western: "Western", traditional: "Traditional",
  "indo-western": "Indo-Western", occasion: "Occasion Wear",
};
const AGE_GROUPS = ["All", "2-5", "6-10", "11-14"];

export default function KidsShop() {
  const { user } = useAuth();
  const [activeGender, setActiveGender] = useState(user?.kidsGender || "boys");
  const [category, setCategory]   = useState("All");
  const [ageGroup, setAgeGroup]   = useState(user?.ageGroup || "All");
  const [sortPrice, setSortPrice] = useState(false);
  const [products, setProducts]   = useState([]);
  const [loading, setLoading]     = useState(true);
  const [cartFeedback, setCartFeedback] = useState(null);

  useEffect(() => {
    setLoading(true);
    fetchCatalogue(activeGender, {
      category: category !== "All" ? category : undefined,
      age_group: ageGroup !== "All" ? ageGroup : undefined,
      sort_price: sortPrice,
    })
      .then(setProducts)
      .catch(() => setProducts([]))
      .finally(() => setLoading(false));
  }, [activeGender, category, ageGroup, sortPrice]);

  const handleAddToCart = async (product) => {
    try {
      await addToCart({ id: product.id, name: product.name, price: product.price, quantity: 1, brand: product.brand });
      setCartFeedback(product.id);
      setTimeout(() => setCartFeedback(null), 1500);
    } catch { /* silent */ }
  };

  const accentColor = activeGender === "boys" ? "var(--purple)" : "var(--pink)";

  return (
    <div className="shop-page">
      <Header />

      {/* HERO */}
      <section className="shop-hero" style={{ background: accentColor }}>
        <div className="shop-hero-inner">
          <div className="shop-eyebrow">✦ KIDS' COLLECTION</div>
          <h1 className="shop-hero-title">
            LITTLE ONES,
            <br />
            <span>BIG STYLE.</span>
          </h1>
          <p className="shop-hero-sub">
            Fun, comfortable and age-perfect fashion for boys and girls ages 2–14.
          </p>
        </div>
        <div className="shop-hero-sticker">
          <span>KIDS</span>
          <strong>STYLE</strong>
          <span>✦</span>
        </div>
      </section>

      {/* GENDER TOGGLE */}
      <div className="kids-toggle-row">
        <button
          className={`kids-toggle-btn ${activeGender === "boys" ? "kids-toggle-active boys-active" : ""}`}
          onClick={() => setActiveGender("boys")}
        >
          ◉ BOYS
        </button>
        <button
          className={`kids-toggle-btn ${activeGender === "girls" ? "kids-toggle-active girls-active" : ""}`}
          onClick={() => setActiveGender("girls")}
        >
          ✦ GIRLS
        </button>
      </div>

      {/* FILTERS */}
      <section className="unified-controls">
        <div className="unified-tabs">
          {CATEGORIES.map((cat) => (
            <button
              key={cat}
              className={`unified-tab ${category === cat ? "unified-tab-active" : ""}`}
              onClick={() => setCategory(cat)}
            >
              {cat === "All" ? "All" : CATEGORY_LABELS[cat]}
            </button>
          ))}
        </div>

        <div className="unified-right-controls">
          <select
            className="unified-select"
            value={ageGroup}
            onChange={(e) => setAgeGroup(e.target.value)}
          >
            {AGE_GROUPS.map((ag) => (
              <option key={ag} value={ag}>
                {ag === "All" ? "All Ages" : ag + " yrs"}
              </option>
            ))}
          </select>

          <button
            className={`unified-sort-btn ${sortPrice ? "unified-sort-active" : ""}`}
            onClick={() => setSortPrice(!sortPrice)}
          >
            {sortPrice ? "Price ↑ ✓" : "Sort by Price"}
          </button>
        </div>
      </section>

      {/* PRODUCTS */}
      <section className="unified-products">
        <div className="unified-products-header">
          <h2>
            {activeGender === "boys" ? "Boys" : "Girls"}{" "}
            {category !== "All" ? "— " + CATEGORY_LABELS[category] : ""}
          </h2>
          <span className="unified-count">{loading ? "…" : `${products.length} pieces`}</span>
        </div>

        {loading ? (
          <div className="shop-loading">Loading styles…</div>
        ) : products.length === 0 ? (
          <div className="shop-empty">
            <div className="shop-empty-icon">✦</div>
            <h3>No styles found.</h3>
            <p>Try changing the age group or category filter.</p>
          </div>
        ) : (
          <div className="unified-grid">
            {products.map((product) => (
              <div className="shop-card" key={product.id}>
                <div className={`shop-card-image ${product.className}`}>
                  <div className="shop-card-badge">✦ {product.match}</div>
                  <div className="shop-card-placeholder">
                    <span>AI</span>
                    <strong>FASHION</strong>
                  </div>
                  <div className="shop-card-cat-tag">
                    {CATEGORY_LABELS[product.category] || product.category}
                  </div>
                  {product.ageGroup && (
                    <div className="shop-age-tag">{product.ageGroup} yrs</div>
                  )}
                </div>

                <div className="shop-card-info">
                  <div>
                    <h3>{product.name}</h3>
                    <p>₹{product.price.toLocaleString("en-IN")}</p>
                  </div>
                  <div className="color-options">
                    {product.colors.map((color, i) => (
                      <span key={i} className="color-dot" style={{ background: color }} />
                    ))}
                  </div>
                </div>

                <div className="shop-card-actions">
                  <button
                    className="shop-add-btn"
                    onClick={() => handleAddToCart(product)}
                  >
                    {cartFeedback === product.id ? "Added ✓" : "Add to Bag ✦"}
                  </button>
                  <Link to="/try-on" className="shop-try-btn">Try On</Link>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      <section className="shop-cta">
        <p>DRESS THE LITTLE ONES IN STYLE</p>
        <h2>
          Fun fits for every
          <br />
          <span>little personality.</span>
        </h2>
        <Link to="/explore" className="shop-cta-btn">Explore All Styles ✦</Link>
      </section>
    </div>
  );
}
