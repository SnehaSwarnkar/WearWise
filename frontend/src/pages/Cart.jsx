import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import Header from "./Header";
import "./Cart.css";
import { getCart, updateCartQuantity, removeFromCart } from "../api/cart";

function Cart() {
  const navigate = useNavigate();
  const [cart, setCart] = useState({ items: [], subtotal: 0, shipping: 0, total: 0 });
  const [loading, setLoading] = useState(true);

  const loadCart = () => {
    getCart()
      .then(setCart)
      .catch(() => setCart({ items: [], subtotal: 0, shipping: 0, total: 0 }))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadCart();
  }, []);

  const handleQuantityChange = async (itemId, change) => {
    const item = cart.items.find((i) => i.id === itemId);
    if (!item) return;
    const newQty = Math.max(1, (item.quantity || 1) + change);
    try {
      const updated = await updateCartQuantity(itemId, newQty);
      setCart(updated);
    } catch {
      // ignore
    }
  };

  const handleRemove = async (itemId) => {
    try {
      const updated = await removeFromCart(itemId);
      setCart(updated);
    } catch {
      // ignore
    }
  };

  if (loading) {
    return (
      <main className="cart-page">
        <Header />
        <section className="cart-hero">
          <div>
            <span className="cart-label">✦ YOUR SELECTION</span>
            <h1>YOUR<br /><span>BAG.</span></h1>
          </div>
        </section>
        <section className="cart-content">
          <div className="cart-empty">
            <p>Loading your bag…</p>
          </div>
        </section>
      </main>
    );
  }

  const items = cart.items || [];

  return (
    <main className="cart-page">
      <Header />

      {/* HERO */}
      <section className="cart-hero">
        <div>
          <span className="cart-label">✦ YOUR SELECTION</span>
          <h1>
            YOUR
            <br />
            <span>BAG.</span>
          </h1>
          <p>Everything you loved, selected and ready for your next look.</p>
        </div>
        <div className="cart-count">
          <strong>{items.length}</strong>
          <span>ITEMS</span>
        </div>
      </section>

      {/* CART */}
      <section className="cart-content">
        {items.length === 0 ? (
          <div className="cart-empty">
            <div className="cart-empty-icon">🛍</div>
            <h2>Your bag is waiting.</h2>
            <p>Explore fashion, find your favorites and add them to your bag.</p>
            <Link to="/explore" className="cart-action">
              Continue Shopping →
            </Link>
          </div>
        ) : (
          <div className="cart-layout">
            {/* ITEMS */}
            <div className="cart-items">
              <div className="cart-items-header">
                <span>
                  {items.length} SELECTED ITEM{items.length !== 1 ? "S" : ""}
                </span>
              </div>

              {items.map((item) => (
                <article className="cart-item" key={item.id}>
                  <div className="cart-item-image">
                    {item.image ? (
                      <img src={item.image} alt={item.name} />
                    ) : (
                      <div className="cart-item-placeholder">AI</div>
                    )}
                  </div>

                  <div className="cart-item-details">
                    <span className="cart-brand">{item.brand || "WEARWISE EDIT"}</span>
                    <h2>{item.name}</h2>
                    {item.color && <p>Color: {item.color}</p>}
                    {item.size && <p>Size: {item.size}</p>}

                    <div className="cart-item-bottom">
                      <div className="quantity-control">
                        <button
                          onClick={() => handleQuantityChange(item.id, -1)}
                          aria-label="Decrease quantity"
                        >
                          −
                        </button>
                        <span>{item.quantity || 1}</span>
                        <button
                          onClick={() => handleQuantityChange(item.id, 1)}
                          aria-label="Increase quantity"
                        >
                          +
                        </button>
                      </div>

                      <strong className="cart-price">
                        ₹{(item.price * (item.quantity || 1)).toLocaleString("en-IN")}
                      </strong>
                    </div>
                  </div>

                  <button
                    className="cart-remove"
                    onClick={() => handleRemove(item.id)}
                    aria-label="Remove item"
                  >
                    ×
                  </button>
                </article>
              ))}
            </div>

            {/* SUMMARY */}
            <aside className="order-summary">
              <div className="summary-heading">
                <span>ORDER SUMMARY</span>
                <span>✦</span>
              </div>

              <div className="summary-row">
                <span>Subtotal</span>
                <strong>₹{cart.subtotal.toLocaleString("en-IN")}</strong>
              </div>

              <div className="summary-row">
                <span>Shipping</span>
                <strong>{cart.shipping === 0 ? "FREE" : `₹${cart.shipping}`}</strong>
              </div>

              {cart.subtotal >= 2000 && (
                <div className="free-shipping">✦ You unlocked free shipping</div>
              )}

              <div className="summary-divider" />

              <div className="summary-total">
                <span>TOTAL</span>
                <strong>₹{cart.total.toLocaleString("en-IN")}</strong>
              </div>

              <button
                className="checkout-button"
                onClick={() => navigate("/checkout")}
              >
                Proceed to Checkout →
              </button>

              <Link to="/explore" className="continue-shopping">
                ← Continue Shopping
              </Link>
            </aside>
          </div>
        )}
      </section>
    </main>
  );
}

export default Cart;
