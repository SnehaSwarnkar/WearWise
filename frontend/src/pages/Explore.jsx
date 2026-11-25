import "../App.css";
import { Link } from "react-router-dom";
import { useState, useEffect } from "react";
import Header from "./Header";
import { fetchProducts } from "../api/products";
import { addToCart } from "../api/cart";
import { addToWishlist } from "../api/saved";

const CATEGORIES = [
  { id: "All", label: "All" },
  { id: "Tops", label: "T-Shirts & Tops" },
  { id: "Shirts", label: "Shirts" },
  { id: "Trousers", label: "Trousers" },
  { id: "Jeans", label: "Jeans" },
  { id: "Skirts", label: "Skirts" },
  { id: "Dresses", label: "Dresses" },
  { id: "Jackets", label: "Jackets" },
];

function Explore() {
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
        sku: product.sku,
        name: product.name,
        price: product.price,
        size: product.available_sizes?.[0] || "M",
        quantity: 1,
        brand: product.seller_name || product.brand || "WEARWISE EDIT",
        image: product.image || undefined,
      });
      setCartFeedback(product.id);
      setTimeout(() => setCartFeedback(null), 1500);
    } catch { /* silent */ }
  };

  const handleWishlist = async (product) => {
    if (wishlisted.has(product.id)) return;
    try {
      await addToWishlist(product);
    } catch { /* silent */ }
    setWishlisted((prev) => new Set([...prev, product.id]));
  };

  return (
    <div className="explore-page">
      <Header />

      {/* ── HERO ── */}
      <section className="explore-hero">
        <div>
          <p className="explore-tag">VIRTUAL TRY-ON MARKETPLACE ✦</p>
          <h1>
            Explore your
            <br />
            <span>next obsession.</span>
          </h1>
          <p className="explore-subtext">
            Browse outfits by category, inspect product details, and try pieces on
            in Photo Try-On or Interactive 3D.
          </p>
        </div>
        <div className="explore-sticker">
          <span>FIND</span>
          <strong>YOUR</strong>
          <span>LOOK</span>
        </div>
      </section>

      {/* ── CONTROLS ── */}
      <section className="unified-controls">
        <div className="unified-tabs" role="tablist" aria-label="Clothing categories">
          {CATEGORIES.map((cat) => (
            <button
              key={cat.id}
              type="button"
              data-testid={`category-tab-${cat.id}`}
              className={`unified-tab ${selectedCategory === cat.id ? "unified-tab-active" : ""}`}
              onClick={() => setSelectedCategory(cat.id)}
            >
              {cat.label}
            </button>
          ))}
        </div>

        <div className="unified-right-controls">
          <button
            type="button"
            className={`unified-sort-btn ${sortPrice ? "unified-sort-active" : ""}`}
            onClick={() => setSortPrice(!sortPrice)}
          >
            {sortPrice ? "Price ↑ ✓" : "Sort by Price"}
          </button>
        </div>
      </section>

      {/* ── PRODUCTS ── */}
      <section className="unified-products">
        <div className="unified-products-header">
          <div>
            <p>CURATED PIECES</p>
            <h2>
              Scroll. Stop.
              <br />
              <span>Try it on.</span>
            </h2>
          </div>
          <span className="unified-count">
            {loading ? "…" : `${products.length} pieces`}
          </span>
        </div>

        {loading ? (
          <div className="shop-loading">Loading products…</div>
        ) : products.length === 0 ? (
          <div style={{ padding: "36px 20px", textAlign: "center", border: "2px solid var(--border)", borderRadius: "12px", background: "#fff" }}>
            No pieces found in this category right now.
          </div>
        ) : (
          <div className="unified-grid">
            {products.map((product) => {
              const productKey = encodeURIComponent(product.sku || String(product.id));
              const caps = product.tryOnCapabilities || {};
              const hasImgTryOn = Boolean(caps.imageTryOnEnabled);
              const has3DTryOn = Boolean(caps.threeDTryOnEnabled);

              return (
                <div className="shop-card" key={product.sku || product.id} data-testid={`product-card-${product.sku || product.id}`}>
                  {/* IMAGE */}
                  <Link to={`/product/${productKey}`} style={{ textDecoration: "none", color: "inherit", display: "block" }}>
                    <div className={`shop-card-image ${product.className}`}>
                      <div className="shop-card-badge">{product.category}</div>
                      {product.image ? (
                        <img
                          src={product.image}
                          alt={product.name}
                          onError={(e) => {
                            e.currentTarget.style.display = "none";
                          }}
                          style={{ width: "100%", height: "100%", objectFit: "cover", position: "absolute", inset: 0 }}
                        />
                      ) : (
                        <div className="shop-card-placeholder">
                          <span>WEARWISE</span>
                          <strong>{product.category?.toUpperCase() || "STYLE"}</strong>
                        </div>
                      )}
                      <button
                        type="button"
                        className={`heart-btn ${wishlisted.has(product.id) ? "heart-active" : ""}`}
                        onClick={(e) => {
                          e.preventDefault();
                          handleWishlist(product);
                        }}
                        aria-label="Save to wishlist"
                        title="Save to wishlist"
                      >
                        {wishlisted.has(product.id) ? "♥" : "♡"}
                      </button>
                    </div>
                  </Link>

                  {/* INFO */}
                  <div className="shop-card-info">
                    <div>
                      <Link to={`/product/${productKey}`} style={{ textDecoration: "none", color: "inherit" }}>
                        <h3>{product.name}</h3>
                      </Link>
                      <p>₹{Number(product.price).toLocaleString("en-IN")}</p>
                      <div style={{ display: "flex", gap: "6px", flexWrap: "wrap", marginTop: "6px" }}>
                        {(caps.imageTryOnEnabled || caps.sellerImageTryOnEnabled) && (
                          <span style={{ fontSize: "11px", fontWeight: 800, padding: "2px 8px", borderRadius: "999px", border: "1.5px solid #151515", background: caps.imageTryOnEnabled ? "#FFF8F1" : "#f1f5f9", color: caps.imageTryOnEnabled ? "#151515" : "#64748b" }}>
                            {caps.imageTryOnEnabled ? "Image Try-On" : "Image Try-On (Setup Pending)"}
                          </span>
                        )}
                        {has3DTryOn && (
                          <span style={{ fontSize: "11px", fontWeight: 800, padding: "2px 8px", borderRadius: "999px", border: "1.5px solid #151515", background: "var(--lime)" }}>
                            Interactive 3D
                          </span>
                        )}
                      </div>
                    </div>
                    <div className="color-options">
                      {(product.colors || []).map((color, i) => (
                        <span key={i} className="color-dot" style={{ background: color }} />
                      ))}
                    </div>
                  </div>

                  {/* ACTIONS */}
                  <div className="shop-card-actions" style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                    <div style={{ display: "flex", gap: "8px" }}>
                      <button
                        type="button"
                        className="shop-add-btn"
                        onClick={() => handleAddToCart(product)}
                        style={{ flex: 1 }}
                      >
                        {cartFeedback === product.id ? "Added ✓" : "Add to Bag"}
                      </button>
                      <Link to={`/product/${productKey}`} className="shop-try-btn" data-testid={`view-product-${product.sku || product.id}`}>
                        Details
                      </Link>
                    </div>
                    <Link
                      to={`/product/${productKey}?openTryOn=1`}
                      data-testid={`card-tryon-${product.sku || product.id}`}
                      className="shop-fit-btn"
                      style={{
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        gap: "6px",
                        background: has3DTryOn ? "var(--lime)" : "#fff",
                        color: "#151515",
                        fontWeight: 800,
                        fontSize: "12px",
                        padding: "8px 12px",
                        borderRadius: "4px",
                        border: "2px solid var(--border)",
                        textDecoration: "none",
                        boxShadow: "2px 2px 0 var(--border)",
                        width: "100%",
                      }}
                    >
                      Try On →
                    </Link>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </section>

      {/* ── CTA ── */}
      <section className="explore-cta">
        <p>SELLING ON WEARWISE?</p>
        <h2>
          List your designs.
          <br />
          <span>Choose Image or 3D Try-On.</span>
        </h2>
        <Link to="/merchant-studio">Open Seller Studio →</Link>
      </section>
    </div>
  );
}

export default Explore;
