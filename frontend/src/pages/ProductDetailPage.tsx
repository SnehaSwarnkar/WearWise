import React, { useEffect, useState } from 'react';
import { Link, useNavigate, useParams, useSearchParams } from 'react-router-dom';
import Header from './Header';
import { fetchProduct, fetchProductBySku, fetchProductReviews, submitProductReview } from '../api/products';
import { addToCart } from '../api/cart';
import { useAuth } from '../context/AuthContext';

interface TryOnCapabilities {
  mode: 'IMAGE_ONLY' | 'THREE_D_ONLY' | 'IMAGE_AND_THREE_D';
  imageTryOnEnabled: boolean;
  threeDTryOnEnabled: boolean;
  imageTryOnReady?: boolean;
  threeDTryOnReady?: boolean;
  imageDisabledReason?: string | null;
  threeDDisabledReason?: string | null;
}

interface ProductDetail {
  id: number;
  sku?: string;
  name: string;
  category: string;
  price: number;
  colors: string[];
  image?: string | null;
  brand?: string;
  seller_name?: string;
  description?: string;
  available_sizes?: string[];
  published_revision?: number | null;
  published_version?: string | null;
  storefront_images?: Array<{ id?: string; viewpoint?: string; url: string }>;
  material_profile?: Record<string, any> | null;
  measurement_chart?: Record<string, any> | null;
  tryOnCapabilities?: TryOnCapabilities;
  rating_average?: number | null;
  review_count?: number;
}

interface ReviewItem {
  id: string;
  author_name: string;
  rating: number;
  comment: string;
  size_purchased?: string | null;
  fit_feedback?: string | null;
  verified_purchase?: boolean;
  created_at: string;
}

export default function ProductDetailPage() {
  const { sku = '' } = useParams<{ sku: string }>();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { user } = useAuth();

  const [product, setProduct] = useState<ProductDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [notFoundError, setNotFoundError] = useState<string | null>(null);

  const [selectedSize, setSelectedSize] = useState('M');
  const [selectedColor, setSelectedColor] = useState('#151515');
  const [activeImageIdx, setActiveImageIdx] = useState(0);
  const [failedImages, setFailedImages] = useState<Record<string, boolean>>({});

  const [tryOnSelectorOpen, setTryOnSelectorOpen] = useState(searchParams.get('openTryOn') === '1');
  const [cartFeedback, setCartFeedback] = useState<string | null>(null);
  const [addingToCart, setAddingToCart] = useState(false);

  const [reviews, setReviews] = useState<ReviewItem[]>([]);
  const [reviewCount, setReviewCount] = useState(0);
  const [averageRating, setAverageRating] = useState<number | null>(null);
  const [newRating, setNewRating] = useState(5);
  const [newComment, setNewComment] = useState('');
  const [newFitFeedback, setNewFitFeedback] = useState('True to Size');
  const [newAuthorName, setNewAuthorName] = useState('');
  const [reviewStatus, setReviewStatus] = useState<string | null>(null);
  const [submittingReview, setSubmittingReview] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setNotFoundError(null);

    const load = async () => {
      try {
        const prod = /^\d+$/.test(sku)
          ? await fetchProduct(Number(sku))
          : await fetchProductBySku(sku);
        if (cancelled) return;
        setProduct(prod);
        const sizes = prod.available_sizes?.length ? prod.available_sizes : ['S', 'M', 'L'];
        setSelectedSize(sizes.includes('M') ? 'M' : sizes[0]);
        setSelectedColor((prod.colors && prod.colors[0]) || '#151515');
        setActiveImageIdx(0);

        const reviewSku = prod.sku || String(prod.id);
        const revData = await fetchProductReviews(reviewSku).catch(() => ({
          reviews: [],
          review_count: 0,
          average_rating: null,
        }));
        if (cancelled) return;
        setReviews(revData.reviews || []);
        setReviewCount(revData.review_count || 0);
        setAverageRating(revData.average_rating ?? null);
      } catch (err: any) {
        if (!cancelled) {
          setNotFoundError(err?.message || 'We could not find this product in our catalog.');
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    load();
    return () => {
      cancelled = true;
    };
  }, [sku]);

  useEffect(() => {
    if (searchParams.get('openTryOn') === '1') {
      setTryOnSelectorOpen(true);
    }
  }, [searchParams]);

  const galleryImages = (() => {
    if (!product) return [];
    const urls: string[] = [];
    if (product.storefront_images?.length) {
      product.storefront_images.forEach((im) => {
        if (im?.url && !urls.includes(im.url)) urls.push(im.url);
      });
    }
    if (product.image && !urls.includes(product.image)) {
      urls.unshift(product.image);
    }
    return urls;
  })();

  const handleAddToCart = async () => {
    if (!product || addingToCart) return;
    setAddingToCart(true);
    setCartFeedback(null);
    try {
      await addToCart({
        id: product.id,
        sku: product.sku,
        published_revision: product.published_revision || undefined,
        name: product.name,
        price: product.price,
        size: selectedSize,
        color: selectedColor,
        quantity: 1,
        image: galleryImages[0] || product.image || undefined,
        brand: product.seller_name || product.brand || 'WEARWISE EDIT',
      });
      setCartFeedback(`Added ${product.name} (Size ${selectedSize}) to your bag.`);
    } catch {
      setCartFeedback('Could not add this item to your bag right now. Please try again.');
    } finally {
      setAddingToCart(false);
    }
  };

  const handleLaunchImageTryOn = () => {
    if (!product) return;
    const targetSku = product.sku || String(product.id);
    navigate(
      `/image-try-on?sku=${encodeURIComponent(targetSku)}&size=${encodeURIComponent(selectedSize)}&color=${encodeURIComponent(selectedColor)}`
    );
  };

  const handleLaunch3DTryOn = () => {
    if (!product) return;
    const targetSku = product.sku || String(product.id);
    const revParam = product.published_revision ? `&revision=${encodeURIComponent(String(product.published_revision))}` : '';
    navigate(
      `/experimental-try-on?sku=${encodeURIComponent(targetSku)}&size=${encodeURIComponent(selectedSize)}&color=${encodeURIComponent(selectedColor)}${revParam}`
    );
  };

  const handleSubmitReview = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!product || !newComment.trim() || submittingReview) return;
    setSubmittingReview(true);
    setReviewStatus(null);
    try {
      const targetSku = product.sku || String(product.id);
      await submitProductReview(targetSku, {
        rating: newRating,
        comment: newComment.trim(),
        fit_feedback: newFitFeedback,
        size_purchased: selectedSize,
        author_name: user?.name || newAuthorName.trim() || undefined,
      });
      const updated = await fetchProductReviews(targetSku);
      setReviews(updated.reviews || []);
      setReviewCount(updated.review_count || 0);
      setAverageRating(updated.average_rating ?? null);
      setNewComment('');
      setReviewStatus('Thank you! Your review has been published.');
    } catch (err: any) {
      setReviewStatus(err?.message || 'Could not submit your review right now.');
    } finally {
      setSubmittingReview(false);
    }
  };

  const caps = product?.tryOnCapabilities;
  const sizes = product?.available_sizes?.length ? product.available_sizes : ['S', 'M', 'L'];
  const selectedSizeMeas = product?.measurement_chart?.[selectedSize] || null;

  return (
    <div style={{ minHeight: '100vh', background: '#FFF8F1', color: '#151515', overflowX: 'hidden' }}>
      <Header />
      <main style={{ maxWidth: '1200px', margin: '0 auto', padding: 'clamp(14px, 3vw, 24px)', boxSizing: 'border-box', overflowX: 'hidden' }}>
        <div style={{ marginBottom: '16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Link to="/explore" style={{ fontWeight: 800, fontSize: '13px', color: '#151515', textDecoration: 'none' }}>
            ← Back to Explore
          </Link>
          <Link to="/cart" style={{ fontWeight: 800, fontSize: '13px', color: '#151515', textDecoration: 'none' }}>
            View Bag →
          </Link>
        </div>

        {loading && (
          <div style={{ padding: '48px', textAlign: 'center', border: '2px solid #151515', borderRadius: '14px', background: '#fff', fontWeight: 800 }}>
            Loading product details...
          </div>
        )}

        {!loading && notFoundError && (
          <div style={{ padding: '32px', border: '2px solid #dc2626', borderRadius: '14px', background: '#fef2f2', color: '#991b1b', fontWeight: 700 }}>
            {notFoundError}
          </div>
        )}

        {!loading && product && (
          <>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 300px), 1fr))', gap: '24px', alignItems: 'start' }}>
              {/* Left Gallery */}
              <div style={{ minWidth: 0 }}>
                <div
                  style={{
                    border: '2px solid #151515',
                    borderRadius: '16px',
                    overflow: 'hidden',
                    background: '#fff',
                    boxShadow: '6px 6px 0 #151515',
                    minHeight: '420px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    position: 'relative',
                  }}
                >
                  {galleryImages[activeImageIdx] && !failedImages[galleryImages[activeImageIdx]] ? (
                    <img
                      src={galleryImages[activeImageIdx]}
                      alt={product.name}
                      onError={() =>
                        setFailedImages((prev) => ({ ...prev, [galleryImages[activeImageIdx]]: true }))
                      }
                      style={{ width: '100%', height: '460px', objectFit: 'cover' }}
                    />
                  ) : (
                    <div
                      style={{
                        width: '100%',
                        height: '460px',
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: 'center',
                        justifyContent: 'center',
                        background: `linear-gradient(135deg, ${selectedColor}26, #fff)`,
                        gap: '8px',
                      }}
                    >
                      <span style={{ fontSize: '12px', fontWeight: 900, letterSpacing: '1px', textTransform: 'uppercase' }}>
                        {product.category}
                      </span>
                      <strong style={{ fontSize: '28px', fontWeight: 900 }}>{product.name}</strong>
                      <span style={{ fontSize: '12px', color: '#64748b' }}>Storefront photo coming soon</span>
                    </div>
                  )}
                </div>

                {galleryImages.length > 1 && (
                  <div style={{ display: 'flex', gap: '10px', marginTop: '12px', flexWrap: 'wrap' }}>
                    {galleryImages.map((src, idx) => (
                      <button
                        key={src}
                        type="button"
                        onClick={() => setActiveImageIdx(idx)}
                        style={{
                          width: '72px',
                          height: '72px',
                          padding: 0,
                          borderRadius: '10px',
                          overflow: 'hidden',
                          border: idx === activeImageIdx ? '3px solid #FF3D9A' : '2px solid #151515',
                          cursor: 'pointer',
                          background: '#fff',
                        }}
                      >
                        <img src={src} alt={`${product.name} view ${idx + 1}`} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                      </button>
                    ))}
                  </div>
                )}
              </div>

              {/* Right Details & Actions */}
              <div style={{ minWidth: 0, background: '#fff', border: '2px solid #151515', borderRadius: '16px', padding: '20px', boxShadow: '4px 4px 0 #151515', boxSizing: 'border-box' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
                  <span style={{ fontSize: '12px', fontWeight: 900, letterSpacing: '0.7px', color: '#FF3D9A', textTransform: 'uppercase' }}>
                    {product.seller_name || product.brand || 'WEARWISE EDIT'} · {product.category}
                  </span>
                  <span data-testid="pdp-rating-summary" style={{ fontSize: '13px', fontWeight: 800 }}>
                    {reviewCount > 0 && averageRating !== null
                      ? `★ ${averageRating.toFixed(1)} (${reviewCount} review${reviewCount === 1 ? '' : 's'})`
                      : 'No customer reviews yet'}
                  </span>
                </div>

                <h1 data-testid="pdp-title" style={{ fontSize: '30px', fontWeight: 900, margin: '8px 0' }}>
                  {product.name}
                </h1>
                <div data-testid="pdp-price" style={{ fontSize: '24px', fontWeight: 900, marginBottom: '12px' }}>
                  ₹{Number(product.price).toLocaleString('en-IN')}
                </div>

                <p style={{ fontSize: '14px', lineHeight: 1.55, color: '#334155', margin: '0 0 18px' }}>
                  {product.description || 'Thoughtfully tailored piece built for everyday versatility.'}
                </p>

                {/* Color Selection */}
                <div style={{ marginBottom: '16px' }}>
                  <div style={{ fontSize: '12px', fontWeight: 800, textTransform: 'uppercase', marginBottom: '8px' }}>
                    Color
                  </div>
                  <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
                    {(product.colors || ['#151515']).map((c) => {
                      const isHex = c.startsWith('#');
                      const selected = selectedColor === c;
                      return (
                        <button
                          key={c}
                          type="button"
                          onClick={() => setSelectedColor(c)}
                          aria-label={`Select color ${c}`}
                          style={{
                            minWidth: isHex ? '32px' : 'auto',
                            height: '32px',
                            padding: isHex ? 0 : '0 12px',
                            borderRadius: isHex ? '999px' : '8px',
                            background: isHex ? c : '#FFF8F1',
                            border: selected ? '3px solid #FF3D9A' : '2px solid #151515',
                            fontWeight: 800,
                            fontSize: '12px',
                            cursor: 'pointer',
                          }}
                        >
                          {!isHex ? c : ''}
                        </button>
                      );
                    })}
                  </div>
                </div>

                {/* Size Selection */}
                <div style={{ marginBottom: '18px' }}>
                  <div style={{ fontSize: '12px', fontWeight: 800, textTransform: 'uppercase', marginBottom: '8px' }}>
                    Select Size
                  </div>
                  <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                    {sizes.map((sz) => (
                      <button
                        key={sz}
                        type="button"
                        data-testid={`pdp-size-${sz}`}
                        onClick={() => setSelectedSize(sz)}
                        style={{
                          padding: '10px 18px',
                          borderRadius: '8px',
                          border: '2px solid #151515',
                          background: selectedSize === sz ? '#151515' : '#FFF8F1',
                          color: selectedSize === sz ? '#fff' : '#151515',
                          fontWeight: 900,
                          fontSize: '13px',
                          cursor: 'pointer',
                        }}
                      >
                        {sz}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Purchase & TRY ON Buttons */}
                <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', marginBottom: '14px' }}>
                  <button
                    type="button"
                    data-testid="pdp-add-to-bag-btn"
                    onClick={handleAddToCart}
                    disabled={addingToCart}
                    style={{
                      flex: '1 1 180px',
                      padding: '14px 20px',
                      borderRadius: '10px',
                      border: '2px solid #151515',
                      background: '#D8FF3F',
                      color: '#151515',
                      fontWeight: 900,
                      fontSize: '14px',
                      cursor: 'pointer',
                      boxShadow: '3px 3px 0 #151515',
                    }}
                  >
                    {addingToCart ? 'Adding...' : `Add Size ${selectedSize} to Bag`}
                  </button>

                  <button
                    type="button"
                    data-testid="open-tryon-selector-btn"
                    onClick={() => setTryOnSelectorOpen((prev) => !prev)}
                    style={{
                      flex: '1 1 180px',
                      padding: '14px 20px',
                      borderRadius: '10px',
                      border: '2px solid #151515',
                      background: '#FF3D9A',
                      color: '#fff',
                      fontWeight: 900,
                      fontSize: '14px',
                      cursor: 'pointer',
                      boxShadow: '3px 3px 0 #151515',
                    }}
                  >
                    TRY ON ✦
                  </button>
                </div>

                {cartFeedback && (
                  <div data-testid="pdp-cart-banner" style={{ padding: '10px 14px', borderRadius: '8px', border: '2px solid #151515', background: '#ecfccb', fontSize: '13px', fontWeight: 700, marginBottom: '14px' }}>
                    {cartFeedback}{' '}
                    <Link to="/cart" style={{ color: '#151515', fontWeight: 900, textDecoration: 'underline', marginLeft: '6px' }}>
                      Open Bag
                    </Link>
                  </div>
                )}

                {/* Dual-Mode TRY ON Selector */}
                {tryOnSelectorOpen && (
                  <div
                    data-testid="tryon-mode-selector"
                    style={{
                      marginTop: '10px',
                      padding: '16px',
                      borderRadius: '12px',
                      border: '2px solid #151515',
                      background: '#FFF8F1',
                    }}
                  >
                    <div style={{ fontSize: '12px', fontWeight: 900, textTransform: 'uppercase', marginBottom: '10px' }}>
                      Choose Your Try-On Experience
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '12px' }}>
                      {/* Image Try-On Option */}
                      <div style={{ padding: '12px', borderRadius: '10px', border: '2px solid #151515', background: '#fff' }}>
                        <div style={{ fontWeight: 900, fontSize: '13px', marginBottom: '4px' }}>IMAGE TRY-ON</div>
                        <p style={{ fontSize: '12px', color: '#475569', margin: '0 0 10px', lineHeight: 1.4 }}>
                          Upload your photo to preview how this outfit drapes on you.
                        </p>
                        <button
                          type="button"
                          data-testid="tryon-mode-image-btn"
                          disabled={!caps?.imageTryOnEnabled}
                          onClick={handleLaunchImageTryOn}
                          style={{
                            width: '100%',
                            padding: '10px',
                            borderRadius: '8px',
                            border: '2px solid #151515',
                            background: caps?.imageTryOnEnabled ? '#151515' : '#e2e8f0',
                            color: caps?.imageTryOnEnabled ? '#fff' : '#64748b',
                            fontWeight: 800,
                            fontSize: '12px',
                            cursor: caps?.imageTryOnEnabled ? 'pointer' : 'not-allowed',
                          }}
                        >
                          {caps?.imageTryOnEnabled ? 'Open Image Try-On →' : 'Unavailable for This Item'}
                        </button>
                        {!caps?.imageTryOnEnabled && (
                          <p data-testid="image-tryon-disabled-reason" style={{ fontSize: '11px', color: '#b45309', margin: '8px 0 0', fontWeight: 700 }}>
                            {caps?.imageDisabledReason || 'The seller has not enabled Image Try-On for this item.'}
                          </p>
                        )}
                      </div>

                      {/* Interactive 3D Try-On Option */}
                      <div style={{ padding: '12px', borderRadius: '10px', border: '2px solid #151515', background: '#fff' }}>
                        <div style={{ fontWeight: 900, fontSize: '13px', marginBottom: '4px' }}>INTERACTIVE 3D TRY-ON</div>
                        <p style={{ fontSize: '12px', color: '#475569', margin: '0 0 10px', lineHeight: 1.4 }}>
                          Inspect real 3D garment fit and drape on an adjustable body profile.
                        </p>
                        <button
                          type="button"
                          data-testid="tryon-mode-3d-btn"
                          disabled={!caps?.threeDTryOnEnabled}
                          onClick={handleLaunch3DTryOn}
                          style={{
                            width: '100%',
                            padding: '10px',
                            borderRadius: '8px',
                            border: '2px solid #151515',
                            background: caps?.threeDTryOnEnabled ? '#D8FF3F' : '#e2e8f0',
                            color: caps?.threeDTryOnEnabled ? '#151515' : '#64748b',
                            fontWeight: 800,
                            fontSize: '12px',
                            cursor: caps?.threeDTryOnEnabled ? 'pointer' : 'not-allowed',
                          }}
                        >
                          {caps?.threeDTryOnEnabled ? 'Launch 3D Fitting Room →' : 'Unavailable for This Item'}
                        </button>
                        {!caps?.threeDTryOnEnabled && (
                          <p data-testid="three-d-tryon-disabled-reason" style={{ fontSize: '11px', color: '#b45309', margin: '8px 0 0', fontWeight: 700 }}>
                            {caps?.threeDDisabledReason || 'The seller has not enabled Interactive 3D Try-On for this item.'}
                          </p>
                        )}
                      </div>
                    </div>
                  </div>
                )}

                {/* Fabric & Sizing Highlights */}
                {(product.material_profile || selectedSizeMeas) && (
                  <div style={{ marginTop: '18px', paddingTop: '16px', borderTop: '1px solid #e2e8f0', fontSize: '13px', color: '#334155' }}>
                    {product.material_profile?.composition && (
                      <div style={{ marginBottom: '6px' }}>
                        <strong>Fabric:</strong> {product.material_profile.name || product.material_profile.composition}
                      </div>
                    )}
                    {selectedSizeMeas && (
                      <div>
                        <strong>Size {selectedSize} Fit Specs:</strong>{' '}
                        {selectedSizeMeas.half_chest_width_cm ? `Half chest ${selectedSizeMeas.half_chest_width_cm} cm` : ''}{' '}
                        {selectedSizeMeas.back_length_cm ? `· Length ${selectedSizeMeas.back_length_cm} cm` : ''}
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>

            {/* Customer Reviews Section */}
            <section
              data-testid="pdp-reviews-section"
              style={{
                marginTop: '32px',
                background: '#fff',
                border: '2px solid #151515',
                borderRadius: '16px',
                padding: '20px',
                boxShadow: '4px 4px 0 #151515',
                boxSizing: 'border-box',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', flexWrap: 'wrap', gap: '8px' }}>
                <h2 style={{ margin: 0, fontSize: '20px', fontWeight: 900 }}>Customer Reviews</h2>
                <span style={{ fontSize: '13px', fontWeight: 800 }}>
                  {reviewCount > 0 && averageRating !== null
                    ? `${averageRating.toFixed(1)} / 5 from ${reviewCount} review${reviewCount === 1 ? '' : 's'}`
                    : 'No customer reviews yet'}
                </span>
              </div>

              {reviews.length === 0 ? (
                <div data-testid="pdp-reviews-empty" style={{ padding: '16px', borderRadius: '10px', background: '#FFF8F1', border: '1.5px solid #cbd5e1', fontSize: '13px', color: '#475569', marginBottom: '20px' }}>
                  No customer reviews yet for this product. Be the first shopper to share how it fits and feels.
                </div>
              ) : (
                <div style={{ display: 'grid', gap: '12px', marginBottom: '20px' }}>
                  {reviews.map((rev) => (
                    <div key={rev.id} style={{ padding: '14px', borderRadius: '10px', border: '1.5px solid #cbd5e1', background: '#FFF8F1' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px', flexWrap: 'wrap', gap: '8px' }}>
                        <div>
                          <strong style={{ fontSize: '14px' }}>{rev.author_name}</strong>{' '}
                          <span style={{ color: '#FF3D9A', fontWeight: 900 }}>{'★'.repeat(rev.rating)}</span>
                          {rev.verified_purchase && (
                            <span style={{ marginLeft: '8px', fontSize: '11px', fontWeight: 800, background: '#ecfccb', padding: '2px 8px', borderRadius: '999px', border: '1px solid #151515' }}>
                              Verified Purchase
                            </span>
                          )}
                        </div>
                        <span style={{ fontSize: '12px', color: '#64748b' }}>
                          {rev.size_purchased ? `Size ${rev.size_purchased}` : ''}{' '}
                          {rev.fit_feedback ? `· ${rev.fit_feedback}` : ''}
                        </span>
                      </div>
                      <p style={{ margin: 0, fontSize: '13px', lineHeight: 1.5 }}>{rev.comment}</p>
                    </div>
                  ))}
                </div>
              )}

              {/* Submit Review Form */}
              <form onSubmit={handleSubmitReview} style={{ borderTop: '1px solid #e2e8f0', paddingTop: '16px', display: 'grid', gap: '12px' }}>
                <div style={{ fontWeight: 900, fontSize: '14px' }}>Write a Review</div>
                <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
                  {!user && (
                    <input
                      type="text"
                      placeholder="Your name (optional)"
                      value={newAuthorName}
                      onChange={(e) => setNewAuthorName(e.target.value)}
                      style={{ padding: '8px 12px', borderRadius: '8px', border: '2px solid #151515', fontSize: '13px' }}
                    />
                  )}
                  <select
                    aria-label="Rating"
                    value={newRating}
                    onChange={(e) => setNewRating(Number(e.target.value))}
                    style={{ padding: '8px 12px', borderRadius: '8px', border: '2px solid #151515', fontWeight: 700, fontSize: '13px' }}
                  >
                    {[5, 4, 3, 2, 1].map((n) => (
                      <option key={n} value={n}>{n} Star{n > 1 ? 's' : ''}</option>
                    ))}
                  </select>
                  <select
                    aria-label="Fit feedback"
                    value={newFitFeedback}
                    onChange={(e) => setNewFitFeedback(e.target.value)}
                    style={{ padding: '8px 12px', borderRadius: '8px', border: '2px solid #151515', fontWeight: 700, fontSize: '13px' }}
                  >
                    <option value="True to Size">True to Size</option>
                    <option value="Runs Small">Runs Small</option>
                    <option value="Runs Large">Runs Large</option>
                  </select>
                </div>
                <textarea
                  rows={3}
                  placeholder="Share your experience with sizing, fabric feel, and styling..."
                  value={newComment}
                  onChange={(e) => setNewComment(e.target.value)}
                  required
                  style={{ width: '100%', padding: '10px 12px', borderRadius: '8px', border: '2px solid #151515', fontSize: '13px', boxSizing: 'border-box' }}
                />
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
                  <button
                    type="submit"
                    data-testid="submit-review-btn"
                    disabled={submittingReview || newComment.trim().length < 3}
                    style={{
                      padding: '10px 18px',
                      borderRadius: '8px',
                      border: '2px solid #151515',
                      background: '#151515',
                      color: '#fff',
                      fontWeight: 800,
                      fontSize: '13px',
                      cursor: 'pointer',
                    }}
                  >
                    {submittingReview ? 'Submitting...' : 'Post Review'}
                  </button>
                  {reviewStatus && <span style={{ fontSize: '13px', fontWeight: 700 }}>{reviewStatus}</span>}
                </div>
              </form>
            </section>
          </>
        )}
      </main>
    </div>
  );
}
