/**
 * Reusable shop layout used by MenShop, WomenShop and KidsShop.
 * Renders the section hero, category tabs, occasion filter, product grid.
 */
import { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import Header from "./Header";
import { fetchCatalogue } from "../api/catalogue";
import { addToCart } from "../api/cart";
import { addToWishlist } from "../api/saved";
import { apiClient } from "../api/client";

const CATEGORIES = ["All", "western", "traditional", "indo-western", "occasion"];
const OCCASIONS  = ["All", "casual", "work", "festive", "wedding", "party"];

const CATEGORY_LABELS = {
  "western": "Western",
  "traditional": "Traditional",
  "indo-western": "Indo-Western",
  "occasion": "Occasion Wear",
};

export default function ShopLayout({ gender, heroTitle, heroSub, accentColor, eyebrow }) {
  const navigate = useNavigate();
  const [category, setCategory]   = useState("All");
  const [occasion, setOccasion]   = useState("All");
  const [sortPrice, setSortPrice] = useState(false);
  const [products, setProducts]   = useState([]);
  const [loading, setLoading]     = useState(true);
  const [cartFeedback, setCartFeedback] = useState(null);
  const [wishlisted, setWishlisted]     = useState(new Set());
  const [garmentsMap, setGarmentsMap]   = useState({});

  useEffect(() => {
    apiClient
      .listGarments()
      .then((list) => {
        const map = {};
        (list || []).forEach((g) => {
          if (g.sku) map[g.sku] = g;
        });
        setGarmentsMap(map);
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    setLoading(true);
    fetchCatalogue(gender, {
      category: category !== "All" ? category : undefined,
      occasion: occasion !== "All" ? occasion : undefined,
      sort_price: sortPrice,
    })
      .then(setProducts)
      .catch(() => setProducts([]))
      .finally(() => setLoading(false));
  }, [gender, category, occasion, sortPrice]);

  const handleAddToCart = async (product) => {
    try {
      await addToCart({ id: product.id, name: product.name, price: product.price, quantity: 1, brand: product.brand });
      setCartFeedback(product.id);
      setTimeout(() => setCartFeedback(null), 1500);
    } catch { /* silent */ }
  };

  const handleWishlist = async (product) => {
    if (wishlisted.has(product.id)) return;
    try {
      await addToWishlist(product);
      setWishlisted((prev) => new Set([...prev, product.id]));
    } catch {
      setWishlisted((prev) => new Set([...prev, product.id]));
    }
  };

  return (
    <div className="shop-page">
      <Header />

      {/* HERO */}
      <section className="shop-hero" style={{ background: accentColor }}>
        <div className="shop-hero-inner">
          <div className="shop-eyebrow">{eyebrow}</div>
          <h1 className="shop-hero-title">{heroTitle}</h1>
          <p className="shop-hero-sub">{heroSub}</p>
        </div>
        <div className="shop-hero-sticker">
          <span>FIND</span>
          <strong>YOUR</strong>
          <span>LOOK</span>
        </div>
      </section>

      {/* CATEGORY TABS */}
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
            value={occasion}
            onChange={(e) => setOccasion(e.target.value)}
          >
            <option value="All">All Occasions</option>
            {OCCASIONS.slice(1).map((occ) => (
              <option key={occ} value={occ}>
                {occ.charAt(0).toUpperCase() + occ.slice(1)}
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

      {/* PRODUCT GRID */}
      <section className="unified-products">
        <div className="unified-products-header">
          <h2>
            {category === "All" ? "All Styles" : CATEGORY_LABELS[category]}
            {occasion !== "All" && <span> — {occasion.charAt(0).toUpperCase() + occasion.slice(1)}</span>}
          </h2>
          <span className="unified-count">
            {loading ? "…" : `${products.length} pieces`}
          </span>
        </div>

        {loading ? (
          <div className="shop-loading">Loading styles…</div>
        ) : products.length === 0 ? (
          <div className="shop-empty">
            <div className="shop-empty-icon">✦</div>
            <h3>No styles found.</h3>
            <p>Try a different category or occasion filter.</p>
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
                  <button
                    className={`heart-btn ${wishlisted.has(product.id) ? "heart-active" : ""}`}
                    onClick={() => handleWishlist(product)}
                    aria-label="Save to wishlist"
                  >
                    {wishlisted.has(product.id) ? "♥" : "♡"}
                  </button>
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

                <div className="shop-card-actions" style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  <div style={{ display: 'flex', gap: '8px' }}>
                    <button
                      className="shop-add-btn"
                      onClick={() => handleAddToCart(product)}
                      style={{ flex: 1 }}
                    >
                      {cartFeedback === product.id ? "Added ✓" : "Add to Bag ✦"}
                    </button>
                    <Link to="/try-on" className="shop-try-btn">
                      Try On
                    </Link>
                  </div>
                  {garmentsMap[product.sku] ? (
                    <Link
                      to={`/fit?garment_id=${garmentsMap[product.sku].garment_id}&sku=${product.sku}`}
                      className="shop-fit-btn"
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: '6px',
                        background: 'var(--lime)',
                        color: '#151515',
                        fontWeight: 800,
                        fontSize: '12px',
                        padding: '8px 12px',
                        borderRadius: '4px',
                        border: '2px solid var(--border)',
                        textDecoration: 'none',
                        boxShadow: '2px 2px 0 var(--border)',
                        width: '100%',
                      }}
                    >
                      <span>Check My Fit ✦</span>
                      <small style={{ fontSize: '10px', opacity: 0.8 }}>({product.sku})</small>
                    </Link>
                  ) : (
                    <div style={{ fontSize: '11px', color: 'var(--text-soft)', textAlign: 'center', padding: '2px 0' }}>
                      Fit specs pending registration
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* BOTTOM CTA */}
      <section className="shop-cta">
        <p>WANT TO SEE IT ON YOU?</p>
        <h2>
          Don't just imagine it.
          <br />
          <span>See it on you.</span>
        </h2>
        <Link to="/try-on" className="shop-cta-btn">
          Start Virtual Try-On ✦
        </Link>
      </section>
    </div>
  );
}
