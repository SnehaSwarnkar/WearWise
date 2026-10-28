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
