/**
 * WearWise Merchant Digital Garment Studio API Client
 */

const BASE_URL = 'http://localhost:8000/api/v1/merchant/garments';

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
  if (!res.ok) throw new Error('Failed to create garment identity');
  return res.json();
}

export async function uploadViewpointImage(garmentId, viewpoint, file) {
  const formData = new FormData();
  formData.append('viewpoint', viewpoint);
  formData.append('file', file);

  const res = await fetch(`${BASE_URL}/${garmentId}/images`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) throw new Error(`Failed to upload ${viewpoint} image`);
  return res.json();
}

export async function savePatternSpec(garmentId, payload) {
  const res = await fetch(`${BASE_URL}/${garmentId}/pattern`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error('Failed to save pattern specification');
  return res.json();
}

export async function saveMeasurements(garmentId, payload) {
  const res = await fetch(`${BASE_URL}/${garmentId}/measurements`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error('Failed to save size measurements');
  return res.json();
}

export async function saveFabricProps(garmentId, payload) {
  const res = await fetch(`${BASE_URL}/${garmentId}/fabric`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error('Failed to save fabric properties');
  return res.json();
}

export async function trigger3DGeneration(garmentId) {
  const res = await fetch(`${BASE_URL}/${garmentId}/generate`, {
    method: 'POST',
  });
  if (!res.ok) throw new Error('Failed to trigger 3D generation');
  return res.json();
}

export async function approveGarment(garmentId, principalId = 'brand_director_demo', notes = 'Physically verified boxy fit and ISO 8559-2 grading.') {
  const res = await fetch(`${BASE_URL}/${garmentId}/approve?principal_id=${encodeURIComponent(principalId)}&approval_notes=${encodeURIComponent(notes)}`, {
    method: 'POST',
  });
  if (!res.ok) throw new Error('Failed to approve digital garment');
  return res.json();
}

export async function publishGarment(garmentId, publisherId = 'catalog_admin_demo') {
  const res = await fetch(`${BASE_URL}/${garmentId}/publish?publisher_id=${encodeURIComponent(publisherId)}`, {
    method: 'POST',
  });
  if (!res.ok) throw new Error('Failed to publish digital garment');
  return res.json();
}

export async function fetchShopperGarmentAsset(garmentId, size = 'M') {
  const res = await fetch(`${BASE_URL}/${garmentId}/shopper-asset?size=${encodeURIComponent(size)}`);
  if (!res.ok) throw new Error('Garment asset not published or unavailable');
  return res.json();
}
