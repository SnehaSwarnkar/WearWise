import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import "./SavedLooks.css";
import Header from "./Header";
import { getSavedLooks, removeSavedLook } from "../api/saved";
import { getWishlist, removeFromWishlist } from "../api/saved";

function SavedLooks() {
  const [savedLooks, setSavedLooks] = useState([]);
  const [wishlist, setWishlist] = useState([]);
  const [activeTab, setActiveTab] = useState("looks");

  useEffect(() => {
    getSavedLooks().then(setSavedLooks).catch(() => setSavedLooks([]));
    getWishlist().then(setWishlist).catch(() => setWishlist([]));
  }, []);

  const handleRemoveLook = async (id) => {
    try {
      await removeSavedLook(id);
      setSavedLooks((prev) => prev.filter((l) => l.id !== id));
    } catch { /* ignore */ }
  };

  const handleRemoveWishlistItem = async (id) => {
    try {
      await removeFromWishlist(id);
      setWishlist((prev) => prev.filter((w) => w.id !== id));
    } catch { /* ignore */ }
  };

  return (
    <main className="saved-page">
         <Header />

      {/* HERO */}
      <section className="saved-hero">
        <div>
          <span className="saved-label">
            ✦ YOUR COLLECTION
          </span>

          <h1>
            SAVED
            <br />
            <span>FOR LATER.</span>
          </h1>

          <p>
            Keep your favorite outfits and fashion pieces in one place.
            Revisit them whenever you're ready to wear, compare or shop.
          </p>
        </div>

        <div className="saved-count-card">
          <strong>
            {savedLooks.length + wishlist.length}
          </strong>

          <span>
            SAVED ITEMS
          </span>
        </div>
      </section>


      {/* TABS */}
      <section className="saved-content">

        <div className="saved-tabs">

          <button
            className={activeTab === "looks" ? "active" : ""}
            onClick={() => setActiveTab("looks")}
          >
            ✦ Saved Looks
            <span>{savedLooks.length}</span>
          </button>

          <button
            className={activeTab === "wishlist" ? "active" : ""}
            onClick={() => setActiveTab("wishlist")}
          >
            ♡ Wishlist
            <span>{wishlist.length}</span>
          </button>

        </div>


        {/* SAVED LOOKS */}
        {activeTab === "looks" && (
          <section>

            {savedLooks.length === 0 ? (

              <div className="saved-empty">

                <div className="empty-symbol">
                  ✦
                </div>

                <h2>
                  No saved looks yet.
                </h2>

                <p>
                  When you find an outfit you love, save it here
                  so you can come back to it later.
                </p>

                <Link
                  to="/explore"
                  className="saved-action"
                >
                  Explore Looks →
                </Link>

              </div>

            ) : (

              <div className="looks-grid">

                {savedLooks.map((look) => (

                  <article
                    className="saved-look-card"
                    key={look.id}
                  >

                    <div className="saved-look-image">

                      <img
                        src={look.image}
                        alt={look.name}
                      />

                      <button
                        className="remove-save"
                        onClick={() => handleRemoveLook(look.id)}
                        aria-label="Remove saved look"
                      >
                        ×
                      </button>

                    </div>

                    <div className="saved-look-info">

                      <span>
                        SAVED LOOK
                      </span>

                      <h3>
                        {look.name}
                      </h3>

                      <p>
                        {look.description}
                      </p>

                      <button className="view-look">
                        View Look →
                      </button>

                    </div>

                  </article>

                ))}

              </div>

            )}

          </section>
        )}


        {/* WISHLIST */}
        {activeTab === "wishlist" && (
          <section>

            {wishlist.length === 0 ? (

              <div className="saved-empty">

                <div className="empty-symbol">
                  ♡
                </div>

                <h2>
                  Your wishlist is empty.
                </h2>

                <p>
                  Save products you love and keep them here
                  for your next shopping session.
                </p>

                <Link
                  to="/explore"
                  className="saved-action"
                >
                  Discover Products →
                </Link>

              </div>

            ) : (

              <div className="wishlist-grid">

                {wishlist.map((item) => (

                  <article
                    className="wishlist-card"
                    key={item.id}
                  >

                    <div className="wishlist-image">

                      <img
                        src={item.image}
                        alt={item.name}
                      />

                      <button
                        className="remove-save"
                        onClick={() =>
                          handleRemoveWishlistItem(item.id)
                        }
                        aria-label="Remove wishlist item"
                      >
                        ×
                      </button>

                    </div>

                    <div className="wishlist-info">

                      <span>
                        {item.brand || "FASHION"}
                      </span>

                      <h3>
                        {item.name}
                      </h3>

                      <strong>
                        {item.price || ""}
                      </strong>

                    </div>

                  </article>

                ))}

              </div>

            )}

          </section>
        )}

      </section>

    </main>
  );
}

export default SavedLooks;