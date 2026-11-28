import { api, getCsrfToken, getSessionId, getStoreApiBase } from "./client";

// ── Place order ───────────────────────────────────────────────────────────────

export function placeOrder(customer, paymentMethod, idempotencyKey = null) {
  return api.post("/api/orders/place", {
    session_id: getSessionId(),
    customer,
    paymentMethod,
    idempotency_key: idempotencyKey,
  });
}

// ── My orders (authenticated shopper) ─────────────────────────────────────────

export async function getMyOrders() {
  return api.get("/api/orders/my");
}

// ── Order detail (authenticated shopper or matching session) ──────────────────

export async function getOrderDetail(orderId) {
  const res = await fetch(`${getStoreApiBase()}/api/orders/detail/${orderId}`, {
    credentials: "include",
    headers: {
      "X-Session-Id": getSessionId(),
      ...(getCsrfToken() ? { "X-CSRF-Token": getCsrfToken() } : {}),
    },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Order not found");
  }
  return res.json();
}

// ── Legacy session-based (guest) ──────────────────────────────────────────────

export function getOrders() {
  return api.get(`/api/orders/${getSessionId()}`);
}
