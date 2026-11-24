import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import Header from "./Header";
import "../App.css";

function OrderConfirmation() {
  const [order, setOrder] = useState(null);

  useEffect(() => {
    const saved = localStorage.getItem("wearwise-last-order");
    if (saved) {
      setOrder(JSON.parse(saved));
    }
  }, []);

  return (
    <div className="order-confirm-page">
      <Header />

      <main className="order-confirm-main">

        <div className="order-confirm-card">

          <div className="order-confirm-icon">✦</div>

          <span className="order-confirm-label">ORDER CONFIRMED</span>

          <h1>
            YOUR LOOK
            <br />
            IS ON ITS WAY.
          </h1>

          {order && (
            <div className="order-confirm-details">
              <div className="order-confirm-row">
                <span>ORDER ID</span>
                <strong>#{order.id}</strong>
              </div>

              <div className="order-confirm-row">
                <span>TOTAL</span>
                <strong>₹{order.total?.toLocaleString("en-IN")}</strong>
              </div>

              <div className="order-confirm-row">
                <span>PAYMENT</span>
                <strong>{order.paymentMethod?.toUpperCase()}</strong>
              </div>

              <div className="order-confirm-row">
                <span>DELIVERY TO</span>
                <strong>
                  {order.customer?.firstName} {order.customer?.lastName},&nbsp;
                  {order.customer?.city}
                </strong>
              </div>
            </div>
          )}

          <p className="order-confirm-note">
            You'll receive a confirmation on{" "}
            <strong>{order?.customer?.email || "your email"}</strong>.
            Your order will be delivered in 5–7 business days.
          </p>

          <div className="order-confirm-actions">
            <Link to="/explore" className="order-confirm-btn primary">
              Continue Shopping →
            </Link>

            <Link to="/" className="order-confirm-btn secondary">
              Back to Home
            </Link>
          </div>

        </div>

      </main>
    </div>
  );
}

export default OrderConfirmation;
