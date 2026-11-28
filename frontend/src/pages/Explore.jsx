import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { Heart, Search } from "lucide-react";
import "../App.css";
import Header from "./Header";
import { fetchProducts, fetchRecommendations } from "../api/products";
import { addToWishlist, getWishlist } from "../api/saved";

const CATEGORIES = ["All", "Tops", "Shirts", "Trousers", "Jeans", "Skirts", "Dresses", "Jackets"];

function ExploreProductCard({ product, onWishlistToggle, wishlisted }) {
  const detailPath = product.sku ? `/product/${encodeURIComponent(product.sku)}` : `/shop`;
  const mode = product.tryOnCapabilities?.mode || product.try_on_mode || "IMAGE_ONLY";
  const badgeLabel =
    mode === "IMAGE_AND_THREE_D"
      ? "Photo + 3D Try-On"
      : mode === "THREE_D_ONLY"
        ? "3D Try-On"
        : "Photo Try-On";

  return (
    <div
      data-testid={`explore-card-${product.sku || product.id}`}
      style={{
        background: "#ffffff",
        border: "2.5px solid #151515",
        boxShadow: "5px 5px 0 #151515",
        display: "flex",
        flexDirection: "column",
        overflow: "hidden",
      }}
    >
      <div style={{ position: "relative", aspectRatio: "4 / 5", background: "#f3ece4" }}>
        <Link to={detailPath} style={{ display: "block", width: "100%", height: "100%" }}>
          {product.image ? (
            <img
              src={product.image}
              alt={product.name}
              style={{ width: "100%", height: "100%", objectFit: "cover", display: "block" }}
            />
          ) : (
            <div style={{ padding: "24px", fontSize: "13px", color: "#6b7280" }}>No image</div>
          )}
        </Link>
        <span
          style={{
            position: "absolute",
            top: "10px",
            left: "10px",
            background: "#d8ff3f",
            border: "1.5px solid #151515",
            padding: "3px 8px",
            fontSize: "10px",
            fontWeight: 900,
          }}
        >
          {badgeLabel}
        </span>
        <button
          type="button"
          aria-label={`Save ${product.name} to wishlist`}
          onClick={() => onWishlistToggle(product)}
          style={{
            position: "absolute",
            top: "10px",
            right: "10px",
            width: "34px",
            height: "34px",
            borderRadius: "50%",
            border: "2px solid #151515",
            background: wishlisted ? "#ff3d9a" : "#ffffff",
            color: wishlisted ? "#ffffff" : "#151515",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            cursor: "pointer",
          }}
        >
          <Heart size={16} fill={wishlisted ? "#ffffff" : "none"} />
        </button>
      </div>

      <div style={{ padding: "14px", display: "flex", flexDirection: "column", gap: "6px", flex: 1 }}>
        <div style={{ fontSize: "11px", fontWeight: 800, color: "#6b7280", textTransform: "uppercase" }}>
          {product.seller_name || product.brand || "WearWise"} · {product.category}
        </div>
        <Link to={detailPath} style={{ textDecoration: "none", color: "#151515", fontWeight: 900, fontSize: "15px" }}>
          {product.name}
        </Link>
        <div style={{ marginTop: "auto", paddingTop: "8px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <strong style={{ fontSize: "15px" }}>₹{Number(product.price || 0).toLocaleString()}</strong>
          <Link to={detailPath} style={{ fontSize: "12px", fontWeight: 900, color: "#151515" }}>
            View Piece →
          </Link>
        </div>
      </div>
    </div>
  );
}

function Explore() {
  const [activeCategory, setActiveCategory] = useState("All");
  const [search, setSearch] = useState("");
  const [products, setProducts] = useState([]);
  const [recommended, setRecommended] = useState([]);
  const [newest, setNewest] = useState([]);
  const [wishlistIds, setWishlistIds] = useState(new Set());
  const [loading, setLoading] = useState(true);
  const [toast, setToast] = useState(null);

  useEffect(() => {
    let alive = true;
    setLoading(true);
    Promise.all([
      fetchProducts(activeCategory, false, { search: search.trim() || undefined }).catch(() => []),
      fetchRecommendations(null, 4).catch(() => ({ items: [] })),
      fetchProducts(null, false, { sort: "newest" }).catch(() => []),
      getWishlist().catch(() => []),
    ]).then(([allList, rec, newItems, wish]) => {
      if (!alive) return;
      const mainList = Array.isArray(allList) ? allList : [];
      const seenIds = new Set(mainList.map((x) => x.id));
      const recItems = (Array.isArray(rec?.items) ? rec.items : []).filter((x) => !seenIds.has(x.id));
      const newList = (Array.isArray(newItems) ? newItems : []).filter((x) => !seenIds.has(x.id)).slice(0, 4);
      setProducts(mainList);
      setRecommended(recItems);
      setNewest(newList);
      setWishlistIds(new Set((Array.isArray(wish) ? wish : []).map((w) => w.product_id)));
      setLoading(false);
    });
    return () => {
      alive = false;
    };
  }, [activeCategory, search]);

  const handleToggleWishlist = async (product) => {
    try {
      await addToWishlist(product);
      setWishlistIds((prev) => new Set([...prev, product.id]));
      setToast(`Saved "${product.name}" to your Wishlist.`);
      setTimeout(() => setToast(null), 2600);
    } catch {
      setToast("Could not update Wishlist right now.");
    }
  };

  return (
    <div style={{ minHeight: "100vh", background: "#fff8f1", color: "#151515" }}>
      <Header />

      <div style={{ maxWidth: "1280px", margin: "0 auto", padding: "32px 24px 60px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", flexWrap: "wrap", gap: "16px", marginBottom: "24px" }}>
          <div>
            <span style={{ fontSize: "11px", fontWeight: 900, letterSpacing: "0.08em", color: "#ff3d9a" }}>
              ✦ DISCOVER WEARWISE
            </span>
            <h1 style={{ fontFamily: '"Archivo Black", sans-serif', fontSize: "clamp(32px, 4vw, 48px)", margin: "4px 0 6px", letterSpacing: "-1.5px" }}>
              EXPLORE FASHION
            </h1>
            <p style={{ margin: 0, fontSize: "14px", color: "#454854" }}>
              Browse catalog highlights, seasonal arrivals, and styles curated by department and category.
            </p>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "8px", border: "2.5px solid #151515", background: "#ffffff", padding: "6px 12px", minWidth: "250px" }}>
            <Search size={16} />
            <input
              type="search"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search styles, shirts, jackets…"
              style={{ border: "none", outline: "none", width: "100%", fontSize: "13px", fontWeight: 600 }}
            />
          </div>
        </div>

        {/* Collections Quick Links */}
        <div style={{ display: "flex", gap: "10px", flexWrap: "wrap", marginBottom: "20px" }}>
          {[
            { label: "Men's Edit", to: "/shop/men" },
            { label: "Women's Edit", to: "/shop/women" },
            { label: "Kids' Edit", to: "/shop/kids" },
            { label: "All Shopping Catalog", to: "/shop" },
          ].map((col) => (
            <Link
              key={col.to}
              to={col.to}
              style={{
                padding: "7px 14px",
                border: "2px solid #151515",
                background: "#ffffff",
                color: "#151515",
                fontWeight: 800,
                fontSize: "12px",
                textDecoration: "none",
              }}
            >
              {col.label} →
            </Link>
          ))}
        </div>

        {/* Category Filter Tabs */}
        <div style={{ display: "flex", gap: "8px", flexWrap: "wrap", marginBottom: "26px" }}>
          {CATEGORIES.map((cat) => {
            const active = activeCategory === cat;
            return (
              <button
                key={cat}
                type="button"
                data-testid={`category-tab-${cat}`}
                onClick={() => setActiveCategory(cat)}
                style={{
                  padding: "8px 16px",
                  border: "2px solid #151515",
                  background: active ? "#151515" : "#ffffff",
                  color: active ? "#d8ff3f" : "#151515",
                  fontWeight: 900,
                  fontSize: "12px",
                  cursor: "pointer",
                }}
              >
                {cat}
              </button>
            );
          })}
        </div>

        {toast && (
          <div style={{ marginBottom: "18px", padding: "10px 14px", background: "#d8ff3f", border: "2px solid #151515", fontWeight: 800, fontSize: "13px" }}>
            {toast}
          </div>
        )}

        {/* Main Browse Grid */}
        <section style={{ marginBottom: "42px" }}>
          <h2 style={{ fontFamily: '"Archivo Black", sans-serif', fontSize: "20px", margin: "0 0 14px" }}>
            {activeCategory === "All" ? "TRENDING & CATALOG PICKS" : `${activeCategory.toUpperCase()} COLLECTION`}
          </h2>
          {loading ? (
            <p style={{ fontSize: "14px", color: "#6b7280" }}>Loading catalog items…</p>
          ) : products.length === 0 ? (
            <div style={{ padding: "24px", background: "#ffffff", border: "2px solid #151515" }}>
              No items matched your current filter. <button type="button" onClick={() => { setActiveCategory("All"); setSearch(""); }} style={{ textDecoration: "underline", fontWeight: 800, cursor: "pointer", background: "none", border: "none" }}>Reset filters</button>
            </div>
          ) : (
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(240px, 1fr))", gap: "18px" }}>
              {products.map((p) => (
                <ExploreProductCard
                  key={p.id}
                  product={p}
                  wishlisted={wishlistIds.has(p.id)}
                  onWishlistToggle={handleToggleWishlist}
                />
              ))}
            </div>
          )}
        </section>

        {/* Catalog-Based Recommendations */}
        {recommended.length > 0 && (
          <section style={{ marginBottom: "42px" }}>
            <div style={{ marginBottom: "14px" }}>
              <h2 style={{ fontFamily: '"Archivo Black", sans-serif', fontSize: "20px", margin: 0 }}>
                RECOMMENDED FROM OUR CATALOG
              </h2>
              <span style={{ fontSize: "12px", color: "#6b7280" }}>
                Sorted by popular styles and virtual try-on availability
              </span>
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(240px, 1fr))", gap: "18px" }}>
              {recommended.map((p) => (
                <ExploreProductCard
                  key={`rec-${p.id}`}
                  product={p}
                  wishlisted={wishlistIds.has(p.id)}
                  onWishlistToggle={handleToggleWishlist}
                />
              ))}
            </div>
          </section>
        )}

        {/* Recently Added */}
        {newest.length > 0 && (
          <section>
            <h2 style={{ fontFamily: '"Archivo Black", sans-serif', fontSize: "20px", margin: "0 0 14px" }}>
              RECENTLY ADDED
            </h2>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(240px, 1fr))", gap: "18px" }}>
              {newest.map((p) => (
                <ExploreProductCard
                  key={`new-${p.id}`}
                  product={p}
                  wishlisted={wishlistIds.has(p.id)}
                  onWishlistToggle={handleToggleWishlist}
                />
              ))}
            </div>
          </section>
        )}
      </div>
    </div>
  );
}

export default Explore;
