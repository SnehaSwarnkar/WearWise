import React, { useEffect, useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import Header from './Header';
import { fetchProductBySku } from '../api/products';
import { addToCart } from '../api/cart';
import { devAuthHeaderProvider } from '../api/client';

const BODY_ENGINE_BASE =
  import.meta.env?.VITE_BODY_API_URL ||
  import.meta.env?.VITE_API_URL ||
  'http://127.0.0.1:8000';

const ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/webp'];
const MIN_BYTES = 10 * 1024;
const MAX_BYTES = 10 * 1024 * 1024;

export default function ImageTryOnPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const sku = searchParams.get('sku') || 'TSH-WW-CREW-001';
  const size = searchParams.get('size') || 'M';
  const color = searchParams.get('color') || '';

  const [product, setProduct] = useState<any>(null);
  const [providerMeta, setProviderMeta] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [consentChecked, setConsentChecked] = useState(false);

  const [submitting, setSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [providerUnavailableMsg, setProviderUnavailableMsg] = useState<string | null>(null);

  const [jobId, setJobId] = useState<string | null>(null);
  const [resultViews, setResultViews] = useState<Record<string, any> | null>(null);
  const [deletedMsg, setDeletedMsg] = useState<string | null>(null);
  const [cartMsg, setCartMsg] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    Promise.all([
      fetchProductBySku(sku).catch(() => null),
      fetch(`${BODY_ENGINE_BASE}/api/v1/try-on/vton/providers`)
        .then((r) => (r.ok ? r.json() : null))
        .catch(() => null),
    ])
      .then(([prod, prov]) => {
        if (cancelled) return;
        setProduct(prod);
        setProviderMeta(prov);
        if (prov && prov.available === false) {
          setProviderUnavailableMsg(
            prov.unavailable_reason ||
              'AI Photo Try-On service is not connected right now. Please connect an external VTON provider or use Interactive 3D Try-On.'
          );
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [sku]);

  useEffect(() => {
    return () => {
      if (previewUrl) URL.revokeObjectURL(previewUrl);
    };
  }, [previewUrl]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    setErrorMsg(null);
    setDeletedMsg(null);
    if (!file) return;

    if (!ALLOWED_TYPES.includes(file.type)) {
      setErrorMsg('Please choose a JPEG, PNG, or WebP photograph.');
      return;
    }
    if (file.size < MIN_BYTES) {
      setErrorMsg('Photograph file is too small. Please choose a clear photo of at least 10 KB.');
      return;
    }
    if (file.size > MAX_BYTES) {
      setErrorMsg('Photograph exceeds the 10 MB size limit. Please choose a smaller photo.');
      return;
    }

    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setSelectedFile(file);
    setPreviewUrl(URL.createObjectURL(file));
  };

  const handleClearPhoto = () => {
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setSelectedFile(null);
    setPreviewUrl(null);
    setErrorMsg(null);
  };

  const pollResults = async (targetJobId: string) => {
    const headers = devAuthHeaderProvider.getAuthHeaders();
    for (let i = 0; i < 20; i += 1) {
      await new Promise((r) => setTimeout(r, 1000));
      const res = await fetch(`${BODY_ENGINE_BASE}/api/v1/try-on/vton/jobs/${encodeURIComponent(targetJobId)}/results`, {
        headers,
      });
      if (!res.ok) continue;
      const data = await res.json();
      if (data.status === 'completed') {
        setResultViews(data.views || {});
        setSubmitting(false);
        return;
      }
      if (data.status === 'failed') {
        setErrorMsg(data.error_message || 'Could not generate a try-on preview from this photo.');
        setSubmitting(false);
        return;
      }
    }
    setSubmitting(false);
    setErrorMsg('Try-on preview timed out. Please retry with another photo.');
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    setDeletedMsg(null);
    setResultViews(null);

    if (!selectedFile) {
      setErrorMsg('Please select a photograph before continuing.');
      return;
    }
    if (!consentChecked) {
      setErrorMsg('Please confirm permission to process your photograph for virtual try-on.');
      return;
    }

    setSubmitting(true);
    try {
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('garment_sku', sku);
      formData.append('consent', 'true');

      const res = await fetch(`${BODY_ENGINE_BASE}/api/v1/try-on/vton/jobs`, {
        method: 'POST',
        headers: devAuthHeaderProvider.getAuthHeaders(),
        body: formData,
      });

      const body = await res.json().catch(() => ({}));
      if (res.status === 503) {
        const msg =
          body?.error?.message ||
          body?.detail?.message ||
          body?.message ||
          'AI Photo Try-On is currently awaiting a connected external provider.';
        setProviderUnavailableMsg(msg);
        setSubmitting(false);
        return;
      }
      if (!res.ok) {
        const msg = body?.error?.message || body?.detail?.message || body?.detail || 'Could not process this photograph.';
        setErrorMsg(typeof msg === 'string' ? msg : 'Could not process this photograph.');
        setSubmitting(false);
        return;
      }

      setJobId(body.job_id);
      await pollResults(body.job_id);
    } catch {
      setErrorMsg('Could not reach the try-on service. Please check your connection and try again.');
      setSubmitting(false);
    }
  };

  const handleDeleteSession = async () => {
    if (!jobId) {
      handleClearPhoto();
      return;
    }
    try {
      const res = await fetch(`${BODY_ENGINE_BASE}/api/v1/try-on/vton/jobs/${encodeURIComponent(jobId)}`, {
        method: 'DELETE',
        headers: devAuthHeaderProvider.getAuthHeaders(),
      });
      if (res.ok) {
        setJobId(null);
        setResultViews(null);
        handleClearPhoto();
        setDeletedMsg('Your try-on images and session data have been permanently deleted.');
      }
    } catch {
      setErrorMsg('Could not delete the session right now. Please try again.');
    }
  };

  const handleAddToCart = async () => {
    if (!product) return;
    setCartMsg(null);
    try {
      await addToCart({
        id: product.id,
        sku: product.sku || sku,
        published_revision: product.published_revision || undefined,
        name: product.name,
        price: product.price,
        size,
        color: color || undefined,
        quantity: 1,
        image: product.image || undefined,
        brand: product.seller_name || product.brand || 'WEARWISE EDIT',
      });
      setCartMsg(`Added ${product.name} (Size ${size}) to your bag.`);
    } catch {
      setCartMsg('Could not add this item to your bag right now.');
    }
  };

  const caps = product?.tryOnCapabilities;
  const imageTryOnDisabled = Boolean(product && caps && caps.imageTryOnEnabled === false);

  return (
    <div style={{ minHeight: '100vh', background: '#FFF8F1', color: '#151515', overflowX: 'hidden' }}>
      <Header />
      <main style={{ maxWidth: '1080px', margin: '0 auto', padding: 'clamp(14px, 3vw, 24px)', boxSizing: 'border-box', overflowX: 'hidden' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', flexWrap: 'wrap', gap: '10px' }}>
          <Link to={`/product/${encodeURIComponent(sku)}`} data-testid="back-to-pdp-link" style={{ fontWeight: 800, fontSize: '13px', color: '#151515', textDecoration: 'none' }}>
            ← Back to Product
          </Link>
          <Link to="/cart" style={{ fontWeight: 800, fontSize: '13px', color: '#151515', textDecoration: 'none' }}>
            View Bag →
          </Link>
        </div>

        {/* Selected Product Banner */}
        <div style={{ background: '#fff', border: '2px solid #151515', borderRadius: '14px', padding: '18px 20px', marginBottom: '20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px', boxShadow: '4px 4px 0 #151515' }}>
          <div>
            <span style={{ fontSize: '11px', fontWeight: 900, letterSpacing: '0.8px', color: '#FF3D9A', textTransform: 'uppercase' }}>
              Image-Based Virtual Try-On
            </span>
            <h1 style={{ margin: '4px 0', fontSize: '24px', fontWeight: 900 }}>
              {product?.name || sku}
            </h1>
            <div style={{ fontSize: '13px', fontWeight: 700, color: '#475569' }}>
              {product ? `₹${Number(product.price).toLocaleString('en-IN')} · ` : ''}
              Size {size}
              {color ? ` · Color ${color}` : ''}
            </div>
          </div>

          <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
            {caps?.threeDTryOnEnabled && (
              <button
                type="button"
                onClick={() => navigate(`/experimental-try-on?sku=${encodeURIComponent(sku)}&size=${encodeURIComponent(size)}&color=${encodeURIComponent(color)}`)}
                style={{ padding: '10px 14px', borderRadius: '8px', border: '2px solid #151515', background: '#fff', fontWeight: 800, fontSize: '12px', cursor: 'pointer' }}
              >
                Switch to 3D Try-On
              </button>
            )}
            {product && (
              <button
                type="button"
                data-testid="image-tryon-add-cart-btn"
                onClick={handleAddToCart}
                style={{ padding: '10px 16px', borderRadius: '8px', border: '2px solid #151515', background: '#D8FF3F', fontWeight: 900, fontSize: '12px', cursor: 'pointer' }}
              >
                Add Size {size} to Bag
              </button>
            )}
          </div>
        </div>

        {cartMsg && (
          <div style={{ padding: '12px 16px', background: '#ecfccb', border: '2px solid #151515', borderRadius: '10px', fontSize: '13px', fontWeight: 700, marginBottom: '16px' }}>
            {cartMsg}{' '}
            <Link to="/cart" style={{ color: '#151515', textDecoration: 'underline', marginLeft: '6px' }}>
              Go to Bag
            </Link>
          </div>
        )}

        {loading ? (
          <div style={{ padding: '40px', background: '#fff', border: '2px solid #151515', borderRadius: '14px', textAlign: 'center', fontWeight: 800 }}>
            Preparing Image Try-On...
          </div>
        ) : imageTryOnDisabled ? (
          <div data-testid="image-tryon-blocked-banner" style={{ padding: '24px', background: '#fffbeb', border: '2px solid #f59e0b', borderRadius: '14px', color: '#92400e', fontWeight: 700 }}>
            <h2 style={{ margin: '0 0 8px', fontSize: '18px' }}>Image Try-On is Disabled for This Item</h2>
            <p style={{ margin: '0 0 14px', fontSize: '14px' }}>
              {caps?.imageDisabledReason || 'The seller configured this item exclusively for Interactive 3D Try-On.'}
            </p>
            {caps?.threeDTryOnEnabled && (
              <Link
                to={`/experimental-try-on?sku=${encodeURIComponent(sku)}&size=${encodeURIComponent(size)}`}
                style={{ display: 'inline-block', padding: '10px 16px', borderRadius: '8px', border: '2px solid #151515', background: '#D8FF3F', color: '#151515', fontWeight: 900, textDecoration: 'none' }}
              >
                Open Interactive 3D Try-On →
              </Link>
            )}
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 280px), 1fr))', gap: '20px', alignItems: 'start' }}>
            {/* Upload & Privacy Card */}
            <form onSubmit={handleSubmit} style={{ minWidth: 0, boxSizing: 'border-box', background: '#fff', border: '2px solid #151515', borderRadius: '14px', padding: '20px', boxShadow: '4px 4px 0 #151515' }}>
              <h2 style={{ margin: '0 0 8px', fontSize: '18px', fontWeight: 900 }}>Upload Your Photo</h2>
              <p style={{ fontSize: '13px', color: '#475569', margin: '0 0 14px', lineHeight: 1.5 }}>
                Your photo is used solely to preview how this garment looks on you. Camera metadata is removed automatically and temporary uploads are deleted right after processing.
              </p>

              {providerUnavailableMsg && (
                <div data-testid="vton-provider-unavailable-banner" style={{ padding: '12px 14px', borderRadius: '10px', border: '2px solid #f59e0b', background: '#fffbeb', color: '#92400e', fontSize: '13px', fontWeight: 700, marginBottom: '14px' }}>
                  <strong>AI Photo Try-On Service Unavailable:</strong> {providerUnavailableMsg}
                </div>
              )}

              <div style={{ marginBottom: '14px' }}>
                <label
                  htmlFor="vton-photo-input"
                  style={{
                    display: 'block',
                    padding: '18px',
                    borderRadius: '10px',
                    border: '2px dashed #151515',
                    background: '#FFF8F1',
                    textAlign: 'center',
                    cursor: 'pointer',
                    fontWeight: 800,
                    fontSize: '13px',
                  }}
                >
                  {selectedFile ? `Selected: ${selectedFile.name}` : 'Choose a JPEG, PNG, or WebP photo (10 KB – 10 MB)'}
                  <input
                    id="vton-photo-input"
                    data-testid="vton-file-input"
                    type="file"
                    accept="image/jpeg,image/png,image/webp"
                    onChange={handleFileChange}
                    style={{ display: 'none' }}
                  />
                </label>
              </div>

              {previewUrl && (
                <div style={{ marginBottom: '14px', position: 'relative' }}>
                  <img
                    src={previewUrl}
                    alt="Selected shopper preview"
                    style={{ width: '100%', maxHeight: '300px', objectFit: 'contain', borderRadius: '10px', border: '1.5px solid #151515', background: '#f8fafc' }}
                  />
                  <button
                    type="button"
                    onClick={handleClearPhoto}
                    style={{ marginTop: '8px', padding: '6px 12px', borderRadius: '6px', border: '1.5px solid #151515', background: '#fff', fontWeight: 800, fontSize: '12px', cursor: 'pointer' }}
                  >
                    Remove Photo
                  </button>
                </div>
              )}

              <label style={{ display: 'flex', alignItems: 'flex-start', gap: '8px', fontSize: '12.5px', fontWeight: 700, marginBottom: '14px', cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  data-testid="vton-consent-checkbox"
                  checked={consentChecked}
                  onChange={(e) => setConsentChecked(e.target.checked)}
                  style={{ marginTop: '2px' }}
                />
                <span>
                  I consent to temporary private processing of my photo for this virtual try-on preview.
                </span>
              </label>

              {errorMsg && (
                <div data-testid="vton-error-banner" style={{ padding: '10px 12px', borderRadius: '8px', border: '2px solid #dc2626', background: '#fef2f2', color: '#991b1b', fontSize: '12.5px', fontWeight: 700, marginBottom: '12px' }}>
                  {errorMsg}
                </div>
              )}

              {deletedMsg && (
                <div data-testid="vton-deleted-banner" style={{ padding: '10px 12px', borderRadius: '8px', border: '2px solid #151515', background: '#ecfccb', fontSize: '12.5px', fontWeight: 700, marginBottom: '12px' }}>
                  {deletedMsg}
                </div>
              )}

              <button
                type="submit"
                data-testid="vton-submit-btn"
                disabled={submitting || !providerMeta?.available}
                style={{
                  width: '100%',
                  padding: '12px 18px',
                  borderRadius: '10px',
                  border: '2px solid #151515',
                  background: !providerMeta?.available ? '#e2e8f0' : '#FF3D9A',
                  color: !providerMeta?.available ? '#64748b' : '#fff',
                  fontWeight: 900,
                  fontSize: '14px',
                  cursor: submitting ? 'wait' : !providerMeta?.available ? 'not-allowed' : 'pointer',
                }}
              >
                {submitting
                  ? 'Generating Try-On Preview...'
                  : !providerMeta?.available
                    ? 'Image Try-On Service Unavailable'
                    : 'Generate Image Try-On'}
              </button>
            </form>

            {/* Output & Privacy Controls Panel */}
            <div style={{ background: '#fff', border: '2px solid #151515', borderRadius: '14px', padding: '20px', boxShadow: '4px 4px 0 #151515' }}>
              <h2 style={{ margin: '0 0 8px', fontSize: '18px', fontWeight: 900 }}>Your Try-On Preview</h2>
              {!resultViews ? (
                <div style={{ padding: '32px 18px', borderRadius: '10px', background: '#FFF8F1', border: '1.5px solid #cbd5e1', textAlign: 'center', fontSize: '13px', color: '#475569' }}>
                  {providerMeta?.available
                    ? 'Upload your photo and confirm consent to generate a garment try-on preview.'
                    : 'No simulated overlay will be shown while the AI photo try-on provider is disconnected. Connect an external VTON service or explore this item in Interactive 3D when supported.'}
                </div>
              ) : (
                <div>
                  {resultViews.front?.url && (
                    <img
                      src={`${BODY_ENGINE_BASE}${resultViews.front.url}`}
                      alt="Virtual try-on result"
                      style={{ width: '100%', borderRadius: '10px', border: '2px solid #151515', marginBottom: '12px' }}
                    />
                  )}
                  <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
                    <button
                      type="button"
                      onClick={() => {
                        setResultViews(null);
                        handleClearPhoto();
                      }}
                      style={{ padding: '8px 14px', borderRadius: '8px', border: '2px solid #151515', background: '#fff', fontWeight: 800, fontSize: '12px', cursor: 'pointer' }}
                    >
                      Retry Another Photo
                    </button>
                    <button
                      type="button"
                      data-testid="vton-delete-session-btn"
                      onClick={handleDeleteSession}
                      style={{ padding: '8px 14px', borderRadius: '8px', border: '2px solid #dc2626', background: '#fef2f2', color: '#991b1b', fontWeight: 800, fontSize: '12px', cursor: 'pointer' }}
                    >
                      Delete Photo &amp; Result
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
