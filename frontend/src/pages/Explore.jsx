import "../App.css";
import { Link } from "react-router-dom";
import { useState, useEffect } from "react";
import Header from "./Header";
import { fetchProducts } from "../api/products";
import { addToCart } from "../api/cart";
import { addToWishlist } from "../api/saved";

function Explore() {
  const [selectedCategory, setSelectedCategory] = useState("All");
  const [sortPrice, setSortPrice] = useState(false);
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [cartFeedback, setCartFeedback] = useState(null);   // id of item just added
  const [wishlisted, setWishlisted] = useState(new Set());  // product ids in wishlist

  // Fetch products from API whenever filters change
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
    } catch {
      // Silently fail — user can try again
    }
  };

  const handleWishlist = async (product) => {
    if (wishlisted.has(product.id)) return; // already saved
    try {
      await addToWishlist(product);
      setWishlisted((prev) => new Set([...prev, product.id]));
    } catch {
      // e.g. 409 already in wishlist — still mark it locally
      setWishlisted((prev) => new Set([...prev, product.id]));
    }
  };

  return (
    <div className="explore-page">
      <Header />

      {/* EXPLORE HERO */}
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

      {/* CATEGORY FILTER */}
      <section className="explore-controls">
        <div className="category-filter">
          {["All", "Tops", "Jeans", "Dresses", "Jackets"].map((category) => (
            <button
              key={category}
              className={
                selectedCategory === category
                  ? "category-btn active-category"
                  : "category-btn"
              }
              onClick={() => setSelectedCategory(category)}
            >
              {category}
            </button>
          ))}
        </div>

        <button
          className={sortPrice ? "price-sort-btn price-active" : "price-sort-btn"}
          onClick={() => setSortPrice(!sortPrice)}
        >
          {sortPrice ? "Price: Low to High ✓" : "Sort by Price"}
        </button>
      </section>

      {/* AI MESSAGE */}
      <section className="ai-message">
        <div className="ai-message-icon">✦</div>
        <div>
          <p>AI STYLE NOTE</p>
          <h3>
            These picks are shown based on current fashion exploration trends.
          </h3>
        </div>
        <Link to="/my-style">Personalize My Feed →</Link>
      </section>

      {/* PRODUCTS */}
      <section className="products-section">
        <div className="products-header">
          <div>
            <p>CURATED FOR EXPLORATION</p>
            <h2>
              Scroll. Stop.
              <br />
              <span>Obsess.</span>
            </h2>
          </div>
          <span className="product-count">
            {loading ? "..." : `${products.length} pieces`}
          </span>
        </div>

        {loading ? (
          <div className="explore-loading">Loading products…</div>
        ) : (
          <div className="product-grid">
            {products.map((product) => (
              <div className="product-card" key={product.id}>
                <div className={`product-image ${product.className}`}>
                  <div className="product-badge">✦ {product.match}</div>
                  <div className="product-placeholder">
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

                <div className="product-info">
                  <div>
                    <h3>{product.name}</h3>
                    <p>₹{product.price}</p>
                  </div>
                  <div className="color-options">
                    {product.colors.map((color, index) => (
                      <span
                        key={index}
                        className="color-dot"
                        style={{ background: color }}
                      />
                    ))}
                  </div>
                </div>

                <div className="product-actions">
                  <button
                    className="try-product-btn"
                    onClick={() => handleAddToCart(product)}
                  >
                    {cartFeedback === product.id ? "Added ✓" : "Add to Bag ✦"}
                  </button>

                  <Link to="/try-on" className="compare-product-btn">
                    Try On
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* COLOR EXPLORATION */}
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

      {/* CTA */}
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
