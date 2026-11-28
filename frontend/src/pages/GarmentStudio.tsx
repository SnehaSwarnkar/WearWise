import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { AppLayout } from '../components/layout/AppLayout';
import { useAuth } from '../context/AuthContext';
import { apiClient } from '../api/client';
import { GarmentProfile, GarmentCreateRequest, GarmentSizeCreateRequest } from '../types/api';
import {
  ShoppingBag,
  PlusCircle,
  Tag,
  CheckCircle2,
  Sparkles,
  Layers,
  Ruler,
  AlertCircle,
  Scissors,
} from 'lucide-react';

export const GarmentStudio: React.FC = () => {
  const { role, switchRole } = useAuth();
  const navigate = useNavigate();

  const [garments, setGarments] = useState<GarmentProfile[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  // Register Garment Form State
  const [showRegisterModal, setShowRegisterModal] = useState<boolean>(false);
  const [sku, setSku] = useState('TSH-WW-CREW-001');
  const [title, setTitle] = useState('Everyday Heavyweight Crewneck Tee');
  const [category, setCategory] = useState<'t_shirt' | 'casual_shirt' | 'trousers' | 'jeans'>('t_shirt');
  const [cottonPct, setCottonPct] = useState(1.0);
  const [polyPct, setPolyPct] = useState(0.0);
  const [mechStretchPct, setMechStretchPct] = useState(0.015);
  const [recoveryPct, setRecoveryPct] = useState(0.9);
  const [stretchDir, setStretchDir] = useState<'rigid_zero' | 'mono_weft' | 'mono_warp' | 'bi_directional'>('rigid_zero');
  const [registering, setRegistering] = useState<boolean>(false);

  // Add Size Form State
  const [showAddSizeModal, setShowAddSizeModal] = useState<boolean>(false);
  const [selectedGarmentForSize, setSelectedGarmentForSize] = useState<GarmentProfile | null>(null);
  const [sizeLabel, setSizeLabel] = useState('M');
  const [sortOrder, setSortOrder] = useState(3);
  const [chestWidth, setChestWidth] = useState(46.5);
  const [shoulderWidth, setShoulderWidth] = useState(41.5);
  const [backLength, setBackLength] = useState(69.0);
  const [waistWidth, setWaistWidth] = useState(44.0);
  const [hipWidth, setHipWidth] = useState(47.0);
  const [measProcedure, setMeasProcedure] = useState('flat_relaxed_tabletop_bs_4952');
  const [addingSize, setAddingSize] = useState<boolean>(false);

  const [banner, setBanner] = useState<{ type: 'success' | 'error' | 'info'; message: string } | null>(null);

  const fetchGarments = async () => {
    setLoading(true);
    try {
      const list = await apiClient.listGarments();
      setGarments(list);
    } catch (err: any) {
      console.warn('Failed to load garments:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchGarments();
  }, []);

  const handleRegisterGarment = async (e: React.FormEvent) => {
    e.preventDefault();
    setRegistering(true);
    setBanner(null);

    const payload: GarmentCreateRequest = {
      sku,
      title,
      category,
      fabric_properties: {
        fibre_composition: {
          cotton: cottonPct,
          polyester: polyPct,
        },
        mechanical_stretch_pct: mechStretchPct,
        stretch_recovery_pct: recoveryPct,
        stretch_direction: stretchDir,
      },
    };

    try {
      const created = await apiClient.createGarment(payload);
      setShowRegisterModal(false);
      setBanner({
        type: 'success',
        message: `Garment "${created.title}" (SKU: ${created.sku}) registered successfully under Brand catalog.`,
      });
      fetchGarments();
    } catch (err: any) {
      setBanner({
        type: 'error',
        message: err.message || 'Failed to register garment.',
      });
    } finally {
      setRegistering(false);
    }
  };

  const handleAddSize = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedGarmentForSize) return;
    setAddingSize(true);
    setBanner(null);

    const measurements = [
      {
        dimension_code: 'garment_half_chest_width',
        value_cm: chestWidth,
        tolerance_cm: 1.0,
        measurement_procedure: measProcedure,
        provenance: 'demonstration_fixture',
      },
      {
        dimension_code: 'garment_shoulder_seam_width',
        value_cm: shoulderWidth,
        tolerance_cm: 1.0,
        measurement_procedure: measProcedure,
        provenance: 'demonstration_fixture',
      },
      {
        dimension_code: 'garment_back_length',
        value_cm: backLength,
        tolerance_cm: 1.0,
        measurement_procedure: measProcedure,
        provenance: 'demonstration_fixture',
      },
    ];

    if (waistWidth > 0) {
      measurements.push({
        dimension_code: 'garment_waist_width',
        value_cm: waistWidth,
        tolerance_cm: 1.0,
        measurement_procedure: measProcedure,
        provenance: 'demonstration_fixture',
      });
    }

    if (hipWidth > 0) {
      measurements.push({
        dimension_code: 'garment_hip_width',
        value_cm: hipWidth,
        tolerance_cm: 1.0,
        measurement_procedure: measProcedure,
        provenance: 'demonstration_fixture',
      });
    }

    const payload: GarmentSizeCreateRequest = {
      size_label: sizeLabel,
      sort_order: sortOrder,
      measurements,
    };

    try {
      await apiClient.addGarmentSize(selectedGarmentForSize.garment_id, payload);
      setShowAddSizeModal(false);
      setBanner({
        type: 'success',
        message: `Size ${sizeLabel} successfully added to garment "${selectedGarmentForSize.title}".`,
      });
      fetchGarments();
    } catch (err: any) {
      setBanner({
        type: 'error',
        message: err.message || 'Failed to add size specification.',
      });
    } finally {
      setAddingSize(false);
    }
  };

  return (
    <AppLayout banner={banner || undefined}>
      {/* Header */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '24px',
          flexWrap: 'wrap',
          gap: '12px',
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <h1 style={{ fontSize: '24px', fontWeight: 800, color: '#ffffff' }}>Merchant Garment Studio</h1>
            <span className="badge badge-cyan">{garments.length} Garments Cataloged</span>
          </div>
          <p style={{ fontSize: '13px', color: 'var(--text-muted)', marginTop: '2px' }}>
            Fibre composition, tensile mechanical stretch, BS 4952 measurement provenance, and finished size specifications.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '10px' }}>
          {role !== 'brand' && (
            <button
              onClick={() => switchRole('brand')}
              className="btn-secondary"
              style={{ fontSize: '13px', color: '#c084fc' }}
            >
              Switch to Merchant Brand Mode
            </button>
          )}

          <button onClick={() => setShowRegisterModal(true)} className="btn-primary">
            <PlusCircle size={16} />
            <span>Register New Garment</span>
          </button>
        </div>
      </div>

      {/* Garments List / Catalog */}
      {loading ? (
        <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-dim)', fontSize: '14px' }}>
          Loading merchant catalog...
        </div>
      ) : garments.length > 0 ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {garments.map((g) => (
            <div key={g.garment_id} className="card">
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'flex-start',
                  marginBottom: '16px',
                  flexWrap: 'wrap',
                  gap: '12px',
                }}
              >
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '4px' }}>
                    <h2 style={{ fontSize: '17px', fontWeight: 700, color: '#ffffff' }}>{g.title}</h2>
                    <span className="badge badge-cyan">{g.category.replace('_', ' ')}</span>
                  </div>
                  <div style={{ fontSize: '12px', color: 'var(--text-dim)' }}>
                    SKU: <strong className="mono" style={{ color: 'var(--text-muted)' }}>{g.sku}</strong> &bull; Revision{' '}
                    {g.current_revision} &bull; Registered {new Date(g.created_at).toLocaleDateString()}
                  </div>
                </div>

                <div style={{ display: 'flex', gap: '10px' }}>
                  <button
                    onClick={() => {
                      setSelectedGarmentForSize(g);
                      setShowAddSizeModal(true);
                    }}
                    className="btn-secondary"
                    style={{ fontSize: '12px' }}
                  >
                    <PlusCircle size={14} />
                    <span>Add Size Variant</span>
                  </button>

                  <button
                    onClick={() => navigate(`/fit?garment_id=${g.garment_id}`)}
                    className="btn-primary"
                    style={{ fontSize: '12px' }}
                  >
                    <Sparkles size={14} />
                    <span>Evaluate Honest Fit</span>
                  </button>
                </div>
              </div>

              {/* Fabric Mechanical Properties */}
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))',
                  gap: '12px',
                  background: 'var(--bg-surface-raised)',
                  padding: '12px 16px',
                  borderRadius: '8px',
                  marginBottom: '16px',
                  fontSize: '12px',
                }}
              >
                <div>
                  <span style={{ color: 'var(--text-dim)', display: 'block', marginBottom: '2px' }}>
                    Fibre Composition
                  </span>
                  <strong style={{ color: '#ffffff' }}>
                    {Object.entries(g.fabric_properties?.fibre_composition || {})
                      .map(([fib, frac]) => `${(frac * 100).toFixed(0)}% ${fib}`)
                      .join(', ') || '100% Cotton'}
                  </strong>
                </div>

                <div>
                  <span style={{ color: 'var(--text-dim)', display: 'block', marginBottom: '2px' }}>
                    Mechanical Tensile Stretch
                  </span>
                  <strong style={{ color: 'var(--accent-cyan)' }}>
                    {((g.fabric_properties?.mechanical_stretch_pct ?? 0) * 100).toFixed(1)}% Stretch
                  </strong>
                </div>

                <div>
                  <span style={{ color: 'var(--text-dim)', display: 'block', marginBottom: '2px' }}>
                    Elastic Recovery
                  </span>
                  <strong style={{ color: 'var(--accent-emerald)' }}>
                    {((g.fabric_properties?.stretch_recovery_pct ?? 0.9) * 100).toFixed(0)}% Recovery
                  </strong>
                </div>

                <div>
                  <span style={{ color: 'var(--text-dim)', display: 'block', marginBottom: '2px' }}>
                    Stretch Direction
                  </span>
                  <strong style={{ color: 'var(--text-muted)' }}>
                    {g.fabric_properties?.stretch_direction || 'rigid_zero'}
                  </strong>
                </div>
              </div>

              {/* Sizes Specification Table */}
              <div>
                <span style={{ fontSize: '12px', fontWeight: 700, color: '#ffffff', display: 'block', marginBottom: '8px' }}>
                  Finished Size Specifications ({g.sizes.length} Sizes)
                </span>

                {g.sizes.length > 0 ? (
                  <div style={{ overflowX: 'auto' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px' }}>
                      <thead>
                        <tr style={{ borderBottom: '1px solid var(--border-medium)', textAlign: 'left', color: 'var(--text-dim)' }}>
                          <th style={{ padding: '8px 10px', fontWeight: 600 }}>Size Label</th>
                          <th style={{ padding: '8px 10px', fontWeight: 600 }}>Half-Chest Width</th>
                          <th style={{ padding: '8px 10px', fontWeight: 600 }}>Shoulder Seam</th>
                          <th style={{ padding: '8px 10px', fontWeight: 600 }}>Back Length</th>
                          <th style={{ padding: '8px 10px', fontWeight: 600 }}>Waist Width</th>
                          <th style={{ padding: '8px 10px', fontWeight: 600 }}>Provenance</th>
                        </tr>
                      </thead>
                      <tbody>
                        {g.sizes
                          .sort((a, b) => a.sort_order - b.sort_order)
                          .map((s) => (
                            <tr key={s.size_label} style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                              <td style={{ padding: '10px', fontWeight: 800, color: '#ffffff' }}>
                                <span className="badge badge-cyan" style={{ fontSize: '11px' }}>
                                  {s.size_label}
                                </span>
                              </td>
                              <td style={{ padding: '10px', fontWeight: 600, color: 'var(--accent-cyan)' }}>
                                {s.measurements['garment_half_chest_width']
                                  ? `${s.measurements['garment_half_chest_width'].toFixed(1)} cm`
                                  : '—'}
                              </td>
                              <td style={{ padding: '10px', color: 'var(--text-main)' }}>
                                {s.measurements['garment_shoulder_seam_width']
                                  ? `${s.measurements['garment_shoulder_seam_width'].toFixed(1)} cm`
                                  : '—'}
                              </td>
                              <td style={{ padding: '10px', color: 'var(--text-main)' }}>
                                {s.measurements['garment_back_length']
                                  ? `${s.measurements['garment_back_length'].toFixed(1)} cm`
                                  : '—'}
                              </td>
                              <td style={{ padding: '10px', color: 'var(--text-muted)' }}>
                                {s.measurements['garment_waist_width']
                                  ? `${s.measurements['garment_waist_width'].toFixed(1)} cm`
                                  : '—'}
                              </td>
                              <td style={{ padding: '10px' }}>
                                <span className="badge badge-muted" style={{ fontSize: '9px' }}>
                                  BS 4952 Tabletop
                                </span>
                              </td>
                            </tr>
                          ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <div style={{ padding: '16px', textAlign: 'center', color: 'var(--text-dim)', fontSize: '12px' }}>
                    No sizes added yet. Click &quot;Add Size Variant&quot; above to specify finished dimensions.
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="card" style={{ padding: '40px', textAlign: 'center' }}>
          <ShoppingBag size={42} color="var(--accent-cyan)" style={{ margin: '0 auto 16px' }} />
          <h2 style={{ fontSize: '17px', fontWeight: 700, color: '#ffffff', marginBottom: '8px' }}>
            Merchant Garment Catalog Empty
          </h2>
          <p style={{ fontSize: '13px', color: 'var(--text-muted)', maxWidth: '420px', margin: '0 auto 20px', lineHeight: 1.5 }}>
            Register your first garment specification to enable Honest Fit dimensional ease comparisons against customer body
            avatars.
          </p>
          <button onClick={() => setShowRegisterModal(true)} className="btn-primary">
            <PlusCircle size={16} />
            <span>Register First Garment</span>
          </button>
        </div>
      )}

      {/* Modal: Register Garment */}
      {showRegisterModal && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0,0,0,0.75)',
            backdropFilter: 'blur(4px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 100,
          }}
          onClick={() => setShowRegisterModal(false)}
        >
          <div className="card-raised" style={{ width: '520px', maxWidth: '90vw' }} onClick={(e) => e.stopPropagation()}>
            <h2 style={{ fontSize: '18px', fontWeight: 800, color: '#ffffff', marginBottom: '16px' }}>
              Register Merchant Garment Specification
            </h2>

            <form onSubmit={handleRegisterGarment}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px', marginBottom: '14px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, marginBottom: '6px' }}>SKU *</label>
                  <input
                    type="text"
                    required
                    value={sku}
                    onChange={(e) => setSku(e.target.value)}
                    className="input-field mono"
                  />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, marginBottom: '6px' }}>Category *</label>
                  <select
                    value={category}
                    onChange={(e) => setCategory(e.target.value as any)}
                    className="input-field"
                  >
                    <option value="t_shirt">T-Shirt</option>
                    <option value="casual_shirt">Casual Shirt</option>
                    <option value="trousers">Trousers</option>
                    <option value="jeans">Jeans</option>
                  </select>
                </div>
              </div>

              <div style={{ marginBottom: '14px' }}>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, marginBottom: '6px' }}>
                  Garment Title *
                </label>
                <input
                  type="text"
                  required
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="input-field"
                />
              </div>

              {/* Chemical vs Mechanical Split */}
              <div style={{ background: 'var(--bg-surface)', padding: '14px', borderRadius: '8px', marginBottom: '16px', border: '1px solid var(--border-subtle)' }}>
                <span style={{ fontSize: '11px', fontWeight: 700, color: 'var(--accent-cyan)', textTransform: 'uppercase', display: 'block', marginBottom: '10px' }}>
                  Fabric & Mechanical Stretch Specification
                </span>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '10px' }}>
                  <div>
                    <label style={{ display: 'block', fontSize: '11px', color: 'var(--text-muted)', marginBottom: '4px' }}>
                      Cotton Proportion [0.0 - 1.0]
                    </label>
                    <input
                      type="number"
                      step="0.05"
                      min="0.0"
                      max="1.0"
                      value={cottonPct}
                      onChange={(e) => setCottonPct(parseFloat(e.target.value))}
                      className="input-field mono"
                    />
                  </div>
                  <div>
                    <label style={{ display: 'block', fontSize: '11px', color: 'var(--text-muted)', marginBottom: '4px' }}>
                      Tensile Mechanical Stretch %
                    </label>
                    <input
                      type="number"
                      step="0.005"
                      min="0.0"
                      max="0.5"
                      value={mechStretchPct}
                      onChange={(e) => setMechStretchPct(parseFloat(e.target.value))}
                      className="input-field mono"
                    />
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                  <div>
                    <label style={{ display: 'block', fontSize: '11px', color: 'var(--text-muted)', marginBottom: '4px' }}>
                      Stretch Direction
                    </label>
                    <select
                      value={stretchDir}
                      onChange={(e) => setStretchDir(e.target.value as any)}
                      className="input-field"
                    >
                      <option value="rigid_zero">Rigid (Zero Stretch)</option>
                      <option value="mono_weft">Mono-Weft (Horizontal)</option>
                      <option value="mono_warp">Mono-Warp (Vertical)</option>
                      <option value="bi_directional">Bi-Directional</option>
                    </select>
                  </div>
                  <div>
                    <label style={{ display: 'block', fontSize: '11px', color: 'var(--text-muted)', marginBottom: '4px' }}>
                      Recovery Ratio
                    </label>
                    <input
                      type="number"
                      step="0.05"
                      min="0.5"
                      max="1.0"
                      value={recoveryPct}
                      onChange={(e) => setRecoveryPct(parseFloat(e.target.value))}
                      className="input-field mono"
                    />
                  </div>
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
                <button type="button" onClick={() => setShowRegisterModal(false)} className="btn-secondary">
                  Cancel
                </button>
                <button type="submit" disabled={registering} className="btn-primary">
                  {registering ? 'Registering...' : 'Register Garment'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Add Size Variant */}
      {showAddSizeModal && selectedGarmentForSize && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0,0,0,0.75)',
            backdropFilter: 'blur(4px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 100,
          }}
          onClick={() => setShowAddSizeModal(false)}
        >
          <div className="card-raised" style={{ width: '520px', maxWidth: '90vw' }} onClick={(e) => e.stopPropagation()}>
            <h2 style={{ fontSize: '18px', fontWeight: 800, color: '#ffffff', marginBottom: '6px' }}>
              Add Size Specification & Finished Dimensions
            </h2>
            <div style={{ fontSize: '12px', color: 'var(--text-dim)', marginBottom: '16px' }}>
              Garment: <strong style={{ color: '#ffffff' }}>{selectedGarmentForSize.title}</strong>
            </div>

            <form onSubmit={handleAddSize}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px', marginBottom: '14px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, marginBottom: '6px' }}>
                    Size Label (e.g. S, M, L) *
                  </label>
                  <input
                    type="text"
                    required
                    value={sizeLabel}
                    onChange={(e) => setSizeLabel(e.target.value.toUpperCase())}
                    className="input-field mono"
                  />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, marginBottom: '6px' }}>
                    Sort Order (Rank) *
                  </label>
                  <input
                    type="number"
                    required
                    value={sortOrder}
                    onChange={(e) => setSortOrder(parseInt(e.target.value, 10))}
                    className="input-field mono"
                  />
                </div>
              </div>

              {/* Dimensions Input */}
              <div style={{ background: 'var(--bg-surface)', padding: '14px', borderRadius: '8px', marginBottom: '16px' }}>
                <span style={{ fontSize: '11px', fontWeight: 700, color: 'var(--accent-cyan)', textTransform: 'uppercase', display: 'block', marginBottom: '10px' }}>
                  Finished Physical Dimensions (cm)
                </span>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '12px' }}>
                  <div>
                    <label style={{ display: 'block', fontSize: '11px', color: 'var(--text-muted)', marginBottom: '4px' }}>
                      Half-Chest Width (cm) *
                    </label>
                    <input
                      type="number"
                      step="0.1"
                      required
                      value={chestWidth}
                      onChange={(e) => setChestWidth(parseFloat(e.target.value))}
                      className="input-field mono"
                    />
                  </div>

                  <div>
                    <label style={{ display: 'block', fontSize: '11px', color: 'var(--text-muted)', marginBottom: '4px' }}>
                      Shoulder Seam Width (cm) *
                    </label>
                    <input
                      type="number"
                      step="0.1"
                      required
                      value={shoulderWidth}
                      onChange={(e) => setShoulderWidth(parseFloat(e.target.value))}
                      className="input-field mono"
                    />
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                  <div>
                    <label style={{ display: 'block', fontSize: '11px', color: 'var(--text-muted)', marginBottom: '4px' }}>
                      Back Length (cm) *
                    </label>
                    <input
                      type="number"
                      step="0.1"
                      required
                      value={backLength}
                      onChange={(e) => setBackLength(parseFloat(e.target.value))}
                      className="input-field mono"
                    />
                  </div>

                  <div>
                    <label style={{ display: 'block', fontSize: '11px', color: 'var(--text-muted)', marginBottom: '4px' }}>
                      Waist Width (cm)
                    </label>
                    <input
                      type="number"
                      step="0.1"
                      value={waistWidth}
                      onChange={(e) => setWaistWidth(parseFloat(e.target.value))}
                      className="input-field mono"
                    />
                  </div>
                </div>
              </div>

              <div style={{ marginBottom: '16px' }}>
                <label style={{ display: 'block', fontSize: '12px', color: 'var(--text-muted)', marginBottom: '6px' }}>
                  Measurement Procedure & Provenance Standard
                </label>
                <select
                  value={measProcedure}
                  onChange={(e) => setMeasProcedure(e.target.value)}
                  className="input-field"
                >
                  <option value="flat_relaxed_tabletop_bs_4952">BS 4952 Tabletop Relaxed</option>
                  <option value="straight_across_relaxed">Straight Across Relaxed</option>
                  <option value="digital_3d_pattern_spec">Digital 3D CAD Pattern Specification</option>
                </select>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
                <button type="button" onClick={() => setShowAddSizeModal(false)} className="btn-secondary">
                  Cancel
                </button>
                <button type="submit" disabled={addingSize} className="btn-primary">
                  {addingSize ? 'Adding...' : 'Add Size Specification'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </AppLayout>
  );
};
