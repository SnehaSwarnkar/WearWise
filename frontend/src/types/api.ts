/**
 * WearWise Canonical API TypeScript Definitions
 * Directly reflects OpenAPI 3.1.0 backend schema and domain models.
 */

// -----------------------------------------------------------------------------
// Standard Error Envelope
// -----------------------------------------------------------------------------
export interface ApiErrorDetail {
  loc?: (string | number)[];
  msg?: string;
  type?: string;
  field?: string;
  reason?: string;
}

export interface ApiErrorEnvelope {
  error: {
    code: string;
    message: string;
    status_code: number;
    timestamp?: string;
    details?: ApiErrorDetail[];
  };
}

// -----------------------------------------------------------------------------
// Semantic Body Shape Controls
// -----------------------------------------------------------------------------
export interface BodyShapeControls {
  shoulder_width: number;
  chest_fullness: number;
  belly_fullness: number;
  waist_definition: number;
  arm_fullness: number;
  hip_fullness: number;
  thigh_fullness: number;
  calf_fullness: number;
}

export interface ControlDefinition {
  min: number;
  max: number;
  step?: number;
  default: number;
  description: string;
  anatomical_region: string;
}

export type ControlDefinitionMap = Record<keyof BodyShapeControls, ControlDefinition>;

// -----------------------------------------------------------------------------
// Anthropometric Body Measurements
// -----------------------------------------------------------------------------
export interface BodyMeasurement {
  value_cm: number;
  acquisition_method: 'user_reported' | 'geometry_extracted' | 'derived' | 'fixture_calibrated';
  validation_state: 'validated' | 'unvalidated' | 'flagged_plausibility';
  lifecycle_status: 'active' | 'superseded' | 'disputed';
  assessment_state: 'eligible' | 'provisional' | 'unassessed';
  tolerance_cm: number;
}

export type ActiveMeasurementsMap = Record<string, BodyMeasurement>;

export interface MeasurementHistoryItem {
  revision_number: number;
  created_at: string;
  measurements: Record<string, { value_cm: number; acquisition_method: string }>;
}

// -----------------------------------------------------------------------------
// Shopper Body Profiles & Revisions
// -----------------------------------------------------------------------------
export interface BodyProfile {
  profile_id: string;
  user_id: string;
  current_revision: number;
  avatar_name?: string | null;
  body_shape?: string | null;
  age_range?: string | null;
  presentation_gender: 'masculine' | 'feminine' | 'neutral';
  stature_cm: number;
  reported_weight_kg: number | null;
  active_measurements: ActiveMeasurementsMap;
  shape_controls: BodyShapeControls;
  latest_asset_url: string | null;
  created_at: string;
  updated_at: string;
}

export interface ProfileCreateRequest {
  presentation_gender: 'masculine' | 'feminine' | 'neutral';
  stature_cm: number;
  reported_weight_kg?: number | null;
  avatar_name?: string | null;
  body_shape?: string | null;
  age_range?: string | null;
  initial_controls?: Partial<BodyShapeControls>;
}

export interface ProfileUpdateRequest {
  presentation_gender?: 'masculine' | 'feminine' | 'neutral';
  stature_cm?: number;
  reported_weight_kg?: number | null;
  avatar_name?: string | null;
  body_shape?: string | null;
  age_range?: string | null;
}

export interface UpdateControlsRequest {
  expected_revision: number;
  controls: Partial<BodyShapeControls>;
}

export interface ProfileRevisionSummary {
  revision_number: number;
  created_at: string;
  measurement_count: number;
  has_controls: boolean;
}

// -----------------------------------------------------------------------------
// 3D Avatar Generation & Assets
// -----------------------------------------------------------------------------
export interface AvatarGenerateRequest {
  profile_id: string;
  pose?: string;
  format?: 'glb';
  rigged?: boolean;
}

export interface AvatarGenerationResponse {
  avatar_id: string;
  profile_id: string;
  profile_revision?: number;
  asset_url?: string;
  format: 'glb' | string;
  size_bytes: number;
  sha256_checksum: string;
  is_valid_manifold: boolean;
  vertex_count: number;
  triangle_count?: number;
  extracted_measurements?: Record<string, any>;
  extracted_measurements_count?: number;
  generation_duration_ms: number;
}

export interface AvatarStatusResponse {
  avatar_id: string;
  profile_id: string;
  is_valid_manifold: boolean;
  vertex_count: number;
  sha256_checksum: string;
  format: string;
  size_bytes: number;
}

// -----------------------------------------------------------------------------
// Merchant Garment Catalog & Specifications
// -----------------------------------------------------------------------------
export interface FabricProperties {
  fibre_composition: Record<string, number>;
  mechanical_stretch_pct: number;
  stretch_recovery_pct: number;
  stretch_direction: 'rigid_zero' | 'mono_weft' | 'mono_warp' | 'bi_directional';
}

export interface GarmentMeasurementInput {
  dimension_code: string;
  value_cm: number;
  tolerance_cm?: number;
  measurement_procedure?: string;
  provenance?: string;
}

export interface GarmentSizeCreateRequest {
  size_label: string;
  sort_order: number;
  measurements: GarmentMeasurementInput[];
}

export interface GarmentSizeResponse {
  size_label: string;
  sort_order: number;
  measurements: Record<string, number>;
}

export interface GarmentProfile {
  garment_id: string;
  brand_id: string;
  sku: string;
  title: string;
  category: string;
  current_revision: number;
  fabric_properties: FabricProperties;
  sizes: GarmentSizeResponse[];
  created_at: string;
}

export interface GarmentCreateRequest {
  sku: string;
  title: string;
  category: string;
  fabric_properties: FabricProperties;
}

// -----------------------------------------------------------------------------
// Honest Fit Evaluation & Recommendations
// -----------------------------------------------------------------------------
export interface FitEvaluationRequest {
  profile_id: string;
  garment_id: string;
  user_fit_preference: 'fitted' | 'regular' | 'relaxed';
}

export interface RegionalFitComparison {
  region: string;
  body_measurement_cm: number;
  garment_dimension_cm: number;
  ease_cm: number;
  classification: 'compression' | 'snug' | 'fitted' | 'regular' | 'relaxed' | 'oversized';
  explanation: string;
}

export interface AlternativeSizeInfo {
  size_label: string;
  fit_summary: string;
}

export interface FitRecommendationResponse {
  recommendation_id: string;
  garment_id: string;
  recommended_size: string;
  composite_fit_score: number;
  status: 'recommended' | 'alternative' | 'wearable_deviation' | 'rejected';
  alternative_size?: AlternativeSizeInfo | null;
  regional_comparisons: RegionalFitComparison[];
  disclaimer?: string;
}

export interface RecentRecommendationItem {
  recommendation_id: string;
  garment_id: string;
  recommended_size: string;
  composite_fit_score: number;
  status: string;
  alternative_size?: AlternativeSizeInfo | null;
  rulebook_version: string;
  evaluated_at: string;
}

// -----------------------------------------------------------------------------
// Auth & Principal Contracts
// -----------------------------------------------------------------------------
export type PrincipalType = 'user' | 'brand';

export interface AuthPrincipal {
  id: string;
  type: PrincipalType;
  token?: string;
  isDev: boolean;
}
