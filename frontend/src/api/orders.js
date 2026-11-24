import { api, getSessionId } from "./client";
import { getToken } from "./auth";

const STORE_BASE_URL = import.meta.env.VITE_STORE_API_URL || "http://127.0.0.1:8001";

// ── Place order ───────────────────────────────────────────────────────────────

export function placeOrder(customer, paymentMethod) {
  const token = getToken();
  return api.post(
    "/api/orders/place",
    {
      session_id: getSessionId(),
      customer,
      paymentMethod,
    },
    token ? { Authorization: `Bearer ${token}` } : {}
  );
}

// ── My orders (authenticated) ─────────────────────────────────────────────────

export async function getMyOrders() {
  const token = getToken();
  if (!token) throw new Error("Not authenticated");
  const res = await fetch(`${STORE_BASE_URL}/api/orders/my`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to load orders");
  }
  return res.json();
}

// ── Order detail (authenticated) ──────────────────────────────────────────────

export async function getOrderDetail(orderId) {
  const token = getToken();
  const headers = token ? { Authorization: `Bearer ${token}` } : {};
  const res = await fetch(`${STORE_BASE_URL}/api/orders/detail/${orderId}`, { headers });
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
