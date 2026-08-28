import "../App.css";
import { Link } from "react-router-dom";
import { useState } from "react";
import Header from "./Header";

function Explore() {
  const [selectedCategory, setSelectedCategory] = useState("All");
  const [sortPrice, setSortPrice] = useState(false);
  

  const products = [
    {
      id: 1,
      name: "Cherry Baby Tee",
      category: "Tops",
      price: 799,
      match: "94% Style Match",
      className: "product-pink",
      colors: ["#ff3d9a", "#ffffff", "#1d1d1d"],
    },
    {
      id: 2,
      name: "Cloud Oversized Shirt",
      category: "Tops",
      price: 1199,
      match: "89% Style Match",
      className: "product-lime",
      colors: ["#d8ff3f", "#ffffff", "#8d6bff"],
    },
    {
      id: 3,
      name: "Classic Wide Leg Denim",
      category: "Jeans",
      price: 1499,
      match: "96% Style Match",
      className: "product-blue",
      colors: ["#6f8fe8", "#232323", "#b9d3ff"],
    },
    {
      id: 4,
      name: "Sunset Mini Dress",
      category: "Dresses",
      price: 1899,
      match: "92% Style Match",
      className: "product-orange",
      colors: ["#ff633d", "#ff3d9a", "#ffd43b"],
    },
    {
      id: 5,
      name: "Electric Purple Jacket",
      category: "Jackets",
      price: 2299,
      match: "91% Style Match",
      className: "product-purple",
      colors: ["#8d6bff", "#1d1d1d", "#ff3d9a"],
    },
    {
      id: 6,
      name: "Matcha Everyday Top",
      category: "Tops",
      price: 899,
      match: "88% Style Match",
      className: "product-green",
      colors: ["#9ecb72", "#ffffff", "#1d1d1d"],
    },
  ];

  let filteredProducts =
    selectedCategory === "All"
      ? products
      : products.filter(
          (product) => product.category === selectedCategory
        );

  if (sortPrice) {
    filteredProducts = [...filteredProducts].sort(
      (a, b) => a.price - b.price
    );
  }

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
            No pressure. No budget questions. Just scroll,
            discover and find pieces that feel like you.
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
          {["All", "Tops", "Jeans", "Dresses", "Jackets"].map(
            (category) => (
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
            )
          )}
        </div>


        <button
          className={
            sortPrice
              ? "price-sort-btn price-active"
              : "price-sort-btn"
          }
          onClick={() => setSortPrice(!sortPrice)}
        >
          {sortPrice
            ? "Price: Low to High ✓"
            : "Sort by Price"}
        </button>

      </section>


      {/* AI MESSAGE */}
      <section className="ai-message">
        <div className="ai-message-icon">✦</div>

        <div>
          <p>AI STYLE NOTE</p>
          <h3>
            These picks are shown based on current
            fashion exploration trends.
          </h3>
        </div>

        <Link to="/my-style">
          Personalize My Feed →
        </Link>
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
            {filteredProducts.length} pieces
          </span>
        </div>


        <div className="product-grid">

          {filteredProducts.map((product) => (

            <div className="product-card" key={product.id}>

              <div
                className={`product-image ${product.className}`}
              >

                <div className="product-badge">
                  ✦ {product.match}
                </div>

                <div className="product-placeholder">
                  <span>AI</span>
                  <strong>FASHION</strong>
                </div>

                <button className="heart-btn">
                  ♡
                </button>

              </div>


              <div className="product-info">

                <div>
                  <h3>{product.name}</h3>

                  <p>
                    ₹{product.price}
                  </p>
                </div>

                <div className="color-options">

                  {product.colors.map(
                    (color, index) => (
                      <span
                        key={index}
                        className="color-dot"
                        style={{ background: color }}
                      ></span>
                    )
                  )}

                </div>

              </div>


              <div className="product-actions">

                <Link
                  to="/try-on"
                  className="try-product-btn"
                >
                  Try This On ✦
                </Link>

                <Link
                  to="/try-on"
                  className="compare-product-btn"
                >
                  Compare
                </Link>

              </div>

            </div>

          ))}

        </div>

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
            Love the same top in different colors?
            Try multiple variations and compare which one
            may suit your style best.
          </p>

          <Link to="/try-on" className="color-explore-btn">
            Compare Colors →
          </Link>

        </div>


        <div className="color-visual">

          <div className="color-shirt shirt-one">
            TOP
          </div>

          <div className="color-shirt shirt-two">
            TOP
          </div>

          <div className="color-shirt shirt-three">
            TOP
          </div>

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

        <Link to="/try-on">
          Start Virtual Try-On →
        </Link>

      </section>

    </div>
  );
}

export default Explore;