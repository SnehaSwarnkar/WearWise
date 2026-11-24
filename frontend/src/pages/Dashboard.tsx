import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { AppLayout } from '../components/layout/AppLayout';
import { AvatarViewer } from '../components/avatar/AvatarViewer';
import { useAuth } from '../context/AuthContext';
import { apiClient } from '../api/client';
import { RecentRecommendationItem } from '../types/api';
import {
  User,
  Box,
  ShoppingBag,
  Sparkles,
  ArrowRight,
  CheckCircle2,
  Clock,
  Layers,
  Activity,
  PlusCircle,
} from 'lucide-react';

export const Dashboard: React.FC = () => {
  const { activeProfile, role, refreshProfiles } = useAuth();
  const navigate = useNavigate();

  const [recentRecs, setRecentRecs] = useState<RecentRecommendationItem[]>([]);
  const [loadingRecs, setLoadingRecs] = useState(false);

  useEffect(() => {
    if (activeProfile) {
      setLoadingRecs(true);
      apiClient
        .listRecentFitRecommendations(activeProfile.profile_id)
        .then((data) => setRecentRecs(data))
        .catch((err) => console.warn('Could not load recent fit recommendations:', err))
        .finally(() => setLoadingRecs(false));
    } else {
      setRecentRecs([]);
    }
  }, [activeProfile]);

  return (
    <AppLayout>
      {/* Welcome & Quick Summary Header */}
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
              WearWise Executive Dashboard
            </h1>
            <span className="badge badge-cyan">MVP Release</span>
          </div>
          <p style={{ fontSize: '14px', color: 'var(--text-muted)' }}>
            Real-time anthropometry, NAVER Anny 3D avatar workspace, and deterministic Honest Fit evaluation.
          </p>
        </div>

        {/* Quick actions */}
        <div style={{ display: 'flex', gap: '10px' }}>
          {activeProfile ? (
            <>
              <button onClick={() => navigate('/avatar')} className="btn-primary">
                <Box size={16} />
                <span>3D Avatar Studio</span>
              </button>
              <button onClick={() => navigate('/fit')} className="btn-secondary">
                <Sparkles size={16} color="var(--accent-cyan)" />
                <span>Evaluate Fit</span>
              </button>
            </>
          ) : (
            <button onClick={() => navigate('/profile')} className="btn-primary">
              <PlusCircle size={16} />
              <span>Create Shopper Profile</span>
            </button>
          )}
        </div>
      </div>

      {/* Main Grid: Left = Avatar & Profile Summary; Right = Measurements & Recommendations */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'minmax(340px, 460px) 1fr',
          gap: '24px',
          alignItems: 'start',
        }}
      >
        {/* Left Column: 3D Avatar Preview & Profile Spec */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {/* Avatar Preview Card */}
          <div className="card" style={{ padding: '16px' }}>
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: '12px',
                padding: '0 4px',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Box size={16} color="var(--accent-cyan)" />
                <span style={{ fontSize: '13px', fontWeight: 700, color: '#ffffff' }}>Current 3D Avatar</span>
              </div>
              <button
                onClick={() => navigate('/avatar')}
                style={{
                  fontSize: '12px',
                  color: 'var(--accent-cyan)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px',
                  fontWeight: 600,
                }}
              >
                <span>Studio</span>
                <ArrowRight size={13} />
              </button>
            </div>

            <AvatarViewer
              assetUrl={activeProfile?.latest_asset_url}
              height="380px"
              initialAutoRotate={true}
            />

            {activeProfile?.latest_asset_url && (
              <div
                style={{
                  marginTop: '12px',
                  display: 'flex',
                  justifyContent: 'space-between',
                  fontSize: '11px',
                  color: 'var(--text-dim)',
                  padding: '0 4px',
                }}
              >
                <span>Format: GLB (glTF 2.0 Binary)</span>
                <span>Content-Addressed SHA-256 Storage</span>
              </div>
            )}
          </div>

          {/* Profile Details Card */}
          <div className="card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <User size={16} color="var(--accent-cyan)" />
                <h3 style={{ fontSize: '14px', fontWeight: 700, color: '#ffffff' }}>Profile Anchor Specification</h3>
              </div>
              <button
                onClick={() => navigate('/profile')}
                style={{ fontSize: '12px', color: 'var(--accent-cyan)', fontWeight: 600 }}
              >
                Edit
              </button>
            </div>

            {activeProfile ? (
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
                <div style={{ background: 'var(--bg-surface-raised)', padding: '12px', borderRadius: '8px' }}>
                  <div style={{ fontSize: '11px', color: 'var(--text-dim)', textTransform: 'uppercase', marginBottom: '4px' }}>
                    Stature (Height)
                  </div>
                  <div style={{ fontSize: '20px', fontWeight: 800, color: '#ffffff' }}>
                    {activeProfile.stature_cm} <span style={{ fontSize: '13px', color: 'var(--text-muted)' }}>cm</span>
                  </div>
                  <div style={{ fontSize: '10px', color: 'var(--accent-emerald)', marginTop: '2px' }}>
                    Canonical Anchor
                  </div>
                </div>

                <div style={{ background: 'var(--bg-surface-raised)', padding: '12px', borderRadius: '8px' }}>
                  <div style={{ fontSize: '11px', color: 'var(--text-dim)', textTransform: 'uppercase', marginBottom: '4px' }}>
                    Reported Weight
                  </div>
                  <div style={{ fontSize: '20px', fontWeight: 800, color: '#ffffff' }}>
                    {activeProfile.reported_weight_kg ? (
                      <>
                        {activeProfile.reported_weight_kg} <span style={{ fontSize: '13px', color: 'var(--text-muted)' }}>kg</span>
                      </>
                    ) : (
                      <span style={{ fontSize: '14px', color: 'var(--text-dim)' }}>Not recorded</span>
                    )}
                  </div>
                  <div style={{ fontSize: '10px', color: 'var(--text-dim)', marginTop: '2px' }}>
                    Auxiliary Metric
                  </div>
                </div>

                <div style={{ background: 'var(--bg-surface-raised)', padding: '12px', borderRadius: '8px' }}>
                  <div style={{ fontSize: '11px', color: 'var(--text-dim)', textTransform: 'uppercase', marginBottom: '4px' }}>
                    Presentation Gender
                  </div>
                  <div style={{ fontSize: '15px', fontWeight: 700, color: '#ffffff', textTransform: 'capitalize' }}>
                    {activeProfile.presentation_gender}
                  </div>
                </div>

                <div style={{ background: 'var(--bg-surface-raised)', padding: '12px', borderRadius: '8px' }}>
                  <div style={{ fontSize: '11px', color: 'var(--text-dim)', textTransform: 'uppercase', marginBottom: '4px' }}>
                    Revision / Lock
                  </div>
                  <div style={{ fontSize: '15px', fontWeight: 700, color: 'var(--accent-cyan)' }}>
                    Revision {activeProfile.current_revision}
                  </div>
                  <div style={{ fontSize: '10px', color: 'var(--text-dim)', marginTop: '2px' }}>
                    Optimistic Lock Active
                  </div>
                </div>
              </div>
            ) : (
              <div style={{ textAlign: 'center', padding: '24px 0' }}>
                <p style={{ fontSize: '13px', color: 'var(--text-muted)', marginBottom: '12px' }}>
                  No active body profile loaded.
                </p>
                <button onClick={() => navigate('/profile')} className="btn-primary" style={{ fontSize: '12px' }}>
                  Create Profile Now
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Active Measurements & Recent Recommendations */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          {/* Active Measurements Table Card */}
          <div className="card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Activity size={16} color="var(--accent-cyan)" />
                <h3 style={{ fontSize: '14px', fontWeight: 700, color: '#ffffff' }}>
                  Active Body Measurements (Anthropometry)
                </h3>
              </div>
              <span className="badge badge-emerald">
                {activeProfile ? Object.keys(activeProfile.active_measurements).length : 0} Measurements
              </span>
            </div>

            {activeProfile && Object.keys(activeProfile.active_measurements).length > 0 ? (
              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
                  <thead>
                    <tr style={{ borderBottom: '1px solid var(--border-medium)', textAlign: 'left', color: 'var(--text-dim)' }}>
                      <th style={{ padding: '10px 12px', fontWeight: 600 }}>Dimension Code</th>
                      <th style={{ padding: '10px 12px', fontWeight: 600 }}>Extracted Value</th>
                      <th style={{ padding: '10px 12px', fontWeight: 600 }}>Method</th>
                      <th style={{ padding: '10px 12px', fontWeight: 600 }}>Quality Assessment</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(activeProfile.active_measurements).map(([code, m]) => (
                      <tr
                        key={code}
                        style={{
                          borderBottom: '1px solid var(--border-subtle)',
                          transition: 'background 0.15s ease',
                        }}
                      >
                        <td style={{ padding: '12px', fontWeight: 600, color: '#ffffff' }} className="mono">
                          {code}
                        </td>
                        <td style={{ padding: '12px', fontWeight: 700, color: 'var(--accent-cyan)', fontSize: '14px' }}>
                          {m.value_cm.toFixed(2)} cm
                        </td>
                        <td style={{ padding: '12px' }}>
                          <span
                            className={
                              m.acquisition_method === 'geometry_extracted'
                                ? 'badge badge-cyan'
                                : 'badge badge-muted'
                            }
                            style={{ fontSize: '10px' }}
                          >
                            {m.acquisition_method}
                          </span>
                        </td>
                        <td style={{ padding: '12px' }}>
                          <span
                            className={
                              m.assessment_state === 'eligible'
                                ? 'badge badge-emerald'
                                : m.assessment_state === 'provisional'
                                ? 'badge badge-amber'
                                : 'badge badge-muted'
                            }
                            style={{ fontSize: '10px' }}
                          >
                            {m.assessment_state}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div style={{ padding: '24px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '13px' }}>
                No active measurements found. Generate an avatar from the 3D Avatar Studio to extract geometry-backed body
                dimensions.
              </div>
            )}
          </div>

          {/* Recent Recommendations Card */}
          <div className="card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Sparkles size={16} color="var(--accent-cyan)" />
                <h3 style={{ fontSize: '14px', fontWeight: 700, color: '#ffffff' }}>Recent Honest Fit Recommendations</h3>
              </div>
              <button
                onClick={() => navigate('/fit')}
                style={{ fontSize: '12px', color: 'var(--accent-cyan)', fontWeight: 600 }}
              >
                New Fit Evaluation
              </button>
            </div>

            {loadingRecs ? (
              <div style={{ padding: '24px', textAlign: 'center', color: 'var(--text-dim)', fontSize: '13px' }}>
                Loading recommendations...
              </div>
            ) : recentRecs.length > 0 ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {recentRecs.map((rec) => (
                  <div
                    key={rec.recommendation_id}
                    style={{
                      background: 'var(--bg-surface-raised)',
                      border: '1px solid var(--border-medium)',
                      borderRadius: '8px',
                      padding: '14px 16px',
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                    }}
                  >
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                        <span style={{ fontSize: '15px', fontWeight: 800, color: '#ffffff' }}>
                          Recommended: Size {rec.recommended_size}
                        </span>
                        <span className="badge badge-cyan">{rec.status}</span>
                      </div>
                      <div style={{ fontSize: '11px', color: 'var(--text-dim)' }}>
                        Rulebook {rec.rulebook_version} &bull; {new Date(rec.evaluated_at).toLocaleDateString()}
                        {rec.alternative_size && (
                          <span style={{ marginLeft: '8px', color: 'var(--accent-amber)' }}>
                            (Alt: {rec.alternative_size.size_label})
                          </span>
                        )}
                      </div>
                    </div>

                    <div style={{ textAlign: 'right' }}>
                      <div style={{ fontSize: '18px', fontWeight: 800, color: 'var(--accent-emerald)' }}>
                        {rec.composite_fit_score.toFixed(1)}{' '}
                        <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>/ 100</span>
                      </div>
                      <div style={{ fontSize: '10px', color: 'var(--text-dim)' }}>Provisional Score</div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div style={{ padding: '24px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '13px' }}>
                No fit evaluations recorded yet. Navigate to <strong>Honest Fit</strong> to evaluate garments against your active body measurements.
              </div>
            )}
          </div>
        </div>
      </div>
    </AppLayout>
  );
};
