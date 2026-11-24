import { api, getSessionId } from "./client";

const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export function getWardrobe(category = null) {
  const params = category && category !== "All" ? `?category=${category}` : "";
  return api.get(`/api/wardrobe/${getSessionId()}${params}`);
}

export function uploadClothes(files, category = "Tops") {
  const form = new FormData();
  form.append("session_id", getSessionId());
  form.append("category", category);
  files.forEach((f) => form.append("files", f));
  return fetch(`${BASE_URL}/api/wardrobe/upload`, {
    method: "POST",
    body: form,
  }).then((r) => {
    if (!r.ok) throw new Error("Upload failed");
    return r.json();
  });
}

export function updateWardrobeItem(itemId, updates) {
  return api.patch(`/api/wardrobe/${itemId}`, updates);
}

export function deleteWardrobeItem(itemId) {
  return api.delete(`/api/wardrobe/${itemId}`);
}
