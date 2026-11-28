import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { AppLayout } from '../components/layout/AppLayout';
import { useAuth } from '../context/AuthContext';
import { apiClient } from '../api/client';
import { GarmentProfile, FitRecommendationResponse } from '../types/api';
import { addToCart } from '../api/cart';
import {
  Sparkles,
  CheckCircle2,
  AlertTriangle,
  Info,
  Ruler,
  ShoppingBag,
  User,
  Layers,
  ArrowRight,
  ShieldAlert,
} from 'lucide-react';

export const HonestFitPage: React.FC = () => {
  const { activeProfile } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [garments, setGarments] = useState<GarmentProfile[]>([]);
  const [selectedGarmentId, setSelectedGarmentId] = useState<string>('');
  const [userFitPreference, setUserFitPreference] = useState<'fitted' | 'regular' | 'relaxed'>('regular');
  const [evaluating, setEvaluating] = useState<boolean>(false);
  const [fitResult, setFitResult] = useState<FitRecommendationResponse | null>(null);
  const [addedToCart, setAddedToCart] = useState<boolean>(false);

  const [banner, setBanner] = useState<{ type: 'success' | 'error' | 'info'; message: string } | null>(null);

  // Parse query params for pre-selected garment_id or sku
  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const gId = params.get('garment_id');
    const skuParam = params.get('sku');

    apiClient
      .listGarments()
      .then((list) => {
        setGarments(list);
        if (list.length > 0) {
          const matched = list.find((g) => (gId && g.garment_id === gId) || (skuParam && g.sku === skuParam));
          if (matched) {
            setSelectedGarmentId(matched.garment_id);
          } else {
            setSelectedGarmentId(list[0].garment_id);
          }
        }
      })
      .catch((err) => console.warn('Could not load garments:', err));
  }, [location.search]);

  const selectedGarment = garments.find((g) => g.garment_id === selectedGarmentId);

  const handleAddRecommendedToCart = async (size: string) => {
    try {
      await addToCart({
        id: 1,
        name: selectedGarment?.title || 'Everyday Heavyweight Crewneck Tee',
        price: 799,
        quantity: 1,
        brand: 'WEARWISE EDIT',
        size: size,
        sku: selectedGarment?.sku || 'TSH-WW-CREW-001',
      });
      setAddedToCart(true);
      setTimeout(() => setAddedToCart(false), 3000);
    } catch (err: any) {
      console.warn('Failed to add recommended size to cart:', err);
    }
  };

  const handleEvaluateFit = async () => {
    if (!activeProfile) {
      setBanner({
        type: 'error',
        message: 'Please create or select an active shopper body profile before evaluating fit.',
      });
      return;
    }
    if (!selectedGarmentId) {
      setBanner({
        type: 'error',
        message: 'Please select a merchant garment to evaluate.',
      });
      return;
    }

    setEvaluating(true);
    setBanner(null);

    try {
      const res = await apiClient.evaluateFit({
        profile_id: activeProfile.profile_id,
        garment_id: selectedGarmentId,
        user_fit_preference: userFitPreference,
      });

      setFitResult(res);
      setBanner({
        type: 'success',
        message: `Honest Fit evaluated successfully. Recommended: Size ${res.recommended_size} (Score: ${res.composite_fit_score.toFixed(1)}/100).`,
      });
    } catch (err: any) {
      setBanner({
        type: 'error',
        message: err.message || 'Honest Fit evaluation failed.',
      });
    } finally {
      setEvaluating(false);
    }
  };

  const getClassificationBadgeClass = (classification: string) => {
    switch (classification.toLowerCase()) {
      case 'regular':
        return 'badge-emerald';
      case 'fitted':
      case 'relaxed':
        return 'badge-cyan';
      case 'snug':
      case 'oversized':
        return 'badge-amber';
      case 'compression':
      case 'tight':
      case 'baggy':
        return 'badge-rose';
      default:
        return 'badge-muted';
    }
  };

  return (
    <AppLayout banner={banner || undefined}>
      {/* Page Title */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
          marginBottom: '24px',
          flexWrap: 'wrap',
          gap: '12px',
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <h1 style={{ fontSize: '24px', fontWeight: 800, color: '#ffffff' }}>Honest Fit Studio</h1>
            <span className="badge badge-cyan">Rev 1.2.1 Rulebook</span>
          </div>
          <p style={{ fontSize: '13px', color: 'var(--text-muted)', marginTop: '2px' }}>
            Deterministic regional ease calculations, ISO 8559-1 coverage gating, and transparent recommendations.
          </p>
        </div>

        {activeProfile && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span className="badge badge-emerald">
              Profile: {activeProfile.presentation_gender} ({activeProfile.stature_cm} cm)
            </span>
          </div>
        )}
      </div>

      {/* Main Container */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'minmax(340px, 420px) 1fr',
          gap: '24px',
          alignItems: 'start',
        }}
      >
        {/* Left Column: Garment Selector & Silhouette Preference */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {/* Garment Selector Card */}
          <div className="card">
            <h2 style={{ fontSize: '15px', fontWeight: 700, color: '#ffffff', marginBottom: '14px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <ShoppingBag size={16} color="var(--accent-cyan)" />
              <span>Select Garment for Evaluation</span>
            </h2>

            {garments.length > 0 ? (
              <div style={{ marginBottom: '16px' }}>
                <label style={{ display: 'block', fontSize: '12px', color: 'var(--text-muted)', marginBottom: '6px' }}>
                  Registered Merchant Garments
                </label>
                <select
                  value={selectedGarmentId}
                  onChange={(e) => setSelectedGarmentId(e.target.value)}
                  className="input-field"
                  style={{ fontSize: '13px' }}
                >
                  {garments.map((g) => (
                    <option key={g.garment_id} value={g.garment_id}>
                      {g.title} ({g.sku}) &bull; {g.category}
                    </option>
                  ))}
                </select>
              </div>
            ) : (
              <div style={{ padding: '16px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '13px' }}>
                No garments found in catalog.
                <button
                  onClick={() => navigate('/garments')}
                  className="btn-secondary"
                  style={{ marginTop: '10px', width: '100%' }}
                >
                  Register Garment in Studio
                </button>
              </div>
            )}

            {/* Selected Garment Spec Preview */}
            {selectedGarment && (
              <div
                style={{
                  background: 'var(--bg-surface-raised)',
                  border: '1px solid var(--border-medium)',
                  borderRadius: '8px',
                  padding: '12px',
                  fontSize: '12px',
                  marginBottom: '16px',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                  <span style={{ color: 'var(--text-dim)' }}>Category</span>
                  <span style={{ color: '#ffffff', fontWeight: 600 }}>{selectedGarment.category}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                  <span style={{ color: 'var(--text-dim)' }}>Available Sizes</span>
                  <span style={{ color: 'var(--accent-cyan)', fontWeight: 600 }}>
                    {selectedGarment.sizes.map((s) => s.size_label).join(', ') || 'No sizes'}
                  </span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--text-dim)' }}>Mechanical Stretch</span>
                  <span style={{ color: 'var(--accent-emerald)', fontWeight: 600 }}>
                    {((selectedGarment.fabric_properties?.mechanical_stretch_pct ?? 0) * 100).toFixed(1)}% (
                    {selectedGarment.fabric_properties?.stretch_direction || 'rigid_zero'})
                  </span>
                </div>
              </div>
            )}

            {/* User Fit Preference Selector */}
            <div style={{ marginBottom: '20px' }}>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: 'var(--text-main)', marginBottom: '8px' }}>
                Your Silhouette Fit Preference
              </label>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '8px' }}>
                {(['fitted', 'regular', 'relaxed'] as const).map((pref) => (
                  <button
                    key={pref}
                    type="button"
                    onClick={() => setUserFitPreference(pref)}
                    style={{
                      padding: '10px 6px',
                      borderRadius: '8px',
                      fontSize: '12px',
                      fontWeight: 600,
                      textTransform: 'capitalize',
                      background: userFitPreference === pref ? 'rgba(56, 189, 248, 0.15)' : 'var(--bg-surface-raised)',
                      border: `1px solid ${userFitPreference === pref ? 'var(--accent-cyan)' : 'var(--border-medium)'}`,
                      color: userFitPreference === pref ? '#ffffff' : 'var(--text-muted)',
                    }}
                  >
                    {pref}
                  </button>
                ))}
              </div>
            </div>

            <button
              onClick={handleEvaluateFit}
              disabled={evaluating || !activeProfile || !selectedGarmentId}
              className="btn-primary"
              style={{ width: '100%', padding: '12px 0' }}
            >
              <Sparkles size={16} />
              <span>{evaluating ? 'Evaluating Dimensional Ease...' : 'Evaluate Honest Fit'}</span>
            </button>
          </div>

          {/* Active Shopper Measurements Card */}
          <div className="card">
            <h2 style={{ fontSize: '14px', fontWeight: 700, color: '#ffffff', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <User size={15} color="var(--accent-cyan)" />
              <span>Shopper Body Inputs (Avatar Ground Truth)</span>
            </h2>

            {activeProfile && Object.keys(activeProfile.active_measurements).length > 0 ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '12px' }}>
                {Object.entries(activeProfile.active_measurements).map(([code, m]) => (
                  <div
                    key={code}
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      padding: '8px 10px',
                      background: 'var(--bg-surface-raised)',
                      borderRadius: '6px',
                    }}
                  >
                    <span className="mono" style={{ color: 'var(--text-muted)' }}>
                      {code}
                    </span>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <strong style={{ color: '#ffffff' }}>{m.value_cm.toFixed(1)} cm</strong>
                      <span
                        className={
                          m.assessment_state === 'eligible' ? 'badge badge-emerald' : 'badge badge-amber'
                        }
                        style={{ fontSize: '9px', padding: '1px 6px' }}
                      >
                        {m.assessment_state}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div style={{ padding: '16px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '12px' }}>
                No measurements extracted yet. Generate an avatar first.
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Honest Fit Results & Regional Breakdown */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          {fitResult ? (
            <>
              {/* Top Recommended Hero Card */}
              <div
                className="card-raised"
                style={{
                  background: 'linear-gradient(135deg, rgba(15, 23, 42, 0.95), rgba(30, 41, 59, 0.85))',
                  border: '1px solid rgba(56, 189, 248, 0.3)',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '16px' }}>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '6px' }}>
                      <span className="badge badge-emerald">Selected Recommendation</span>
                      <span className="badge badge-cyan">{userFitPreference.toUpperCase()} Preference</span>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'baseline', gap: '12px', marginTop: '8px' }}>
                      <span style={{ fontSize: '38px', fontWeight: 900, color: '#ffffff' }}>
                        Size {fitResult.recommended_size}
                      </span>
                      <span style={{ fontSize: '14px', color: 'var(--text-muted)' }}>
                        Recommended Fit ({fitResult.status})
                      </span>
                    </div>
                  </div>

                  {/* Composite Score Gauge */}
                  <div
                    style={{
                      textAlign: 'right',
                      background: 'rgba(15, 23, 42, 0.7)',
                      padding: '12px 18px',
                      borderRadius: '10px',
                      border: '1px solid var(--border-medium)',
                    }}
                  >
                    <div style={{ fontSize: '11px', color: 'var(--text-dim)', textTransform: 'uppercase', marginBottom: '2px' }}>
                      Composite Fit Score
                    </div>
                    <div style={{ fontSize: '28px', fontWeight: 900, color: 'var(--accent-emerald)' }}>
                      {fitResult.composite_fit_score.toFixed(1)}
                      <span style={{ fontSize: '14px', color: 'var(--text-muted)' }}> / 100</span>
                    </div>
                    <div style={{ fontSize: '10px', color: 'var(--accent-amber)', marginTop: '2px' }}>
                      Provisional Penalty Model
                    </div>
                  </div>
                </div>

                {/* Alternative Wearable Size Card */}
                {fitResult.alternative_size && (
                  <div
                    style={{
                      marginTop: '20px',
                      padding: '12px 16px',
                      background: 'rgba(245, 158, 11, 0.08)',
                      border: '1px solid rgba(245, 158, 11, 0.25)',
                      borderRadius: '8px',
                      fontSize: '12px',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '10px',
                    }}
                  >
                    <Info size={18} color="var(--accent-amber)" style={{ flexShrink: 0 }} />
                    <div>
                      <strong style={{ color: '#ffffff' }}>Wearable Alternative: Size {fitResult.alternative_size.size_label}</strong>
                      <div style={{ color: 'var(--text-muted)', marginTop: '2px' }}>
                        {fitResult.alternative_size.fit_summary}
                      </div>
                    </div>
                  </div>
                )}

                {/* Add to Bag Action */}
                <div style={{ marginTop: '22px', display: 'flex', alignItems: 'center', gap: '14px', flexWrap: 'wrap' }}>
                  <button
                    onClick={() => handleAddRecommendedToCart(fitResult.recommended_size)}
                    style={{
                      background: 'var(--lime, #d8ff3f)',
                      color: '#151515',
                      fontWeight: 800,
                      fontSize: '13px',
                      padding: '12px 22px',
                      borderRadius: '4px',
                      border: '2px solid var(--border, #151515)',
                      boxShadow: '3px 3px 0 var(--border, #151515)',
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '8px',
                      cursor: 'pointer',
                    }}
                  >
                    <ShoppingBag size={17} />
                    <span>Add Recommended Size {fitResult.recommended_size} to Bag ✦</span>
                  </button>
                  <button
                    onClick={() => navigate('/cart')}
                    style={{
                      background: 'var(--bg-surface-raised)',
                      color: 'var(--text-main)',
                      fontWeight: 700,
                      fontSize: '13px',
                      padding: '12px 18px',
                      borderRadius: '4px',
                      border: '1.5px solid var(--border-medium)',
                      cursor: 'pointer',
                    }}
                  >
                    View Bag →
                  </button>
                  {addedToCart && (
                    <span style={{ color: 'var(--accent-emerald)', fontWeight: 800, fontSize: '13px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <CheckCircle2 size={16} /> Added size {fitResult.recommended_size} to bag!
                    </span>
                  )}
                </div>
              </div>

              {/* Regional Ease Breakdown Table */}
              <div className="card">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <Ruler size={18} color="var(--accent-cyan)" />
                    <h3 style={{ fontSize: '15px', fontWeight: 700, color: '#ffffff' }}>
                      Regional Dimensional Ease Breakdown
                    </h3>
                  </div>
                  <span className="badge badge-cyan">{fitResult.regional_comparisons.length} Regions Evaluated</span>
                </div>

                <div style={{ overflowX: 'auto' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
                    <thead>
                      <tr style={{ borderBottom: '1px solid var(--border-medium)', textAlign: 'left', color: 'var(--text-dim)' }}>
                        <th style={{ padding: '10px 12px', fontWeight: 600 }}>Anatomical Region</th>
                        <th style={{ padding: '10px 12px', fontWeight: 600 }}>Body Girth</th>
                        <th style={{ padding: '10px 12px', fontWeight: 600 }}>Garment Flat</th>
                        <th style={{ padding: '10px 12px', fontWeight: 600 }}>Dimensional Ease</th>
                        <th style={{ padding: '10px 12px', fontWeight: 600 }}>Classification</th>
                        <th style={{ padding: '10px 12px', fontWeight: 600 }}>Evidence Explanation</th>
                      </tr>
                    </thead>
                    <tbody>
                      {fitResult.regional_comparisons.map((c) => (
                        <tr key={c.region} style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                          <td style={{ padding: '12px', fontWeight: 700, color: '#ffffff' }} className="mono">
                            {c.region.replace('_circumference', '').replace('_breadth', '')}
                          </td>
                          <td style={{ padding: '12px', color: 'var(--text-muted)' }}>
                            {c.body_measurement_cm.toFixed(1)} cm
                          </td>
                          <td style={{ padding: '12px', color: 'var(--text-muted)' }}>
                            {c.garment_dimension_cm.toFixed(1)} cm
                          </td>
                          <td style={{ padding: '12px', fontWeight: 800, fontSize: '14px', color: c.ease_cm >= 0 ? 'var(--accent-cyan)' : 'var(--accent-rose)' }}>
                            {c.ease_cm >= 0 ? `+${c.ease_cm.toFixed(2)}` : c.ease_cm.toFixed(2)} cm
                          </td>
                          <td style={{ padding: '12px' }}>
                            <span className={`badge ${getClassificationBadgeClass(c.classification)}`}>
                              {c.classification}
                            </span>
                          </td>
                          <td style={{ padding: '12px', fontSize: '12px', color: 'var(--text-dim)', maxWidth: '280px' }}>
                            {c.explanation}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Provisional Scoring Disclaimer & Governance Banner */}
              <div
                style={{
                  padding: '16px',
                  background: 'rgba(15, 23, 42, 0.7)',
                  border: '1px solid var(--border-medium)',
                  borderRadius: '10px',
                  fontSize: '12px',
                  color: 'var(--text-muted)',
                  display: 'flex',
                  gap: '12px',
                  lineHeight: 1.6,
                }}
              >
                <ShieldAlert size={20} color="var(--accent-amber)" style={{ flexShrink: 0, marginTop: '2px' }} />
                <div>
                  <strong style={{ color: '#ffffff' }}>WearWise Honest Fit Engineering Disclaimer:</strong>
                  <p style={{ marginTop: '4px' }}>
                    {fitResult.disclaimer ||
                      'WearWise Honest Fit Rev 1.2.1 evaluates dimensional ease against symmetric engineering penalty functions. All scores and regional classifications are provisional and designed for sizing assistance, not clinical anthropometry or calibrated bespoke tailoring.'}
                  </p>
                </div>
              </div>
            </>
          ) : (
            /* Empty State */
            <div className="card" style={{ padding: '60px 24px', textAlign: 'center' }}>
              <div
                style={{
                  width: '56px',
                  height: '56px',
                  borderRadius: '50%',
                  background: 'rgba(56, 189, 248, 0.08)',
                  border: '1px solid rgba(56, 189, 248, 0.2)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  margin: '0 auto 16px',
                }}
              >
                <Sparkles size={24} color="var(--accent-cyan)" />
              </div>
              <h2 style={{ fontSize: '18px', fontWeight: 800, color: '#ffffff', marginBottom: '8px' }}>
                Honest Fit Evaluation Ready
              </h2>
              <p style={{ fontSize: '13px', color: 'var(--text-muted)', maxWidth: '440px', margin: '0 auto 20px', lineHeight: 1.6 }}>
                Select a merchant garment from the left panel and click &quot;Evaluate Honest Fit&quot; to calculate dimensional ease,
                regional fit classifications, and composite sizing scores.
              </p>
            </div>
          )}
        </div>
      </div>
    </AppLayout>
  );
};
