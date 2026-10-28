const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

/**
 * @param {"men"|"women"|"boys"|"girls"} gender
 * @param {object} filters  { category, occasion, age_group, sort_price }
 */
export async function fetchCatalogue(gender, filters = {}) {
  const params = new URLSearchParams();
  if (filters.category)  params.set("category",  filters.category);
  if (filters.occasion)  params.set("occasion",  filters.occasion);
  if (filters.age_group) params.set("age_group", filters.age_group);
  if (filters.sort_price) params.set("sort_price", "true");
  const qs = params.toString();
  const res = await fetch(`${BASE_URL}/api/catalogue/${gender}${qs ? "?" + qs : ""}`);
  if (!res.ok) throw new Error("Failed to load catalogue");
  return res.json();
}
