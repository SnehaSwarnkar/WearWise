import "../App.css";
import { Link, useSearchParams } from "react-router-dom";
import { useState, useEffect } from "react";
import Header from "./Header";
import { fetchProducts } from "../api/products";
import { addToCart } from "../api/cart";
import { addToWishlist } from "../api/saved";
import { COLLECTIONS } from "../data/collections";

const CATEGORIES = ["All", "Tops", "Jeans", "Dresses", "Jackets"];

function Explore() {
  const [searchParams] = useSearchParams();
  const activeCollectionSlug = searchParams.get("collection");
  const activeCollection = activeCollectionSlug
    ? COLLECTIONS.find((c) => c.slug === activeCollectionSlug)
    : null;

  const [selectedCategory, setSelectedCategory] = useState("All");
  const [sortPrice, setSortPrice]               = useState(false);
  const [products, setProducts]                 = useState([]);
  const [loading, setLoading]                   = useState(true);
  const [cartFeedback, setCartFeedback]         = useState(null);
  const [wishlisted, setWishlisted]             = useState(new Set());

  useEffect(() => {
    setLoading(true);
    fetchProducts(selectedCategory, sortPrice)
      .then(setProducts)
      .catch(() => setProducts([]))
      .finally(() => setLoading(false));
  }, [selectedCategory, sortPrice]);

  const handleAddToCart = async (product) => {
    try {
      await addToCart({
        id: product.id,
        name: product.name,
        price: product.price,
        quantity: 1,
        brand: product.brand || "WEARWISE EDIT",
      });
      setCartFeedback(product.id);
      setTimeout(() => setCartFeedback(null), 1500);
    } catch { /* silent */ }
  };

  const handleWishlist = async (product) => {
    if (wishlisted.has(product.id)) return;
    try {
      await addToWishlist(product);
    } catch { /* silent — 409 means already in wishlist */ }
    setWishlisted((prev) => new Set([...prev, product.id]));
  };

  return (
    <div className="explore-page">
      <Header />

      {/* ── COLLECTION BANNER (shown when arriving from a collection link) ── */}
      {activeCollection && (
        <div className="collection-banner" style={{ "--coll-accent": activeCollection.accentColor, background: activeCollection.bgGradient }}>
          <div className="collection-banner-inner">
            <span className="coll-banner-icon">{activeCollection.icon}</span>
            <div>
              <h2 className="coll-banner-title">{activeCollection.title}</h2>
              <p className="coll-banner-tagline">{activeCollection.tagline}</p>
              <p className="coll-banner-desc">{activeCollection.description}</p>
            </div>
            <Link to="/explore" className="coll-banner-clear">View All →</Link>
          </div>
        </div>
      )}

      {/* ── HERO (shown when no collection is selected) ── */}
      {!activeCollection && (
        <section className="explore-hero">
          <div>
            <p className="explore-tag">FASHION DISCOVERY MODE ✦</p>
            <h1>
              Explore your
              <br />
              <span>next obsession.</span>
            </h1>
            <p className="explore-subtext">
              No pressure. No budget questions. Just scroll, discover and find
              pieces that feel like you.
            </p>
          </div>
          <div className="explore-sticker">
            <span>FIND</span>
            <strong>YOUR</strong>
            <span>LOOK</span>
          </div>
        </section>
      )}

      {/* ── CONTROLS ── */}
      <section className="unified-controls">
        <div className="unified-tabs">
          {CATEGORIES.map((cat) => (
            <button
              key={cat}
              className={`unified-tab ${selectedCategory === cat ? "unified-tab-active" : ""}`}
              onClick={() => setSelectedCategory(cat)}
            >
              {cat}
            </button>
          ))}
        </div>

        <div className="unified-right-controls">
          <button
            className={`unified-sort-btn ${sortPrice ? "unified-sort-active" : ""}`}
            onClick={() => setSortPrice(!sortPrice)}
          >
            {sortPrice ? "Price ↑ ✓" : "Sort by Price"}
          </button>
        </div>
      </section>

      {/* ── AI NOTE ── */}
      <section className="ai-message">
        <div className="ai-message-icon">✦</div>
        <div>
          <p>AI STYLE NOTE</p>
          <h3>
            {activeCollection
              ? `Showing picks for "${activeCollection.title}"`
              : "These picks are shown based on current fashion exploration trends."}
          </h3>
        </div>
        <Link to="/my-style">Personalize My Feed →</Link>
      </section>

      {/* ── COLLECTION QUICK-NAV ── */}
      <div className="coll-quicknav">
        <Link
          to="/explore"
          className={`coll-qn-chip ${!activeCollection ? "coll-qn-active" : ""}`}
        >
          All
        </Link>
        {COLLECTIONS.map((col) => (
          <Link
            key={col.id}
            to={`/explore?collection=${col.slug}`}
            className={`coll-qn-chip ${activeCollection?.id === col.id ? "coll-qn-active" : ""}`}
          >
            {col.icon} {col.title.split(" ")[0]}
          </Link>
        ))}
      </div>

      {/* ── PRODUCTS ── */}
      <section className="unified-products">
        <div className="unified-products-header">
          <div>
            <p>CURATED FOR EXPLORATION</p>
            <h2>
              Scroll. Stop.
              <br />
              <span>Obsess.</span>
            </h2>
          </div>
          <span className="unified-count">
            {loading ? "…" : `${products.length} pieces`}
          </span>
        </div>

        {loading ? (
          <div className="shop-loading">Loading products…</div>
        ) : (
          <div className="unified-grid">
            {products.map((product) => (
              <div className="shop-card" key={product.id}>

                {/* IMAGE */}
                <div className={`shop-card-image ${product.className}`}>
                  <div className="shop-card-badge">✦ {product.match}</div>
                  <div className="shop-card-placeholder">
                    <span>AI</span>
                    <strong>FASHION</strong>
                  </div>
                  <button
                    className={`heart-btn ${wishlisted.has(product.id) ? "heart-active" : ""}`}
                    onClick={() => handleWishlist(product)}
                    aria-label="Save to wishlist"
                    title="Save to wishlist"
                  >
                    {wishlisted.has(product.id) ? "♥" : "♡"}
                  </button>
                </div>

                {/* INFO */}
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

                {/* ACTIONS */}
                <div className="shop-card-actions">
                  <button
                    className="shop-add-btn"
                    onClick={() => handleAddToCart(product)}
                  >
                    {cartFeedback === product.id ? "Added ✓" : "Add to Bag ✦"}
                  </button>
                  <Link to="/try-on" className="shop-try-btn">
                    Try On
                  </Link>
                </div>

              </div>
            ))}
          </div>
        )}
      </section>

      {/* ── COLOR SECTION ── */}
      <section className="color-explore-section">
        <div className="color-explore-text">
          <p>PLAY WITH COLOR</p>
          <h2>
            Same outfit.
            <br />
            <span>Different energy.</span>
          </h2>
          <p className="color-description">
            Love the same top in different colors? Try multiple variations and
            compare which one may suit your style best.
          </p>
          <Link to="/try-on" className="color-explore-btn">
            Compare Colors →
          </Link>
        </div>
        <div className="color-visual">
          <div className="color-shirt shirt-one">TOP</div>
          <div className="color-shirt shirt-two">TOP</div>
          <div className="color-shirt shirt-three">TOP</div>
        </div>
      </section>

      {/* ── CTA ── */}
      <section className="explore-cta">
        <p>FOUND SOMETHING YOU LIKE?</p>
        <h2>
          Don't just imagine it.
          <br />
          <span>See it on you.</span>
        </h2>
        <Link to="/try-on">Start Virtual Try-On →</Link>
      </section>
    </div>
  );
}

export default Explore;
