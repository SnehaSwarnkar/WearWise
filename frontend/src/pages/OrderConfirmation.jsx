import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import Header from "./Header";
import { getOrderDetail } from "../api/orders";
import "../App.css";

function OrderConfirmation() {
  const [searchParams] = useSearchParams();
  const orderIdParam = searchParams.get("orderId");
  const [order, setOrder] = useState(null);
  const [loadError, setLoadError] = useState(null);

  useEffect(() => {
    const saved = localStorage.getItem("wearwise-last-order");
    const parsedSaved = saved ? JSON.parse(saved) : null;
    const targetId = orderIdParam || parsedSaved?.id;
    if (!targetId) return;

    getOrderDetail(targetId)
      .then((fetched) => {
        setOrder(fetched);
        localStorage.setItem("wearwise-last-order", JSON.stringify(fetched));
      })
      .catch((err) => {
        if (parsedSaved && parsedSaved.id === targetId) {
          setOrder(parsedSaved);
        } else {
          setLoadError(err.message || "Could not load order confirmation");
        }
      });
  }, [orderIdParam]);

  return (
    <div className="order-confirm-page">
      <Header />

      <main className="order-confirm-main">

        <div className="order-confirm-card">

          <div className="order-confirm-icon">✦</div>

          <span className="order-confirm-label" data-testid="confirm-demo-label">
            DEMO ORDER RECORDED · NO REAL PAYMENT CAPTURED
          </span>

          <h1>
            YOUR DEMO ORDER
            <br />
            IS RECORDED.
          </h1>

          {loadError && (
            <div style={{ color: "#991b1b", fontSize: "13px", fontWeight: 700, marginBottom: "12px" }}>
              {loadError}
            </div>
          )}

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
                <strong>{order.paymentMethod?.toUpperCase()} ({order.payment_status || "DEMO_NO_PAYMENT_CAPTURED"})</strong>
              </div>

              <div className="order-confirm-row">
                <span>DELIVERY TO</span>
                <strong>
                  {order.customer?.firstName} {order.customer?.lastName},&nbsp;
                  {order.customer?.city}
                </strong>
              </div>

              {order.items && order.items.length > 0 && (
                <div style={{ marginTop: "12px", borderTop: "1px dashed var(--border-soft)", paddingTop: "10px" }}>
                  <span style={{ fontSize: "11px", fontWeight: 700, letterSpacing: "0.06em", color: "var(--text-soft)", display: "block", marginBottom: "6px" }}>ORDERED ITEMS:</span>
                  <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                    {order.items.map((it, idx) => (
                      <div key={idx} style={{ display: "flex", justifyContent: "space-between", fontSize: "13px" }}>
                        <span>
                          {it.name} {it.size ? <strong style={{ color: "var(--pink)" }}>(Size {it.size})</strong> : null} × {it.quantity || 1}
                        </span>
                        <strong>₹{((it.price || 0) * (it.quantity || 1)).toLocaleString("en-IN")}</strong>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          <p className="order-confirm-note">
            You'll receive a confirmation on{" "}
            <strong>{order?.customer?.email || "your email"}</strong>.
            Your order will be delivered in 5–7 business days.
          </p>

          <div className="order-confirm-actions">
            <Link to="/orders" className="order-confirm-btn primary">
              View Order History →
            </Link>

            <Link to="/explore" className="order-confirm-btn secondary">
              Continue Shopping
            </Link>
          </div>

        </div>

      </main>
    </div>
  );
}

export default OrderConfirmation;
