import { useEffect, useState } from "react";
import "./Wardrobe.css";
import Header from "./Header";

function Wardrobe() {
  const [items, setItems] = useState(() => {
    const saved = localStorage.getItem("wearwise-wardrobe");
    return saved ? JSON.parse(saved) : [];
  });

  const [category, setCategory] = useState("All");

  useEffect(() => {
    localStorage.setItem("wearwise-wardrobe", JSON.stringify(items));
  }, [items]);

  const handleUpload = (event) => {
    const files = Array.from(event.target.files);

    files.forEach((file) => {
      const reader = new FileReader();

      reader.onload = () => {
        const newItem = {
          id: Date.now() + Math.random(),
          name: file.name,
          category: "Tops",
          image: reader.result,
        };

        setItems((prev) => [...prev, newItem]);
      };

      reader.readAsDataURL(file);
    });

    event.target.value = "";
  };

  const deleteItem = (id) => {
    setItems((prev) => prev.filter((item) => item.id !== id));
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
          <div className="wardrobe-badge">
            ✦ YOUR DIGITAL CLOSET
          </div>

          <h1>
            YOUR
            <br />
            <span>WARDROBE.</span>
          </h1>

          <p>
            Upload the clothes you already own and build your personal
            digital wardrobe. Use them later to create outfits,
            discover combinations and style your looks.
          </p>
        </div>

        <div className="wardrobe-upload-box">

          <div className="upload-icon">
            +
          </div>

          <h2>Add clothes</h2>

          <p>
            Upload photos of your favorite pieces.
          </p>

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

          <span>
            PNG, JPG or WEBP
          </span>

        </div>

      </section>

      <section className="wardrobe-section">

        <div className="wardrobe-heading">
          <div>
            <span>MY CLOSET</span>
            <h2>Your Pieces</h2>
          </div>

          <strong>
            {items.length} ITEMS
          </strong>
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

        {filteredItems.length === 0 ? (
          <div className="empty-wardrobe">

            <div className="empty-plus">+</div>

            <h3>Your wardrobe is waiting.</h3>

            <p>
              Add your first clothing piece to start building your
              digital closet.
            </p>

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
                    src={item.image}
                    alt={item.name}
                  />

                  <button
                    className="delete-item"
                    onClick={() => deleteItem(item.id)}
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