import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Header from './Header';
import { AvatarViewer } from '../components/avatar/AvatarViewer';
import {
  fetchMerchantGarments,
  fetchGarmentDetails,
  createGarmentIdentity,
  uploadViewpointImage,
  savePatternSpec,
  saveMeasurements,
  saveFabricProps,
  trigger3DGeneration,
  publishGarment,
} from '../api/merchantGarments';
import './MerchantGarmentStudio.css';
import {
  CheckCircle2,
  AlertTriangle,
  Upload,
  ArrowRight,
  ArrowLeft,
  Layers,
  Scissors,
  Ruler,
  Cpu,
  Eye,
  Sparkles,
  Check,
} from 'lucide-react';

export default function MerchantGarmentStudio() {
  const navigate = useNavigate();

  const [activeStep, setActiveStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [successMessage, setSuccessMessage] = useState(null);
  const [errorMessage, setErrorMessage] = useState(null);

  // Active Garment State
  const [garmentId, setGarmentId] = useState('ww-seed-tsh-ww-crew-001');
  const [garmentData, setGarmentData] = useState(null);

  // Step 1: Product Identity
  const [identity, setIdentity] = useState({
    name: 'WearWise Signature Boxy Crew Tee',
    sku: 'TSH-WW-CREW-001',
    category: 'T-Shirt',
    description: 'Heavyweight drop-shoulder boxy tee with ribbed crewneck collar, white piping, and chest pocket.',
    color_variant: 'Coral Pink / White Trim',
    available_sizes: ['S', 'M', 'L'],
  });

  // Step 2: Viewpoint Images
  const [uploadedImages, setUploadedImages] = useState({
    front: null,
    back: null,
    left_side: null,
    right_side: null,
    close_up: null,
  });

  // Step 3: Pattern & Construction
  const [patternSpec, setPatternSpec] = useState({
    pattern_mode: 'parametric',
    construction_type: 'boxy_drop_shoulder',
    has_cad_data: true,
    provisional: false,
    assumptions_note: 'Calibrated against ISO 8559-2 dropped-shoulder block',
  });

  // Step 4: Finished Measurements (S, M, L)
  const [activeSizeTab, setActiveSizeTab] = useState('M');
  const [measurementsTable, setMeasurementsTable] = useState({
    S: { half_chest_width_cm: 50.0, back_length_cm: 64.0, shoulder_breadth_cm: 47.0, sleeve_length_cm: 15.0, collar_circumference_cm: 42.0, dimensional_ease_chest_cm: '+2.0 cm' },
    M: { half_chest_width_cm: 54.0, back_length_cm: 67.0, shoulder_breadth_cm: 50.0, sleeve_length_cm: 17.0, collar_circumference_cm: 44.0, dimensional_ease_chest_cm: '+4.5 cm (Recommended)' },
    L: { half_chest_width_cm: 58.0, back_length_cm: 70.0, shoulder_breadth_cm: 53.0, sleeve_length_cm: 19.0, collar_circumference_cm: 46.0, dimensional_ease_chest_cm: '+8.0 cm' },
  });

  // Step 5: Fabric Properties
  const [fabricProps, setFabricProps] = useState({
    name: 'Heavyweight Cotton Waffle Knit',
    composition: '100% Combed Organic Cotton',
    structure: 'Waffle / Honeycomb Knit',
    gsm: 240.0,
    thickness_mm: 1.15,
    warp_stretch_percent: 14.5,
    weft_stretch_percent: 28.0,
    elastic_recovery_percent: 88.0,
    bending_stiffness: 18.5,
    shear_stiffness: 22.0,
  });

  // Step 6: 3D Preview State
  const [previewSize, setPreviewSize] = useState('M');
  const [armAngle, setArmAngle] = useState(0);
  const [garmentStatus, setGarmentStatus] = useState('published');
  const [isGenerating, setIsGenerating] = useState(false);

  // Load initial garment data
  useEffect(() => {
    fetchMerchantGarments()
      .then((garments) => {
        if (garments && garments.length > 0) {
          const g = garments[0];
          setGarmentId(g.id);
          setGarmentData(g);
          setIdentity({
            name: g.name,
            sku: g.sku,
            category: g.category,
            description: g.description,
            color_variant: g.color_variant,
            available_sizes: g.available_sizes || ['S', 'M', 'L'],
          });
          if (g.images) setUploadedImages(g.images);
          if (g.pattern) setPatternSpec(g.pattern);
          if (g.measurements) setMeasurementsTable(g.measurements);
          if (g.fabric_properties) setFabricProps(g.fabric_properties);
          if (g.status) setGarmentStatus(g.status);
        }
      })
      .catch((err) => console.warn('Could not load merchant garments:', err));
  }, []);

  const showFeedback = (msg, isError = false) => {
    if (isError) {
      setErrorMessage(msg);
      setTimeout(() => setErrorMessage(null), 4000);
    } else {
      setSuccessMessage(msg);
      setTimeout(() => setSuccessMessage(null), 3000);
    }
  };

  // Step 1: Save Identity
  const handleSaveIdentity = async () => {
    setLoading(true);
    try {
      const resp = await createGarmentIdentity(identity);
      setGarmentId(resp.id);
      setGarmentData(resp);
      showFeedback('Step 1: Garment identity created successfully.');
      setActiveStep(2);
    } catch (err) {
      showFeedback(err.message, true);
    } finally {
      setLoading(false);
    }
  };

  // Step 2: Upload Viewpoint
  const handleFileUpload = async (viewpoint, file) => {
    if (!file) return;
    setLoading(true);
    try {
      const resp = await uploadViewpointImage(garmentId, viewpoint, file);
      setUploadedImages(resp.images);
      showFeedback(`Uploaded ${viewpoint} image successfully.`);
    } catch (err) {
      showFeedback(err.message, true);
    } finally {
      setLoading(false);
    }
  };

  // Step 3: Save Pattern Spec
  const handleSavePattern = async () => {
    setLoading(true);
    try {
      const resp = await savePatternSpec(garmentId, patternSpec);
      setPatternSpec(resp.pattern);
      showFeedback('Step 3: Pattern specification updated.');
      setActiveStep(4);
    } catch (err) {
      showFeedback(err.message, true);
    } finally {
      setLoading(false);
    }
  };

  // Step 4: Save Measurements
  const handleSaveMeasurements = async () => {
    setLoading(true);
    try {
      const current = measurementsTable[activeSizeTab];
      await saveMeasurements(garmentId, { size_label: activeSizeTab, ...current });
      showFeedback(`Step 4: Size ${activeSizeTab} measurements saved.`);
      setActiveStep(5);
    } catch (err) {
      showFeedback(err.message, true);
    } finally {
      setLoading(false);
    }
  };

  // Step 5: Save Fabric
  const handleSaveFabric = async () => {
    setLoading(true);
    try {
      const resp = await saveFabricProps(garmentId, fabricProps);
      setFabricProps(resp.fabric_properties);
      showFeedback('Step 5: Fabric mechanical properties registered.');
      setActiveStep(6);
    } catch (err) {
      showFeedback(err.message, true);
    } finally {
      setLoading(false);
    }
  };

  // Step 6: Generate 3D
  const handleGenerate3D = async () => {
    setIsGenerating(true);
    try {
      const resp = await trigger3DGeneration(garmentId);
      setGarmentStatus(resp.status);
      showFeedback('3D Garment Generated successfully! Ready for motion review.');
    } catch (err) {
      showFeedback(err.message, true);
    } finally {
      setIsGenerating(false);
    }
  };

  // Step 6: Publish
  const handlePublish = async () => {
    setLoading(true);
    try {
      const resp = await publishGarment(garmentId);
      setGarmentStatus(resp.status);
      showFeedback('✦ Garment published to active shopper catalog!');
    } catch (err) {
      showFeedback(err.message, true);
    } finally {
      setLoading(false);
    }
  };

  const stepsMeta = [
    { num: 1, label: 'Identity', sub: 'SKU & Category' },
    { num: 2, label: 'Images', sub: 'Multi-View Photos' },
    { num: 3, label: 'Pattern', sub: 'CAD & Panels' },
    { num: 4, label: 'Measurements', sub: 'Finished S/M/L' },
    { num: 5, label: 'Fabric', sub: 'Mechanical GSM' },
    { num: 6, label: '3D Preview', sub: 'Motion & Publish' },
  ];

  return (
    <div className="merchant-studio-page">
      <Header />

      <main className="merchant-studio-main">
        {/* Header Title */}
        <div className="merchant-studio-header">
          <div className="merchant-studio-pretitle">MERCHANT SUITE · DIGITAL GARMENT STUDIO</div>
          <h1 className="merchant-studio-title">Merchant Digital Garment Platform</h1>
          <p className="merchant-studio-desc">
            Transform physical fashion products into size-graded, physically responsive 3D assets conforming to the
            NAVER Anny anthropometric body engine.
          </p>
        </div>

        {/* Feedback alerts */}
        {successMessage && (
          <div style={{ background: '#ecfdf5', border: '2px solid #10b981', borderRadius: '10px', padding: '12px 18px', marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '10px', fontSize: '13px', fontWeight: 700, color: '#065f46' }}>
            <CheckCircle2 size={18} />
            <span>{successMessage}</span>
          </div>
        )}
        {errorMessage && (
          <div style={{ background: '#fff1f2', border: '2px solid #f43f5e', borderRadius: '10px', padding: '12px 18px', marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '10px', fontSize: '13px', fontWeight: 700, color: '#9f1239' }}>
            <AlertTriangle size={18} />
            <span>{errorMessage}</span>
          </div>
        )}

        {/* 6-Step Wizard Navigation */}
        <div className="merchant-steps-nav">
          {stepsMeta.map((s) => (
            <button
              key={s.num}
              type="button"
              className={`step-nav-pill ${activeStep === s.num ? 'active' : ''} ${activeStep > s.num ? 'completed' : ''}`}
              onClick={() => setActiveStep(s.num)}
            >
              <div className="step-num">{activeStep > s.num ? '✓' : s.num}</div>
              <div className="step-label-group">
                <span className="step-label-title">{s.label}</span>
                <span className="step-label-sub">{s.sub}</span>
              </div>
            </button>
          ))}
        </div>

        {/* ====================================================================
            STEP 1: PRODUCT IDENTITY
            ==================================================================== */}
        {activeStep === 1 && (
          <div className="merchant-card">
            <h2 className="merchant-card-title">Step 1 — Product Identity</h2>
            <p className="merchant-card-subtitle">
              Define product commercial metadata, SKU code, and target apparel category.
            </p>

            <div className="form-grid-2">
              <div className="form-group">
                <label className="form-label">Product Name</label>
                <input
                  type="text"
                  className="form-input"
                  value={identity.name}
                  onChange={(e) => setIdentity({ ...identity, name: e.target.value })}
                />
              </div>

              <div className="form-group">
                <label className="form-label">Product SKU (Unique)</label>
                <input
                  type="text"
                  className="form-input"
                  value={identity.sku}
                  onChange={(e) => setIdentity({ ...identity, sku: e.target.value })}
                />
              </div>
            </div>

            <div className="form-grid-2">
              <div className="form-group">
                <label className="form-label">Category</label>
                <select
                  className="form-select"
                  value={identity.category}
                  onChange={(e) => setIdentity({ ...identity, category: e.target.value })}
                >
                  <option value="T-Shirt">T-Shirt / Crewneck</option>
                  <option value="Hoodie">Hoodie / Sweatshirt</option>
                  <option value="Polo">Polo Shirt</option>
                  <option value="Dress">Dress</option>
                  <option value="Jacket">Jacket / Outerwear</option>
                </select>
              </div>

              <div className="form-group">
                <label className="form-label">Color Variant Description</label>
                <input
                  type="text"
                  className="form-input"
                  value={identity.color_variant}
                  onChange={(e) => setIdentity({ ...identity, color_variant: e.target.value })}
                />
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">Product Description</label>
              <textarea
                className="form-textarea"
                rows={3}
                value={identity.description}
                onChange={(e) => setIdentity({ ...identity, description: e.target.value })}
              />
            </div>

            <div className="actions-row">
              <span style={{ fontSize: '12px', color: '#666' }}>SKU Association: {identity.sku}</span>
              <button type="button" className="btn-primary-merchant" onClick={handleSaveIdentity} disabled={loading}>
                CONTINUE TO IMAGE UPLOAD <ArrowRight size={16} />
              </button>
            </div>
          </div>
        )}

        {/* ====================================================================
            STEP 2: GARMENT IMAGE UPLOAD
            ==================================================================== */}
        {activeStep === 2 && (
          <div className="merchant-card">
            <h2 className="merchant-card-title">Step 2 — Multi-View Garment Photography</h2>
            <p className="merchant-card-subtitle">
              Upload multi-angle reference photos for texture extraction and pattern reconstruction.
            </p>

            <div className="image-slots-grid">
              {[
                { key: 'front', label: 'Front View *' },
                { key: 'back', label: 'Back View' },
                { key: 'left_side', label: 'Left Side *' },
                { key: 'right_side', label: 'Right Side' },
                { key: 'close_up', label: 'Fabric Close-Up' },
              ].map((slot) => (
                <div
                  key={slot.key}
                  className={`upload-slot-card ${uploadedImages[slot.key] ? 'filled' : ''}`}
                  onClick={() => document.getElementById(`upload-${slot.key}`)?.click()}
                >
                  <input
                    id={`upload-${slot.key}`}
                    type="file"
                    accept="image/*"
                    style={{ display: 'none' }}
                    onChange={(e) => handleFileUpload(slot.key, e.target.files?.[0])}
                  />
                  {uploadedImages[slot.key] ? (
                    <>
                      <img src={uploadedImages[slot.key]} alt={slot.label} className="slot-preview-img" />
                      <span className="slot-view-title">{slot.label} (Uploaded)</span>
                    </>
                  ) : (
                    <>
                      <Upload size={24} color="#888" />
                      <span className="slot-view-title">{slot.label}</span>
                      <span style={{ fontSize: '10px', color: '#999' }}>Click to upload</span>
                    </>
                  )}
                </div>
              ))}
            </div>

            <div className="actions-row">
              <button type="button" className="btn-secondary-merchant" onClick={() => setActiveStep(1)}>
                <ArrowLeft size={16} /> BACK
              </button>
              <button type="button" className="btn-primary-merchant" onClick={() => setActiveStep(3)}>
                CONTINUE TO PATTERN INPUT <ArrowRight size={16} />
              </button>
            </div>
          </div>
        )}

        {/* ====================================================================
            STEP 3: PATTERN AND CONSTRUCTION INPUT
            ==================================================================== */}
        {activeStep === 3 && (
          <div className="merchant-card">
            <h2 className="merchant-card-title">Step 3 — Pattern & Construction Input</h2>
            <p className="merchant-card-subtitle">
              Specify garment construction blocks or upload production CAD DXF/SVG pattern files.
            </p>

            <div className="form-grid-2">
              <div className="form-group">
                <label className="form-label">Pattern Input Method</label>
                <select
                  className="form-select"
                  value={patternSpec.pattern_mode}
                  onChange={(e) => setPatternSpec({ ...patternSpec, pattern_mode: e.target.value })}
                >
                  <option value="parametric">Guided Parametric Builder</option>
                  <option value="cad_dxf">Production CAD DXF File</option>
                  <option value="svg">2D Vector SVG Pattern</option>
                </select>
              </div>

              <div className="form-group">
                <label className="form-label">Construction Silhouette</label>
                <select
                  className="form-select"
                  value={patternSpec.construction_type}
                  onChange={(e) => setPatternSpec({ ...patternSpec, construction_type: e.target.value })}
                >
                  <option value="boxy_drop_shoulder">Boxy Dropped Shoulder (Reference Approved)</option>
                  <option value="set_in_sleeve">Classic Set-In Sleeve</option>
                  <option value="raglan">Athletic Raglan Sleeve</option>
                  <option value="oversized_kimono">Oversized Kimono Cut</option>
                </select>
              </div>
            </div>

            {/* Pattern status badge */}
            <div style={{ background: '#f8fafc', border: '1.5px solid var(--black)', borderRadius: '10px', padding: '16px', margin: '16px 0' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                <strong style={{ fontSize: '13px' }}>Pattern Verification Status</strong>
                <span
                  style={{
                    padding: '4px 10px',
                    borderRadius: '6px',
                    fontFamily: 'Archivo Black',
                    fontSize: '11px',
                    background: patternSpec.provisional ? '#fef3c7' : '#dcfce7',
                    color: patternSpec.provisional ? '#92400e' : '#166534',
                  }}
                >
                  {patternSpec.provisional ? 'PROVISIONAL PATTERN' : 'CAD PRODUCTION VERIFIED'}
                </span>
              </div>
              <p style={{ fontSize: '12px', color: '#555', margin: 0 }}>
                {patternSpec.assumptions_note}
              </p>
            </div>

            <div className="actions-row">
              <button type="button" className="btn-secondary-merchant" onClick={() => setActiveStep(2)}>
                <ArrowLeft size={16} /> BACK
              </button>
              <button type="button" className="btn-primary-merchant" onClick={handleSavePattern} disabled={loading}>
                CONTINUE TO MEASUREMENTS <ArrowRight size={16} />
              </button>
            </div>
          </div>
        )}

        {/* ====================================================================
            STEP 4: FINISHED MEASUREMENTS
            ==================================================================== */}
        {activeStep === 4 && (
          <div className="merchant-card">
            <h2 className="merchant-card-title">Step 4 — Finished Garment Measurements Table</h2>
            <p className="merchant-card-subtitle">
              Calibrate size-graded dimensions under ISO 8559-2 / BS 4952 standards for accurate Honest Fit calculation.
            </p>

            {/* Size tabs */}
            <div style={{ display: 'flex', gap: '8px', marginBottom: '16px' }}>
              {['S', 'M', 'L'].map((sz) => (
                <button
                  key={sz}
                  type="button"
                  style={{
                    padding: '8px 16px',
                    borderRadius: '6px',
                    border: '2px solid var(--black)',
                    fontFamily: 'Archivo Black',
                    fontSize: '12px',
                    background: activeSizeTab === sz ? 'var(--pink)' : '#ffffff',
                    color: activeSizeTab === sz ? '#ffffff' : 'var(--black)',
                    cursor: 'pointer',
                  }}
                  onClick={() => setActiveSizeTab(sz)}
                >
                  SIZE {sz} {sz === 'M' ? '(Canonical Base)' : ''}
                </button>
              ))}
            </div>

            <table className="measurements-table">
              <thead>
                <tr>
                  <th>Dimension Code</th>
                  <th>Description</th>
                  <th>Value (cm)</th>
                  <th>Dimensional Ease vs Baseline</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td><code>HALF_CHEST</code></td>
                  <td>Half-Chest Width (Armpit to Armpit)</td>
                  <td><strong>{measurementsTable[activeSizeTab]?.half_chest_width_cm} cm</strong></td>
                  <td><span style={{ color: '#16a34a', fontWeight: 700 }}>{measurementsTable[activeSizeTab]?.dimensional_ease_chest_cm}</span></td>
                </tr>
                <tr>
                  <td><code>BACK_LENGTH</code></td>
                  <td>Back Length from High Point Shoulder to Hem</td>
                  <td><strong>{measurementsTable[activeSizeTab]?.back_length_cm} cm</strong></td>
                  <td>Calibrated Boxy Drape</td>
                </tr>
                <tr>
                  <td><code>SHOULDER_BREADTH</code></td>
                  <td>Across Shoulder Seam to Seam</td>
                  <td><strong>{measurementsTable[activeSizeTab]?.shoulder_breadth_cm} cm</strong></td>
                  <td>Dropped Shoulder Ease</td>
                </tr>
                <tr>
                  <td><code>SLEEVE_LENGTH</code></td>
                  <td>Dropped Shoulder Sleeve Length</td>
                  <td><strong>{measurementsTable[activeSizeTab]?.sleeve_length_cm} cm</strong></td>
                  <td>Above-Elbow Silhouette</td>
                </tr>
                <tr>
                  <td><code>COLLAR_CIRCUM</code></td>
                  <td>Crewneck Collar Opening Circumference</td>
                  <td><strong>{measurementsTable[activeSizeTab]?.collar_circumference_cm} cm</strong></td>
                  <td>Ribbed Text Collar</td>
                </tr>
              </tbody>
            </table>

            <div className="actions-row">
              <button type="button" className="btn-secondary-merchant" onClick={() => setActiveStep(3)}>
                <ArrowLeft size={16} /> BACK
              </button>
              <button type="button" className="btn-primary-merchant" onClick={handleSaveMeasurements} disabled={loading}>
                CONTINUE TO FABRIC PROPERTIES <ArrowRight size={16} />
              </button>
            </div>
          </div>
        )}

        {/* ====================================================================
            STEP 5: FABRIC MECHANICAL PROPERTIES
            ==================================================================== */}
        {activeStep === 5 && (
          <div className="merchant-card">
            <h2 className="merchant-card-title">Step 5 — Fabric Mechanical Properties</h2>
            <p className="merchant-card-subtitle">
              Input physical tensile, stretch, and bending characteristics governing real-time cloth simulation.
            </p>

            <div className="form-grid-2">
              <div className="form-group">
                <label className="form-label">Fabric Name / Blend</label>
                <input
                  type="text"
                  className="form-input"
                  value={fabricProps.name}
                  onChange={(e) => setFabricProps({ ...fabricProps, name: e.target.value })}
                />
              </div>

              <div className="form-group">
                <label className="form-label">Fiber Composition</label>
                <input
                  type="text"
                  className="form-input"
                  value={fabricProps.composition}
                  onChange={(e) => setFabricProps({ ...fabricProps, composition: e.target.value })}
                />
              </div>
            </div>

            <div className="form-grid-2">
              <div className="form-group">
                <label className="form-label">Areal Density (GSM - g/m²)</label>
                <input
                  type="number"
                  className="form-input"
                  value={fabricProps.gsm}
                  onChange={(e) => setFabricProps({ ...fabricProps, gsm: parseFloat(e.target.value) || 0 })}
                />
              </div>

              <div className="form-group">
                <label className="form-label">Fabric Thickness (mm)</label>
                <input
                  type="number"
                  step="0.05"
                  className="form-input"
                  value={fabricProps.thickness_mm}
                  onChange={(e) => setFabricProps({ ...fabricProps, thickness_mm: parseFloat(e.target.value) || 0 })}
                />
              </div>
            </div>

            <div className="form-grid-2">
              <div className="form-group">
                <label className="form-label">Weft Tensile Stretch (%)</label>
                <input
                  type="number"
                  className="form-input"
                  value={fabricProps.weft_stretch_percent}
                  onChange={(e) => setFabricProps({ ...fabricProps, weft_stretch_percent: parseFloat(e.target.value) || 0 })}
                />
              </div>

              <div className="form-group">
                <label className="form-label">Elastic Recovery (%)</label>
                <input
                  type="number"
                  className="form-input"
                  value={fabricProps.elastic_recovery_percent}
                  onChange={(e) => setFabricProps({ ...fabricProps, elastic_recovery_percent: parseFloat(e.target.value) || 0 })}
                />
              </div>
            </div>

            <div className="actions-row">
              <button type="button" className="btn-secondary-merchant" onClick={() => setActiveStep(4)}>
                <ArrowLeft size={16} /> BACK
              </button>
              <button type="button" className="btn-primary-merchant" onClick={handleSaveFabric} disabled={loading}>
                CONTINUE TO 3D PREVIEW & GENERATION <ArrowRight size={16} />
              </button>
            </div>
          </div>
        )}

        {/* ====================================================================
            STEP 6: 3D PREVIEW & MOTION TEST
            ==================================================================== */}
        {activeStep === 6 && (
          <div className="merchant-card">
            <h2 className="merchant-card-title">Step 6 — 3D Garment Generation & Arm Motion Test</h2>
            <p className="merchant-card-subtitle">
              Inspect the physically responsive 3D garment fitted to the upright pearl-white NAVER Anny mannequin in the
              high-fashion burgundy studio.
            </p>

            <div className="preview-stage-layout">
              {/* Left Column: 3D Studio Canvas */}
              <div>
                <AvatarViewer
                  assetUrl="/avatars/anny_skinned_male.glb"
                  garmentUrl={`/garments/TSH-WW-CREW-001_${previewSize}.glb`}
                  showGarment={true}
                  armAngle={armAngle}
                  studioBackground="#720e2c"
                  fabricProfile="knit"
                  height="520px"
                />

                {/* Motion Control Slider */}
                <div className="motion-control-card">
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <strong style={{ fontSize: '13px' }}>AVATAR MOTION & ARM ELEVATION TEST</strong>
                    <span style={{ fontFamily: 'Archivo Black', fontSize: '14px', color: 'var(--pink)' }}>
                      {armAngle}° ELEVATION
                    </span>
                  </div>

                  <div className="slider-group">
                    <input
                      type="range"
                      min={0}
                      max={90}
                      step={5}
                      value={armAngle}
                      onChange={(e) => setArmAngle(parseInt(e.target.value, 10))}
                      className="arm-motion-slider"
                    />
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: '#666' }}>
                      <span>0° (Rest / A-Pose)</span>
                      <span>30° (Relaxed)</span>
                      <span>45° (Mid Stretch)</span>
                      <span>90° (T-Pose Max)</span>
                    </div>
                  </div>

                  <p style={{ fontSize: '11px', color: '#666', margin: '8px 0 0', lineHeight: 1.4 }}>
                    ✦ Drag the slider to verify underarm stretch resistance, sleeve lift, and fabric folds driven by the
                    XPBD cloth physics solver.
                  </p>
                </div>
              </div>

              {/* Right Column: Controls, Size Switcher & Publication */}
              <div>
                {/* Size Geometry Switcher */}
                <div style={{ background: '#ffffff', border: '1.5px solid var(--black)', borderRadius: '10px', padding: '16px', marginBottom: '16px' }}>
                  <label className="form-label" style={{ display: 'block', marginBottom: '8px' }}>
                    SELECT SIZE VARIANT TO INSPECT:
                  </label>
                  <div style={{ display: 'flex', gap: '8px' }}>
                    {['S', 'M', 'L'].map((sz) => (
                      <button
                        key={sz}
                        type="button"
                        style={{
                          flex: 1,
                          padding: '10px',
                          border: '2px solid var(--black)',
                          borderRadius: '8px',
                          fontFamily: 'Archivo Black',
                          fontSize: '12px',
                          background: previewSize === sz ? 'var(--pink)' : '#f8fafc',
                          color: previewSize === sz ? '#ffffff' : 'var(--black)',
                          cursor: 'pointer',
                        }}
                        onClick={() => setPreviewSize(sz)}
                      >
                        SIZE {sz}
                      </button>
                    ))}
                  </div>
                  <div style={{ fontSize: '11px', color: '#666', marginTop: '10px' }}>
                    Loads discrete graded geometry: <code>TSH-WW-CREW-001_{previewSize}.glb</code>
                  </div>
                </div>

                {/* Garment Specifications Summary */}
                <div style={{ background: '#f8fafc', border: '1.5px solid var(--black)', borderRadius: '10px', padding: '16px', marginBottom: '16px', fontSize: '12px', lineHeight: 1.6 }}>
                  <strong style={{ display: 'block', marginBottom: '6px' }}>✦ DIGITAL ASSET SPECIFICATION</strong>
                  <div>SKU: <strong>{identity.sku}</strong></div>
                  <div>Fabric: <strong>{fabricProps.name} ({fabricProps.gsm} GSM)</strong></div>
                  <div>Collar Detail: <strong>Ribbed White Text "CLASSY"</strong></div>
                  <div>Pocket: <strong>Left Chest White Patch with Graphic</strong></div>
                  <div>Physics Engine: <strong>Client-Side XPBD Cloth Solver (60 FPS)</strong></div>
                </div>

                {/* Status & Publication Actions */}
                <div style={{ background: garmentStatus === 'published' ? '#ecfdf5' : '#fef3c7', border: '2px solid var(--black)', borderRadius: '10px', padding: '16px', marginBottom: '20px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                    <span style={{ fontSize: '11px', fontWeight: 800, textTransform: 'uppercase' }}>PUBLICATION STATE</span>
                    <span style={{ fontFamily: 'Archivo Black', fontSize: '12px', color: garmentStatus === 'published' ? '#166534' : '#92400e' }}>
                      ● {garmentStatus.toUpperCase()}
                    </span>
                  </div>
                  <p style={{ fontSize: '12px', margin: 0, color: '#444' }}>
                    {garmentStatus === 'published'
                      ? 'This digital garment is live and available for shoppers in Mode A 3D Try-On.'
                      : 'Assets generated. Review motion deformation above before publishing to catalog.'}
                  </p>
                </div>

                {/* Action Buttons */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                  <button
                    type="button"
                    className="btn-primary-merchant"
                    onClick={handlePublish}
                    disabled={loading}
                    style={{ justifyContent: 'center', padding: '14px' }}
                  >
                    <Sparkles size={18} />
                    {garmentStatus === 'published' ? 'RE-PUBLISH DIGITAL GARMENT' : '✦ PUBLISH TO SHOPPER CATALOG'}
                  </button>

                  <button
                    type="button"
                    className="btn-secondary-merchant"
                    onClick={() => navigate('/try-on')}
                    style={{ justifyContent: 'center', padding: '12px' }}
                  >
                    OPEN IN SHOPPER TRY-ON STUDIO →
                  </button>
                </div>
              </div>
            </div>

            <div className="actions-row">
              <button type="button" className="btn-secondary-merchant" onClick={() => setActiveStep(5)}>
                <ArrowLeft size={16} /> BACK
              </button>
              <button type="button" className="btn-secondary-merchant" onClick={() => navigate('/try-on')}>
                DONE (GO TO SHOPPER TRY-ON) →
              </button>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
