import { useEffect, useState } from "react";
import "./Wardrobe.css";
import Header from "./Header";
import { getWardrobe, uploadClothes, deleteWardrobeItem } from "../api/wardrobe";

const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

function Wardrobe() {
  const [items, setItems] = useState([]);
  const [category, setCategory] = useState("All");
  const [loading, setLoading] = useState(true);

  const loadItems = (cat = category) => {
    getWardrobe(cat)
      .then(setItems)
      .catch(() => setItems([]))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadItems(category);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [category]);

  const handleUpload = async (event) => {
    const files = Array.from(event.target.files);
    if (!files.length) return;
    try {
      const newItems = await uploadClothes(files, "Tops");
      setItems((prev) => [...prev, ...newItems]);
    } catch {
      // ignore upload errors silently
    }
    event.target.value = "";
  };

  const handleDelete = async (id) => {
    try {
      await deleteWardrobeItem(id);
      setItems((prev) => prev.filter((item) => item.id !== id));
    } catch {
      // ignore
    }
  };

  const filteredItems =
    category === "All"
      ? items
      : items.filter((item) => item.category === category);

  return (
    <main className="wardrobe-page">
      <Header />

      <section className="wardrobe-hero">
        <div className="wardrobe-intro">
          <div className="wardrobe-badge">✦ YOUR DIGITAL CLOSET</div>
          <h1>
            YOUR
            <br />
            <span>WARDROBE.</span>
          </h1>
          <p>
            Upload the clothes you already own and build your personal digital
            wardrobe. Use them later to create outfits, discover combinations
            and style your looks.
          </p>
        </div>

        <div className="wardrobe-upload-box">
          <div className="upload-icon">+</div>
          <h2>Add clothes</h2>
          <p>Upload photos of your favorite pieces.</p>
          <label className="wardrobe-upload-btn">
            ✦ Upload Clothes
            <input
              type="file"
              accept="image/png,image/jpeg,image/webp"
              multiple
              onChange={handleUpload}
              hidden
            />
          </label>
          <span>PNG, JPG or WEBP</span>
        </div>
      </section>

      <section className="wardrobe-section">
        <div className="wardrobe-heading">
          <div>
            <span>MY CLOSET</span>
            <h2>Your Pieces</h2>
          </div>
          <strong>{items.length} ITEMS</strong>
        </div>

        <div className="wardrobe-filters">
          {["All", "Tops", "Bottoms", "Dresses", "Shoes", "Accessories"].map(
            (filter) => (
              <button
                key={filter}
                className={category === filter ? "active-filter" : ""}
                onClick={() => setCategory(filter)}
              >
                {filter}
              </button>
            )
          )}
        </div>

        {loading ? (
          <div className="empty-wardrobe">
            <p>Loading your wardrobe…</p>
          </div>
        ) : filteredItems.length === 0 ? (
          <div className="empty-wardrobe">
            <div className="empty-plus">+</div>
            <h3>Your wardrobe is waiting.</h3>
            <p>Add your first clothing piece to start building your digital closet.</p>
            <label className="empty-upload">
              Add Your First Piece
              <input
                type="file"
                accept="image/png,image/jpeg,image/webp"
                multiple
                onChange={handleUpload}
                hidden
              />
            </label>
          </div>
        ) : (
          <div className="wardrobe-grid">
            {filteredItems.map((item) => (
              <article className="wardrobe-item" key={item.id}>
                <div className="wardrobe-image">
                  <img
                    src={
                      item.image_url?.startsWith("/uploads")
                        ? `${BASE_URL}${item.image_url}`
                        : item.image_url || item.image
                    }
                    alt={item.name}
                  />
                  <button
                    className="delete-item"
                    onClick={() => handleDelete(item.id)}
                  >
                    ×
                  </button>
                </div>
                <div className="wardrobe-item-info">
                  <strong>{item.name}</strong>
                  <span>{item.category}</span>
                </div>
              </article>
            ))}
          </div>
        )}
      </section>
    </main>
  );
}

export default Wardrobe;
