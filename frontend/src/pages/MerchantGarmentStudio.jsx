import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Header from './Header';
import { AvatarViewer } from '../components/avatar/AvatarViewer';
import {
  fetchMerchantGarments,
  fetchGarmentDetails,
  createGarmentIdentity,
  uploadViewpointImage,
  deleteGarmentImage,
  uploadCADPattern,
  saveGuidedPattern,
  requestAIRepairPattern,
  saveMeasurements,
  fetchFabricPresets,
  saveFabricProps,
  trigger3DGeneration,
  fetchQAReport,
  approveGarment,
  publishGarment,
  fetchGarmentManifest,
  fetchPrototypePreviewMeta,
  fetchGarmentRevisions,
  rollbackGarment,
  updateTryOnMode,
  prepareImageTryOn,
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
  Trash2,
  FileText,
  Download,
  Info,
  ShieldCheck,
} from 'lucide-react';

export default function MerchantGarmentStudio({ embedded = false } = {}) {
  const navigate = useNavigate();

  const [activeStep, setActiveStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [successMessage, setSuccessMessage] = useState(null);
  const [errorMessage, setErrorMessage] = useState(null);

  // Active Garment State
  const [garmentId, setGarmentId] = useState('ww-seed-tsh-ww-crew-001');
  const [garmentData, setGarmentData] = useState(null);
  const [garmentsList, setGarmentsList] = useState([]);
  const [revisionsList, setRevisionsList] = useState([]);
  const [downstreamStale, setDownstreamStale] = useState(false);
  const [staleReason, setStaleReason] = useState(null);

  // Step 1: Product Identity
  const [identity, setIdentity] = useState({
    name: 'WearWise Signature Boxy Crew Tee',
    sku: 'TSH-WW-CREW-001',
    category: 'T-Shirt',
    subcategory: 'Oversized Drop-Shoulder Tee',
    description: 'Heavyweight drop-shoulder boxy tee with ribbed crewneck collar, clean hem band, and chest pocket.',
    color_variant: 'Coral Pink / White Trim',
    price: 2999,
    available_sizes: ['S', 'M', 'L'],
    try_on_mode: 'IMAGE_AND_THREE_D',
  });

  // Step 2: Dual-Role Viewpoint Images
  const [imageRole, setImageRole] = useState('both'); // 'storefront_gallery', 'technical_reference', 'both'
  const [uploadedImages, setUploadedImages] = useState({
    front: '/garments/reference_front.jpg',
    back: null,
    left_side: '/garments/reference_side.jpg',
    right_side: null,
    close_up: '/garments/garment_texture_diffuse.png',
    collar: null,
    cuff: null,
    construction: null,
  });
  const [imagesMeta, setImagesMeta] = useState([]);

  // Step 3: Pattern & Construction
  const [patternMethodTab, setPatternMethodTab] = useState('guided'); // 'guided', 'cad', 'ai'
  const [patternSpec, setPatternSpec] = useState({
    pattern_mode: 'parametric',
    construction_type: 'boxy_drop_shoulder',
    collar_type: 'ribbed_crewneck',
    hem_finish: 'clean_28mm',
    has_pocket: true,
    pocket_type: 'left_chest_patch',
    has_cad_data: true,
    provisional: false,
    confidence_label: 'PARAMETRIC_TEMPLATE',
    assumptions_note: 'Calibrated against ISO 8559-2 dropped-shoulder block with 11 explicit seams',
    panels: [
      { id: 'PANEL-FRONT-TORSO', name: 'Front Torso Panel', seam_count: 5 },
      { id: 'PANEL-BACK-TORSO', name: 'Back Torso Panel', seam_count: 5 },
      { id: 'PANEL-SLEEVE-L', name: 'Left Dropped Sleeve', seam_count: 2 },
      { id: 'PANEL-SLEEVE-R', name: 'Right Dropped Sleeve', seam_count: 2 },
      { id: 'PANEL-COLLAR-RIB', name: 'Ribbed Crewneck Collar (1x1 Rib)', seam_count: 1 },
      { id: 'PANEL-HEM-BAND', name: 'Clean 28mm Hem Band', seam_count: 1 },
      { id: 'PANEL-POCKET-CHEST', name: 'Left Chest Patch Pocket', seam_count: 1 },
    ],
  });
  const [cadUnits, setCadUnits] = useState('mm');

  // Step 4: Finished Measurements (S, M, L)
  const [activeSizeTab, setActiveSizeTab] = useState('M');
  const [measurementsTable, setMeasurementsTable] = useState({
    S: {
      half_chest_width_cm: 50.0,
      back_length_cm: 64.0,
      shoulder_breadth_cm: 47.0,
      sleeve_length_cm: 15.0,
      sleeve_opening_cm: 19.5,
      bicep_width_cm: 21.0,
      armhole_depth_cm: 25.0,
      collar_circumference_cm: 42.0,
      hem_width_cm: 49.0,
      dimensional_ease_chest_cm: '+2.0 cm',
      measurement_type: 'flat_tabletop',
    },
    M: {
      half_chest_width_cm: 54.0,
      back_length_cm: 67.0,
      shoulder_breadth_cm: 50.0,
      sleeve_length_cm: 17.0,
      sleeve_opening_cm: 20.5,
      bicep_width_cm: 22.0,
      armhole_depth_cm: 26.5,
      collar_circumference_cm: 44.0,
      hem_width_cm: 53.0,
      dimensional_ease_chest_cm: '+4.5 cm (Recommended)',
      measurement_type: 'flat_tabletop',
    },
    L: {
      half_chest_width_cm: 58.0,
      back_length_cm: 70.0,
      shoulder_breadth_cm: 53.0,
      sleeve_length_cm: 19.0,
      sleeve_opening_cm: 21.5,
      bicep_width_cm: 23.0,
      armhole_depth_cm: 28.0,
      collar_circumference_cm: 46.0,
      hem_width_cm: 57.0,
      dimensional_ease_chest_cm: '+8.0 cm',
      measurement_type: 'flat_tabletop',
    },
  });

  // Step 5: Fabric Properties & Presets
  const [fabricPresetsList, setFabricPresetsList] = useState([]);
  const [fabricProps, setFabricProps] = useState({
    name: 'Heavyweight Cotton Waffle Knit (240 GSM)',
    composition: '100% Combed Organic Cotton',
    structure: 'Waffle / Honeycomb Knit',
    gsm: 240.0,
    thickness_mm: 1.15,
    warp_stretch_percent: 14.5,
    weft_stretch_percent: 28.0,
    elastic_recovery_percent: 88.0,
    bending_stiffness: 18.5,
    shear_stiffness: 22.0,
    preset_id: 'cotton_waffle_knit_240gsm',
  });

  // Step 6: 3D Preview, Motion, QA & Publication
  const [previewSize, setPreviewSize] = useState('M');
  const [prototypeMeta, setPrototypeMeta] = useState(null);
  const [prototypeError, setPrototypeError] = useState(null);
  const [armAngle, setArmAngle] = useState(0);
  const [garmentStatus, setGarmentStatus] = useState('published');
  const [isGenerating, setIsGenerating] = useState(false);
  const [pipelineProgress, setPipelineProgress] = useState([]);
  const [qaReport, setQaReport] = useState(null);
  const [manifestData, setManifestData] = useState(null);
  const [showManifestModal, setShowManifestModal] = useState(false);

  const applyGarmentDoc = (g) => {
    if (!g) return;
    setGarmentId(g.id);
    setGarmentData(g);
    setIdentity({
      name: g.name,
      sku: g.sku,
      category: g.category || 'T-Shirt',
      subcategory: g.subcategory || 'Oversized Drop-Shoulder Tee',
      description: g.description || '',
      color_variant: g.color_variant || '',
      price: g.price || 2999,
      available_sizes: g.available_sizes || ['S', 'M', 'L'],
      try_on_mode: g.try_on_mode || 'IMAGE_AND_THREE_D',
    });
    if (g.images) setUploadedImages(g.images);
    if (g.images_meta) setImagesMeta(g.images_meta);
    if (g.pattern) setPatternSpec(g.pattern);
    if (g.measurements) setMeasurementsTable(g.measurements);
    if (g.fabric_properties) setFabricProps(g.fabric_properties);
    if (g.status) setGarmentStatus(g.status);
    setQaReport(g.qa_report || null);
    setManifestData(g.manifest || null);
    setDownstreamStale(Boolean(g.downstream_stale));
    setStaleReason(g.stale_reason || null);
  };

  const refreshRevisions = (id) => {
    if (!id) return;
    fetchGarmentRevisions(id)
      .then((res) => setRevisionsList(res?.revisions || []))
      .catch(() => setRevisionsList([]));
  };

  // Load initial garment data & fabric presets
  useEffect(() => {
    fetchFabricPresets()
      .then((data) => {
        if (data && data.presets) setFabricPresetsList(data.presets);
      })
      .catch((err) => console.warn('Could not load fabric presets:', err));

    fetchMerchantGarments()
      .then((garments) => {
        if (garments && garments.length > 0) {
          setGarmentsList(garments);
          applyGarmentDoc(garments[0]);
          refreshRevisions(garments[0].id);
        }
      })
      .catch((err) => console.warn('Could not load merchant garments:', err));
  }, []);

  // Resolve explicit unpublished prototype candidate assets for TSH-WW-CREW-001 or ungenerated SKUs
  useEffect(() => {
    const activeSku = identity?.sku || 'TSH-WW-CREW-001';
    if (activeSku !== 'TSH-WW-CREW-001' && garmentData?.size_variants) {
      setPrototypeMeta(null);
      setPrototypeError(null);
      return;
    }
    setPrototypeError(null);
    fetchPrototypePreviewMeta(activeSku, 'rev3')
      .then((meta) => {
        setPrototypeMeta(meta);
        setPrototypeError(null);
      })
      .catch((err) => {
        setPrototypeMeta(null);
        setPrototypeError(err?.message || `Prototype candidate assets unavailable for ${activeSku}`);
      });
  }, [identity?.sku, garmentData?.size_variants]);

  const handleStartNewDraft = () => {
    setGarmentId('');
    setGarmentData(null);
    setRevisionsList([]);
    setQaReport(null);
    setManifestData(null);
    setPipelineProgress([]);
    setDownstreamStale(false);
    setStaleReason(null);
    setGarmentStatus('draft');
    setIdentity({
      name: '',
      sku: '',
      category: 'T-Shirt',
      subcategory: 'Oversized Drop-Shoulder Tee',
      description: '',
      color_variant: 'Coral Pink / White Trim',
      price: 2999,
      available_sizes: ['S', 'M', 'L'],
      try_on_mode: 'IMAGE_AND_THREE_D',
    });
    setUploadedImages({
      front: null,
      back: null,
      left_side: null,
      right_side: null,
      close_up: null,
      collar: null,
      cuff: null,
      construction: null,
    });
    setImagesMeta([]);
    setActiveStep(1);
    showFeedback('Ready to configure a new unique product SKU.');
  };

  const showFeedback = (msg, isError = false) => {
    if (isError) {
      setErrorMessage(msg);
      setTimeout(() => setErrorMessage(null), 5000);
    } else {
      setSuccessMessage(msg);
      setTimeout(() => setSuccessMessage(null), 4000);
    }
  };

  // Step 1: Save Identity
  const handleSaveIdentity = async () => {
    setLoading(true);
    try {
      const resp = await createGarmentIdentity(identity);
      applyGarmentDoc(resp);
      setGarmentsList((prev) => [resp, ...prev.filter((x) => x.id !== resp.id)]);
      refreshRevisions(resp.id);
      showFeedback('Step 1: Product identity and SKU created successfully.');
      setActiveStep(2);
    } catch (err) {
      showFeedback(err.message, true);
    } finally {
      setLoading(false);
    }
  };

  // Step 2: Upload Viewpoint with Dual Role
  const handleFileUpload = async (viewpoint, file) => {
    if (!file) return;
    setLoading(true);
    try {
      const resp = await uploadViewpointImage(garmentId, viewpoint, file, imageRole);
      applyGarmentDoc(resp.garment);
      showFeedback(`Uploaded ${viewpoint} image (${imageRole}) successfully.`);
    } catch (err) {
      showFeedback(err.message, true);
    } finally {
      setLoading(false);
    }
  };

  // Step 2: Delete Image
  const handleDeleteImage = async (imageId) => {
    setLoading(true);
    try {
      const resp = await deleteGarmentImage(garmentId, imageId);
      setImagesMeta(resp.images_meta);
      showFeedback('Image deleted successfully.');
    } catch (err) {
      showFeedback(err.message, true);
    } finally {
      setLoading(false);
    }
  };

  // Step 3: CAD Upload
  const handleCADUpload = async (file) => {
    if (!file) return;
    setLoading(true);
    try {
      const resp = await uploadCADPattern(garmentId, file, cadUnits);
      applyGarmentDoc(resp.garment);
      showFeedback(`Method A: CAD pattern parsed (${resp.cad_validation.panel_count} panels).`);
    } catch (err) {
      showFeedback(err.message, true);
    } finally {
      setLoading(false);
    }
  };

  // Step 3: Save Guided Pattern
  const handleSaveGuidedPattern = async () => {
    setLoading(true);
    try {
      const resp = await saveGuidedPattern(garmentId, {
        silhouette: patternSpec.construction_type,
        collar_type: patternSpec.collar_type || 'ribbed_crewneck',
        hem_finish: patternSpec.hem_finish || 'clean_28mm',
        has_pocket: patternSpec.has_pocket !== false,
        pocket_type: patternSpec.pocket_type || 'left_chest_patch',
        pocket_width_cm: patternSpec.pocket_width_cm || null,
        pocket_height_cm: patternSpec.pocket_height_cm || null,
        measurements: measurementsTable[activeSizeTab],
      });
      applyGarmentDoc(resp.garment);
      showFeedback('Method B: Guided pattern synthesized with explicit 2D panels and seams.');
      setActiveStep(4);
    } catch (err) {
      showFeedback(err.message, true);
    } finally {
      setLoading(false);
    }
  };

  // Step 3: AI Reconstruct Pattern
  const handleAIRepair = async () => {
    setLoading(true);
    try {
      const resp = await requestAIRepairPattern(garmentId, { adapter: 'SwiftTailorAdapter' });
      applyGarmentDoc(resp.garment);
      showFeedback('Method C: Provisional AI adapter pattern generated (requires merchant verification).');
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
      const updated = await saveMeasurements(garmentId, { size_label: activeSizeTab, ...current });
      applyGarmentDoc(updated);
      showFeedback(`Step 4: Size ${activeSizeTab} flat & circumference measurements saved.`);
      setActiveStep(5);
    } catch (err) {
      showFeedback(err.message, true);
    } finally {
      setLoading(false);
    }
  };

  // Step 5: Select Preset
  const handleSelectPreset = (preset) => {
    setFabricProps({
      ...preset,
      preset_id: preset.id,
    });
    showFeedback(`Loaded provisional preset: ${preset.name}`);
  };

  // Step 5: Save Fabric
  const handleSaveFabric = async () => {
    setLoading(true);
    try {
      const resp = await saveFabricProps(garmentId, fabricProps);
      applyGarmentDoc(resp);
      showFeedback('Step 5: Fabric mechanical properties registered.');
      setActiveStep(6);
    } catch (err) {
      showFeedback(err.message, true);
    } finally {
      setLoading(false);
    }
  };

  // Step 6: Generate 3D with 13-stage Pipeline
  const handleGenerate3D = async () => {
    setIsGenerating(true);
    setPipelineProgress([]);
    try {
      const resp = await trigger3DGeneration(garmentId);
      setGarmentStatus(resp.status);
      setPipelineProgress(resp.pipeline_stages || []);
      setQaReport(resp.qa_report);
      setDownstreamStale(false);
      setStaleReason(null);
      setGarmentData((prev) => ({
        ...(prev || {}),
        id: garmentId,
        revision: resp.revision,
        active_revision: resp.revision,
        status: resp.status,
        downstream_stale: false,
        mesh_assets: resp.assets,
        size_variants: resp.size_variants,
        qa_report: resp.qa_report,
      }));
      refreshRevisions(garmentId);
      showFeedback(`✦ 3D Garments synthesized across S, M, L (rev${resp.revision}). QA Status: ${resp.qa_report.overall_status}.`);
    } catch (err) {
      showFeedback(err.message, true);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleSelectTryOnMode = async (mode) => {
    setIdentity((prev) => ({ ...prev, try_on_mode: mode }));
    if (!garmentId) return;
    setLoading(true);
    try {
      const updated = await updateTryOnMode(garmentId, mode);
      applyGarmentDoc(updated);
      const labelMap = {
        IMAGE_ONLY: 'Image Try-On only',
        THREE_D_ONLY: '3D Try-On only',
        IMAGE_AND_THREE_D: 'Both Image & 3D Try-On',
      };
      showFeedback(`Updated virtual try-on setting to ${labelMap[mode] || mode}.`);
    } catch (err) {
      showFeedback(err.message, true);
    } finally {
      setLoading(false);
    }
  };

  const handlePrepareImageTryOn = async () => {
    if (!garmentId) {
      showFeedback('Save product details first before preparing your listing.', true);
      return;
    }
    setLoading(true);
    try {
      const resp = await prepareImageTryOn(garmentId);
      setGarmentStatus(resp.status);
      setQaReport(resp.qa_report);
      setDownstreamStale(false);
      setGarmentData((prev) => ({
        ...(prev || {}),
        id: garmentId,
        revision: resp.revision,
        active_revision: resp.revision,
        status: resp.status,
        downstream_stale: false,
        qa_report: resp.qa_report,
      }));
      refreshRevisions(garmentId);
      showFeedback('Front product photos verified for Image Try-On. Review and publish below.');
    } catch (err) {
      showFeedback(err.message, true);
    } finally {
      setLoading(false);
    }
  };

  // Step 6.1: Formal Merchant Approval
  const [approverPrincipal, setApproverPrincipal] = useState('brand_director_demo');
  const [approvalNotes, setApprovalNotes] = useState('Physically verified boxy fit, seam stitching, and ISO 8559-2 grading.');
  const [approvalDetails, setApprovalDetails] = useState(null);

  const handleApprove = async () => {
    setLoading(true);
    try {
      const resp = await approveGarment(garmentId, approverPrincipal, approvalNotes);
      setGarmentStatus(resp.status);
      setApprovalDetails(resp);
      showFeedback('✦ Garment revision formally approved by Brand Director! Ready for storefront publication.');
    } catch (err) {
      showFeedback(err.message, true);
    } finally {
      setLoading(false);
    }
  };

  // Step 6.2: Storefront Publication & Manifest Compilation
  const handlePublish = async () => {
    setLoading(true);
    try {
      const resp = await publishGarment(garmentId, 'catalog_admin_demo');
      setGarmentStatus(resp.status);
      setManifestData(resp.manifest);
      showFeedback(`✦ Digital Garment published to active shopper catalog (${resp.published_version})!`);
    } catch (err) {
      showFeedback(err.message, true);
    } finally {
      setLoading(false);
    }
  };

  const handleViewManifest = async () => {
    try {
      const m = manifestData || await fetchGarmentManifest(garmentId);
      setManifestData(m);
      setShowManifestModal(true);
    } catch (err) {
      showFeedback(err.message, true);
    }
  };

  const stepsMeta = [
    { num: 1, label: 'Add product details', sub: 'Name, price & sizes' },
    { num: 2, label: 'Upload product photos', sub: 'Front & side views' },
    { num: 3, label: 'Choose garment style', sub: 'Guided or pattern' },
    { num: 4, label: 'Add size measurements', sub: 'S / M / L specs' },
    { num: 5, label: 'Choose fabric', sub: 'Material & feel' },
    { num: 6, label: 'Preview & publish', sub: 'Review & publish' },
  ];

  const getSellerStatusInfo = () => {
    if (downstreamStale) {
      return { label: 'Needs attention', next: 'This preview is outdated after recent edits. Create a new 3D preview before publishing.' };
    }
    if (garmentStatus === 'published') {
      return { label: 'Published', next: 'Your product is live in the staging catalog for shoppers to try on and purchase.' };
    }
    if (garmentStatus === 'approved' || qaReport?.overall_status === 'PASSED') {
      return { label: 'Ready to review', next: 'Review your 3D preview and measurements, then publish when ready.' };
    }
    if (qaReport?.overall_status === 'FAILED') {
      return { label: 'Needs attention', next: 'Check your product measurements or style details before creating the preview again.' };
    }
    if (garmentId) {
      return { label: 'In progress', next: 'Complete your product details, measurements, and fabric, then create your 3D preview.' };
    }
    return { label: 'Not started', next: 'Start by adding your product details and saving your draft.' };
  };
  const sellerStatus = getSellerStatusInfo();

  return (
    <div className="merchant-studio-page">
      {!embedded && <Header />}

      <main className="merchant-studio-main" style={embedded ? { paddingTop: '8px' } : undefined}>
        {/* Header Title */}
        <div className="merchant-studio-header">
          <div className="merchant-studio-pretitle">SELLER STUDIO · PRODUCT SETUP</div>
          <h1 className="merchant-studio-title">Seller Product Studio</h1>
          <p className="merchant-studio-desc">
            Add your product details, photos, measurements, and fabric to create an interactive 3D preview for shoppers.
          </p>
          <div
            data-testid="seller-status-summary"
            style={{
              marginTop: '10px',
              padding: '10px 14px',
              borderRadius: '10px',
              background: '#FFF8F1',
              border: '1.5px solid #151515',
              fontSize: '13px',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              flexWrap: 'wrap',
              gap: '8px',
            }}
          >
            <span><strong>Status:</strong> {sellerStatus.label}</span>
            <span style={{ color: '#475569' }}>{sellerStatus.next}</span>
          </div>
          <div style={{ display: 'flex', gap: '10px', alignItems: 'center', marginTop: '10px', flexWrap: 'wrap' }}>
            <button
              type="button"
              data-testid="new-draft-btn"
              className="btn-secondary-merchant"
              onClick={handleStartNewDraft}
              style={{ padding: '7px 14px', fontSize: '12px' }}
            >
              + NEW DRAFT PRODUCT
            </button>
            {garmentsList.length > 0 && (
              <select
                data-testid="garment-switcher"
                className="form-select"
                style={{ width: 'auto', minWidth: '260px', padding: '6px 10px', fontSize: '12px' }}
                value={garmentId || ''}
                onChange={(e) => {
                  const found = garmentsList.find((x) => x.id === e.target.value);
                  if (found) {
                    applyGarmentDoc(found);
                    refreshRevisions(found.id);
                  }
                }}
              >
                {garmentsList.map((g) => (
                  <option key={g.id} value={g.id}>
                    {g.sku} — {g.name} ({g.status})
                  </option>
                ))}
              </select>
            )}
          </div>
        </div>

        {/* Feedback alerts */}
        {successMessage && (
          <div className="feedback-banner success">
            <CheckCircle2 size={18} />
            <span>{successMessage}</span>
          </div>
        )}
        {errorMessage && (
          <div className="feedback-banner error">
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
            <div className="card-header-badge-row">
              <h2 className="merchant-card-title">Step 1 — Product Commercial Identity & SKU</h2>
              <span className="badge-purple">CATALOG ASSOCIATION</span>
            </div>
            <p className="merchant-card-subtitle">
              Define the physical clothing product identity, unique SKU, commercial price, and target apparel category.
            </p>

            <div className="form-grid-2">
              <div className="form-group">
                <label className="form-label">Product Name *</label>
                <input
                  type="text"
                  className="form-input"
                  value={identity.name}
                  onChange={(e) => setIdentity({ ...identity, name: e.target.value })}
                />
              </div>

              <div className="form-group">
                <label className="form-label">Product SKU (Unique Identifier) *</label>
                <input
                  type="text"
                  className="form-input font-mono"
                  value={identity.sku}
                  onChange={(e) => setIdentity({ ...identity, sku: e.target.value })}
                />
              </div>
            </div>

            <div className="form-grid-3">
              <div className="form-group">
                <label className="form-label">Category</label>
                <select
                  className="form-select"
                  value={identity.category}
                  onChange={(e) => setIdentity({ ...identity, category: e.target.value })}
                >
                  <option value="Tops">T-Shirt / Tops</option>
                  <option value="Shirts">Shirts</option>
                  <option value="Trousers">Trousers</option>
                  <option value="Jeans">Jeans</option>
                  <option value="Skirts">Skirts</option>
                  <option value="Dresses">Dresses</option>
                  <option value="Jackets">Jackets</option>
                  <option value="T-Shirt">T-Shirt (Legacy)</option>
                </select>
              </div>

              <div className="form-group">
                <label className="form-label">Subcategory / Cut</label>
                <input
                  type="text"
                  className="form-input"
                  value={identity.subcategory}
                  onChange={(e) => setIdentity({ ...identity, subcategory: e.target.value })}
                />
              </div>

              <div className="form-group">
                <label className="form-label">Price (INR ₹)</label>
                <input
                  type="number"
                  className="form-input"
                  value={identity.price}
                  onChange={(e) => setIdentity({ ...identity, price: parseFloat(e.target.value) || 0 })}
                />
              </div>
            </div>

            <div className="form-grid-2">
              <div className="form-group">
                <label className="form-label">Color Variant Description</label>
                <input
                  type="text"
                  className="form-input"
                  value={identity.color_variant}
                  onChange={(e) => setIdentity({ ...identity, color_variant: e.target.value })}
                />
              </div>

              <div className="form-group">
                <label className="form-label">Available Sizes</label>
                <div className="size-tags-container">
                  {['XS', 'S', 'M', 'L', 'XL'].map((sz) => {
                    const isSelected = identity.available_sizes.includes(sz);
                    return (
                      <button
                        key={sz}
                        type="button"
                        className={`size-toggle-btn ${isSelected ? 'selected' : ''}`}
                        onClick={() => {
                          const newSizes = isSelected
                            ? identity.available_sizes.filter((s) => s !== sz)
                            : [...identity.available_sizes, sz];
                          setIdentity({ ...identity, available_sizes: newSizes });
                        }}
                      >
                        {sz}
                      </button>
                    );
                  })}
                </div>
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

            {/* Dual-Mode Virtual Try-On Options */}
            <div
              data-testid="seller-tryon-options"
              style={{
                marginTop: '14px',
                marginBottom: '16px',
                padding: '16px',
                borderRadius: '12px',
                border: '2px solid #151515',
                background: '#FFF8F1',
              }}
            >
              <div style={{ fontSize: '13px', fontWeight: 900, textTransform: 'uppercase', marginBottom: '6px' }}>
                Choose Virtual Try-On Options
              </div>
              <p style={{ fontSize: '12.5px', color: '#475569', margin: '0 0 12px' }}>
                Decide how shoppers can try on this piece. Image Try-On only listings require garment photos without forcing 3D modelling.
              </p>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(210px, 1fr))', gap: '10px' }}>
                {[
                  {
                    id: 'IMAGE_ONLY',
                    title: 'Image Try-On only',
                    desc: 'Upload product photos and publish without building a 3D model.',
                  },
                  {
                    id: 'THREE_D_ONLY',
                    title: '3D Try-On only',
                    desc: 'Create and verify S/M/L 3D fit models; photo try-on disabled.',
                  },
                  {
                    id: 'IMAGE_AND_THREE_D',
                    title: 'Both Image & 3D Try-On',
                    desc: 'Offer shoppers both photo try-on and interactive 3D fitting.',
                  },
                ].map((opt) => {
                  const selected = (identity.try_on_mode || 'IMAGE_AND_THREE_D') === opt.id;
                  return (
                    <button
                      key={opt.id}
                      type="button"
                      data-testid={`seller-mode-${opt.id}`}
                      onClick={() => handleSelectTryOnMode(opt.id)}
                      style={{
                        textAlign: 'left',
                        padding: '12px',
                        borderRadius: '10px',
                        border: selected ? '2.5px solid #FF3D9A' : '2px solid #151515',
                        background: selected ? '#fff' : '#f8fafc',
                        cursor: 'pointer',
                      }}
                    >
                      <div style={{ fontWeight: 900, fontSize: '13px', marginBottom: '4px' }}>
                        {selected ? '✓ ' : ''}
                        {opt.title}
                      </div>
                      <div style={{ fontSize: '11.5px', color: '#475569', lineHeight: 1.4 }}>{opt.desc}</div>
                    </button>
                  );
                })}
              </div>
            </div>

            <div className="actions-row">
              <span className="info-subtext">Active SKU: <strong>{identity.sku}</strong> · Ready for Step 2</span>
              <button type="button" className="btn-primary-merchant" onClick={handleSaveIdentity} disabled={loading}>
                CONTINUE TO IMAGE UPLOAD <ArrowRight size={16} />
              </button>
            </div>
          </div>
        )}

        {/* ====================================================================
            STEP 2: GARMENT IMAGE UPLOAD & DUAL ROLES
            ==================================================================== */}
        {activeStep === 2 && (
          <div className="merchant-card">
            <div className="card-header-badge-row">
              <h2 className="merchant-card-title">Step 2 — Multi-View Photography & Image Role Assignment</h2>
              <span className="badge-lime">DUAL-ROLE SEPARATION</span>
            </div>
            <p className="merchant-card-subtitle">
              Upload photographs and assign roles: <strong>Storefront Gallery</strong> (shopper-facing commerce) vs 
              <strong>Technical Reconstruction Reference</strong> (internal geometry/texture extraction).
            </p>

            {/* Role Selector Header */}
            <div className="role-selector-bar">
              <span className="role-bar-label">SELECT ROLE FOR NEW UPLOADS:</span>
              <div className="role-options-group">
                {[
                  { id: 'both', label: 'Dual-Role (Storefront & Reconstruction)' },
                  { id: 'technical_reference', label: 'Technical Reference Only (Private)' },
                  { id: 'storefront_gallery', label: 'Storefront Gallery Only (Public)' },
                ].map((r) => (
                  <button
                    key={r.id}
                    type="button"
                    className={`role-tab-btn ${imageRole === r.id ? 'active' : ''}`}
                    onClick={() => setImageRole(r.id)}
                  >
                    {r.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Checklist of required technical references */}
            <div className="checklist-box">
              <div className="checklist-title">
                <ShieldCheck size={16} color="#059669" />
                <span>TECHNICAL RECONSTRUCTION CHECKLIST</span>
              </div>
              <div className="checklist-items">
                {[
                  { key: 'front', label: 'Front View (Required)' },
                  { key: 'back', label: 'Back View (Required)' },
                  { key: 'left_side', label: 'Left/Right Side View (Required)' },
                  { key: 'close_up', label: 'Fabric Texture Close-Up (Required)' },
                ].map((item) => {
                  const isPresent = !!uploadedImages[item.key] || (item.key === 'left_side' && (uploadedImages.left_side || uploadedImages.right_side));
                  return (
                    <div key={item.key} className={`checklist-item ${isPresent ? 'done' : 'missing'}`}>
                      {isPresent ? <CheckCircle2 size={14} color="#10b981" /> : <AlertTriangle size={14} color="#f59e0b" />}
                      <span>{item.label}</span>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* 8 Upload Slots Grid */}
            <div className="image-slots-grid-8">
              {[
                { key: 'front', label: 'Front View *', req: true },
                { key: 'back', label: 'Back View *', req: true },
                { key: 'left_side', label: 'Left Side *', req: true },
                { key: 'right_side', label: 'Right Side', req: false },
                { key: 'close_up', label: 'Fabric Close-Up *', req: true },
                { key: 'collar', label: 'Collar Detail', req: false },
                { key: 'cuff', label: 'Sleeve Cuff', req: false },
                { key: 'construction', label: 'Seam Construction', req: false },
              ].map((slot) => {
                const imgUrl = uploadedImages[slot.key];
                return (
                  <div
                    key={slot.key}
                    className={`upload-slot-card ${imgUrl ? 'filled' : ''}`}
                    onClick={() => document.getElementById(`upload-${slot.key}`)?.click()}
                  >
                    <input
                      id={`upload-${slot.key}`}
                      type="file"
                      accept="image/*"
                      style={{ display: 'none' }}
                      onChange={(e) => handleFileUpload(slot.key, e.target.files?.[0])}
                    />
                    {imgUrl ? (
                      <>
                        <img src={imgUrl} alt={slot.label} className="slot-preview-img" />
                        <span className="slot-view-title">{slot.label}</span>
                        <span className="slot-role-badge">✓ Loaded</span>
                      </>
                    ) : (
                      <>
                        <Upload size={22} color="#888" />
                        <span className="slot-view-title">{slot.label}</span>
                        <span className="slot-subtext">Click to upload</span>
                      </>
                    )}
                  </div>
                );
              })}
            </div>

            <div className="actions-row">
              <button type="button" className="btn-secondary-merchant" onClick={() => setActiveStep(1)}>
                <ArrowLeft size={16} /> BACK
              </button>
              {identity.try_on_mode === 'IMAGE_ONLY' ? (
                <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
                  <button type="button" className="btn-secondary-merchant" onClick={() => setActiveStep(3)}>
                    Optional: Sizes &amp; Fabric
                  </button>
                  <button
                    type="button"
                    data-testid="skip-to-publish-image-only-btn"
                    className="btn-primary-merchant"
                    onClick={() => setActiveStep(6)}
                  >
                    CONTINUE TO REVIEW &amp; PUBLISH <ArrowRight size={16} />
                  </button>
                </div>
              ) : (
                <button type="button" className="btn-primary-merchant" onClick={() => setActiveStep(3)}>
                  CONTINUE TO PATTERN SPECIFICATION <ArrowRight size={16} />
                </button>
              )}
            </div>
          </div>
        )}

        {/* ====================================================================
            STEP 3: PATTERN AND CONSTRUCTION SPECIFICATION (3 METHODS)
            ==================================================================== */}
        {activeStep === 3 && (
          <div className="merchant-card">
            <div className="card-header-badge-row">
              <h2 className="merchant-card-title">Step 3 — 2D Pattern & Construction Specification</h2>
              <span className={`confidence-badge-lg ${patternSpec.confidence_label || 'PARAMETRIC_TEMPLATE'}`}>
                {patternSpec.confidence_label || 'PARAMETRIC_TEMPLATE'}
              </span>
            </div>
            <p className="merchant-card-subtitle">
              Synthesize 2D pattern panels and seam relationships using one of three supported methods:
            </p>

            {/* 3 Method Tabs */}
            <div className="pattern-method-tabs">
              <button
                type="button"
                className={`pattern-method-tab ${patternMethodTab === 'guided' ? 'active' : ''}`}
                onClick={() => setPatternMethodTab('guided')}
              >
                <div className="method-tab-title">METHOD B: GUIDED BUILDER</div>
                <div className="method-tab-sub">Parametric GarmentCode Engine (Primary MVP)</div>
              </button>

              <button
                type="button"
                className={`pattern-method-tab ${patternMethodTab === 'cad' ? 'active' : ''}`}
                onClick={() => setPatternMethodTab('cad')}
              >
                <div className="method-tab-title">METHOD A: CAD / DXF / SVG</div>
                <div className="method-tab-sub">2D Upload &amp; Structural Validation (Reference Only)</div>
              </button>

              <button
                type="button"
                className={`pattern-method-tab ${patternMethodTab === 'ai' ? 'active' : ''}`}
                onClick={() => setPatternMethodTab('ai')}
              >
                <div className="method-tab-title">METHOD C: AI RECONSTRUCTION</div>
                <div className="method-tab-sub">Provisional Image-Based Synthesizer</div>
              </button>
            </div>

            {/* Tab 1: Method B (Guided Parametric) */}
            {patternMethodTab === 'guided' && (
              <div className="method-content-box">
                <div className="form-grid-2">
                  <div className="form-group">
                    <label className="form-label">Silhouette Block</label>
                    <select
                      className="form-select"
                      value={patternSpec.construction_type}
                      onChange={(e) => setPatternSpec({ ...patternSpec, construction_type: e.target.value })}
                    >
                      <option value="boxy_drop_shoulder">Boxy Dropped Shoulder (ISO 8559-2 Calibrated)</option>
                      <option value="set_in_sleeve">Classic Set-In Sleeve Tee</option>
                      <option value="raglan_athletic">Athletic Raglan Block</option>
                    </select>
                  </div>

                  <div className="form-group">
                    <label className="form-label">Collar Construction</label>
                    <select
                      className="form-select"
                      value={patternSpec.collar_type || 'ribbed_crewneck'}
                      onChange={(e) => setPatternSpec({ ...patternSpec, collar_type: e.target.value })}
                    >
                      <option value="ribbed_crewneck">1x1 Ribbed Knit Crewneck (25mm)</option>
                      <option value="bound_neckline">Self-Fabric Bound Neckline</option>
                      <option value="wide_scoop">Wide Relaxed Scoop</option>
                    </select>
                  </div>
                </div>

                <div className="form-grid-2">
                  <div className="form-group">
                    <label className="form-label">Hem & Sleeve Finish</label>
                    <select
                      className="form-select"
                      value={patternSpec.hem_finish || 'clean_28mm'}
                      onChange={(e) => setPatternSpec({ ...patternSpec, hem_finish: e.target.value })}
                    >
                      <option value="clean_28mm">Clean 28mm Folded Hem Band</option>
                      <option value="raw_edge">Raw Laser-Cut Edge</option>
                      <option value="twin_needle">Twin-Needle Topstitch</option>
                    </select>
                  </div>

                  <div className="form-group">
                    <label className="form-label">Patch Pocket Details</label>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginTop: '8px' }}>
                      <input
                        type="checkbox"
                        id="has_pocket_cb"
                        checked={patternSpec.has_pocket !== false}
                        onChange={(e) => setPatternSpec({ ...patternSpec, has_pocket: e.target.checked })}
                      />
                      <label htmlFor="has_pocket_cb" style={{ fontSize: '13px', fontWeight: 600 }}>
                        Left Chest Patch Pocket with Graphic (115 x 135 mm)
                      </label>
                    </div>
                  </div>
                </div>

                <button
                  type="button"
                  className="btn-primary-merchant"
                  onClick={handleSaveGuidedPattern}
                  disabled={loading}
                  style={{ marginTop: '10px' }}
                >
                  <Cpu size={16} /> SYNTHESIZE 7 PANELS & 11 EXPLICIT SEAMS
                </button>
              </div>
            )}

            {/* Tab 2: Method A (CAD Upload) */}
            {patternMethodTab === 'cad' && (
              <div className="method-content-box">
                <div className="form-grid-2">
                  <div className="form-group">
                    <label className="form-label">Pattern Dimensional Units</label>
                    <select
                      className="form-select"
                      value={cadUnits}
                      onChange={(e) => setCadUnits(e.target.value)}
                    >
                      <option value="mm">Millimeters (Standard ISO)</option>
                      <option value="cm">Centimeters</option>
                      <option value="inch">Inches (US Apparel)</option>
                    </select>
                  </div>

                  <div className="form-group">
                    <label className="form-label">Upload Graded DXF / SVG File</label>
                    <input
                      type="file"
                      accept=".dxf,.svg"
                      className="form-input"
                      onChange={(e) => handleCADUpload(e.target.files?.[0])}
                    />
                  </div>
                </div>

                <p className="info-subtext" data-testid="cad-capability-disclosure">
                  ℹ Validates DXF closed polyline loops/layers or SVG path/polygon/group counts and stores the file as a pattern reference. Arbitrary uploaded CAD geometry is NOT yet extruded into 3D; 3D synthesis currently uses the Method B 7-panel parametric builder.
                </p>
              </div>
            )}

            {/* Tab 3: Method C (AI Reconstruction) */}
            {patternMethodTab === 'ai' && (
              <div className="method-content-box">
                <p style={{ fontSize: '13px', color: '#444', lineHeight: 1.5, marginBottom: '16px' }}>
                  Provisional AI adapter (SwiftTailor / ReWeaver) analyzes uploaded front, back, and side viewpoint photos
                  to extract panel contours and seam boundaries. Assets produced will carry the explicit 
                  <strong style={{ color: '#b45309' }}> AI_RECONSTRUCTED</strong> confidence label.
                </p>

                <button
                  type="button"
                  className="btn-primary-merchant"
                  onClick={handleAIRepair}
                  disabled={loading}
                >
                  <Sparkles size={16} /> TRIGGER AI PATTERN RECONSTRUCTION
                </button>
              </div>
            )}

            {/* Pattern Panels & Seams Overview */}
            <div className="pattern-breakdown-card">
              <div className="breakdown-header">
                <strong>7 DEFINED PATTERN PANELS & SEAM TOPOLOGY</strong>
                <span className="badge-purple">11 SEAM RELATIONSHIPS</span>
              </div>
              <div className="panels-chips-grid">
                {(patternSpec.panels || []).map((p) => (
                  <div key={p.id || p.name} className="panel-chip">
                    <Scissors size={14} color="#8d6bff" />
                    <span className="panel-chip-name">{p.name || p.id}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="actions-row">
              <button type="button" className="btn-secondary-merchant" onClick={() => setActiveStep(2)}>
                <ArrowLeft size={16} /> BACK
              </button>
              <button type="button" className="btn-primary-merchant" onClick={() => setActiveStep(4)}>
                CONTINUE TO MEASUREMENTS <ArrowRight size={16} />
              </button>
            </div>
          </div>
        )}

        {/* ====================================================================
            STEP 4: FINISHED GARMENT MEASUREMENTS (S, M, L)
            ==================================================================== */}
        {activeStep === 4 && (
          <div className="merchant-card">
            <div className="card-header-badge-row">
              <h2 className="merchant-card-title">Step 4 — Finished Garment Measurement Specifications</h2>
              <span className="badge-lime">ISO 8559-2 GRADING</span>
            </div>
            <p className="merchant-card-subtitle">
              Enter finished dimensions for sizes S, M, and L. Delineates <strong>Flat Tabletop</strong> measurements
              (armpit to armpit) from full body perimeters.
            </p>

            {/* Size tabs */}
            <div className="size-selector-tabs">
              {['S', 'M', 'L'].map((sz) => (
                <button
                  key={sz}
                  type="button"
                  className={`size-tab-pill ${activeSizeTab === sz ? 'active' : ''}`}
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
                  <th>Measurement Location</th>
                  <th>Type</th>
                  <th>Value (cm)</th>
                  <th>Grading vs Baseline (M)</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td><code>HALF_CHEST</code></td>
                  <td>Half-Chest Width (Armpit to Armpit)</td>
                  <td><span className="meas-type-flat">Flat Tabletop</span></td>
                  <td>
                    <input
                      type="number"
                      step="0.5"
                      className="table-input"
                      value={measurementsTable[activeSizeTab]?.half_chest_width_cm || 54}
                      onChange={(e) => {
                        const val = parseFloat(e.target.value) || 0;
                        setMeasurementsTable({
                          ...measurementsTable,
                          [activeSizeTab]: { ...measurementsTable[activeSizeTab], half_chest_width_cm: val },
                        });
                      }}
                    />
                  </td>
                  <td><strong>{measurementsTable[activeSizeTab]?.dimensional_ease_chest_cm}</strong></td>
                </tr>
                <tr>
                  <td><code>BACK_LENGTH</code></td>
                  <td>Back Length from High Point Shoulder to Hem</td>
                  <td><span className="meas-type-flat">Flat Tabletop</span></td>
                  <td>
                    <input
                      type="number"
                      step="0.5"
                      className="table-input"
                      value={measurementsTable[activeSizeTab]?.back_length_cm || 67}
                      onChange={(e) => {
                        const val = parseFloat(e.target.value) || 0;
                        setMeasurementsTable({
                          ...measurementsTable,
                          [activeSizeTab]: { ...measurementsTable[activeSizeTab], back_length_cm: val },
                        });
                      }}
                    />
                  </td>
                  <td>Calibrated Boxy Drape</td>
                </tr>
                <tr>
                  <td><code>SHOULDER_BREADTH</code></td>
                  <td>Across Shoulder (Seam to Seam Across Back)</td>
                  <td><span className="meas-type-flat">Flat Tabletop</span></td>
                  <td>
                    <input
                      type="number"
                      step="0.5"
                      className="table-input"
                      value={measurementsTable[activeSizeTab]?.shoulder_breadth_cm || 50}
                      onChange={(e) => {
                        const val = parseFloat(e.target.value) || 0;
                        setMeasurementsTable({
                          ...measurementsTable,
                          [activeSizeTab]: { ...measurementsTable[activeSizeTab], shoulder_breadth_cm: val },
                        });
                      }}
                    />
                  </td>
                  <td>Dropped Shoulder Ease</td>
                </tr>
                <tr>
                  <td><code>SLEEVE_LENGTH</code></td>
                  <td>Dropped Shoulder Sleeve Length</td>
                  <td><span className="meas-type-flat">Flat Tabletop</span></td>
                  <td>
                    <input
                      type="number"
                      step="0.5"
                      className="table-input"
                      value={measurementsTable[activeSizeTab]?.sleeve_length_cm || 17}
                      onChange={(e) => {
                        const val = parseFloat(e.target.value) || 0;
                        setMeasurementsTable({
                          ...measurementsTable,
                          [activeSizeTab]: { ...measurementsTable[activeSizeTab], sleeve_length_cm: val },
                        });
                      }}
                    />
                  </td>
                  <td>Above-Elbow Silhouette</td>
                </tr>
                <tr>
                  <td><code>COLLAR_CIRCUM</code></td>
                  <td>Crewneck Collar Opening Circumference</td>
                  <td><span className="meas-type-circ">Circumference</span></td>
                  <td>
                    <input
                      type="number"
                      step="0.5"
                      className="table-input"
                      value={measurementsTable[activeSizeTab]?.collar_circumference_cm || 44}
                      onChange={(e) => {
                        const val = parseFloat(e.target.value) || 0;
                        setMeasurementsTable({
                          ...measurementsTable,
                          [activeSizeTab]: { ...measurementsTable[activeSizeTab], collar_circumference_cm: val },
                        });
                      }}
                    />
                  </td>
                  <td>1x1 Ribbed Knit Opening</td>
                </tr>
                <tr>
                  <td><code>HEM_WIDTH</code></td>
                  <td>Bottom Hem Width Across</td>
                  <td><span className="meas-type-flat">Flat Tabletop</span></td>
                  <td>
                    <input
                      type="number"
                      step="0.5"
                      className="table-input"
                      value={measurementsTable[activeSizeTab]?.hem_width_cm || 53}
                      onChange={(e) => {
                        const val = parseFloat(e.target.value) || 0;
                        setMeasurementsTable({
                          ...measurementsTable,
                          [activeSizeTab]: { ...measurementsTable[activeSizeTab], hem_width_cm: val },
                        });
                      }}
                    />
                  </td>
                  <td>Boxy Straight Cut Hem</td>
                </tr>
              </tbody>
            </table>

            <div className="actions-row">
              <button type="button" className="btn-secondary-merchant" onClick={() => setActiveStep(3)}>
                <ArrowLeft size={16} /> BACK
              </button>
              <button type="button" className="btn-primary-merchant" onClick={handleSaveMeasurements} disabled={loading}>
                SAVE & CONTINUE TO FABRIC PROPERTIES <ArrowRight size={16} />
              </button>
            </div>
          </div>
        )}

        {/* ====================================================================
            STEP 5: FABRIC MECHANICAL PROPERTIES (8 PRESETS)
            ==================================================================== */}
        {activeStep === 5 && (
          <div className="merchant-card">
            <div className="card-header-badge-row">
              <h2 className="merchant-card-title">Step 5 — Fabric Mechanical Properties & Preset Library</h2>
              <span className="badge-purple">XPBD PHYSICS PROFILE</span>
            </div>
            <p className="merchant-card-subtitle">
              Select from calibrated textile presets or define custom physical density, tensile stretch, and bending stiffness.
            </p>

            {/* 8 Preset Pills */}
            <div className="fabric-presets-box">
              <div className="presets-box-title">PROVISIONAL PRESET PROFILES (ONE-CLICK LOAD):</div>
              <div className="presets-grid">
                {fabricPresetsList.map((preset) => {
                  const isSelected = fabricProps.preset_id === preset.id;
                  return (
                    <button
                      key={preset.id}
                      type="button"
                      className={`preset-pill ${isSelected ? 'selected' : ''}`}
                      onClick={() => handleSelectPreset(preset)}
                    >
                      <div className="preset-pill-name">{preset.name}</div>
                      <div className="preset-pill-sub">{preset.gsm} GSM · {preset.structure}</div>
                    </button>
                  );
                })}
              </div>
            </div>

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

            <div className="form-grid-3">
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

            <div className="form-grid-3">
              <div className="form-group">
                <label className="form-label">Warp Tensile Stretch (%)</label>
                <input
                  type="number"
                  step="0.5"
                  className="form-input"
                  value={fabricProps.warp_stretch_percent || 14.5}
                  onChange={(e) => setFabricProps({ ...fabricProps, warp_stretch_percent: parseFloat(e.target.value) || 0 })}
                />
              </div>

              <div className="form-group">
                <label className="form-label">Weft Tensile Stretch (%)</label>
                <input
                  type="number"
                  step="0.5"
                  className="form-input"
                  value={fabricProps.weft_stretch_percent}
                  onChange={(e) => setFabricProps({ ...fabricProps, weft_stretch_percent: parseFloat(e.target.value) || 0 })}
                />
              </div>

              <div className="form-group">
                <label className="form-label">Bending Stiffness (mg·cm)</label>
                <input
                  type="number"
                  step="0.5"
                  className="form-input"
                  value={fabricProps.bending_stiffness}
                  onChange={(e) => setFabricProps({ ...fabricProps, bending_stiffness: parseFloat(e.target.value) || 0 })}
                />
              </div>
            </div>

            <div className="actions-row">
              <button type="button" className="btn-secondary-merchant" onClick={() => setActiveStep(4)}>
                <ArrowLeft size={16} /> BACK
              </button>
              <button type="button" className="btn-primary-merchant" onClick={handleSaveFabric} disabled={loading}>
                SAVE & CONTINUE TO 3D PREVIEW <ArrowRight size={16} />
              </button>
            </div>
          </div>
        )}

        {/* ====================================================================
            STEP 6: 3D GENERATION, STATIC MANNEQUIN PREVIEW, QA & PUBLICATION
            ==================================================================== */}
        {activeStep === 6 && (
          <div className="merchant-card">
            <div className="card-header-badge-row">
              <h2 className="merchant-card-title">Step 6 — Review 3D Preview &amp; Publish Product</h2>
              <span className={`confidence-badge-lg ${qaReport?.confidence_level || 'PARAMETRIC_TEMPLATE'}`}>
                {sellerStatus.label}
              </span>
            </div>
            <p className="merchant-card-subtitle">
              Create your interactive 3D preview, check garment shape and fit across sizes, and publish when ready.
            </p>

            {/* Pipeline Trigger & Progress Banner */}
            <div className="generate-trigger-bar">
              {identity.try_on_mode === 'IMAGE_ONLY' ? (
                <button
                  type="button"
                  data-testid="verify-image-tryon-btn"
                  className="btn-generate-hero"
                  onClick={handlePrepareImageTryOn}
                  disabled={loading}
                >
                  <CheckCircle2 size={20} />
                  <span>{loading ? 'VERIFYING PHOTOS...' : 'VERIFY PHOTOS FOR IMAGE TRY-ON (NO 3D REQUIRED)'}</span>
                </button>
              ) : (
                <button
                  type="button"
                  data-testid="create-3d-preview-btn"
                  className="btn-generate-hero"
                  onClick={handleGenerate3D}
                  disabled={isGenerating}
                >
                  {isGenerating ? <Cpu className="animate-spin" size={20} /> : <Sparkles size={20} />}
                  <span>{isGenerating ? 'CREATING YOUR PREVIEW...' : 'CREATE 3D PREVIEW & CHECK SHAPE'}</span>
                </button>
              )}
            </div>

            {/* 13 Pipeline Stages (if triggered or generated) */}
            {pipelineProgress.length > 0 && (
              <div className="pipeline-stages-container">
                <div className="pipeline-title">13-STAGE COMPILATION PIPELINE RESULTS:</div>
                <div className="stages-grid">
                  {pipelineProgress.map((stg) => (
                    <div key={stg.stage} className="stage-mini-pill">
                      <CheckCircle2 size={13} color="#10b981" />
                      <span className="stage-num">#{stg.stage}</span>
                      <span className="stage-name">{stg.name}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="preview-stage-layout">
              {/* Left Column: 3D Studio Canvas OR Image Try-On Photo Summary */}
              <div>
                {identity.try_on_mode === 'IMAGE_ONLY' ? (
                  <div
                    data-testid="seller-image-only-preview"
                    style={{
                      padding: '24px',
                      borderRadius: '14px',
                      border: '2px solid #151515',
                      background: '#FFF8F1',
                      textAlign: 'center',
                    }}
                  >
                    <h3 style={{ margin: '0 0 8px', fontSize: '16px', fontWeight: 900 }}>
                      Image Try-On Listing Ready (No 3D Model Required)
                    </h3>
                    <p style={{ fontSize: '13px', color: '#475569', margin: '0 0 16px' }}>
                      Shoppers will see your product photos and use Image Try-On on the product page.
                    </p>
                    {uploadedImages.front ? (
                      <img
                        src={uploadedImages.front}
                        alt={identity.name || 'Front garment photo'}
                        style={{ maxWidth: '100%', maxHeight: '320px', objectFit: 'contain', borderRadius: '10px', border: '1.5px solid #151515', background: '#fff' }}
                      />
                    ) : (
                      <div style={{ padding: '18px', borderRadius: '8px', border: '1.5px dashed #dc2626', color: '#991b1b', fontWeight: 700, fontSize: '13px' }}>
                        Upload a front garment photo in Step 2 before publishing.
                      </div>
                    )}
                  </div>
                ) : (
                  <>
                {downstreamStale && (
                  <div
                    data-testid="downstream-stale-banner"
                    style={{
                      marginBottom: '10px',
                      padding: '10px 14px',
                      borderRadius: '8px',
                      background: '#fffbeb',
                      border: '1px solid #f59e0b',
                      color: '#92400e',
                      fontSize: '12px',
                      fontWeight: 600,
                    }}
                  >
                    This preview is outdated because product details changed. Create a new 3D preview before approving and publishing.
                  </div>
                )}
                {prototypeError && !garmentData?.size_variants?.[previewSize]?.asset_url && (
                  <div
                    data-testid="prototype-preview-error"
                    style={{
                      marginBottom: '10px',
                      padding: '10px 14px',
                      borderRadius: '8px',
                      background: '#fef2f2',
                      border: '1px solid #ef4444',
                      color: '#991b1b',
                      fontSize: '12px',
                      fontWeight: 600,
                    }}
                  >
                    Prototype Candidate Unavailable: {prototypeError} (Legacy public catalog fallback disabled)
                  </div>
                )}
                {(() => {
                  const activeVariant = garmentData?.size_variants?.[previewSize] || prototypeMeta?.size_variants?.[previewSize] || null;
                  const activeUrl = activeVariant?.asset_url || null;
                  const activeQa = garmentData?.size_variants?.[previewSize] ? (qaReport || garmentData?.qa_report) : (prototypeMeta || qaReport);
                  const unavailErr = activeUrl
                    ? null
                    : prototypeError ||
                      (!prototypeMeta && !garmentData?.size_variants
                        ? 'Resolving prototype candidate asset...'
                        : `Missing candidate GLB for SKU ${identity.sku} Size ${previewSize}`);
                  return (
                    <AvatarViewer
                      assetUrl="/avatars/anny_baseline_male.glb"
                      garmentUrl={activeUrl}
                      garmentQaReport={activeQa}
                      garmentUnavailableError={unavailErr}
                      showGarment={Boolean(activeUrl)}
                      armAngle={armAngle}
                      studioBackground="#720e2c"
                      fabricProfile="knit"
                      height="520px"
                    />
                  );
                })()}

                {/* Motion Control Slider */}
                <div className="motion-control-card">
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <strong style={{ fontSize: '13px' }}>STATIC MANNEQUIN ARM ELEVATION INSPECTION</strong>
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
                </div>
                  </>
                )}
              </div>

              {/* Right Column: Controls, QA Report, Approval & Publication */}
              <div>
                {/* Size Geometry Switcher */}
                <div className="size-inspect-card">
                  <label className="form-label" style={{ display: 'block', marginBottom: '8px' }}>
                    SELECT SIZE VARIANT GEOMETRY TO INSPECT:
                  </label>
                  <div style={{ display: 'flex', gap: '8px' }}>
                    {['S', 'M', 'L'].map((sz) => (
                      <button
                        key={sz}
                        type="button"
                        className={`size-inspect-btn ${previewSize === sz ? 'active' : ''}`}
                        onClick={() => setPreviewSize(sz)}
                      >
                        SIZE {sz}
                      </button>
                    ))}
                  </div>
                  <div style={{ fontSize: '11px', color: '#666', marginTop: '10px' }}>
                    {(() => {
                      const v = garmentData?.size_variants?.[previewSize] || prototypeMeta?.size_variants?.[previewSize];
                      const revLbl = garmentData?.active_revision ? `rev${garmentData.active_revision}` : prototypeMeta?.revision;
                      return (
                        <>
                          Active 3D mesh:{' '}
                          <code>
                            {v?.glb_file ||
                              (prototypeError ? 'UNAVAILABLE (NO LEGACY FALLBACK)' : `${identity.sku}_${previewSize}.glb`)}
                          </code>
                          {v?.sha256 && (
                            <div style={{ marginTop: '4px', color: '#475569' }}>
                              SHA-256: <code>{v.sha256.slice(0, 16)}...</code> · Revision:{' '}
                              <code>{revLbl}</code>
                            </div>
                          )}
                        </>
                      );
                    })()}
                  </div>
                </div>

                {/* Automated Full QA Report Card */}
                {qaReport && (
                  <div className="qa-report-card">
                    <div className="qa-header">
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <ShieldCheck size={18} color="#059669" />
                        <strong>AUTOMATED QUALITY ASSESSMENT</strong>
                      </div>
                      <span className={`qa-status-pill ${qaReport.overall_status.toLowerCase()}`}>
                        {qaReport.overall_status}
                      </span>
                    </div>

                    <div className="qa-checks-list">
                      <div className="qa-check-row">
                        <span>Geometry QA (Euler char = -2, open neck/cuffs/hem):</span>
                        <strong className="status-pass">{qaReport.checks?.geometry_qa?.status || 'PASSED'}</strong>
                      </div>
                      <div className="qa-check-row">
                        <span>Measurement QA (Tolerance &le; 2.5 cm vs CAD specs):</span>
                        <strong className="status-pass">{qaReport.checks?.measurement_qa?.status || 'PASSED'}</strong>
                      </div>
                      <div className="qa-check-row">
                        <span>Texture QA (2048x2048 PBR atlas diffuse/roughness):</span>
                        <strong className="status-pass">{qaReport.checks?.texture_qa?.status || 'PASSED'}</strong>
                      </div>
                      <div className="qa-check-row">
                        <span>Variant QA (S, M, L discrete mesh topologies):</span>
                        <strong className="status-pass">{qaReport.checks?.variant_qa?.status || 'PASSED'}</strong>
                      </div>
                    </div>
                  </div>
                )}

                {/* Publication State & Gate */}
                <div className={`pub-state-card ${garmentStatus}`}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                    <span style={{ fontSize: '11px', fontWeight: 800, textTransform: 'uppercase' }}>PUBLICATION GATE</span>
                    <span className="pub-status-badge">● {garmentStatus.toUpperCase()}</span>
                  </div>
                  <p style={{ fontSize: '12px', margin: 0, color: '#444' }}>
                    {garmentStatus === 'published' && '✦ Published to active catalog (v1.0). Package manifest compiled with SHA-256 asset checksums.'}
                    {garmentStatus === 'approved' && '✦ Approved by Brand Director (Rev 1). Immutable package manifest ready for compilation.'}
                    {garmentStatus !== 'published' && garmentStatus !== 'approved' && 'Assets generated. Review QA audit above, then complete formal merchant approval.'}
                  </p>

                  {/* Formal Approval Form */}
                  {garmentStatus !== 'approved' && garmentStatus !== 'published' && (
                    <div style={{ marginTop: '14px', paddingTop: '12px', borderTop: '1px solid #cbd5e1' }}>
                      <div className="form-group" style={{ marginBottom: '8px' }}>
                        <label className="form-label" style={{ fontSize: '11px' }}>Approving Authority Principal ID</label>
                        <input
                          type="text"
                          className="form-input"
                          style={{ padding: '6px 10px', fontSize: '12px' }}
                          value={approverPrincipal}
                          onChange={(e) => setApproverPrincipal(e.target.value)}
                        />
                      </div>
                      <div className="form-group" style={{ marginBottom: '10px' }}>
                        <label className="form-label" style={{ fontSize: '11px' }}>Approval Audit Notes</label>
                        <input
                          type="text"
                          className="form-input"
                          style={{ padding: '6px 10px', fontSize: '12px' }}
                          value={approvalNotes}
                          onChange={(e) => setApprovalNotes(e.target.value)}
                        />
                      </div>
                      <button
                        type="button"
                        className="btn-primary-merchant"
                        onClick={handleApprove}
                        disabled={loading}
                        style={{ width: '100%', justifyContent: 'center', background: 'var(--lime)', color: 'var(--black)' }}
                      >
                        <Check size={16} /> FORMALLY APPROVE ASSET REVISION
                      </button>
                    </div>
                  )}
                </div>

                {/* Publication Actions */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginTop: '12px' }}>
                  {(garmentStatus === 'approved' || garmentStatus === 'published') && (
                    <button
                      type="button"
                      className="btn-primary-merchant"
                      onClick={handlePublish}
                      disabled={loading}
                      style={{ justifyContent: 'center', padding: '14px' }}
                    >
                      <Sparkles size={18} />
                      {garmentStatus === 'published' ? 'RE-PUBLISH PACKAGE MANIFEST' : '✦ PUBLISH TO SHOPPER CATALOG (v1.0)'}
                    </button>
                  )}

                  <button
                    type="button"
                    className="btn-secondary-merchant"
                    onClick={handleViewManifest}
                    style={{ justifyContent: 'center', padding: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}
                  >
                    <FileText size={16} />
                    VIEW DIGITAL GARMENT PACKAGE MANIFEST (.JSON)
                  </button>

                  <button
                    type="button"
                    className="btn-secondary-merchant"
                    onClick={() => navigate(identity.sku ? `/product/${encodeURIComponent(identity.sku)}` : '/explore')}
                    style={{ justifyContent: 'center', padding: '12px' }}
                  >
                    OPEN PRODUCT LISTING AS SHOPPER →
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

        {/* ====================================================================
            MANIFEST VIEWER MODAL
            ==================================================================== */}
        {showManifestModal && manifestData && (
          <div className="manifest-modal-overlay" onClick={() => setShowManifestModal(false)}>
            <div className="manifest-modal-card" onClick={(e) => e.stopPropagation()}>
              <div className="manifest-modal-header">
                <div>
                  <h3 style={{ margin: 0, fontFamily: 'Archivo Black', fontSize: '18px' }}>
                    Digital Garment Package Manifest
                  </h3>
                  <div style={{ fontSize: '12px', color: '#666', marginTop: '4px' }}>
                    SKU: <strong>{manifestData.sku}</strong> · Version: <strong>{manifestData.published_version}</strong>
                  </div>
                </div>
                <button
                  type="button"
                  className="manifest-close-btn"
                  onClick={() => setShowManifestModal(false)}
                >
                  ✕
                </button>
              </div>

              <div className="manifest-json-viewer">
                <pre>{JSON.stringify(manifestData, null, 2)}</pre>
              </div>

              <div className="manifest-modal-footer">
                <span style={{ fontSize: '12px', color: '#666' }}>
                  SHA-256 Checksums Verified · Reusable Digital Garment Asset
                </span>
                <button
                  type="button"
                  className="btn-primary-merchant"
                  onClick={() => {
                    const blob = new Blob([JSON.stringify(manifestData, null, 2)], { type: 'application/json' });
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `${manifestData.sku}_manifest.json`;
                    a.click();
                  }}
                >
                  <Download size={16} /> DOWNLOAD MANIFEST (.JSON)
                </button>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
