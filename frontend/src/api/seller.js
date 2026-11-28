import { api } from "./client";

export function fetchSellerDashboard() {
  return api.get("/api/seller/dashboard");
}

export function fetchSellerProducts() {
  return api.get("/api/seller/products");
}

export function createSellerProduct(payload) {
  return api.post("/api/seller/products", payload);
}

export function updateSellerProduct(productId, payload) {
  return api.patch(`/api/seller/products/${encodeURIComponent(productId)}`, payload);
}

export function fetchSellerOrders() {
  return api.get("/api/seller/orders");
}

export function updateSellerOrderStatus(orderId, status) {
  return api.patch(`/api/seller/orders/${encodeURIComponent(orderId)}/status`, { status });
}

export function fetchSellerProfile() {
  return api.get("/api/seller/profile");
}

export function updateSellerProfile(payload) {
  return api.patch("/api/seller/profile", payload);
}
