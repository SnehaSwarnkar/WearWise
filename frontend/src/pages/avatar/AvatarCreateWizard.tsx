import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { ChevronDown, ChevronUp, Sparkles } from 'lucide-react';
import Header from '../Header';
import { apiClient } from '../../api/client';
import { BodyProfile, BodyShapeControls } from '../../types/api';
import { ConsumerAvatarViewport } from '../../components/avatar/ConsumerAvatarViewport';

type PresentationGender = 'masculine' | 'feminine' | 'neutral';

interface ShapePreset {
  id: string;
  label: string;
  desc: string;
  controls: BodyShapeControls;
}

const MASCULINE_SHAPES: ShapePreset[] = [
  {
    id: 'Rectangle',
    label: 'Rectangle',
    desc: 'Balanced shoulder, waist, and hip widths',
    controls: { shoulder_width: 0.50, chest_fullness: 0.50, belly_fullness: 0.45, waist_definition: 0.45, arm_fullness: 0.50, hip_fullness: 0.50, thigh_fullness: 0.50, calf_fullness: 0.50 },
  },
  {
    id: 'Inverted Triangle',
    label: 'Inverted Triangle',
    desc: 'Broader shoulders and chest tapering cleanly to the waist',
    controls: { shoulder_width: 0.78, chest_fullness: 0.72, belly_fullness: 0.35, waist_definition: 0.72, arm_fullness: 0.65, hip_fullness: 0.42, thigh_fullness: 0.52, calf_fullness: 0.50 },
  },
  {
    id: 'Trapezoid',
    label: 'Trapezoid',
    desc: 'Structured upper frame with proportional athletic taper',
    controls: { shoulder_width: 0.66, chest_fullness: 0.64, belly_fullness: 0.42, waist_definition: 0.62, arm_fullness: 0.60, hip_fullness: 0.48, thigh_fullness: 0.54, calf_fullness: 0.52 },
  },
  {
    id: 'Triangle',
    label: 'Triangle',
    desc: 'Softer shoulders with fuller midsection and lower frame',
    controls: { shoulder_width: 0.38, chest_fullness: 0.48, belly_fullness: 0.68, waist_definition: 0.32, arm_fullness: 0.50, hip_fullness: 0.64, thigh_fullness: 0.60, calf_fullness: 0.55 },
  },
  {
    id: 'Oval',
    label: 'Oval',
    desc: 'Fuller chest and midsection proportions throughout',
    controls: { shoulder_width: 0.52, chest_fullness: 0.72, belly_fullness: 0.80, waist_definition: 0.22, arm_fullness: 0.68, hip_fullness: 0.66, thigh_fullness: 0.64, calf_fullness: 0.58 },
  },
];

const FEMININE_SHAPES: ShapePreset[] = [
  {
    id: 'Hourglass',
    label: 'Hourglass',
    desc: 'Balanced bust and hips with a clearly defined waist',
    controls: { shoulder_width: 0.52, chest_fullness: 0.68, belly_fullness: 0.35, waist_definition: 0.80, arm_fullness: 0.48, hip_fullness: 0.70, thigh_fullness: 0.56, calf_fullness: 0.50 },
  },
  {
    id: 'Pear',
    label: 'Pear',
    desc: 'Narrower shoulders with fuller hips and thighs',
    controls: { shoulder_width: 0.38, chest_fullness: 0.44, belly_fullness: 0.42, waist_definition: 0.66, arm_fullness: 0.44, hip_fullness: 0.80, thigh_fullness: 0.72, calf_fullness: 0.56 },
  },
  {
    id: 'Apple',
    label: 'Apple',
    desc: 'Fuller upper torso and midsection with slimmer legs',
    controls: { shoulder_width: 0.56, chest_fullness: 0.72, belly_fullness: 0.74, waist_definition: 0.28, arm_fullness: 0.58, hip_fullness: 0.54, thigh_fullness: 0.48, calf_fullness: 0.46 },
  },
  {
    id: 'Rectangle',
    label: 'Rectangle',
    desc: 'Even alignment from shoulders through waist and hips',
    controls: { shoulder_width: 0.50, chest_fullness: 0.48, belly_fullness: 0.45, waist_definition: 0.42, arm_fullness: 0.48, hip_fullness: 0.50, thigh_fullness: 0.48, calf_fullness: 0.48 },
  },
  {
    id: 'Inverted Triangle',
    label: 'Inverted Triangle',
    desc: 'Broader shoulder line paired with trimmer hips',
    controls: { shoulder_width: 0.72, chest_fullness: 0.60, belly_fullness: 0.38, waist_definition: 0.60, arm_fullness: 0.54, hip_fullness: 0.40, thigh_fullness: 0.44, calf_fullness: 0.46 },
  },
  {
    id: 'Oval',
    label: 'Oval',
    desc: 'Softly rounded bust, waist, and hip curve throughout',
    controls: { shoulder_width: 0.54, chest_fullness: 0.74, belly_fullness: 0.78, waist_definition: 0.24, arm_fullness: 0.66, hip_fullness: 0.74, thigh_fullness: 0.66, calf_fullness: 0.58 },
  },
];

const SLIDER_GROUPS: {
  id: string;
  title: string;
  items: { key: keyof BodyShapeControls; label: string; minLabel: string; maxLabel: string }[];
}[] = [
  {
    id: 'upper',
    title: 'Upper Body (Shoulders, Chest & Arms)',
    items: [
      { key: 'shoulder_width', label: 'Shoulder Width', minLabel: 'Narrower', maxLabel: 'Broader' },
      { key: 'chest_fullness', label: 'Chest / Bust Fullness', minLabel: 'Slimmer', maxLabel: 'Fuller' },
      { key: 'arm_fullness', label: 'Upper Arm Build', minLabel: 'Slender', maxLabel: 'Full' },
    ],
  },
  {
    id: 'torso',
    title: 'Midsection (Waist & Belly)',
    items: [
      { key: 'waist_definition', label: 'Waist Taper', minLabel: 'Straighter', maxLabel: 'More Defined' },
      { key: 'belly_fullness', label: 'Abdomen Profile', minLabel: 'Flatter', maxLabel: 'Fuller' },
    ],
  },
  {
    id: 'lower',
    title: 'Lower Body (Hips, Thighs & Calves)',
    items: [
      { key: 'hip_fullness', label: 'Hip Fullness', minLabel: 'Narrower', maxLabel: 'Fuller' },
      { key: 'thigh_fullness', label: 'Thigh Build', minLabel: 'Slender', maxLabel: 'Full' },
      { key: 'calf_fullness', label: 'Calf Shape', minLabel: 'Slender', maxLabel: 'Full' },
    ],
  },
];

export default function AvatarCreateWizard() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const isEditMode = searchParams.get('edit') === '1';

  const [step, setStep] = useState<1 | 2 | 3 | 4>(1);
  const [existingProfile, setExistingProfile] = useState<BodyProfile | null>(null);
  const [loadingInit, setLoadingInit] = useState(true);

  // Step 1 fields
  const [avatarName, setAvatarName] = useState('My Everyday Avatar');
  const [gender, setGender] = useState<PresentationGender>('masculine');
  const [heightCm, setHeightCm] = useState<number>(174);
  const [bodyShape, setBodyShape] = useState<string>('Rectangle');
  const [ageRange, setAgeRange] = useState<string>('');
  const [weightKg, setWeightKg] = useState<string>('');

  // Step 2/3 state
  const [controls, setControls] = useState<BodyShapeControls>(MASCULINE_SHAPES[0].controls);
  const [controlsDirty, setControlsDirty] = useState<boolean>(false);
  const [assetUrl, setAssetUrl] = useState<string | null>(null);
  const [openGroups, setOpenGroups] = useState<Record<string, boolean>>({
    upper: true,
    torso: false,
    lower: false,
  });

  const [busyMsg, setBusyMsg] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const shapeOptions = useMemo(
    () => (gender === 'feminine' ? FEMININE_SHAPES : MASCULINE_SHAPES),
    [gender]
  );

  useEffect(() => {
    let alive = true;
    apiClient
      .listProfiles()
      .then((list) => {
        if (!alive) return;
        const p = Array.isArray(list) && list.length > 0 ? list[0] : null;
        if (p) {
          setExistingProfile(p);
          setAvatarName(p.avatar_name || 'My Everyday Avatar');
          setGender(p.presentation_gender || 'masculine');
          setHeightCm(Math.round(p.stature_cm || 174));
          setBodyShape(p.body_shape || (p.presentation_gender === 'feminine' ? 'Hourglass' : 'Rectangle'));
          setAgeRange(p.age_range || '');
          setWeightKg(p.reported_weight_kg ? String(p.reported_weight_kg) : '');
          if (p.shape_controls) setControls(p.shape_controls);
          if (p.latest_asset_url) setAssetUrl(p.latest_asset_url);
          if (isEditMode && p.latest_asset_url) {
            setStep(3);
          }
        }
        setLoadingInit(false);
      })
      .catch(() => setLoadingInit(false));
    return () => {
      alive = false;
    };
  }, [isEditMode]);

  const handleGenderChange = (nextGender: PresentationGender) => {
    setGender(nextGender);
    const list = nextGender === 'feminine' ? FEMININE_SHAPES : MASCULINE_SHAPES;
    setBodyShape(list[0].id);
    setControls(list[0].controls);
  };

  const handleShapeSelect = (preset: ShapePreset) => {
    setBodyShape(preset.id);
    setControls({ ...preset.controls });
  };

  const generateForProfile = async (profileId: string): Promise<string | null> => {
    const gen = await apiClient.generateAvatar({ profile_id: profileId, format: 'glb', rigged: true });
    const url = gen.asset_url ?? null;
    setAssetUrl(url);
    setControlsDirty(false);
    return url;
  };

  const handleGenerateInitial = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setBusyMsg('Building your initial 3D avatar…');
    try {
      const parsedWeight = weightKg ? Number(weightKg) : null;
      let savedProfile: BodyProfile;
      if (existingProfile) {
        const patched = await apiClient.updateProfile(existingProfile.profile_id, {
          avatar_name: avatarName,
          presentation_gender: gender,
          stature_cm: heightCm,
          body_shape: bodyShape,
          age_range: ageRange || null,
          reported_weight_kg: parsedWeight,
        });
        const ctrlUpdate = await apiClient.updateControls(existingProfile.profile_id, {
          expected_revision: patched.current_revision ?? existingProfile.current_revision,
          controls,
        });
        savedProfile = {
          ...patched,
          current_revision: ctrlUpdate.current_revision ?? patched.current_revision,
          shape_controls: ctrlUpdate.shape_controls ?? controls,
        };
      } else {
        savedProfile = await apiClient.createProfile({
          avatar_name: avatarName,
          presentation_gender: gender,
          stature_cm: heightCm,
          body_shape: bodyShape,
          age_range: ageRange || null,
          reported_weight_kg: parsedWeight,
          initial_controls: controls,
        });
      }
      setExistingProfile(savedProfile);
      await generateForProfile(savedProfile.profile_id);
      const refreshed = await apiClient.getProfile(savedProfile.profile_id);
      setExistingProfile(refreshed);
      setStep(2);
    } catch (err: any) {
      setError(err.message || 'We could not create your avatar right now. Please try again.');
    } finally {
      setBusyMsg(null);
    }
  };

  const handleApplySliders = async () => {
    if (!existingProfile) return;
    setError(null);
    setBusyMsg('Updating your 3D avatar proportions…');
    try {
      const updated = await apiClient.updateControls(existingProfile.profile_id, {
        expected_revision: existingProfile.current_revision,
        controls,
      });
      setExistingProfile((prev) => (prev ? { ...prev, ...updated } : updated));
      await generateForProfile(updated.profile_id);
      const refreshed = await apiClient.getProfile(updated.profile_id);
      setExistingProfile(refreshed);
    } catch (err: any) {
      setError(err.message || 'Unable to update your proportions right now.');
    } finally {
      setBusyMsg(null);
    }
  };

  const handleSaveAndFinish = async () => {
    if (!existingProfile) return;
    if (!controlsDirty && assetUrl) {
      navigate('/avatar/dashboard');
      return;
    }
    setError(null);
    setBusyMsg('Saving your primary avatar…');
    try {
      const updated = await apiClient.updateControls(existingProfile.profile_id, {
        expected_revision: existingProfile.current_revision,
        controls,
      });
      setExistingProfile((prev) => (prev ? { ...prev, ...updated } : updated));
      await generateForProfile(updated.profile_id);
      const refreshed = await apiClient.getProfile(updated.profile_id);
      setExistingProfile(refreshed);
      navigate('/avatar/dashboard');
    } catch (err: any) {
      setError(err.message || 'Could not save your avatar changes.');
    } finally {
      setBusyMsg(null);
    }
  };

  const feetInches = useMemo(() => {
    const totalIn = Math.round(heightCm / 2.54);
    return `${Math.floor(totalIn / 12)} ft ${totalIn % 12} in`;
  }, [heightCm]);

  return (
    <div style={{ minHeight: '100vh', background: '#fff8f1', color: '#151515' }}>
      <Header />

      <div style={{ maxWidth: '1220px', margin: '0 auto', padding: '28px 24px 64px' }}>
        {/* Progress Header */}
        <div style={{ marginBottom: '24px' }}>
          <div style={{ fontSize: '11px', fontWeight: 900, letterSpacing: '0.08em', color: '#ff3d9a' }}>
            AVATAR SETUP · STEP {step} OF 4
          </div>
          <h1 style={{ fontFamily: '"Archivo Black", sans-serif', fontSize: 'clamp(28px, 3.6vw, 40px)', margin: '4px 0 12px', letterSpacing: '-1px' }}>
            {step === 1 && 'BASIC BODY INFORMATION'}
            {step === 2 && 'YOUR INITIAL 3D AVATAR'}
            {step === 3 && 'CUSTOMIZE YOUR PROPORTIONS'}
            {step === 4 && 'REVIEW & SAVE AVATAR'}
          </h1>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '8px' }}>
            {[
              { n: 1, label: '1. Basic Details' },
              { n: 2, label: '2. Generate Model' },
              { n: 3, label: '3. Fine-Tune Shape' },
              { n: 4, label: '4. Save Profile' },
            ].map((s) => (
              <button
                key={s.n}
                type="button"
                disabled={s.n > 1 && !existingProfile}
                onClick={() => {
                  if (s.n === 1 || existingProfile) setStep(s.n as 1 | 2 | 3 | 4);
                }}
                style={{
                  padding: '8px 10px',
                  border: '2px solid #151515',
                  background: step === s.n ? '#d8ff3f' : step > s.n ? '#151515' : '#ffffff',
                  color: step === s.n ? '#151515' : step > s.n ? '#fff8f1' : '#6b7280',
                  fontWeight: 900,
                  fontSize: '12px',
                  cursor: s.n === 1 || existingProfile ? 'pointer' : 'not-allowed',
                }}
              >
                {s.label}
              </button>
            ))}
          </div>
        </div>

        {error && (
          <div style={{ marginBottom: '16px', padding: '12px 14px', background: '#fee2e2', border: '2px solid #991b1b', color: '#991b1b', fontWeight: 700, fontSize: '13px' }}>
            {error}
          </div>
        )}

        {loadingInit ? (
          <p>Loading setup…</p>
        ) : step === 1 ? (
          /* STEP 1: BASIC INFO ONLY (No overwhelming slider wall!) */
          <form
            onSubmit={handleGenerateInitial}
            data-testid="avatar-step1-form"
            style={{
              background: '#ffffff',
              border: '3px solid #151515',
              boxShadow: '8px 8px 0 #151515',
              padding: '28px',
              display: 'flex',
              flexDirection: 'column',
              gap: '20px',
              maxWidth: '780px',
            }}
          >
            <p style={{ margin: 0, fontSize: '14px', color: '#454854', lineHeight: 1.6 }}>
              We use your height and a starting body shape preset to build a realistic 3D model for garment sizing and try-on. You can adjust every proportion with sliders on the next step.
            </p>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px' }}>
              <label className="auth-field">
                <span>AVATAR NAME</span>
                <input
                  type="text"
                  required
                  value={avatarName}
                  onChange={(e) => setAvatarName(e.target.value)}
                  placeholder="My Everyday Avatar"
                />
              </label>

              <label className="auth-field">
                <span>HEIGHT ({heightCm} cm · {feetInches})</span>
                <input
                  type="number"
                  min={140}
                  max={215}
                  required
                  value={heightCm}
                  onChange={(e) => setHeightCm(Number(e.target.value))}
                />
              </label>
            </div>

            <div>
              <div style={{ fontSize: '12px', fontWeight: 900, marginBottom: '8px' }}>BASE BODY MODEL</div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '10px' }}>
                {[
                  { id: 'masculine', label: 'Masculine' },
                  { id: 'feminine', label: 'Feminine' },
                  { id: 'neutral', label: 'Neutral' },
                ].map((opt) => (
                  <button
                    key={opt.id}
                    type="button"
                    data-testid={`gender-opt-${opt.id}`}
                    onClick={() => handleGenderChange(opt.id as PresentationGender)}
                    style={{
                      padding: '12px',
                      border: '2px solid #151515',
                      background: gender === opt.id ? '#151515' : '#ffffff',
                      color: gender === opt.id ? '#d8ff3f' : '#151515',
                      fontWeight: 900,
                      fontSize: '13px',
                      cursor: 'pointer',
                    }}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <div style={{ fontSize: '12px', fontWeight: 900, marginBottom: '8px' }}>
                STARTING BODY SHAPE PRESET (ADJUSTABLE NEXT STEP)
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '10px' }}>
                {shapeOptions.map((sp) => {
                  const selected = bodyShape === sp.id;
                  return (
                    <button
                      key={sp.id}
                      type="button"
                      data-testid={`shape-preset-${sp.id}`}
                      onClick={() => handleShapeSelect(sp)}
                      style={{
                        textAlign: 'left',
                        padding: '12px',
                        border: '2px solid #151515',
                        background: selected ? '#d8ff3f' : '#fffdf9',
                        color: '#151515',
                        cursor: 'pointer',
                      }}
                    >
                      <strong style={{ display: 'block', fontSize: '14px' }}>{sp.label}</strong>
                      <span style={{ display: 'block', fontSize: '11px', color: '#454854', marginTop: '4px', lineHeight: 1.4 }}>
                        {sp.desc}
                      </span>
                    </button>
                  );
                })}
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px' }}>
              <label className="auth-field">
                <span>AGE RANGE (OPTIONAL)</span>
                <select
                  value={ageRange}
                  onChange={(e) => setAgeRange(e.target.value)}
                  style={{ padding: '10px', border: '2px solid #151515', background: '#ffffff' }}
                >
                  <option value="">Prefer not to specify</option>
                  <option value="18-24">18 – 24</option>
                  <option value="25-39">25 – 39</option>
                  <option value="40-54">40 – 54</option>
                  <option value="55+">55+</option>
                </select>
              </label>

              <label className="auth-field">
                <span>WEIGHT IN KG (OPTIONAL)</span>
                <input
                  type="number"
                  min={35}
                  max={220}
                  value={weightKg}
                  onChange={(e) => setWeightKg(e.target.value)}
                  placeholder="Optional"
                />
              </label>
            </div>

            <div>
              <button
                type="submit"
                disabled={Boolean(busyMsg)}
                data-testid="generate-initial-avatar-btn"
                className="main-btn"
              >
                {busyMsg || 'Generate Initial Body Model →'}
              </button>
            </div>
          </form>
        ) : (
          /* STEPS 2, 3, 4 — Live Flicker-Free 3D Viewport + Contextual Controls */
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '28px', alignItems: 'start' }}>
            <ConsumerAvatarViewport assetUrl={assetUrl} height={520} autoRotate={step === 2 || step === 4} />

            <div
              style={{
                background: '#ffffff',
                border: '3px solid #151515',
                boxShadow: '8px 8px 0 #151515',
                padding: '24px',
                display: 'flex',
                flexDirection: 'column',
                gap: '16px',
              }}
            >
              {step === 2 && (
                <>
                  <h2 style={{ fontSize: '20px', fontWeight: 900, margin: 0 }}>
                    Here is your {bodyShape} starting model
                  </h2>
                  <p style={{ margin: 0, fontSize: '14px', color: '#454854', lineHeight: 1.6 }}>
                    Rotate the 3D preview to check your overall silhouette at <strong>{heightCm} cm</strong>. You can adjust shoulders, chest, waist, belly, hips, and limbs on the next step.
                  </p>
                  <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
                    <button
                      type="button"
                      data-testid="goto-customize-btn"
                      onClick={() => setStep(3)}
                      className="main-btn"
                    >
                      Customize Proportions →
                    </button>
                    <button
                      type="button"
                      onClick={() => setStep(4)}
                      className="outline-btn"
                    >
                      Looks Great · Save Next
                    </button>
                  </div>
                </>
              )}

              {step === 3 && (
                <>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <h2 style={{ fontSize: '18px', fontWeight: 900, margin: 0 }}>Fine-Tune Body Proportions</h2>
                    <button
                      type="button"
                      onClick={() => {
                        const preset = shapeOptions.find((s) => s.id === bodyShape) || shapeOptions[0];
                        setControls({ ...preset.controls });
                      }}
                      style={{ border: '1.5px solid #151515', background: '#ffffff', padding: '5px 10px', fontSize: '11px', fontWeight: 800, cursor: 'pointer' }}
                    >
                      Reset to {bodyShape}
                    </button>
                  </div>

                  {SLIDER_GROUPS.map((grp) => {
                    const isOpen = openGroups[grp.id];
                    return (
                      <div key={grp.id} style={{ border: '2px solid #151515' }}>
                        <button
                          type="button"
                          onClick={() => setOpenGroups((prev) => ({ ...prev, [grp.id]: !prev[grp.id] }))}
                          style={{
                            width: '100%',
                            padding: '10px 14px',
                            background: isOpen ? '#151515' : '#fff8f1',
                            color: isOpen ? '#d8ff3f' : '#151515',
                            border: 'none',
                            display: 'flex',
                            justifyContent: 'space-between',
                            alignItems: 'center',
                            fontWeight: 900,
                            fontSize: '13px',
                            cursor: 'pointer',
                          }}
                        >
                          <span>{grp.title}</span>
                          {isOpen ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                        </button>

                        {isOpen && (
                          <div style={{ padding: '14px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
                            {grp.items.map((sl) => (
                              <div key={sl.key}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', fontWeight: 800, marginBottom: '4px' }}>
                                  <span>{sl.label}</span>
                                  <span>{Math.round(controls[sl.key] * 100)}%</span>
                                </div>
                                <input
                                  type="range"
                                  min={0}
                                  max={1}
                                  step={0.02}
                                  value={controls[sl.key]}
                                  onChange={(e) => {
                                    setControlsDirty(true);
                                    setControls((prev) => ({ ...prev, [sl.key]: parseFloat(e.target.value) }));
                                  }}
                                  style={{ width: '100%', accentColor: '#ff3d9a' }}
                                />
                                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10px', color: '#6b7280' }}>
                                  <span>{sl.minLabel}</span>
                                  <span>{sl.maxLabel}</span>
                                </div>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    );
                  })}

                  <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap', marginTop: '4px' }}>
                    <button
                      type="button"
                      disabled={Boolean(busyMsg)}
                      data-testid="apply-proportions-btn"
                      onClick={handleApplySliders}
                      style={{
                        flex: 1,
                        padding: '12px 16px',
                        border: '2px solid #151515',
                        background: '#d8ff3f',
                        fontWeight: 900,
                        fontSize: '13px',
                        cursor: 'pointer',
                      }}
                    >
                      <Sparkles size={14} style={{ verticalAlign: 'middle', marginRight: '6px' }} />
                      {busyMsg || 'Update 3D Preview'}
                    </button>
                    <button
                      type="button"
                      disabled={Boolean(busyMsg)}
                      onClick={() => setStep(4)}
                      className="main-btn"
                    >
                      Continue to Save →
                    </button>
                  </div>
                </>
              )}

              {step === 4 && (
                <>
                  <h2 style={{ fontSize: '20px', fontWeight: 900, margin: 0 }}>Ready to Save Your Avatar</h2>
                  <div style={{ padding: '14px', background: '#fff8f1', border: '1.5px solid #151515', fontSize: '13px', lineHeight: 1.7 }}>
                    <div><strong>Avatar Name:</strong> {avatarName}</div>
                    <div><strong>Base Model:</strong> {gender === 'feminine' ? 'Feminine' : gender === 'masculine' ? 'Masculine' : 'Neutral'}</div>
                    <div><strong>Shape Preset:</strong> {bodyShape}</div>
                    <div><strong>Height:</strong> {heightCm} cm ({feetInches})</div>
                  </div>
                  <p style={{ margin: 0, fontSize: '13px', color: '#454854' }}>
                    Your single primary avatar is stored to your WearWise account and used automatically whenever you open Virtual Try-On.
                  </p>
                  <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
                    <button
                      type="button"
                      disabled={Boolean(busyMsg)}
                      data-testid="save-avatar-finish-btn"
                      onClick={handleSaveAndFinish}
                      className="main-btn"
                    >
                      {busyMsg || 'Save My Avatar ✓'}
                    </button>
                    <button
                      type="button"
                      disabled={Boolean(busyMsg)}
                      onClick={() => setStep(3)}
                      className="outline-btn"
                    >
                      Back to Proportions
                    </button>
                  </div>
                </>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
