import { api, getSessionId } from "./client";

// ── Saved Looks ──────────────────────────────────────────────────────────────

export function getSavedLooks() {
  return api.get(`/api/saved/looks/${getSessionId()}`);
}

export function saveLook(look) {
  return api.post("/api/saved/looks", {
    session_id: getSessionId(),
    ...look,
  });
}

export function removeSavedLook(lookId) {
  return api.delete(`/api/saved/looks/${lookId}`);
}

// ── Wishlist ─────────────────────────────────────────────────────────────────

export function getWishlist() {
  return api.get(`/api/saved/wishlist/${getSessionId()}`);
}

export function addToWishlist(product) {
  return api.post("/api/saved/wishlist", {
    session_id: getSessionId(),
    product_id: product.id,
    name: product.name,
    price: product.price,
    image: product.image || null,
    brand: product.brand || null,
  });
}

export function removeFromWishlist(itemId) {
  return api.delete(`/api/saved/wishlist/${itemId}`);
}
