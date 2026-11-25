/**
 * WearWise Merchant Digital Garment Studio API Client (Part 1 Platform)
 * Base URL: /api/v1/merchant/garments (proxied to FastAPI in dev/preview or overridden via VITE_MERCHANT_API_BASE)
 */
import { getCsrfToken } from './client';

const BASE_URL = import.meta.env?.VITE_MERCHANT_API_BASE || '/api/v1/merchant/garments';

function merchantFetch(url, options = {}) {
  const method = (options.method || 'GET').toUpperCase();
  const headers = { ...(options.headers || {}) };
  if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(method)) {
    const csrf = getCsrfToken();
    if (csrf && !headers['X-CSRF-Token']) {
      headers['X-CSRF-Token'] = csrf;
    }
  }
  return fetch(url, {
    ...options,
    credentials: 'include',
    headers,
  });
}

async function parseErrorMessage(res, fallback) {
  const err = await res.json().catch(() => ({}));
  if (typeof err.detail === 'string') return err.detail;
  if (err.detail?.message) return err.detail.message;
  if (err.error?.message) return err.error.message;
  return fallback;
}

export async function fetchPrototypePreviewMeta(sku, revision = 'rev3') {
  const res = await merchantFetch(`${BASE_URL}/prototype-preview/${encodeURIComponent(sku)}?revision=${encodeURIComponent(revision)}`);
  if (!res.ok) throw new Error(await parseErrorMessage(res, `Prototype candidate unavailable for ${sku} (${revision})`));
  return res.json();
}

export async function fetchMerchantGarments(brandId = null) {
  const url = brandId ? `${BASE_URL}?brand_id=${brandId}` : BASE_URL;
  const res = await merchantFetch(url);
  if (!res.ok) throw new Error(await parseErrorMessage(res, 'Failed to fetch merchant digital garments'));
  return res.json();
}

export async function fetchGarmentDetails(garmentId) {
  const res = await merchantFetch(`${BASE_URL}/${garmentId}`);
  if (!res.ok) throw new Error(await parseErrorMessage(res, `Failed to fetch garment ${garmentId}`));
  return res.json();
}

export async function createGarmentIdentity(payload) {
  const res = await merchantFetch(BASE_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(await parseErrorMessage(res, 'Failed to create garment identity'));
  return res.json();
}

export async function uploadViewpointImage(garmentId, viewpoint, file, role = 'both') {
  const formData = new FormData();
  formData.append('viewpoint', viewpoint);
  formData.append('role', role);
  formData.append('file', file);

  const res = await merchantFetch(`${BASE_URL}/${garmentId}/images`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) throw new Error(await parseErrorMessage(res, `Failed to upload ${viewpoint} image`));
  return res.json();
}

export async function deleteGarmentImage(garmentId, imageId) {
  const res = await merchantFetch(`${BASE_URL}/${garmentId}/images/${imageId}`, { method: 'DELETE' });
  if (!res.ok) throw new Error(await parseErrorMessage(res, `Failed to delete image ${imageId}`));
  return res.json();
}

export async function uploadCADPattern(garmentId, file, units = 'mm') {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('units', units);

  const res = await merchantFetch(`${BASE_URL}/${garmentId}/pattern/upload`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) throw new Error(await parseErrorMessage(res, 'Failed to upload CAD pattern'));
  return res.json();
}

export async function saveGuidedPattern(garmentId, payload) {
  const res = await merchantFetch(`${BASE_URL}/${garmentId}/pattern/guided`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(await parseErrorMessage(res, 'Failed to generate guided parametric pattern'));
  return res.json();
}

export async function requestAIRepairPattern(garmentId, payload = {}) {
  const res = await merchantFetch(`${BASE_URL}/${garmentId}/pattern/ai-reconstruct`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(await parseErrorMessage(res, 'Failed to trigger AI pattern reconstruction'));
  return res.json();
}

export async function saveMeasurements(garmentId, payload) {
  const res = await merchantFetch(`${BASE_URL}/${garmentId}/measurements`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(await parseErrorMessage(res, 'Failed to save size measurements'));
  return res.json();
}

export async function fetchFabricPresets() {
  const res = await merchantFetch(`${BASE_URL}/presets/fabrics`);
  if (!res.ok) throw new Error('Failed to fetch fabric presets');
  return res.json();
}

export async function saveFabricProps(garmentId, payload) {
  const res = await merchantFetch(`${BASE_URL}/${garmentId}/fabric`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(await parseErrorMessage(res, 'Failed to save fabric properties'));
  return res.json();
}

export async function trigger3DGeneration(garmentId, force = false) {
  const qs = force ? '?force=true' : '';
  const res = await merchantFetch(`${BASE_URL}/${garmentId}/generate${qs}`, { method: 'POST' });
  if (!res.ok) throw new Error(await parseErrorMessage(res, 'Failed to trigger 3D generation'));
  return res.json();
}

export async function fetchGarmentRevisions(garmentId) {
  const res = await merchantFetch(`${BASE_URL}/${garmentId}/revisions`);
  if (!res.ok) throw new Error(await parseErrorMessage(res, 'Failed to fetch revisions'));
  return res.json();
}

export async function rollbackGarment(garmentId, targetRevision, publisherId = 'catalog_admin_demo', reason = 'Catalog rollback') {
  const res = await merchantFetch(`${BASE_URL}/${garmentId}/rollback`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ target_revision: targetRevision, publisher_id: publisherId, reason }),
  });
  if (!res.ok) throw new Error(await parseErrorMessage(res, 'Failed to rollback garment revision'));
  return res.json();
}

export async function exportGarmentPattern(garmentId) {
  const res = await merchantFetch(`${BASE_URL}/${garmentId}/pattern/export`);
  if (!res.ok) throw new Error(await parseErrorMessage(res, 'Failed to export 2D pattern'));
  return res.json();
}

export async function fetchQAReport(garmentId) {
  const res = await merchantFetch(`${BASE_URL}/${garmentId}/qa-report`);
  if (!res.ok) throw new Error(await parseErrorMessage(res, 'Failed to fetch QA report'));
  return res.json();
}

export async function approveGarment(garmentId, principalId = 'brand_director_demo', notes = 'Physically verified boxy fit, seam stitching, and ISO 8559-2 grading.') {
  const res = await merchantFetch(`${BASE_URL}/${garmentId}/approve`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ principal_id: principalId, approval_notes: notes }),
  });
  if (!res.ok) throw new Error(await parseErrorMessage(res, 'Failed to approve digital garment'));
  return res.json();
}

export async function publishGarment(garmentId, publisherId = 'catalog_admin_demo') {
  const res = await merchantFetch(`${BASE_URL}/${garmentId}/publish`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ publisher_id: publisherId }),
  });
  if (!res.ok) throw new Error(await parseErrorMessage(res, 'Failed to publish digital garment'));
  return res.json();
}

export async function fetchGarmentManifest(garmentId) {
  const res = await merchantFetch(`${BASE_URL}/${garmentId}/manifest`);
  if (!res.ok) throw new Error(await parseErrorMessage(res, 'Failed to fetch package manifest'));
  return res.json();
}

export async function fetchShopperGarmentAsset(garmentId, size = 'M') {
  const res = await merchantFetch(`${BASE_URL}/${garmentId}/shopper-asset?size=${encodeURIComponent(size)}`);
  if (!res.ok) throw new Error('Garment asset not published or unavailable');
  return res.json();
}

export async function updateTryOnMode(garmentId, tryOnMode) {
  const res = await merchantFetch(`${BASE_URL}/${garmentId}/try-on-mode`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ try_on_mode: tryOnMode }),
  });
  if (!res.ok) throw new Error(await parseErrorMessage(res, 'Failed to update virtual try-on mode'));
  return res.json();
}

export async function prepareImageTryOn(garmentId) {
  const res = await merchantFetch(`${BASE_URL}/${garmentId}/prepare-image-tryon`, { method: 'POST' });
  if (!res.ok) throw new Error(await parseErrorMessage(res, 'Failed to verify Image Try-On listing readiness'));
  return res.json();
}
