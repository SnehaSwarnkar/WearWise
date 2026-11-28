/**
 * Centralized WearWise API Client
 * Communicates with FastAPI backend, handling Bearer auth, private binary assets, and typed errors.
 */

import {
  ApiErrorEnvelope,
  BodyProfile,
  ProfileCreateRequest,
  ProfileUpdateRequest,
  UpdateControlsRequest,
  ProfileRevisionSummary,
  ActiveMeasurementsMap,
  ControlDefinitionMap,
  AvatarGenerateRequest,
  AvatarGenerationResponse,
  AvatarStatusResponse,
  GarmentProfile,
  GarmentCreateRequest,
  GarmentSizeCreateRequest,
  FitEvaluationRequest,
  FitRecommendationResponse,
  RecentRecommendationItem,
} from '../types/api';

export class ApiClientError extends Error {
  public code: string;
  public statusCode: number;
  public details: any[];

  constructor(code: string, message: string, statusCode: number, details: any[] = []) {
    super(message);
    this.name = 'ApiClientError';
    this.code = code;
    this.statusCode = statusCode;
    this.details = details;
  }
}

// Replaceable authentication header provider
export interface AuthHeaderProvider {
  getAuthHeaders(): Record<string, string>;
}

// Default dev auth provider
class DefaultDevAuthHeaderProvider implements AuthHeaderProvider {
  private token: string | null = null;
  private devUserId: string = 'c1f7a28e-8e3b-48d9-a791-03f4439c1b3e';
  private devBrandId: string = 'e4d9b2a1-5f3c-4b8a-9e1d-8f7a6b5c4d3e';
  private role: 'user' | 'brand' = 'user';

  public setToken(token: string | null) {
    this.token = token;
  }

  public setDevRole(role: 'user' | 'brand', customId?: string) {
    this.role = role;
    if (customId) {
      if (role === 'user') this.devUserId = customId;
      else this.devBrandId = customId;
    }
  }

  public getDevId(): string {
    return this.role === 'user' ? this.devUserId : this.devBrandId;
  }

  public getRole(): 'user' | 'brand' {
    return this.role;
  }

  public getAuthHeaders(): Record<string, string> {
    const headers: Record<string, string> = {};
    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    } else if (!getCsrfToken()) {
      // Only use dev shorthand headers when there is no active HTTP-only cookie session
      const principalId = this.role === 'user' ? this.devUserId : this.devBrandId;
      headers['Authorization'] = `Bearer ${principalId}`;
      if (this.role === 'user') {
        headers['X-User-Id'] = this.devUserId;
      } else {
        headers['X-Brand-Id'] = this.devBrandId;
      }
    }
    return headers;
  }
}

export const devAuthHeaderProvider = new DefaultDevAuthHeaderProvider();

// ── Cookie & CSRF helpers ────────────────────────────────────────────────────
export function getCsrfToken(): string | null {
  if (typeof document === 'undefined') return null;
  const match = document.cookie.match(/(?:^|;\s*)ww_csrf_token=([^;]+)/);
  return match ? decodeURIComponent(match[1]) : null;
}

export function getStoreApiBase(): string {
  if (typeof window !== 'undefined' && ['3000', '4173', '4174', '4175', '5173'].includes(window.location.port)) {
    return '';
  }
  return import.meta.env?.VITE_STORE_API_URL || 'http://127.0.0.1:8001';
}

export function getBodyApiBase(): string {
  if (typeof window !== 'undefined' && ['3000', '4173', '4174', '4175', '5173'].includes(window.location.port)) {
    return '';
  }
  return (
    import.meta.env?.VITE_BODY_API_URL ||
    import.meta.env?.VITE_API_URL ||
    import.meta.env?.VITE_API_BASE_URL ||
    'http://127.0.0.1:8000'
  );
}

// ── Store API Support (for Commerce endpoints on Port 8001) ─────────────────
export const STORE_API_BASE = getStoreApiBase();

export function getSessionId(): string {
  let id = sessionStorage.getItem('ww-session-id');
  if (!id) {
    id = 'sess_' + Math.random().toString(36).slice(2, 11);
    sessionStorage.setItem('ww-session-id', id);
  }
  return id;
}

async function storeRequest(method: string, path: string, body: any = null, isFormData: boolean = false, customHeaders: Record<string, string> = {}) {
  const headers: Record<string, string> = { ...customHeaders };
  if (body && !isFormData) {
    headers['Content-Type'] = 'application/json';
  }
  if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(method.toUpperCase())) {
    const csrf = getCsrfToken();
    if (csrf && !headers['X-CSRF-Token']) {
      headers['X-CSRF-Token'] = csrf;
    }
  }

  const res = await fetch(`${getStoreApiBase()}${path}`, {
    method,
    headers,
    credentials: 'include',
    body: body
      ? isFormData
        ? body
        : JSON.stringify(body)
      : undefined,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Request failed');
  }

  return res.json();
}

export const api = {
  get: (path: string, headers: Record<string, string> = {}) => storeRequest('GET', path, null, false, headers),
  post: (path: string, body: any, headers: Record<string, string> = {}) => storeRequest('POST', path, body, false, headers),
  put: (path: string, body: any, headers: Record<string, string> = {}) => storeRequest('PUT', path, body, false, headers),
  patch: (path: string, body: any, headers: Record<string, string> = {}) => storeRequest('PATCH', path, body, false, headers),
  delete: (path: string, headers: Record<string, string> = {}) => storeRequest('DELETE', path, null, false, headers),
  form: (path: string, formData: FormData, headers: Record<string, string> = {}) => storeRequest('POST', path, formData, true, headers),
};

export class WearWiseApiClient {
  private baseUrl: string;
  private authProvider: AuthHeaderProvider;

  constructor(baseUrl?: string, authProvider?: AuthHeaderProvider) {
    this.baseUrl = baseUrl ?? getBodyApiBase();
    this.authProvider = authProvider ?? devAuthHeaderProvider;
  }

  public setAuthProvider(provider: AuthHeaderProvider) {
    this.authProvider = provider;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...this.authProvider.getAuthHeaders(),
      ...(options.headers as Record<string, string> || {}),
    };
    const method = (options.method || 'GET').toUpperCase();
    if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(method)) {
      const csrf = getCsrfToken();
      if (csrf && !headers['X-CSRF-Token']) {
        headers['X-CSRF-Token'] = csrf;
      }
    }

    const response = await fetch(url, {
      ...options,
      credentials: options.credentials ?? 'include',
      headers,
    });

    if (!response.ok) {
      let code = 'HTTP_ERROR';
      let message = `Request failed with status ${response.status}`;
      let details: any[] = [];

      try {
        const errorJson: ApiErrorEnvelope | any = await response.json();
        if (errorJson.error) {
          code = errorJson.error.code || code;
          message = errorJson.error.message || message;
          details = errorJson.error.details || [];
        } else if (errorJson.detail) {
          if (typeof errorJson.detail === 'string') {
            message = errorJson.detail;
          } else if (typeof errorJson.detail === 'object') {
            code = errorJson.detail.code || code;
            message = errorJson.detail.message || message;
            details = errorJson.detail.details || [];
          }
        }
      } catch {
        // Non-JSON error body
        const text = await response.text().catch(() => '');
        if (text) message = text;
      }

      throw new ApiClientError(code, message, response.status, details);
    }

    if (response.status === 204) {
      return {} as T;
    }

    return response.json();
  }

  // ---------------------------------------------------------------------------
  // Health
  // ---------------------------------------------------------------------------
  public async checkHealth(): Promise<{ status: string; version?: string }> {
    return this.request<{ status: string }>('/health');
  }

  // ---------------------------------------------------------------------------
  // Body Profiles & Revisions
  // ---------------------------------------------------------------------------
  public async listProfiles(): Promise<BodyProfile[]> {
    return this.request<BodyProfile[]>('/api/v1/profiles');
  }

  public async getProfile(profileId: string): Promise<BodyProfile> {
    return this.request<BodyProfile>(`/api/v1/profiles/${profileId}`);
  }

  public async createProfile(payload: ProfileCreateRequest): Promise<BodyProfile> {
    return this.request<BodyProfile>('/api/v1/profiles', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  public async updateProfile(profileId: string, payload: ProfileUpdateRequest): Promise<BodyProfile> {
    return this.request<BodyProfile>(`/api/v1/profiles/${profileId}`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    });
  }

  public async getProfileRevisions(profileId: string): Promise<{ profile_id: string; revisions: ProfileRevisionSummary[] }> {
    return this.request<{ profile_id: string; revisions: ProfileRevisionSummary[] }>(`/api/v1/profiles/${profileId}/revisions`);
  }

  public async getActiveMeasurements(profileId: string): Promise<{ profile_id: string; measurements: ActiveMeasurementsMap }> {
    return this.request<{ profile_id: string; measurements: ActiveMeasurementsMap }>(`/api/v1/profiles/${profileId}/measurements`);
  }

  public async getControlDefinitions(): Promise<{ safe_ranges: ControlDefinitionMap }> {
    return this.request<{ safe_ranges: ControlDefinitionMap }>('/api/v1/controls/definitions');
  }

  public async updateControls(profileId: string, payload: UpdateControlsRequest): Promise<BodyProfile> {
    const res = await this.request<any>(`/api/v1/profiles/${profileId}/controls`, {
      method: 'PUT',
      body: JSON.stringify(payload),
    });
    return {
      ...res,
      current_revision: res.current_revision ?? res.new_revision,
      shape_controls: res.shape_controls ?? res.controls,
    } as BodyProfile;
  }

  // ---------------------------------------------------------------------------
  // 3D Avatar Generation & Assets
  // ---------------------------------------------------------------------------
  public async generateAvatar(payload: AvatarGenerateRequest): Promise<AvatarGenerationResponse> {
    return this.request<AvatarGenerationResponse>('/api/v1/avatar/generate', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  public async getAvatarStatus(avatarId: string): Promise<AvatarStatusResponse> {
    return this.request<AvatarStatusResponse>(`/api/v1/avatar/${avatarId}/status`);
  }

  /**
   * Fetches binary GLB model using authenticated Bearer credentials.
   * Returns ArrayBuffer directly for Three.js GLTFLoader.parse().
   */
  public async fetchGlbArrayBuffer(avatarId: string): Promise<ArrayBuffer> {
    const url = `${this.baseUrl}/api/v1/avatar/assets/${avatarId}.glb`;
    const headers = {
      ...this.authProvider.getAuthHeaders(),
    };

    const response = await fetch(url, {
      headers,
      credentials: 'include',
    });
    if (!response.ok) {
      throw new ApiClientError('GLB_FETCH_FAILED', `Failed to load 3D GLB asset (${response.status})`, response.status);
    }
    return response.arrayBuffer();
  }

  // ---------------------------------------------------------------------------
  // Merchant Garments
  // ---------------------------------------------------------------------------
  public async listGarments(): Promise<GarmentProfile[]> {
    return this.request<GarmentProfile[]>('/api/v1/garments');
  }

  public async getGarment(garmentId: string): Promise<GarmentProfile> {
    return this.request<GarmentProfile>(`/api/v1/garments/${garmentId}`);
  }

  public async createGarment(payload: GarmentCreateRequest): Promise<GarmentProfile> {
    return this.request<GarmentProfile>('/api/v1/garments', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  public async addGarmentSize(garmentId: string, payload: GarmentSizeCreateRequest): Promise<{ garment_id: string; size_id: string; size_label: string; dimension_count: number }> {
    return this.request<{ garment_id: string; size_id: string; size_label: string; dimension_count: number }>(`/api/v1/garments/${garmentId}/sizes`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  // ---------------------------------------------------------------------------
  // Honest Fit Evaluation
  // ---------------------------------------------------------------------------
  public async evaluateFit(payload: FitEvaluationRequest): Promise<FitRecommendationResponse> {
    return this.request<FitRecommendationResponse>('/api/v1/fit/recommend', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  public async getFitRecommendation(recommendationId: string): Promise<FitRecommendationResponse> {
    return this.request<FitRecommendationResponse>(`/api/v1/fit/recommendations/${recommendationId}`);
  }

  public async listRecentFitRecommendations(profileId: string): Promise<RecentRecommendationItem[]> {
    return this.request<RecentRecommendationItem[]>(`/api/v1/fit/recommendations?profile_id=${encodeURIComponent(profileId)}`);
  }

  // ---------------------------------------------------------------------------
  // Mode B: AI Photo Virtual Try-On (VTON)
  // ---------------------------------------------------------------------------
  public async createVtonJob(file: File, garmentSku: string = 'TSH-WW-CREW-001', consent: boolean = true): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('garment_sku', garmentSku);
    formData.append('consent', consent ? 'true' : 'false');

    const authHeaders = this.authProvider.getAuthHeaders();
    const res = await fetch(`${this.baseUrl}/api/v1/try-on/vton/jobs`, {
      method: 'POST',
      headers: { ...authHeaders },
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail?.message || err.detail || 'VTON submission failed');
    }
    return res.json();
  }

  public async getVtonJob(jobId: string): Promise<any> {
    return this.request<any>(`/api/v1/try-on/vton/jobs/${jobId}`);
  }

  public async getVtonResults(jobId: string): Promise<any> {
    return this.request<any>(`/api/v1/try-on/vton/jobs/${jobId}/results`);
  }

  public async deleteVtonJob(jobId: string): Promise<any> {
    return this.request<any>(`/api/v1/try-on/vton/jobs/${jobId}`, {
      method: 'DELETE',
    });
  }

  public async getVtonProviders(): Promise<any> {
    return this.request<any>('/api/v1/try-on/vton/providers');
  }
}

// Global default singleton client
export const apiClient = new WearWiseApiClient();
