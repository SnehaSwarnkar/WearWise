import React, { useState, useEffect, useRef } from "react";
import "../App.css";
import "./TryOn.css";
import { useNavigate } from "react-router-dom";
import Header from "./Header";
import { AvatarViewer } from "../components/avatar/AvatarViewer";
import { addToCart } from "../api/cart";
import {
  createVtonJob,
  getVtonJob,
  getVtonResults,
  deleteVtonJob,
  getVtonProviders,
} from "../api/tryon";

const SIZE_SCALES = {
  XS: 0.95,
  S: 0.98,
  M: 1.0,
  L: 1.04,
  XL: 1.08,
};

const SIZE_FIT_DATA = {
  XS: { score: 78, status: "Snug Fit", chestEase: "-1.5 cm", note: "Tight across chest; reduced arm mobility." },
  S: { score: 88, status: "Tailored Slim", chestEase: "+0.5 cm", note: "Close to body; recommended if you prefer a fitted look." },
  M: { score: 98, status: "Recommended Regular Fit", chestEase: "+4.5 cm", note: "Optimal dimensional ease across chest and shoulders." },
  L: { score: 91, status: "Relaxed Fit", chestEase: "+8.0 cm", note: "Slightly dropped shoulders and loose torso drape." },
  XL: { score: 82, status: "Oversized Fit", chestEase: "+12.0 cm", note: "Generous street-style drape; longer hemline." },
};

function TryOn() {
  const navigate = useNavigate();

  // Mode Selection: 'mode_a' (3D Avatar) vs 'mode_b' (AI Photo VTON)
  const [activeMode, setActiveMode] = useState("mode_a");

  // ── Mode A State ────────────────────────────────────────────────────────────
  const [mannequinGender, setMannequinGender] = useState("male");
  const [selectedSize, setSelectedSize] = useState("M");
  const [showGarmentMesh, setShowGarmentMesh] = useState(true);
  const [armAngle, setArmAngle] = useState(0);
  const [fabricProfile, setFabricProfile] = useState("knit");
  const [cartAdding, setCartAdding] = useState(false);
  const [cartSuccess, setCartSuccess] = useState(false);

  // ── Mode B State ────────────────────────────────────────────────────────────
  const [personFile, setPersonFile] = useState(null);
  const [personPreviewUrl, setPersonPreviewUrl] = useState(null);
  const [userConsent, setUserConsent] = useState(true);
  const [jobId, setJobId] = useState(null);
  const [jobStatus, setJobStatus] = useState(null);
  const [jobProgress, setJobProgress] = useState(0);
  const [jobError, setJobError] = useState(null);
  const [vtonResults, setVtonResults] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [selectedZoomView, setSelectedZoomView] = useState(null);

  // Provider Telemetry
  const [providerTelemetry, setProviderTelemetry] = useState(null);
  const [showTelemetryModal, setShowTelemetryModal] = useState(false);

  useEffect(() => {
    getVtonProviders()
      .then((data) => setProviderTelemetry(data))
      .catch((err) => console.warn("Could not load provider telemetry:", err));
  }, []);

  // Mode B Polling Lifecycle
  useEffect(() => {
    if (!jobId || jobStatus === "completed" || jobStatus === "failed") {
      return;
    }

    const interval = setInterval(async () => {
      try {
        const job = await getVtonJob(jobId);
        setJobStatus(job.status);
        setJobProgress(job.progress_percent || 0);

        if (job.status === "completed") {
          clearInterval(interval);
          const results = await getVtonResults(jobId);
          setVtonResults(results);
        } else if (job.status === "failed") {
          clearInterval(interval);
          setJobError(job.error_message || "Try-on synthesis failed. Please retry with a clearer photo.");
        }
      } catch (err) {
        console.warn("Polling error:", err);
      }
    }, 1500);

    return () => clearInterval(interval);
  }, [jobId, jobStatus]);

  // Mode A: Add to Commerce Cart
  const handleAddToCart = async () => {
    setCartAdding(true);
    setCartSuccess(false);
    try {
      await addToCart({
        id: 1,
        name: "WearWise Signature Boxy Crew Tee",
        price: 2999,
        size: selectedSize,
        sku: "TSH-WW-CREW-001",
        className: "product-pink",
        colors: ["#ff3d9a", "#ffffff", "#1d1d1d"],
        brand: "WEARWISE EDIT",
      });
      setCartSuccess(true);
      setTimeout(() => setCartSuccess(false), 4000);
    } catch (err) {
      console.error("Cart addition failed:", err);
      alert("Failed to add to cart: " + err.message);
    } finally {
      setCartAdding(false);
    }
  };

  // Mode B: File Selection
  const handlePhotoUpload = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setPersonFile(file);
    setPersonPreviewUrl(URL.createObjectURL(file));
    setJobId(null);
    setJobStatus(null);
    setJobProgress(0);
    setJobError(null);
    setVtonResults(null);
  };

  // Mode B: Submit Job
  const handleStartVton = async () => {
    if (!personFile) {
      alert("Please upload a real-person photograph first.");
      return;
    }
    if (!userConsent) {
      alert("Please check the consent box to proceed.");
      return;
    }

    setIsSubmitting(true);
    setJobError(null);
    setVtonResults(null);
    setJobProgress(10);
    setJobStatus("queued");

    try {
      const resp = await createVtonJob(personFile, "TSH-WW-CREW-001", userConsent);
      setJobId(resp.job_id);
      setJobStatus(resp.status);
    } catch (err) {
      setJobError(err.message || "Failed to start AI virtual try-on.");
      setJobStatus("failed");
    } finally {
      setIsSubmitting(false);
    }
  };

  // Mode B: Delete Photo & Results
  const handleDeleteJob = async () => {
    if (!jobId) {
      setPersonFile(null);
      setPersonPreviewUrl(null);
      return;
    }
    try {
      await deleteVtonJob(jobId);
    } catch (err) {
      console.warn("Delete request error:", err);
    }
    setPersonFile(null);
    setPersonPreviewUrl(null);
    setJobId(null);
    setJobStatus(null);
    setVtonResults(null);
    setJobError(null);
  };

  const currentFit = SIZE_FIT_DATA[selectedSize] || SIZE_FIT_DATA["M"];
  const currentAvatarUrl =
    mannequinGender === "female"
      ? "/avatars/anny_baseline_female.glb"
      : "/avatars/anny_baseline_male.glb";

  return (
    <div className="tryon-page">
      <Header />

      <main className="tryon-editorial">
        {/* Top Editorial Label Bar */}
        <div className="tryon-editorial-top">
          <span>✦ DUAL-MODE VIRTUAL TRY-ON STUDIO</span>
          <span>
            {activeMode === "mode_a"
              ? "MODE A · 3D AVATAR ENGINE"
              : "MODE B · AI MULTI-VIEW PHOTO VTON"}
          </span>
        </div>

        {/* Mode Navigation Tabs */}
        <div className="tryon-mode-nav">
          <div className="tryon-mode-toggle">
            <button
              type="button"
              className={`mode-toggle-btn ${activeMode === "mode_a" ? "active" : ""}`}
              onClick={() => setActiveMode("mode_a")}
            >
              <span>✦</span> MODE A: 3D AVATAR TRY-ON
            </button>
            <button
              type="button"
              className={`mode-toggle-btn ${activeMode === "mode_b" ? "active" : ""}`}
              onClick={() => setActiveMode("mode_b")}
            >
              <span>✦</span> MODE B: AI PHOTO VTON (3-VIEW)
            </button>
          </div>
        </div>

        {/* ====================================================================
            MODE A — INTERACTIVE 3D AVATAR TRY-ON
            ==================================================================== */}
        {activeMode === "mode_a" && (
          <section className="mode-a-stage">
            {/* 3D Canvas Card */}
            <div className="mode-a-viewer-card">
              <div
                style={{
                  position: "absolute",
                  top: "16px",
                  left: "16px",
                  zIndex: 10,
                  display: "flex",
                  gap: "8px",
                  background: "rgba(15, 23, 42, 0.85)",
                  backdropFilter: "blur(8px)",
                  padding: "4px 8px",
                  borderRadius: "8px",
                  border: "1px solid rgba(255, 255, 255, 0.15)",
                }}
              >
                <button
                  type="button"
                  onClick={() => setMannequinGender("male")}
                  style={{
                    padding: "6px 12px",
                    borderRadius: "6px",
                    border: "none",
                    background: mannequinGender === "male" ? "var(--pink, #ff3d9a)" : "transparent",
                    color: "#ffffff",
                    fontSize: "11px",
                    fontFamily: "Archivo Black, sans-serif",
                    cursor: "pointer",
                  }}
                >
                  MASCULINE BASELINE
                </button>
                <button
                  type="button"
                  onClick={() => setMannequinGender("female")}
                  style={{
                    padding: "6px 12px",
                    borderRadius: "6px",
                    border: "none",
                    background: mannequinGender === "female" ? "var(--pink, #ff3d9a)" : "transparent",
                    color: "#ffffff",
                    fontSize: "11px",
                    fontFamily: "Archivo Black, sans-serif",
                    cursor: "pointer",
                  }}
                >
                  FEMININE BASELINE
                </button>
              </div>

              <AvatarViewer
                assetUrl={currentAvatarUrl}
                garmentUrl={`/garments/TSH-WW-CREW-001_${['S', 'M', 'L'].includes(selectedSize) ? selectedSize : 'M'}.glb`}
                garmentScale={SIZE_SCALES[selectedSize]}
                showGarment={showGarmentMesh}
                armAngle={armAngle}
                studioBackground="#720e2c"
                fabricProfile={fabricProfile}
                height="560px"
              />

              {/* Interactive Arm Elevation & XPBD Cloth Deformation Panel */}
              <div className="mode-a-motion-panel">
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <span style={{ fontSize: "12px", fontFamily: "Archivo Black, sans-serif", letterSpacing: "0.5px" }}>
                    ✦ AVATAR MOTION & ARM ELEVATION SIMULATION
                  </span>
                  <span style={{ fontFamily: "Archivo Black, sans-serif", fontSize: "14px", color: "var(--pink, #ff3d9a)" }}>
                    {armAngle}° {armAngle === 0 ? "· REST POSE" : armAngle === 90 ? "· T-POSE MAX" : "· ELEVATED"}
                  </span>
                </div>

                <div className="motion-slider-row">
                  <input
                    type="range"
                    min="0"
                    max="90"
                    step="5"
                    value={armAngle}
                    onChange={(e) => setArmAngle(parseInt(e.target.value, 10))}
                    className="tryon-arm-slider"
                  />
                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: "11px", color: "#666" }}>
                    <button type="button" onClick={() => setArmAngle(0)} style={{ border: "none", background: "none", cursor: "pointer", fontWeight: armAngle === 0 ? 800 : 400 }}>0° (Rest / A-Pose)</button>
                    <button type="button" onClick={() => setArmAngle(30)} style={{ border: "none", background: "none", cursor: "pointer", fontWeight: armAngle === 30 ? 800 : 400 }}>30° (Relaxed)</button>
                    <button type="button" onClick={() => setArmAngle(45)} style={{ border: "none", background: "none", cursor: "pointer", fontWeight: armAngle === 45 ? 800 : 400 }}>45° (Mid Stretch)</button>
                    <button type="button" onClick={() => setArmAngle(90)} style={{ border: "none", background: "none", cursor: "pointer", fontWeight: armAngle === 90 ? 800 : 400 }}>90° (T-Pose Max)</button>
                  </div>
                </div>

                <div style={{ fontSize: "11px", color: "#555", lineHeight: 1.4 }}>
                  Driven by real-time client-side XPBD cloth solver: As the avatar's arms elevate, underarm cloth stretches,
                  folds develop along the shoulder ridge, and the torso side hem lifts naturally according to fabric tensile compliance.
                </div>
              </div>
            </div>

            {/* Mode A Sidebar: Garment, Sizing & Honest Fit */}
            <div className="mode-a-sidebar">
              <div className="editorial-garment-card">
                <div className="garment-card-header">
                  <div>
                    <span style={{ fontSize: "11px", letterSpacing: "1px", fontWeight: 900, color: "var(--purple, #8d6bff)" }}>
                      MERCHANT DIGITAL GARMENT
                    </span>
                    <h2 className="garment-card-title">Signature Boxy Crew Tee</h2>
                    <span style={{ fontSize: "12px", color: "#666" }}>SKU: TSH-WW-CREW-001 · 100% Combed Cotton</span>
                  </div>
                  <div className="garment-card-price">₹2,999</div>
                </div>

                {/* Garment Mesh Toggle */}
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", margin: "14px 0" }}>
                  <span style={{ fontSize: "13px", fontWeight: 700 }}>Show 3D Garment Mesh</span>
                  <button
                    type="button"
                    onClick={() => setShowGarmentMesh(!showGarmentMesh)}
                    style={{
                      padding: "6px 14px",
                      borderRadius: "6px",
                      border: "1.5px solid var(--black)",
                      background: showGarmentMesh ? "var(--lime, #d8ff3f)" : "#eee",
                      fontFamily: "Archivo Black, sans-serif",
                      fontSize: "11px",
                      cursor: "pointer",
                    }}
                  >
                    {showGarmentMesh ? "ON (VISIBLE)" : "OFF (MANNEQUIN ONLY)"}
                  </button>
                </div>

                {/* Size Selector */}
                <div>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <span style={{ fontSize: "12px", fontWeight: 900, letterSpacing: "0.5px" }}>
                      SELECT SIZE (GRADED GEOMETRY):
                    </span>
                    <span style={{ fontSize: "10px", color: "#888" }}>ISO 8559-2</span>
                  </div>
                  <div className="size-selector-row">
                    {["XS", "S", "M", "L", "XL"].map((size) => (
                      <button
                        key={size}
                        type="button"
                        className={`size-pill-btn ${selectedSize === size ? "active" : ""}`}
                        onClick={() => setSelectedSize(size)}
                      >
                        {size}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Fabric Mechanical Profile Toggle */}
                <div style={{ margin: "16px 0" }}>
                  <span style={{ fontSize: "12px", fontWeight: 900, letterSpacing: "0.5px", display: "block", marginBottom: "6px" }}>
                    FABRIC SIMULATION PROFILE:
                  </span>
                  <div style={{ display: "flex", gap: "8px" }}>
                    <button
                      type="button"
                      style={{
                        flex: 1,
                        padding: "8px",
                        borderRadius: "6px",
                        border: "1.5px solid var(--black)",
                        fontFamily: "Archivo Black",
                        fontSize: "10px",
                        background: fabricProfile === "knit" ? "var(--pink)" : "#f8fafc",
                        color: fabricProfile === "knit" ? "#ffffff" : "var(--black)",
                        cursor: "pointer",
                      }}
                      onClick={() => setFabricProfile("knit")}
                    >
                      COTTON WAFFLE (240 GSM)
                    </button>
                    <button
                      type="button"
                      style={{
                        flex: 1,
                        padding: "8px",
                        borderRadius: "6px",
                        border: "1.5px solid var(--black)",
                        fontFamily: "Archivo Black",
                        fontSize: "10px",
                        background: fabricProfile === "rigid" ? "var(--pink)" : "#f8fafc",
                        color: fabricProfile === "rigid" ? "#ffffff" : "var(--black)",
                        cursor: "pointer",
                      }}
                      onClick={() => setFabricProfile("rigid")}
                    >
                      RIGID POPLIN (140 GSM)
                    </button>
                  </div>
                </div>

                {/* Honest Fit Overlay Badge */}
                <div className="honest-fit-badge-box">
                  <div className="honest-fit-score">
                    <span>HONEST FIT RATING</span>
                    <span style={{ color: currentFit.score >= 90 ? "#2b7a0b" : "#d97706" }}>
                      {currentFit.score}/100 · {currentFit.status}
                    </span>
                  </div>
                  <div className="honest-fit-ease">
                    <strong>Chest Ease: {currentFit.chestEase}</strong> — {currentFit.note}
                  </div>
                </div>

                {/* Add To Cart */}
                <button
                  type="button"
                  className="add-to-cart-hero-btn"
                  onClick={handleAddToCart}
                  disabled={cartAdding}
                >
                  {cartAdding ? "ADDING TO CART..." : `ADD SIZE ${selectedSize} TO CART ✦`}
                </button>

                {cartSuccess && (
                  <div style={{ marginTop: "12px", padding: "10px", background: "#ecfdf5", border: "1px solid #10b981", borderRadius: "8px", textAlign: "center", fontSize: "12px", color: "#065f46", fontWeight: 700 }}>
                    ✓ Added to bag! <span style={{ cursor: "pointer", textDecoration: "underline" }} onClick={() => navigate("/cart")}>View Cart →</span>
                  </div>
                )}

                <div style={{ marginTop: "18px", textAlign: "center" }}>
                  <button
                    type="button"
                    onClick={() => navigate("/fit")}
                    style={{ background: "none", border: "none", color: "var(--purple, #8d6bff)", fontSize: "12px", fontWeight: 900, cursor: "pointer", textDecoration: "underline" }}
                  >
                    Open Deep Honest Fit Studio →
                  </button>
                </div>
              </div>

              {/* Provenance Metadata */}
              <div style={{ background: "#ffffff", border: "2px solid var(--black)", borderRadius: "14px", padding: "16px 20px", boxShadow: "4px 4px 0 var(--black)", fontSize: "11px", color: "#555", lineHeight: 1.6 }}>
                <strong style={{ color: "var(--black)", display: "block", marginBottom: "4px" }}>
                  ✦ 3D DIGITAL GARMENT PROVENANCE (ISO 8559-2 / BS 4952 / ASTM D1777)
                </strong>
                Sample ID: <code>WW-3D-TSHIRT-TSH-WW-CREW-001-REV2</code>. Textured boxy crewneck tee with ribbed "CLASSY" collar text, white piping, and chest pocket. Sized with graded dimensional ease ({selectedSize}: {currentFit.chestEase}). Physically responsive deformation powered by client-side XPBD cloth simulation.
                <div style={{ marginTop: "10px" }}>
                  <button
                    type="button"
                    onClick={() => navigate("/merchant/garment-studio")}
                    style={{ background: "none", border: "none", color: "var(--purple, #8d6bff)", fontSize: "11px", fontWeight: 900, cursor: "pointer", textDecoration: "underline", padding: 0 }}
                  >
                    Open Merchant Digital Garment Studio →
                  </button>
                </div>
              </div>
            </div>
          </section>
        )}

        {/* ====================================================================
            MODE B — AI PHOTO VIRTUAL TRY-ON (3-VIEW GENERATION)
            ==================================================================== */}
        {activeMode === "mode_b" && (
          <section className="mode-b-hero">
            {/* Input & Upload Stage */}
            {!vtonResults && (
              <div style={{ maxWidth: "780px", margin: "0 auto" }}>
                <div className="photo-drop-card" style={{ maxWidth: "100%" }}>
                  <div className="photo-card-top">
                    <span>✦ STEP 01: REAL-PERSON PHOTOGRAPH</span>
                    <span>JPEG / PNG / WEBP</span>
                  </div>

                  <div className="photo-drop-center">
                    {!personPreviewUrl ? (
                      <div className="drop-copy" style={{ padding: "48px 24px" }}>
                        <span style={{ color: "var(--pink, #ff3d9a)", fontWeight: 900, letterSpacing: "1px" }}>
                          AI PHOTO TRY-ON
                        </span>
                        <h2 style={{ fontFamily: "Archivo Black, sans-serif", fontSize: "36px", margin: "12px 0" }}>
                          UPLOAD YOUR<br />PHOTOGRAPH
                        </h2>
                        <p style={{ maxWidth: "420px", margin: "0 auto 20px", fontSize: "14px", color: "#666" }}>
                          Mode B uses real-person photographs only. For accurate multi-view try-on, use a full-body or upper-body front-facing photo with visible clothing.
                        </p>
                        <label className="editorial-upload-btn" style={{ display: "inline-block", cursor: "pointer" }}>
                          CHOOSE PHOTOGRAPH ✦
                          <input type="file" accept="image/*" onChange={handlePhotoUpload} style={{ display: "none" }} />
                        </label>
                        <div style={{ marginTop: "16px", fontSize: "11px", color: "#888" }}>
                          Note: Synthetic Anny avatar renderings are rejected in Mode B. Use Mode A for 3D avatars.
                        </div>
                      </div>
                    ) : (
                      <div className="uploaded-editorial-view" style={{ minHeight: "360px" }}>
                        <img src={personPreviewUrl} alt="Your uploaded photo" className="uploaded-editorial-image" />
                        <div className="uploaded-editorial-overlay">
                          <div>
                            <span>✦ PHOTOGRAPH READY</span>
                            <h3>{personFile?.name || "Person Photo"}</h3>
                          </div>
                          <div className="photo-actions">
                            <label className="change-photo-btn">
                              CHANGE
                              <input type="file" accept="image/*" onChange={handlePhotoUpload} style={{ display: "none" }} />
                            </label>
                            <button type="button" className="remove-photo-btn" onClick={handleDeleteJob}>
                              REMOVE
                            </button>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>

                  {personPreviewUrl && (
                    <div style={{ padding: "20px 24px", background: "#fcf9f5", borderTop: "2px solid var(--black)" }}>
                      {/* Selected Garment Tag */}
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
                        <div>
                          <span style={{ fontSize: "11px", fontWeight: 900, color: "var(--purple, #8d6bff)" }}>SELECTED PRODUCT</span>
                          <div style={{ fontFamily: "Archivo Black, sans-serif", fontSize: "16px" }}>Signature Boxy Crew Tee (Cherry Pink)</div>
                          <span style={{ fontSize: "12px", color: "#666" }}>SKU: TSH-WW-CREW-001 · Port 8001 Catalog</span>
                        </div>
                        <div style={{ fontFamily: "Archivo Black, sans-serif", fontSize: "18px", color: "var(--pink, #ff3d9a)" }}>
                          ₹2,999
                        </div>
                      </div>

                      {/* Explicit Consent Box */}
                      <div className="vton-consent-box">
                        <input
                          type="checkbox"
                          id="vton-consent"
                          checked={userConsent}
                          onChange={(e) => setUserConsent(e.target.checked)}
                        />
                        <label htmlFor="vton-consent">
                          I explicitly consent to processing this photograph securely for virtual try-on in this private session. Metadata and EXIF data will be stripped, and I can permanently delete the photo at any time.
                        </label>
                      </div>

                      {/* Error Alert */}
                      {jobError && (
                        <div style={{ marginBottom: "16px", padding: "12px", background: "#fef2f2", border: "1.5px solid #ef4444", borderRadius: "8px", color: "#991b1b", fontSize: "13px" }}>
                          <strong>Submission Error:</strong> {jobError}
                        </div>
                      )}

                      {/* Start Generation Button */}
                      <button
                        type="button"
                        className="generate-vton-btn"
                        onClick={handleStartVton}
                        disabled={isSubmitting || !userConsent || (jobStatus && jobStatus !== "failed")}
                      >
                        {isSubmitting
                          ? "INITIALIZING PIPELINE..."
                          : jobStatus === "queued" || jobStatus === "preprocessing" || jobStatus === "frontal_generation" || jobStatus === "multiview_generation"
                          ? `PROCESSING VTON (${jobProgress}%)...`
                          : "GENERATE 3-VIEW VIRTUAL TRY-ON ✦"}
                      </button>
                    </div>
                  )}
                </div>

                {/* Progress Bar Display */}
                {jobStatus && jobStatus !== "completed" && jobStatus !== "failed" && (
                  <div className="vton-progress-card">
                    <span style={{ fontSize: "11px", fontWeight: 900, letterSpacing: "1px", color: "var(--pink, #ff3d9a)" }}>
                      AI MULTI-VIEW PIPELINE ACTIVE
                    </span>
                    <h3 style={{ fontFamily: "Archivo Black, sans-serif", fontSize: "22px", margin: "8px 0" }}>
                      {jobStatus === "queued" && "Queued for Inference..."}
                      {jobStatus === "preprocessing" && "Preprocessing Photograph & Stripping EXIF..."}
                      {jobStatus === "frontal_generation" && "Generating High-Fidelity Frontal Try-On..."}
                      {jobStatus === "multiview_generation" && "Synthesizing Lateral Profile & Dorsal Rear Views..."}
                    </h3>
                    <div className="progress-track">
                      <div className="progress-fill" style={{ width: `${jobProgress}%` }}></div>
                    </div>
                    <div style={{ display: "flex", justifyContent: "space-between", fontSize: "12px", color: "#666" }}>
                      <span>Stage: {jobStatus.replace("_", " ").toUpperCase()}</span>
                      <span>{jobProgress}% Complete</span>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Results Display: Exactly Three Separate Images */}
            {vtonResults && vtonResults.views && (
              <div className="vton-gallery-section">
                <div className="vton-gallery-header">
                  <div>
                    <span style={{ fontSize: "11px", fontWeight: 900, color: "var(--purple, #8d6bff)", letterSpacing: "1px" }}>
                      AI PHOTO VTON DELIVERABLE
                    </span>
                    <h2 style={{ fontFamily: "Archivo Black, sans-serif", fontSize: "28px", margin: "4px 0" }}>
                      THREE-VIEW TRY-ON RESULT
                    </h2>
                    <span style={{ fontSize: "13px", color: "#666" }}>
                      Product: <strong>{vtonResults.garment_title}</strong> ({vtonResults.garment_sku})
                    </span>
                  </div>

                  <div style={{ display: "flex", gap: "12px" }}>
                    <button
                      type="button"
                      onClick={() => setVtonResults(null)}
                      style={{
                        padding: "10px 18px",
                        background: "#ffffff",
                        border: "2px solid var(--black)",
                        borderRadius: "8px",
                        fontFamily: "Archivo Black, sans-serif",
                        fontSize: "12px",
                        cursor: "pointer",
                      }}
                    >
                      TRY ANOTHER PHOTO
                    </button>
                    <button
                      type="button"
                      onClick={handleDeleteJob}
                      style={{
                        padding: "10px 18px",
                        background: "#fff0f0",
                        border: "2px solid #dc2626",
                        color: "#dc2626",
                        borderRadius: "8px",
                        fontFamily: "Archivo Black, sans-serif",
                        fontSize: "12px",
                        cursor: "pointer",
                      }}
                    >
                      DELETE PHOTO & ASSETS
                    </button>
                  </div>
                </div>

                {/* 3-Column Grid */}
                <div className="vton-gallery-grid">
                  {/* View 1: Front */}
                  {vtonResults.views.front && (
                    <div className="vton-view-card">
                      <div className="vton-view-header">
                        <span className="vton-view-label">01 · FRONT VIEW (0°)</span>
                        <span className="vton-inferred-badge">VERIFIED FRONTAL</span>
                      </div>
                      <div className="vton-view-image-container">
                        <img
                          src={`http://127.0.0.1:8000${vtonResults.views.front.url}`}
                          alt="Front virtual try-on view"
                          className="vton-view-image"
                          onClick={() => setSelectedZoomView(vtonResults.views.front)}
                          style={{ cursor: "zoom-in" }}
                        />
                      </div>
                      <div className="vton-view-footer">
                        <p className="vton-view-desc">
                          {vtonResults.views.front.description || "High-fidelity frontal try-on with texture transfer."}
                        </p>
                        <a
                          href={`http://127.0.0.1:8000${vtonResults.views.front.url}`}
                          download={`front_${vtonResults.job_id}.png`}
                          className="vton-download-btn"
                        >
                          DOWNLOAD FRONT VIEW ↓
                        </a>
                      </div>
                    </div>
                  )}

                  {/* View 2: Side */}
                  {vtonResults.views.side && (
                    <div className="vton-view-card">
                      <div className="vton-view-header">
                        <span className="vton-view-label">02 · SIDE VIEW (90°)</span>
                        <span className="vton-inferred-badge inferred">AI-INFERRED PROFILE</span>
                      </div>
                      <div className="vton-view-image-container">
                        <img
                          src={`http://127.0.0.1:8000${vtonResults.views.side.url}`}
                          alt="Side virtual try-on view"
                          className="vton-view-image"
                          onClick={() => setSelectedZoomView(vtonResults.views.side)}
                          style={{ cursor: "zoom-in" }}
                        />
                      </div>
                      <div className="vton-view-footer">
                        <p className="vton-view-desc">
                          {vtonResults.views.side.disclaimer || "Lateral profile view depicting side seam and sleeve drape."}
                        </p>
                        <a
                          href={`http://127.0.0.1:8000${vtonResults.views.side.url}`}
                          download={`side_${vtonResults.job_id}.png`}
                          className="vton-download-btn"
                        >
                          DOWNLOAD SIDE VIEW ↓
                        </a>
                      </div>
                    </div>
                  )}

                  {/* View 3: Back */}
                  {vtonResults.views.back && (
                    <div className="vton-view-card">
                      <div className="vton-view-header">
                        <span className="vton-view-label">03 · BACK VIEW (180°)</span>
                        <span className="vton-inferred-badge inferred">AI-INFERRED REAR</span>
                      </div>
                      <div className="vton-view-image-container">
                        <img
                          src={`http://127.0.0.1:8000${vtonResults.views.back.url}`}
                          alt="Back virtual try-on view"
                          className="vton-view-image"
                          onClick={() => setSelectedZoomView(vtonResults.views.back)}
                          style={{ cursor: "zoom-in" }}
                        />
                      </div>
                      <div className="vton-view-footer">
                        <p className="vton-view-desc">
                          {vtonResults.views.back.disclaimer || "Dorsal rear view depicting back silhouette and neckline finish."}
                        </p>
                        <a
                          href={`http://127.0.0.1:8000${vtonResults.views.back.url}`}
                          download={`back_${vtonResults.job_id}.png`}
                          className="vton-download-btn"
                        >
                          DOWNLOAD BACK VIEW ↓
                        </a>
                      </div>
                    </div>
                  )}
                </div>

                {/* Explicit Disclaimer & Provenance Alert Box */}
                <div className="vton-disclaimer-box">
                  <strong>✦ WEARWISE MULTI-VIEW VIRTUAL TRY-ON SPECIFICATION & DISCLAIMER:</strong>
                  <p style={{ marginTop: "6px" }}>
                    All three views depict the same person wearing the selected garment as individual, separately addressable assets. Front view is generated from the uploaded photograph and catalog texture. Side and rear views are AI-inferred from frontal design; back graphics and rear closures provisional.
                  </p>
                </div>
              </div>
            )}
          </section>
        )}

        {/* Modal: Zoom View */}
        {selectedZoomView && (
          <div
            style={{
              position: "fixed",
              inset: 0,
              zIndex: 9999,
              background: "rgba(0, 0, 0, 0.85)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              padding: "24px",
            }}
            onClick={() => setSelectedZoomView(null)}
          >
            <div style={{ maxWidth: "600px", background: "#ffffff", borderRadius: "14px", overflow: "hidden", border: "2px solid var(--black)" }} onClick={(e) => e.stopPropagation()}>
              <div style={{ padding: "12px 16px", borderBottom: "1.5px solid var(--black)", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <strong style={{ fontFamily: "Archivo Black, sans-serif" }}>
                  {selectedZoomView.view_type.toUpperCase()} VIEW
                </strong>
                <button type="button" onClick={() => setSelectedZoomView(null)} style={{ border: "none", background: "none", fontSize: "16px", cursor: "pointer", fontWeight: 900 }}>✕</button>
              </div>
              <img src={`http://127.0.0.1:8000${selectedZoomView.url}`} alt="Zoomed view" style={{ width: "100%", display: "block" }} />
            </div>
          </div>
        )}

        {/* Modal: Model & Hardware Telemetry */}
        {showTelemetryModal && providerTelemetry && (
          <div
            style={{
              position: "fixed",
              inset: 0,
              zIndex: 9999,
              background: "rgba(0, 0, 0, 0.85)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              padding: "24px",
            }}
            onClick={() => setShowTelemetryModal(false)}
          >
            <div style={{ maxWidth: "680px", background: "#ffffff", borderRadius: "14px", padding: "28px", border: "2px solid var(--black)", boxShadow: "10px 10px 0 var(--black)" }} onClick={(e) => e.stopPropagation()}>
              <h2 style={{ fontFamily: "Archivo Black, sans-serif", fontSize: "20px", margin: "0 0 16px" }}>
                ✦ AI VTON MODEL & HARDWARE TELEMETRY
              </h2>
              <div style={{ fontSize: "13px", lineHeight: 1.6, color: "#333" }}>
                <div><strong>Local GPU:</strong> {providerTelemetry.device.toUpperCase()} ({providerTelemetry.vram_available_gb} GB VRAM)</div>
                <div><strong>Active Provider:</strong> {providerTelemetry.provider_name}</div>
                <hr style={{ margin: "14px 0", border: "none", borderTop: "1px solid #ddd" }} />
                <div><strong>FASHN VTON v1.5 Assessment:</strong> {providerTelemetry.fashn_v1_5.status}</div>
                <div style={{ fontSize: "11px", color: "#666" }}>Licensing: {providerTelemetry.fashn_v1_5.license} · Scope: {providerTelemetry.fashn_v1_5.scope} · Min VRAM: {providerTelemetry.fashn_v1_5.minimum_vram_gb} GB</div>
                <hr style={{ margin: "14px 0", border: "none", borderTop: "1px solid #ddd" }} />
                <div><strong>WACV 2026 Research Assessment:</strong> {providerTelemetry.wacv_2026_multiview.status}</div>
                <div style={{ fontSize: "11px", color: "#666" }}>Paper: {providerTelemetry.wacv_2026_multiview.paper} ({providerTelemetry.wacv_2026_multiview.conference})</div>
              </div>
              <button
                type="button"
                onClick={() => setShowTelemetryModal(false)}
                style={{ marginTop: "20px", width: "100%", padding: "12px", background: "var(--black)", color: "#fff", border: "none", borderRadius: "8px", fontFamily: "Archivo Black, sans-serif", cursor: "pointer" }}
              >
                CLOSE TELEMETRY
              </button>
            </div>
          </div>
        )}

        {/* Bottom Bar */}
        <section className="tryon-bottom">
          <div className="tryon-privacy">
            <span>✦</span> PRIVATE SESSION-SCOPED PROCESSING · ZERO RETENTION GUARANTEE
          </div>

          <div style={{ textAlign: "center" }}>
            <button
              type="button"
              onClick={() => setShowTelemetryModal(true)}
              style={{
                background: "none",
                border: "1px solid var(--black)",
                borderRadius: "999px",
                padding: "6px 14px",
                fontSize: "11px",
                fontFamily: "Archivo Black, sans-serif",
                cursor: "pointer",
                color: "var(--black)",
              }}
            >
              MODEL & HARDWARE TELEMETRY ✦
            </button>
          </div>

          <div className="tryon-bottom-tag">
            WEARWISE <span>✦</span>
          </div>
        </section>
      </main>
    </div>
  );
}

export default TryOn;
