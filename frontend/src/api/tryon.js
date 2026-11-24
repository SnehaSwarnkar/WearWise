import { getSessionId } from "./client";

const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export async function uploadTryOnPhoto(file) {
  const form = new FormData();
  form.append("session_id", getSessionId());
  form.append("file", file);
  const res = await fetch(`${BASE_URL}/api/tryon/upload-photo`, {
    method: "POST",
    body: form,
  });
  if (!res.ok) throw new Error("Photo upload failed");
  return res.json(); // { photo_id, photo_url }
}

export async function processTryOn(photoId, look) {
  const form = new FormData();
  form.append("session_id", getSessionId());
  form.append("photo_id", photoId);
  form.append("look_id", look.id);
  form.append("look_name", look.name);
  const res = await fetch(`${BASE_URL}/api/tryon/process`, {
    method: "POST",
    body: form,
  });
  if (!res.ok) throw new Error("Try-on processing failed");
  return res.json(); // { photo_id, look, result_url, status }
}

export async function getTryOnResult() {
  const res = await fetch(`${BASE_URL}/api/tryon/${getSessionId()}`);
  if (!res.ok) return null;
  return res.json();
}
