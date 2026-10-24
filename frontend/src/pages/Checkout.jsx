import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import Header from "./Header";
import "./Checkout.css";

function Checkout() {
  const navigate = useNavigate();

  const [cart, setCart] = useState(() => {
    const saved = localStorage.getItem("wearwise-cart");
    return saved ? JSON.parse(saved) : [];
  });

  const [paymentMethod, setPaymentMethod] = useState("upi");

  const [form, setForm] = useState({
    firstName: "",
    lastName: "",
    email: "",
    phone: "",
    address: "",
    city: "",
    state: "",
    pincode: "",
  });

  useEffect(() => {
    if (cart.length === 0) {
      return;
    }
  }, [cart]);

  const updateForm = (e) => {
    const { name, value } = e.target;

    setForm((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const subtotal = useMemo(() => {
    return cart.reduce((total, item) => {
      const price =
        Number(
          String(item.price || "").replace(/[^\d.]/g, "")
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

  const handlePlaceOrder = (e) => {
    e.preventDefault();

    const order = {
      id: `WW${Date.now().toString().slice(-6)}`,
      items: cart,
      customer: form,
      paymentMethod,
      subtotal,
      shipping,
      total,
      createdAt: new Date().toISOString(),
      status: "Confirmed",
    };

    localStorage.setItem(
      "wearwise-last-order",
      JSON.stringify(order)
    );

    const existingOrders =
      JSON.parse(
        localStorage.getItem("wearwise-orders") || "[]"
      );

    localStorage.setItem(
      "wearwise-orders",
      JSON.stringify([
        order,
        ...existingOrders,
      ])
    );

    localStorage.removeItem("wearwise-cart");

    navigate("/order-confirmation");
  };

  if (cart.length === 0) {
    return (
      <main className="checkout-page">
        <Header />

        <section className="checkout-empty">
          <div className="checkout-empty-icon">
            🛍
          </div>

          <h1>
            YOUR BAG IS EMPTY.
          </h1>

          <p>
            Add something you love before heading
            to checkout.
          </p>

          <Link
            to="/explore"
            className="checkout-back"
          >
            Explore Fashion →
          </Link>
        </section>
      </main>
    );
  }

  return (
    <main className="checkout-page">

      <Header />

      {/* PAGE INTRO */}
      <section className="checkout-hero">

        <div>
          <span className="checkout-label">
            ✦ SECURE CHECKOUT
          </span>

          <h1>
            COMPLETE
            <br />
            <span>YOUR LOOK.</span>
          </h1>
        </div>

        <div className="checkout-step">
          <span>01</span>
          <strong>CHECKOUT</strong>
          <small>READY TO ORDER</small>
        </div>

      </section>


      {/* CHECKOUT */}
      <form
        className="checkout-layout"
        onSubmit={handlePlaceOrder}
      >

        {/* LEFT */}
        <div className="checkout-form">

          {/* CONTACT */}
          <section className="checkout-section">

            <div className="section-title">
              <span>01</span>
              <h2>Contact Details</h2>
            </div>

            <div className="form-grid">

              <div className="form-field">
                <label>First Name</label>

                <input
                  type="text"
                  name="firstName"
                  value={form.firstName}
                  onChange={updateForm}
                  placeholder="Your first name"
                  required
                />
              </div>

              <div className="form-field">
                <label>Last Name</label>

                <input
                  type="text"
                  name="lastName"
                  value={form.lastName}
                  onChange={updateForm}
                  placeholder="Your last name"
                  required
                />
              </div>

              <div className="form-field">
                <label>Email</label>

                <input
                  type="email"
                  name="email"
                  value={form.email}
                  onChange={updateForm}
                  placeholder="you@example.com"
                  required
                />
              </div>

              <div className="form-field">
                <label>Phone</label>

                <input
                  type="tel"
                  name="phone"
                  value={form.phone}
                  onChange={updateForm}
                  placeholder="+91 98765 43210"
                  required
                />
              </div>

            </div>

          </section>


          {/* DELIVERY */}
          <section className="checkout-section">

            <div className="section-title">
              <span>02</span>
              <h2>Delivery Address</h2>
            </div>

            <div className="form-grid">

              <div className="form-field full">
                <label>Address</label>

                <input
                  type="text"
                  name="address"
                  value={form.address}
                  onChange={updateForm}
                  placeholder="House number, street and area"
                  required
                />
              </div>

              <div className="form-field">
                <label>City</label>

                <input
                  type="text"
                  name="city"
                  value={form.city}
                  onChange={updateForm}
                  placeholder="City"
                  required
                />
              </div>

              <div className="form-field">
                <label>State</label>

                <input
                  type="text"
                  name="state"
                  value={form.state}
                  onChange={updateForm}
                  placeholder="State"
                  required
                />
              </div>

              <div className="form-field">
                <label>PIN Code</label>

                <input
                  type="text"
                  name="pincode"
                  value={form.pincode}
                  onChange={updateForm}
                  placeholder="000000"
                  required
                />
              </div>

            </div>

          </section>


          {/* PAYMENT */}
          <section className="checkout-section">

            <div className="section-title">
              <span>03</span>
              <h2>Payment</h2>
            </div>

            <div className="payment-options">

              <label
                className={
                  paymentMethod === "upi"
                    ? "payment-option active"
                    : "payment-option"
                }
              >
                <input
                  type="radio"
                  name="payment"
                  value="upi"
                  checked={paymentMethod === "upi"}
                  onChange={() =>
                    setPaymentMethod("upi")
                  }
                />

                <div>
                  <strong>UPI</strong>
                  <small>Google Pay, PhonePe, Paytm</small>
                </div>

                <span>✓</span>
              </label>


              <label
                className={
                  paymentMethod === "card"
                    ? "payment-option active"
                    : "payment-option"
                }
              >
                <input
                  type="radio"
                  name="payment"
                  value="card"
                  checked={paymentMethod === "card"}
                  onChange={() =>
                    setPaymentMethod("card")
                  }
                />

                <div>
                  <strong>Card</strong>
                  <small>Credit or debit card</small>
                </div>

                <span>✓</span>
              </label>


              <label
                className={
                  paymentMethod === "cod"
                    ? "payment-option active"
                    : "payment-option"
                }
              >
                <input
                  type="radio"
                  name="payment"
                  value="cod"
                  checked={paymentMethod === "cod"}
                  onChange={() =>
                    setPaymentMethod("cod")
                  }
                />

                <div>
                  <strong>Cash on Delivery</strong>
                  <small>Pay when your order arrives</small>
                </div>

                <span>✓</span>
              </label>

            </div>

          </section>

        </div>


        {/* RIGHT — ORDER REVIEW */}
        <aside className="checkout-summary">

          <div className="summary-top">
            <span>YOUR ORDER</span>
            <span>✦</span>
          </div>


          <div className="checkout-items">

            {cart.map((item) => (

              <div
                className="checkout-item"
                key={item.id}
              >

                <div className="checkout-item-image">
                  <img
                    src={item.image}
                    alt={item.name}
                  />

                  <span>
                    {item.quantity || 1}
                  </span>
                </div>

                <div className="checkout-item-info">
                  <strong>{item.name}</strong>

                  <small>
                    {item.brand || "WEARWISE"}
                  </small>
                </div>

                <strong>
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

            ))}

          </div>


          <div className="summary-line">
            <span>Subtotal</span>
            <strong>
              ₹{subtotal.toLocaleString("en-IN")}
            </strong>
          </div>

          <div className="summary-line">
            <span>Shipping</span>

            <strong>
              {shipping === 0
                ? "FREE"
                : `₹${shipping}`}
            </strong>
          </div>

          <div className="checkout-divider" />

          <div className="checkout-total">
            <span>TOTAL</span>

            <strong>
              ₹{total.toLocaleString("en-IN")}
            </strong>
          </div>


          <button
            type="submit"
            className="place-order"
          >
            Place Order →
          </button>

          <p className="secure-note">
            🔒 Your order information is secure.
          </p>

        </aside>

      </form>

    </main>
  );
}

export default Checkout;