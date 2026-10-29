import { useEffect, useState, useCallback } from "react";
import { Link, useNavigate } from "react-router-dom";
import Header from "./Header";
import { useAuth } from "../context/AuthContext";
import { getMyOrders } from "../api/orders";
import "../App.css";

// ── Status badge colours ──────────────────────────────────────────────────────
const STATUS_META = {
  Confirmed:  { label: "Confirmed",  cls: "order-badge-confirmed"  },
  Processing: { label: "Processing", cls: "order-badge-processing" },
  Shipped:    { label: "Shipped",    cls: "order-badge-shipped"    },
  Delivered:  { label: "Delivered",  cls: "order-badge-delivered"  },
  Cancelled:  { label: "Cancelled",  cls: "order-badge-cancelled"  },
  Pending:    { label: "Pending",    cls: "order-badge-pending"    },
};

function StatusBadge({ status }) {
  const meta = STATUS_META[status] || { label: status, cls: "order-badge-pending" };
  return <span className={`order-badge ${meta.cls}`}>{meta.label}</span>;
}

function formatDate(iso) {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString("en-IN", {
    day: "numeric", month: "short", year: "numeric",
  });
}

function formatPrice(n) {
  return `₹${Number(n || 0).toLocaleString("en-IN")}`;
}

// ── Skeleton loader ───────────────────────────────────────────────────────────
function OrderSkeleton() {
  return (
    <div className="order-card order-skeleton">
      <div className="order-card-header">
        <div className="sk-block sk-title" />
        <div className="sk-block sk-badge" />
      </div>
      <div className="order-items-list">
        {[1, 2].map((i) => (
          <div key={i} className="order-item-row">
            <div className="sk-block sk-thumb" />
            <div className="order-item-info">
              <div className="sk-block sk-line sk-w60" />
              <div className="sk-block sk-line sk-w40" />
            </div>
            <div className="sk-block sk-price" />
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Empty state ───────────────────────────────────────────────────────────────
function EmptyOrders() {
  return (
    <div className="orders-empty">
      <div className="orders-empty-icon">🛍</div>
      <h2>No orders yet</h2>
      <p>
        Your fashion journey starts here. Explore the collection and find
        something you love.
      </p>
      <Link to="/explore" className="orders-empty-cta">
        Shop Now ✦
      </Link>
    </div>
  );
}

// ── Error state ───────────────────────────────────────────────────────────────
function ErrorState({ message, onRetry }) {
  return (
    <div className="orders-error">
      <div className="orders-error-icon">⚠</div>
      <h2>Something went wrong</h2>
      <p>{message || "We couldn't load your orders. Please try again."}</p>
      <button className="orders-retry-btn" onClick={onRetry}>
        Retry
      </button>
    </div>
  );
}

// ── Single order card ─────────────────────────────────────────────────────────
function OrderCard({ order }) {
  const [expanded, setExpanded] = useState(false);
  const itemCount = order.items?.length ?? 0;

  return (
    <article className="order-card">
      {/* HEADER ROW */}
      <div className="order-card-header">
        <div className="order-card-meta">
          <span className="order-id">#{order.id}</span>
          <span className="order-date">{formatDate(order.createdAt)}</span>
        </div>
        <StatusBadge status={order.status} />
      </div>

      {/* ITEMS */}
      <ul className="order-items-list">
        {(expanded ? order.items : order.items?.slice(0, 2))?.map((item, idx) => (
          <li key={`${item.id}-${idx}`} className="order-item-row">
            <div className="order-item-thumb">
              {item.image ? (
                <img src={item.image} alt={item.name} loading="lazy" />
              ) : (
                <div className="order-item-thumb-placeholder">
                  <span>AI</span>
                </div>
              )}
            </div>
            <div className="order-item-info">
              <strong>{item.name}</strong>
              <span>{item.brand || "WEARWISE"}</span>
              {item.color && <span>Color: {item.color}</span>}
              {item.size  && <span>Size: {item.size}</span>}
              <span>Qty: {item.quantity || 1}</span>
            </div>
            <div className="order-item-price">
              {formatPrice(item.price * (item.quantity || 1))}
            </div>
          </li>
        ))}
      </ul>

      {/* SHOW MORE / LESS */}
      {itemCount > 2 && (
        <button
          className="order-show-more"
          onClick={() => setExpanded((e) => !e)}
        >
          {expanded ? "Show less" : `+${itemCount - 2} more item${itemCount - 2 !== 1 ? "s" : ""}`}
        </button>
      )}

      {/* FOOTER */}
      <div className="order-card-footer">
        <div className="order-totals">
          <span>
            Subtotal <strong>{formatPrice(order.subtotal)}</strong>
          </span>
          <span>
            Shipping{" "}
            <strong>{order.shipping === 0 ? "FREE" : formatPrice(order.shipping)}</strong>
          </span>
          <span className="order-total-row">
            Total <strong>{formatPrice(order.total)}</strong>
          </span>
        </div>

        <div className="order-footer-actions">
          <span className="order-payment-method">
            {order.paymentMethod?.toUpperCase()}
          </span>
          <Link
            to={`/orders/${order.id}`}
            className="order-detail-btn"
          >
            View Details →
          </Link>
        </div>
      </div>
    </article>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────
export default function MyOrders() {
  const { user, loading: authLoading } = useAuth();
  const navigate = useNavigate();

  const [orders, setOrders]   = useState([]);
  const [status, setStatus]   = useState("idle"); // idle | loading | success | error
  const [errMsg, setErrMsg]   = useState("");

  const fetchOrders = useCallback(async () => {
    setStatus("loading");
    setErrMsg("");
    try {
      const data = await getMyOrders();
      setOrders(data);
      setStatus("success");
    } catch (err) {
      setErrMsg(err.message || "Could not load orders");
      setStatus("error");
    }
  }, []);

  useEffect(() => {
    if (authLoading) return;
    if (!user) { navigate("/login"); return; }
    fetchOrders();
  }, [user, authLoading, fetchOrders, navigate]);

  return (
    <div className="orders-page">
      <Header />

      {/* PAGE HERO */}
      <section className="orders-hero">
        <div className="orders-hero-inner">
          <span className="orders-eyebrow">✦ YOUR ACCOUNT</span>
          <h1 className="orders-title">
            MY
            <br />
            <span>ORDERS.</span>
          </h1>
          <p className="orders-subtitle">
            Track and manage your fashion orders.
          </p>
        </div>

        {status === "success" && (
          <div className="orders-count-card">
            <strong>{orders.length}</strong>
            <span>{orders.length === 1 ? "ORDER" : "ORDERS"}</span>
          </div>
        )}
      </section>

      {/* CONTENT */}
      <section className="orders-content">

        {(status === "idle" || status === "loading") && (
          <>
            <OrderSkeleton />
            <OrderSkeleton />
          </>
        )}

        {status === "error" && (
          <ErrorState message={errMsg} onRetry={fetchOrders} />
        )}

        {status === "success" && orders.length === 0 && <EmptyOrders />}

        {status === "success" && orders.length > 0 && (
          <div className="orders-list">
            {orders.map((order) => (
              <OrderCard key={order.id} order={order} />
            ))}
          </div>
        )}

      </section>
    </div>
  );
}
