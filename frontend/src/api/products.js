import { api } from "./client";

/**
 * Fetch catalog products with backend filters, search, price range, and sort.
 */
export function fetchProducts(category = null, sortPrice = false, extra = {}) {
  const params = new URLSearchParams();
  if (category && category !== "All") params.set("category", category);
  if (sortPrice) params.set("sort_price", "true");
  if (extra.gender && extra.gender !== "all") params.set("gender", extra.gender);
  if (extra.occasion) params.set("occasion", extra.occasion);
  if (extra.search) params.set("search", extra.search);
  if (extra.min_price !== undefined && extra.min_price !== "" && extra.min_price !== null) {
    params.set("min_price", String(extra.min_price));
  }
  if (extra.max_price !== undefined && extra.max_price !== "" && extra.max_price !== null) {
    params.set("max_price", String(extra.max_price));
  }
  if (extra.sort) params.set("sort", extra.sort);
  const query = params.toString();
  return api.get(`/api/products/${query ? "?" + query : ""}`);
}

export function fetchRecommendations(gender = null, limit = 8) {
  const params = new URLSearchParams();
  if (gender) params.set("gender", gender);
  if (limit) params.set("limit", String(limit));
  return api.get(`/api/products/recommendations?${params.toString()}`);
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
  return api.post(`/api/products/sku/${encodeURIComponent(sku)}/reviews`, payload);
}
