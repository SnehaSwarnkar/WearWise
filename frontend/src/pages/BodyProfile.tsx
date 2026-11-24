import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { AppLayout } from '../components/layout/AppLayout';
import { useAuth } from '../context/AuthContext';
import { apiClient } from '../api/client';
import { ProfileRevisionSummary } from '../types/api';
import {
  User,
  Activity,
  History,
  Edit3,
  CheckCircle2,
  AlertCircle,
  Box,
  Save,
  PlusCircle,
  HelpCircle,
} from 'lucide-react';

export const BodyProfilePage: React.FC = () => {
  const { activeProfile, refreshProfiles, setActiveProfile } = useAuth();
  const navigate = useNavigate();

  // Creation form state
  const [createGender, setCreateGender] = useState<'masculine' | 'feminine' | 'neutral'>('masculine');
  const [createStature, setCreateStature] = useState<number>(178.5);
  const [createWeight, setCreateWeight] = useState<number>(74.0);
  const [creating, setCreating] = useState(false);

  // Edit metadata state
  const [editOpen, setEditOpen] = useState(false);
  const [editGender, setEditGender] = useState<'masculine' | 'feminine' | 'neutral'>('masculine');
  const [editWeight, setEditWeight] = useState<number | ''>('');
  const [savingEdit, setSavingEdit] = useState(false);

  // Revision history
  const [revisions, setRevisions] = useState<ProfileRevisionSummary[]>([]);
  const [loadingRevisions, setLoadingRevisions] = useState(false);

  // Banner message
  const [banner, setBanner] = useState<{ type: 'success' | 'error' | 'info'; message: string } | null>(null);

  useEffect(() => {
    if (activeProfile) {
      setEditGender(activeProfile.presentation_gender);
      setEditWeight(activeProfile.reported_weight_kg ?? '');

      setLoadingRevisions(true);
      apiClient
        .getProfileRevisions(activeProfile.profile_id)
        .then((res) => setRevisions(res.revisions))
        .catch((err) => console.warn('Could not fetch revisions:', err))
        .finally(() => setLoadingRevisions(false));
    }
  }, [activeProfile]);

  const handleCreateProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreating(true);
    setBanner(null);

    try {
      const newProfile = await apiClient.createProfile({
        presentation_gender: createGender,
        stature_cm: createStature,
        reported_weight_kg: createWeight || null,
        initial_controls: {
          shoulder_width: 0.55,
          chest_fullness: 0.50,
          belly_fullness: 0.45,
          waist_definition: 0.60,
          arm_fullness: 0.50,
          hip_fullness: 0.50,
          thigh_fullness: 0.50,
          calf_fullness: 0.50,
        },
      });

      await refreshProfiles();
      setActiveProfile(newProfile);
      setBanner({
        type: 'success',
        message: `Body profile successfully created with canonical stature ${newProfile.stature_cm} cm (Revision 1 initialized).`,
      });
    } catch (err: any) {
      setBanner({
        type: 'error',
        message: err.message || 'Failed to create body profile.',
      });
    } finally {
      setCreating(false);
    }
  };

  const handleSaveMetadata = async () => {
    if (!activeProfile) return;
    setSavingEdit(true);
    setBanner(null);

    try {
      const updated = await apiClient.updateProfile(activeProfile.profile_id, {
        presentation_gender: editGender,
        reported_weight_kg: editWeight !== '' ? Number(editWeight) : null,
      });

      setActiveProfile(updated);
      setEditOpen(false);
      setBanner({
        type: 'success',
        message: 'Profile metadata updated successfully.',
      });
    } catch (err: any) {
      setBanner({
        type: 'error',
        message: err.message || 'Failed to update profile.',
      });
    } finally {
      setSavingEdit(false);
    }
  };

  return (
    <AppLayout banner={banner || undefined}>
      {/* Page Header */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
          marginBottom: '28px',
          flexWrap: 'wrap',
          gap: '16px',
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '6px' }}>
            <h1 style={{ fontSize: '24px', fontWeight: 800, letterSpacing: '-0.02em', color: '#ffffff' }}>
              Body Profile & Anthropometry
            </h1>
            {activeProfile && (
              <span className="badge badge-cyan">Revision {activeProfile.current_revision}</span>
            )}
          </div>
          <p style={{ fontSize: '14px', color: 'var(--text-muted)' }}>
            Authoritative body dimensions, anatomical bounds governance, and revision audit trail.
          </p>
        </div>

        {activeProfile && (
          <div style={{ display: 'flex', gap: '10px' }}>
            <button onClick={() => setEditOpen(!editOpen)} className="btn-secondary">
              <Edit3 size={15} />
              <span>{editOpen ? 'Close Editor' : 'Edit Profile'}</span>
            </button>
            <button onClick={() => navigate('/avatar')} className="btn-primary">
              <Box size={16} />
              <span>Open 3D Avatar Studio</span>
            </button>
          </div>
        )}
      </div>

      {/* Main Body */}
      {!activeProfile ? (
        /* Profile Creation State */
        <div style={{ maxWidth: '640px', margin: '40px auto' }}>
          <div className="card-raised">
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '16px' }}>
              <PlusCircle size={22} color="var(--accent-cyan)" />
              <h2 style={{ fontSize: '18px', fontWeight: 700, color: '#ffffff' }}>
                Create Shopper Body Profile Anchor
              </h2>
            </div>

            <p style={{ fontSize: '13px', color: 'var(--text-muted)', marginBottom: '24px', lineHeight: 1.6 }}>
              Under the WearWise BICE architecture, a body profile anchor establishes canonical stature and semantic shape
              controls in Revision 1, serving as the immutable ground truth for all subsequent avatar generation and fit
              evaluations.
            </p>

            <form onSubmit={handleCreateProfile}>
              <div style={{ marginBottom: '18px' }}>
                <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, marginBottom: '8px' }}>
                  Presentation Gender
                </label>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '10px' }}>
                  {(['masculine', 'feminine', 'neutral'] as const).map((g) => (
                    <button
                      key={g}
                      type="button"
                      onClick={() => setCreateGender(g)}
                      style={{
                        padding: '10px',
                        borderRadius: '8px',
                        fontSize: '13px',
                        fontWeight: 600,
                        textTransform: 'capitalize',
                        background: createGender === g ? 'rgba(56, 189, 248, 0.15)' : 'var(--bg-surface)',
                        border: `1px solid ${createGender === g ? 'var(--accent-cyan)' : 'var(--border-medium)'}`,
                        color: createGender === g ? '#ffffff' : 'var(--text-muted)',
                      }}
                    >
                      {g}
                    </button>
                  ))}
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '24px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, marginBottom: '6px' }}>
                    Stature (Height in cm) *
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    min="100.0"
                    max="230.0"
                    required
                    value={createStature}
                    onChange={(e) => setCreateStature(parseFloat(e.target.value))}
                    className="input-field mono"
                  />
                  <span style={{ fontSize: '11px', color: 'var(--text-dim)', marginTop: '4px', display: 'block' }}>
                    Safe bounds: [100.0, 230.0] cm
                  </span>
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, marginBottom: '6px' }}>
                    Reported Weight (kg)
                  </label>
                  <input
                    type="number"
                    step="0.5"
                    min="30.0"
                    max="300.0"
                    value={createWeight}
                    onChange={(e) => setCreateWeight(parseFloat(e.target.value))}
                    className="input-field mono"
                  />
                  <span style={{ fontSize: '11px', color: 'var(--text-dim)', marginTop: '4px', display: 'block' }}>
                    Auxiliary weight: [30.0, 300.0] kg
                  </span>
                </div>
              </div>

              <button
                type="submit"
                disabled={creating}
                className="btn-primary"
                style={{ width: '100%', padding: '12px 0', fontSize: '15px' }}
              >
                {creating ? 'Initializing Profile Revision 1...' : 'Create Body Profile'}
              </button>
            </form>
          </div>
        </div>
      ) : (
        /* Profile Active View */
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          {/* Edit Metadata Modal/Drawer */}
          {editOpen && (
            <div className="card-raised" style={{ borderColor: 'var(--accent-cyan)' }}>
              <h3 style={{ fontSize: '15px', fontWeight: 700, marginBottom: '14px', color: '#ffffff' }}>
                Edit Profile Metadata
              </h3>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '18px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '12px', color: 'var(--text-muted)', marginBottom: '6px' }}>
                    Presentation Gender
                  </label>
                  <select
                    value={editGender}
                    onChange={(e) => setEditGender(e.target.value as any)}
                    className="input-field"
                  >
                    <option value="masculine">Masculine</option>
                    <option value="feminine">Feminine</option>
                    <option value="neutral">Neutral</option>
                  </select>
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '12px', color: 'var(--text-muted)', marginBottom: '6px' }}>
                    Reported Weight (kg)
                  </label>
                  <input
                    type="number"
                    step="0.5"
                    value={editWeight}
                    onChange={(e) => setEditWeight(e.target.value !== '' ? parseFloat(e.target.value) : '')}
                    className="input-field mono"
                  />
                </div>
              </div>
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
                <button onClick={() => setEditOpen(false)} className="btn-secondary">
                  Cancel
                </button>
                <button onClick={handleSaveMetadata} disabled={savingEdit} className="btn-primary">
                  <Save size={14} />
                  <span>{savingEdit ? 'Saving...' : 'Save Changes'}</span>
                </button>
              </div>
            </div>
          )}

          {/* Profile Overview Card */}
          <div className="card">
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '20px' }}>
              <div>
                <span style={{ fontSize: '11px', color: 'var(--text-dim)', textTransform: 'uppercase' }}>Profile ID</span>
                <div style={{ fontSize: '14px', fontWeight: 600, color: '#ffffff', marginTop: '4px' }} className="mono">
                  {activeProfile.profile_id}
                </div>
              </div>

              <div>
                <span style={{ fontSize: '11px', color: 'var(--text-dim)', textTransform: 'uppercase' }}>Canonical Stature</span>
                <div style={{ fontSize: '20px', fontWeight: 800, color: 'var(--accent-cyan)', marginTop: '2px' }}>
                  {activeProfile.stature_cm} <span style={{ fontSize: '13px', color: 'var(--text-muted)' }}>cm</span>
                </div>
              </div>

              <div>
                <span style={{ fontSize: '11px', color: 'var(--text-dim)', textTransform: 'uppercase' }}>Reported Weight</span>
                <div style={{ fontSize: '20px', fontWeight: 800, color: '#ffffff', marginTop: '2px' }}>
                  {activeProfile.reported_weight_kg ? `${activeProfile.reported_weight_kg} kg` : '—'}
                </div>
              </div>

              <div>
                <span style={{ fontSize: '11px', color: 'var(--text-dim)', textTransform: 'uppercase' }}>Presentation Gender</span>
                <div style={{ fontSize: '16px', fontWeight: 700, color: '#ffffff', marginTop: '4px', textTransform: 'capitalize' }}>
                  {activeProfile.presentation_gender}
                </div>
              </div>

              <div>
                <span style={{ fontSize: '11px', color: 'var(--text-dim)', textTransform: 'uppercase' }}>Active Revision</span>
                <div style={{ fontSize: '16px', fontWeight: 700, color: 'var(--accent-emerald)', marginTop: '4px' }}>
                  Revision {activeProfile.current_revision}
                </div>
              </div>
            </div>
          </div>

          {/* Active Anthropometric Measurements Panel */}
          <div className="card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '18px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Activity size={18} color="var(--accent-cyan)" />
                <h2 style={{ fontSize: '16px', fontWeight: 700, color: '#ffffff' }}>
                  Authoritative Anthropometric Measurements
                </h2>
              </div>
              <span className="badge badge-cyan">
                {Object.keys(activeProfile.active_measurements).length} Active Dimensions
              </span>
            </div>

            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--border-medium)', textAlign: 'left', color: 'var(--text-dim)' }}>
                    <th style={{ padding: '12px' }}>Dimension Code</th>
                    <th style={{ padding: '12px' }}>Extracted Dimension</th>
                    <th style={{ padding: '12px' }}>Tolerance</th>
                    <th style={{ padding: '12px' }}>Acquisition Method</th>
                    <th style={{ padding: '12px' }}>Assessment State</th>
                    <th style={{ padding: '12px' }}>Validation State</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(activeProfile.active_measurements).map(([code, m]) => (
                    <tr key={code} style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                      <td style={{ padding: '14px 12px', fontWeight: 700, color: '#ffffff' }} className="mono">
                        {code}
                      </td>
                      <td style={{ padding: '14px 12px', fontSize: '15px', fontWeight: 800, color: 'var(--accent-cyan)' }}>
                        {m.value_cm.toFixed(2)} cm
                      </td>
                      <td style={{ padding: '14px 12px', color: 'var(--text-muted)' }} className="mono">
                        &plusmn;{m.tolerance_cm.toFixed(2)} cm
                      </td>
                      <td style={{ padding: '14px 12px' }}>
                        <span
                          className={
                            m.acquisition_method === 'geometry_extracted'
                              ? 'badge badge-cyan'
                              : 'badge badge-muted'
                          }
                        >
                          {m.acquisition_method}
                        </span>
                      </td>
                      <td style={{ padding: '14px 12px' }}>
                        <span
                          className={
                            m.assessment_state === 'eligible'
                              ? 'badge badge-emerald'
                              : m.assessment_state === 'provisional'
                              ? 'badge badge-amber'
                              : 'badge badge-muted'
                          }
                        >
                          {m.assessment_state}
                        </span>
                      </td>
                      <td style={{ padding: '14px 12px' }}>
                        <span className="badge badge-muted">{m.validation_state}</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Assessment State Specification Notice */}
            <div
              style={{
                marginTop: '20px',
                padding: '14px 16px',
                background: 'rgba(56, 189, 248, 0.05)',
                border: '1px solid rgba(56, 189, 248, 0.15)',
                borderRadius: '8px',
                display: 'flex',
                gap: '12px',
                fontSize: '12px',
                color: 'var(--text-muted)',
                lineHeight: 1.5,
              }}
            >
              <HelpCircle size={18} color="var(--accent-cyan)" style={{ flexShrink: 0, marginTop: '2px' }} />
              <div>
                <strong>Anthropometry Assessment State Governance:</strong> Dimensions marked{' '}
                <span className="badge badge-emerald" style={{ padding: '1px 6px', fontSize: '10px' }}>
                  eligible
                </span>{' '}
                (stature, chest circumference, waist circumference, biacromial breadth) have satisfied ISO 8559-1 anatomical
                landmark criteria. Dimensions marked{' '}
                <span className="badge badge-amber" style={{ padding: '1px 6px', fontSize: '10px' }}>
                  provisional
                </span>{' '}
                (e.g., hip circumference) are usable for indicative Honest Fit evaluations pending localized gluteal apex curvature calibration.
              </div>
            </div>
          </div>

          {/* Revision History Timeline */}
          <div className="card">
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
              <History size={18} color="var(--accent-cyan)" />
              <h2 style={{ fontSize: '16px', fontWeight: 700, color: '#ffffff' }}>Profile Revision Audit Trail</h2>
            </div>

            {loadingRevisions ? (
              <div style={{ padding: '20px', textAlign: 'center', color: 'var(--text-dim)', fontSize: '13px' }}>
                Loading revisions...
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {revisions.map((rev) => (
                  <div
                    key={rev.revision_number}
                    style={{
                      padding: '12px 16px',
                      background: 'var(--bg-surface-raised)',
                      border: '1px solid var(--border-medium)',
                      borderRadius: '8px',
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                      <span className="badge badge-cyan" style={{ fontSize: '11px' }}>
                        Rev {rev.revision_number}
                      </span>
                      <span style={{ fontSize: '13px', fontWeight: 600, color: '#ffffff' }}>
                        {rev.has_controls ? 'Shape Controls Updated & Persisted' : 'Profile Created'}
                      </span>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '16px', fontSize: '12px', color: 'var(--text-dim)' }}>
                      <span>{rev.measurement_count} Measurements</span>
                      <span>{new Date(rev.created_at).toLocaleString()}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </AppLayout>
  );
};
