import { api, getSessionId } from "./client";

export function getCart() {
  return api.get(`/api/cart/${getSessionId()}`);
}

export function addToCart(item) {
  return api.post("/api/cart/add", {
    session_id: getSessionId(),
    item,
  });
}

export function updateCartQuantity(itemId, quantity, size = null) {
  return api.put("/api/cart/update", {
    session_id: getSessionId(),
    item_id: itemId,
    quantity,
    size,
  });
}

export function removeFromCart(itemId, size = null) {
  const qs = size ? `?size=${encodeURIComponent(size)}` : "";
  return api.delete(`/api/cart/${getSessionId()}/${itemId}${qs}`);
}

export function clearCart() {
  return api.delete(`/api/cart/${getSessionId()}`);
}
