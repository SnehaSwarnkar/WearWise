import { api, getSessionId } from "./client";

const STORE_BASE_URL = import.meta.env.VITE_STORE_API_URL || "http://127.0.0.1:8001";

export function saveAvatarProfile(profile) {
  return api.post("/api/avatar/save", {
    session_id: getSessionId(),
    ...profile,
  });
}

export function getAvatarProfile() {
  return api.get(`/api/avatar/${getSessionId()}`);
}

export function analyzeAvatarPhoto(file, selectedColour) {
  const form = new FormData();
  form.append("session_id", getSessionId());
  form.append("file", file);
  if (selectedColour) form.append("selected_colour", selectedColour);
  return fetch(
    `${STORE_BASE_URL}/api/avatar/analyze-photo`,
    { method: "POST", body: form }
  ).then((r) => {
    if (!r.ok) throw new Error("Photo analysis failed");
    return r.json();
  });
}
