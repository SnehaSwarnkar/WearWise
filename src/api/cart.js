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

export function updateCartQuantity(itemId, quantity) {
  return api.put("/api/cart/update", {
    session_id: getSessionId(),
    item_id: itemId,
    quantity,
  });
}

export function removeFromCart(itemId) {
  return api.delete(`/api/cart/${getSessionId()}/${itemId}`);
}

export function clearCart() {
  return api.delete(`/api/cart/${getSessionId()}`);
}
