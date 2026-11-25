import { api } from "./client";

/**
 * Fetch products, optionally filtered by category and sorted by price.
 * @param {string|null} category  - "All" | "Tops" | "Jeans" | "Dresses" | "Jackets"
 * @param {boolean}     sortPrice - sort ascending by price
 */
export function fetchProducts(category = null, sortPrice = false) {
  const params = new URLSearchParams();
  if (category && category !== "All") params.set("category", category);
  if (sortPrice) params.set("sort_price", "true");
  const query = params.toString();
  return api.get(`/api/products/${query ? "?" + query : ""}`);
}

export function fetchProduct(id) {
  return api.get(`/api/products/${id}`);
}

export function fetchProductBySku(sku) {
  return api.get(`/api/products/sku/${encodeURIComponent(sku)}`);
}

export function fetchProductReviews(sku) {
  return api.get(`/api/products/sku/${encodeURIComponent(sku)}/reviews`);
}

export function submitProductReview(sku, payload) {
  const token = localStorage.getItem("ww-token");
  const headers = token ? { Authorization: `Bearer ${token}` } : {};
  return api.post(`/api/products/sku/${encodeURIComponent(sku)}/reviews`, payload, headers);
}
