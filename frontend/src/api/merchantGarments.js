/**
 * WearWise Merchant Digital Garment Studio API Client (Part 1 Platform)
 * Base URL: /api/v1/merchant/garments (proxied to FastAPI in dev/preview or overridden via VITE_MERCHANT_API_BASE)
 */

const BASE_URL = import.meta.env?.VITE_MERCHANT_API_BASE || '/api/v1/merchant/garments';

export async function fetchPrototypePreviewMeta(sku, revision = 'rev3') {
  const res = await fetch(`${BASE_URL}/prototype-preview/${encodeURIComponent(sku)}?revision=${encodeURIComponent(revision)}`);
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Prototype candidate unavailable for ${sku} (${revision})`);
  }
  return res.json();
}

export async function fetchMerchantGarments(brandId = null) {
  const url = brandId ? `${BASE_URL}?brand_id=${brandId}` : BASE_URL;
  const res = await fetch(url);
  if (!res.ok) throw new Error('Failed to fetch merchant digital garments');
  return res.json();
}

export async function fetchGarmentDetails(garmentId) {
  const res = await fetch(`${BASE_URL}/${garmentId}`);
  if (!res.ok) throw new Error(`Failed to fetch garment ${garmentId}`);
  return res.json();
}

export async function createGarmentIdentity(payload) {
  const res = await fetch(BASE_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to create garment identity');
  }
  return res.json();
}

export async function uploadViewpointImage(garmentId, viewpoint, file, role = 'both') {
  const formData = new FormData();
  formData.append('viewpoint', viewpoint);
  formData.append('role', role);
  formData.append('file', file);

  const res = await fetch(`${BASE_URL}/${garmentId}/images`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Failed to upload ${viewpoint} image`);
  }
  return res.json();
}

export async function deleteGarmentImage(garmentId, imageId) {
  const res = await fetch(`${BASE_URL}/${garmentId}/images/${imageId}`, {
    method: 'DELETE',
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Failed to delete image ${imageId}`);
  }
  return res.json();
}

export async function uploadCADPattern(garmentId, file, units = 'mm') {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('units', units);

  const res = await fetch(`${BASE_URL}/${garmentId}/pattern/upload`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to upload CAD pattern');
  }
  return res.json();
}

export async function saveGuidedPattern(garmentId, payload) {
  const res = await fetch(`${BASE_URL}/${garmentId}/pattern/guided`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to generate guided parametric pattern');
  }
  return res.json();
}

export async function requestAIRepairPattern(garmentId, payload = {}) {
  const res = await fetch(`${BASE_URL}/${garmentId}/pattern/ai-reconstruct`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to trigger AI pattern reconstruction');
  }
  return res.json();
}

export async function saveMeasurements(garmentId, payload) {
  const res = await fetch(`${BASE_URL}/${garmentId}/measurements`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to save size measurements');
  }
  return res.json();
}

export async function fetchFabricPresets() {
  const res = await fetch(`${BASE_URL}/presets/fabrics`);
  if (!res.ok) throw new Error('Failed to fetch fabric presets');
  return res.json();
}

export async function saveFabricProps(garmentId, payload) {
  const res = await fetch(`${BASE_URL}/${garmentId}/fabric`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to save fabric properties');
  }
  return res.json();
}

export async function trigger3DGeneration(garmentId, force = false) {
  const qs = force ? '?force=true' : '';
  const res = await fetch(`${BASE_URL}/${garmentId}/generate${qs}`, {
    method: 'POST',
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to trigger 3D generation');
  }
  return res.json();
}

export async function fetchGarmentRevisions(garmentId) {
  const res = await fetch(`${BASE_URL}/${garmentId}/revisions`);
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to fetch revisions');
  }
  return res.json();
}

export async function rollbackGarment(garmentId, targetRevision, publisherId = 'catalog_admin_demo', reason = 'Catalog rollback') {
  const res = await fetch(`${BASE_URL}/${garmentId}/rollback`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      target_revision: targetRevision,
      publisher_id: publisherId,
      reason,
    }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to rollback garment revision');
  }
  return res.json();
}

export async function exportGarmentPattern(garmentId) {
  const res = await fetch(`${BASE_URL}/${garmentId}/pattern/export`);
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to export 2D pattern');
  }
  return res.json();
}

export async function fetchQAReport(garmentId) {
  const res = await fetch(`${BASE_URL}/${garmentId}/qa-report`);
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to fetch QA report');
  }
  return res.json();
}

export async function approveGarment(garmentId, principalId = 'brand_director_demo', notes = 'Physically verified boxy fit, seam stitching, and ISO 8559-2 grading.') {
  const res = await fetch(`${BASE_URL}/${garmentId}/approve`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      principal_id: principalId,
      approval_notes: notes,
    }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to approve digital garment');
  }
  return res.json();
}

export async function publishGarment(garmentId, publisherId = 'catalog_admin_demo') {
  const res = await fetch(`${BASE_URL}/${garmentId}/publish`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      publisher_id: publisherId,
    }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to publish digital garment');
  }
  return res.json();
}

export async function fetchGarmentManifest(garmentId) {
  const res = await fetch(`${BASE_URL}/${garmentId}/manifest`);
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to fetch package manifest');
  }
  return res.json();
}

export async function fetchShopperGarmentAsset(garmentId, size = 'M') {
  const res = await fetch(`${BASE_URL}/${garmentId}/shopper-asset?size=${encodeURIComponent(size)}`);
  if (!res.ok) throw new Error('Garment asset not published or unavailable');
  return res.json();
}
