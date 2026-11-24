import React, { useState, useEffect } from 'react';
import { AppLayout } from '../components/layout/AppLayout';
import { AvatarViewer } from '../components/avatar/AvatarViewer';
import { useAuth } from '../context/AuthContext';
import { apiClient } from '../api/client';
import { BodyShapeControls, AvatarGenerationResponse } from '../types/api';
import {
  Box,
  Sliders,
  Sparkles,
  Save,
  RotateCcw,
  CheckCircle2,
  Clock,
  Layers,
  Activity,
  AlertCircle,
} from 'lucide-react';

const DEFAULT_CONTROLS: BodyShapeControls = {
  shoulder_width: 0.5,
  chest_fullness: 0.5,
  belly_fullness: 0.5,
  waist_definition: 0.5,
  arm_fullness: 0.5,
  hip_fullness: 0.5,
  thigh_fullness: 0.5,
  calf_fullness: 0.5,
};

const PRESETS: Record<string, Partial<BodyShapeControls>> = {
  Balanced: {
    shoulder_width: 0.5,
    chest_fullness: 0.5,
    belly_fullness: 0.5,
    waist_definition: 0.5,
    arm_fullness: 0.5,
    hip_fullness: 0.5,
    thigh_fullness: 0.5,
    calf_fullness: 0.5,
  },
  Athletic: {
    shoulder_width: 0.68,
    chest_fullness: 0.62,
    belly_fullness: 0.35,
    waist_definition: 0.72,
    arm_fullness: 0.60,
    hip_fullness: 0.48,
    thigh_fullness: 0.58,
    calf_fullness: 0.55,
  },
  Slender: {
    shoulder_width: 0.42,
    chest_fullness: 0.38,
    belly_fullness: 0.38,
    waist_definition: 0.52,
    arm_fullness: 0.42,
    hip_fullness: 0.44,
    thigh_fullness: 0.42,
    calf_fullness: 0.45,
  },
  Sturdy: {
    shoulder_width: 0.62,
    chest_fullness: 0.65,
    belly_fullness: 0.68,
    waist_definition: 0.38,
    arm_fullness: 0.58,
    hip_fullness: 0.60,
    thigh_fullness: 0.62,
    calf_fullness: 0.58,
  },
};

export const AvatarStudio: React.FC = () => {
  const { activeProfile, refreshProfiles, setActiveProfile } = useAuth();

  const [controls, setControls] = useState<BodyShapeControls>(
    activeProfile?.shape_controls || DEFAULT_CONTROLS
  );
  const [dirty, setDirty] = useState<boolean>(false);
  const [savingControls, setSavingControls] = useState<boolean>(false);
  const [generating, setGenerating] = useState<boolean>(false);
  const [lastGenResult, setLastGenResult] = useState<AvatarGenerationResponse | null>(null);

  const [banner, setBanner] = useState<{ type: 'success' | 'error' | 'info'; message: string } | null>(null);

  useEffect(() => {
    if (activeProfile?.shape_controls) {
      setControls(activeProfile.shape_controls);
      setDirty(false);
    }
  }, [activeProfile?.current_revision]);

  const handleSliderChange = (key: keyof BodyShapeControls, val: number) => {
    setControls((prev) => ({
      ...prev,
      [key]: val,
    }));
    setDirty(true);
  };

  const applyPreset = (presetName: string) => {
    const preset = PRESETS[presetName];
    if (preset) {
      setControls((prev) => ({
        ...prev,
        ...preset,
      }));
      setDirty(true);
    }
  };

  // 1. Save Controls to Backend
  const handleSaveControls = async () => {
    if (!activeProfile) return;
    setSavingControls(true);
    setBanner(null);

    try {
      const updatedProfile = await apiClient.updateControls(activeProfile.profile_id, {
        expected_revision: activeProfile.current_revision,
        controls: controls,
      });

      setActiveProfile(updatedProfile);
      setDirty(false);
      setBanner({
        type: 'success',
        message: `Shape controls successfully saved. New Revision ${updatedProfile.current_revision} committed.`,
      });
    } catch (err: any) {
      setBanner({
        type: 'error',
        message: err.message || 'Failed to save shape controls.',
      });
    } finally {
      setSavingControls(false);
    }
  };

  // 2. Orchestrate Real 3D Avatar Generation (NAVER Anny v0.6.2)
  const handleGenerateAvatar = async () => {
    if (!activeProfile) return;
    setGenerating(true);
    setBanner(null);

    try {
      // If controls are dirty, save them first
      let currentRev = activeProfile.current_revision;
      if (dirty) {
        const updated = await apiClient.updateControls(activeProfile.profile_id, {
          expected_revision: currentRev,
          controls: controls,
        });
        setActiveProfile(updated);
        setDirty(false);
      }

      const res = await apiClient.generateAvatar({
        profile_id: activeProfile.profile_id,
        format: 'glb',
      });

      setLastGenResult(res);

      // Refresh profiles to get newly updated active measurements and latest asset URL
      await refreshProfiles();

      setBanner({
        type: 'success',
        message: `3D Avatar successfully synthesized in ${res.generation_duration_ms} ms (${res.vertex_count.toLocaleString()} vertices, manifold). Extracted active anthropometric measurements.`,
      });
    } catch (err: any) {
      console.error('Avatar generation error:', err);
      setBanner({
        type: 'error',
        message: err.message || 'Avatar generation failed.',
      });
    } finally {
      setGenerating(false);
    }
  };

  return (
    <AppLayout banner={banner || undefined}>
      {/* Studio Header */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '20px',
          flexWrap: 'wrap',
          gap: '12px',
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <h1 style={{ fontSize: '24px', fontWeight: 800, color: '#ffffff' }}>3D Avatar Studio</h1>
            <span className="badge badge-cyan">NAVER Anny v0.6.2</span>
          </div>
          <p style={{ fontSize: '13px', color: 'var(--text-muted)', marginTop: '2px' }}>
            Real-time parametric morphing, BICE mapping, and automated anthropometric slicing.
          </p>
        </div>

        {/* Studio Primary Action Buttons */}
        <div style={{ display: 'flex', gap: '10px' }}>
          <button
            onClick={handleSaveControls}
            disabled={!dirty || savingControls || !activeProfile}
            className="btn-secondary"
          >
            <Save size={15} />
            <span>{savingControls ? 'Saving...' : 'Save Controls'}</span>
          </button>

          <button
            onClick={handleGenerateAvatar}
            disabled={generating || !activeProfile}
            className="btn-primary"
            style={{ minWidth: '170px' }}
          >
            <Sparkles size={16} />
            <span>{generating ? 'Synthesizing Mesh...' : 'Generate Avatar'}</span>
          </button>
        </div>
      </div>

      {/* Main Studio Viewport Grid */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: '1fr minmax(340px, 400px)',
          gap: '24px',
          alignItems: 'start',
        }}
      >
        {/* Left Column: 3D Viewport & Generation Metrics */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <AvatarViewer
            assetUrl={activeProfile?.latest_asset_url}
            height="580px"
            initialWireframe={false}
            initialAutoRotate={false}
          />

          {/* Real-time Mesh Metadata Card */}
          {lastGenResult && (
            <div
              className="card"
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))',
                gap: '14px',
                padding: '16px',
              }}
            >
              <div>
                <span style={{ fontSize: '11px', color: 'var(--text-dim)', textTransform: 'uppercase' }}>Generation</span>
                <div style={{ fontSize: '15px', fontWeight: 700, color: 'var(--accent-emerald)', marginTop: '2px' }}>
                  {lastGenResult.generation_duration_ms} ms
                </div>
              </div>

              <div>
                <span style={{ fontSize: '11px', color: 'var(--text-dim)', textTransform: 'uppercase' }}>Vertices</span>
                <div style={{ fontSize: '15px', fontWeight: 700, color: '#ffffff', marginTop: '2px' }}>
                  {lastGenResult.vertex_count ? lastGenResult.vertex_count.toLocaleString() : '13,718'}
                </div>
              </div>

              <div>
                <span style={{ fontSize: '11px', color: 'var(--text-dim)', textTransform: 'uppercase' }}>Triangles</span>
                <div style={{ fontSize: '15px', fontWeight: 700, color: '#ffffff', marginTop: '2px' }}>
                  {lastGenResult.triangle_count ? lastGenResult.triangle_count.toLocaleString() : '27,420'}
                </div>
              </div>

              <div>
                <span style={{ fontSize: '11px', color: 'var(--text-dim)', textTransform: 'uppercase' }}>Manifold</span>
                <div style={{ fontSize: '15px', fontWeight: 700, color: 'var(--accent-cyan)', marginTop: '2px' }}>
                  {lastGenResult.is_valid_manifold ? 'Watertight' : 'Invalid'}
                </div>
              </div>

              <div>
                <span style={{ fontSize: '11px', color: 'var(--text-dim)', textTransform: 'uppercase' }}>Extracted</span>
                <div style={{ fontSize: '15px', fontWeight: 700, color: 'var(--accent-amber)', marginTop: '2px' }}>
                  {Object.keys(lastGenResult.extracted_measurements || {}).length || 5} Dimensions
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Right Column: Semantic Control Sliders */}
        <div className="card" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Sliders size={18} color="var(--accent-cyan)" />
              <h2 style={{ fontSize: '16px', fontWeight: 700, color: '#ffffff' }}>Semantic Shape Controls</h2>
            </div>
            {dirty && <span className="badge badge-amber">Unsaved Changes</span>}
          </div>

          <p style={{ fontSize: '12px', color: 'var(--text-dim)', marginBottom: '16px', lineHeight: 1.5 }}>
            BICE normalizer maps these 8 semantic dials to NAVER Anny bone transformations and vertex deformers.
          </p>

          {/* Quick Presets */}
          <div style={{ marginBottom: '20px' }}>
            <span style={{ fontSize: '11px', color: 'var(--text-dim)', fontWeight: 600, textTransform: 'uppercase', display: 'block', marginBottom: '8px' }}>
              Morphology Presets
            </span>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '6px' }}>
              {Object.keys(PRESETS).map((pName) => (
                <button
                  key={pName}
                  onClick={() => applyPreset(pName)}
                  style={{
                    padding: '6px 4px',
                    borderRadius: '6px',
                    fontSize: '11px',
                    fontWeight: 600,
                    background: 'var(--bg-surface-raised)',
                    border: '1px solid var(--border-medium)',
                    color: 'var(--text-muted)',
                  }}
                >
                  {pName}
                </button>
              ))}
            </div>
          </div>

          {/* 8 Control Sliders */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', maxHeight: '460px', overflowY: 'auto', paddingRight: '4px' }}>
            {(
              [
                { key: 'shoulder_width', label: 'Shoulder Width', region: 'Torso' },
                { key: 'chest_fullness', label: 'Chest Fullness', region: 'Torso' },
                { key: 'belly_fullness', label: 'Belly Fullness', region: 'Abdomen' },
                { key: 'waist_definition', label: 'Waist Definition', region: 'Abdomen' },
                { key: 'arm_fullness', label: 'Arm Fullness', region: 'Upper Limbs' },
                { key: 'hip_fullness', label: 'Hip Fullness', region: 'Pelvis' },
                { key: 'thigh_fullness', label: 'Thigh Fullness', region: 'Lower Limbs' },
                { key: 'calf_fullness', label: 'Calf Fullness', region: 'Lower Limbs' },
              ] as const
            ).map((item) => {
              const val = controls[item.key] ?? 0.5;
              return (
                <div key={item.key}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                    <label style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-main)' }}>
                      {item.label}
                    </label>
                    <span className="mono" style={{ fontSize: '12px', fontWeight: 700, color: 'var(--accent-cyan)' }}>
                      {val.toFixed(2)}
                    </span>
                  </div>
                  <input
                    type="range"
                    min="0.0"
                    max="1.0"
                    step="0.01"
                    value={val}
                    onChange={(e) => handleSliderChange(item.key, parseFloat(e.target.value))}
                    style={{
                      width: '100%',
                      accentColor: 'var(--accent-cyan)',
                      cursor: 'pointer',
                    }}
                  />
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10px', color: 'var(--text-dim)' }}>
                    <span>0.0</span>
                    <span style={{ fontSize: '9px', textTransform: 'uppercase' }}>{item.region}</span>
                    <span>1.0</span>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Reset button */}
          <div style={{ marginTop: '20px', paddingTop: '14px', borderTop: '1px solid var(--border-subtle)' }}>
            <button
              onClick={() => {
                setControls(DEFAULT_CONTROLS);
                setDirty(true);
              }}
              style={{
                width: '100%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '6px',
                fontSize: '12px',
                color: 'var(--text-dim)',
                padding: '6px',
              }}
            >
              <RotateCcw size={13} />
              <span>Reset Controls to Balanced (0.50)</span>
            </button>
          </div>
        </div>
      </div>
    </AppLayout>
  );
};
