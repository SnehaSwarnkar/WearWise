import { api, getSessionId } from "./client";

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
    (import.meta.env.VITE_API_URL || "http://localhost:8000") + "/api/avatar/analyze-photo",
    { method: "POST", body: form }
  ).then((r) => {
    if (!r.ok) throw new Error("Photo analysis failed");
    return r.json();
  });
}
