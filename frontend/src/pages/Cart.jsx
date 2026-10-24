import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import Header from "./Header";
import "./Cart.css";

function Cart() {
  const [cart, setCart] = useState(() => {
    const saved = localStorage.getItem("wearwise-cart");
    return saved ? JSON.parse(saved) : [];
  });

  useEffect(() => {
    localStorage.setItem("wearwise-cart", JSON.stringify(cart));
  }, [cart]);

  const updateQuantity = (id, change) => {
    setCart((prev) =>
      prev
        .map((item) =>
          item.id === id
            ? {
                ...item,
                quantity: Math.max(
                  1,
                  (item.quantity || 1) + change
                ),
              }
            : item
        )
    );
  };

  const removeItem = (id) => {
    setCart((prev) =>
      prev.filter((item) => item.id !== id)
    );
  };

  const subtotal = useMemo(() => {
    return cart.reduce((total, item) => {
      const price =
        Number(
          String(item.price || "")
            .replace(/[^\d.]/g, "")
        ) || 0;

      return total + price * (item.quantity || 1);
    }, 0);
  }, [cart]);

  const shipping =
    subtotal === 0
      ? 0
      : subtotal >= 2000
      ? 0
      : 99;

  const total = subtotal + shipping;

  return (
    <main className="cart-page">

      <Header />

      {/* HERO */}
      <section className="cart-hero">
        <div>
          <span className="cart-label">
            ✦ YOUR SELECTION
          </span>

          <h1>
            YOUR
            <br />
            <span>BAG.</span>
          </h1>

          <p>
            Everything you loved, selected and ready
            for your next look.
          </p>
        </div>

        <div className="cart-count">
          <strong>{cart.length}</strong>
          <span>ITEMS</span>
        </div>
      </section>


      {/* CART */}
      <section className="cart-content">

        {cart.length === 0 ? (

          <div className="cart-empty">

            <div className="cart-empty-icon">
              🛍
            </div>

            <h2>
              Your bag is waiting.
            </h2>

            <p>
              Explore fashion, find your favorites and
              add them to your bag.
            </p>

            <Link
              to="/explore"
              className="cart-action"
            >
              Continue Shopping →
            </Link>

          </div>

        ) : (

          <div className="cart-layout">

            {/* ITEMS */}
            <div className="cart-items">

              <div className="cart-items-header">
                <span>
                  {cart.length} SELECTED ITEM
                  {cart.length !== 1 ? "S" : ""}
                </span>
              </div>

              {cart.map((item) => (

                <article
                  className="cart-item"
                  key={item.id}
                >

                  <div className="cart-item-image">
                    <img
                      src={item.image}
                      alt={item.name}
                    />
                  </div>

                  <div className="cart-item-details">

                    <span className="cart-brand">
                      {item.brand || "WEARWISE EDIT"}
                    </span>

                    <h2>
                      {item.name}
                    </h2>

                    {item.color && (
                      <p>
                        Color: {item.color}
                      </p>
                    )}

                    {item.size && (
                      <p>
                        Size: {item.size}
                      </p>
                    )}

                    <div className="cart-item-bottom">

                      <div className="quantity-control">

                        <button
                          onClick={() =>
                            updateQuantity(item.id, -1)
                          }
                          aria-label="Decrease quantity"
                        >
                          −
                        </button>

                        <span>
                          {item.quantity || 1}
                        </span>

                        <button
                          onClick={() =>
                            updateQuantity(item.id, 1)
                          }
                          aria-label="Increase quantity"
                        >
                          +
                        </button>

                      </div>

                      <strong className="cart-price">
                        ₹
                        {(
                          (Number(
                            String(item.price || "")
                              .replace(/[^\d.]/g, "")
                          ) || 0) *
                          (item.quantity || 1)
                        ).toLocaleString("en-IN")}
                      </strong>

                    </div>

                  </div>

                  <button
                    className="cart-remove"
                    onClick={() => removeItem(item.id)}
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
                <strong>
                  ₹{subtotal.toLocaleString("en-IN")}
                </strong>
              </div>

              <div className="summary-row">
                <span>Shipping</span>

                <strong>
                  {shipping === 0
                    ? "FREE"
                    : `₹${shipping}`}
                </strong>
              </div>

              {subtotal >= 2000 && (
                <div className="free-shipping">
                  ✦ You unlocked free shipping
                </div>
              )}

              <div className="summary-divider" />

              <div className="summary-total">
                <span>TOTAL</span>

                <strong>
                  ₹{total.toLocaleString("en-IN")}
                </strong>
              </div>

              <button className="checkout-button">
                Proceed to Checkout →
              </button>

              <Link
                to="/explore"
                className="continue-shopping"
              >
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