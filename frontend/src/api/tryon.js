import { getSessionId } from "./client";

const STORE_BASE_URL = import.meta.env.VITE_STORE_API_URL || "http://127.0.0.1:8001";

export async function uploadTryOnPhoto(file) {
  const form = new FormData();
  form.append("session_id", getSessionId());
  form.append("file", file);
  const res = await fetch(`${STORE_BASE_URL}/api/tryon/upload-photo`, {
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
  const res = await fetch(`${STORE_BASE_URL}/api/tryon/process`, {
    method: "POST",
    body: form,
  });
  if (!res.ok) throw new Error("Try-on processing failed");
  return res.json(); // { photo_id, look, result_url, status }
}

export async function getTryOnResult() {
  const res = await fetch(`${STORE_BASE_URL}/api/tryon/${getSessionId()}`);
  if (!res.ok) return null;
  return res.json();
}

// ── Mode B: AI Photo VTON (Body Engine Port 8000) ───────────────────────────
const BODY_BASE_URL = import.meta.env.VITE_BODY_API_URL || "http://127.0.0.1:8000";

export async function createVtonJob(file, garmentSku = "TSH-WW-CREW-001", consent = true) {
  const form = new FormData();
  form.append("file", file);
  form.append("garment_sku", garmentSku);
  form.append("consent", consent ? "true" : "false");

  const res = await fetch(`${BODY_BASE_URL}/api/v1/try-on/vton/jobs`, {
    method: "POST",
    headers: {
      "X-User-Id": "c1f7a28e-8e3b-48d9-a791-03f4439c1b3e",
    },
    body: form,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail?.message || err.detail || "AI Photo VTON request failed");
  }
  return res.json();
}

export async function getVtonJob(jobId) {
  const res = await fetch(`${BODY_BASE_URL}/api/v1/try-on/vton/jobs/${jobId}`, {
    headers: { "X-User-Id": "c1f7a28e-8e3b-48d9-a791-03f4439c1b3e" },
  });
  if (!res.ok) throw new Error("Failed to fetch VTON job status");
  return res.json();
}

export async function getVtonResults(jobId) {
  const res = await fetch(`${BODY_BASE_URL}/api/v1/try-on/vton/jobs/${jobId}/results`, {
    headers: { "X-User-Id": "c1f7a28e-8e3b-48d9-a791-03f4439c1b3e" },
  });
  if (!res.ok) throw new Error("Failed to fetch VTON results");
  return res.json();
}

export async function deleteVtonJob(jobId) {
  const res = await fetch(`${BODY_BASE_URL}/api/v1/try-on/vton/jobs/${jobId}`, {
    method: "DELETE",
    headers: { "X-User-Id": "c1f7a28e-8e3b-48d9-a791-03f4439c1b3e" },
  });
  if (!res.ok) throw new Error("Failed to delete VTON job");
  return res.json();
}

export async function getVtonProviders() {
  const res = await fetch(`${BODY_BASE_URL}/api/v1/try-on/vton/providers`);
  if (!res.ok) throw new Error("Failed to fetch provider telemetry");
  return res.json();
}
