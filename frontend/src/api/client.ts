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
    } else {
      // In development mode, use Bearer shorthand with UUID
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

export class WearWiseApiClient {
  private baseUrl: string;
  private authProvider: AuthHeaderProvider;

  constructor(baseUrl?: string, authProvider?: AuthHeaderProvider) {
    // If not supplied, prefer empty string (relative to vite proxy) or localhost:8000
    this.baseUrl = baseUrl ?? (import.meta.env?.VITE_API_BASE_URL !== undefined ? import.meta.env.VITE_API_BASE_URL : 'http://127.0.0.1:8000');
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

    const response = await fetch(url, {
      ...options,
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
    return this.request<BodyProfile>(`/api/v1/profiles/${profileId}/controls`, {
      method: 'PUT',
      body: JSON.stringify(payload),
    });
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

    const response = await fetch(url, { headers });
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
}

// Global default singleton client
export const apiClient = new WearWiseApiClient();
