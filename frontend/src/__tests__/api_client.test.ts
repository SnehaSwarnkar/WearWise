import { describe, it, expect, vi, beforeEach } from 'vitest';
import { WearWiseApiClient, ApiClientError, devAuthHeaderProvider } from '../api/client';

describe('WearWiseApiClient & Dev Auth Boundary', () => {
  beforeEach(() => {
    devAuthHeaderProvider.setToken(null);
    devAuthHeaderProvider.setDevRole('user', 'c1f7a28e-8e3b-48d9-a791-03f4439c1b3e');
  });

  it('attaches default shopper Bearer header in dev mode', () => {
    const headers = devAuthHeaderProvider.getAuthHeaders();
    expect(headers['Authorization']).toBe('Bearer c1f7a28e-8e3b-48d9-a791-03f4439c1b3e');
    expect(headers['X-User-Id']).toBe('c1f7a28e-8e3b-48d9-a791-03f4439c1b3e');
  });

  it('switches to merchant brand principal and updates headers', () => {
    devAuthHeaderProvider.setDevRole('brand', 'e4d9b2a1-5f3c-4b8a-9e1d-8f7a6b5c4d3e');
    const headers = devAuthHeaderProvider.getAuthHeaders();
    expect(headers['Authorization']).toBe('Bearer e4d9b2a1-5f3c-4b8a-9e1d-8f7a6b5c4d3e');
    expect(headers['X-Brand-Id']).toBe('e4d9b2a1-5f3c-4b8a-9e1d-8f7a6b5c4d3e');
  });

  it('prioritizes explicit JWT token over dev shorthand when set', () => {
    devAuthHeaderProvider.setToken('test.jwt.token');
    const headers = devAuthHeaderProvider.getAuthHeaders();
    expect(headers['Authorization']).toBe('Bearer test.jwt.token');
  });

  it('correctly maps standard error envelope on 401 Unauthorized', async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 401,
      json: async () => ({
        error: {
          code: 'CREDENTIALS_REQUIRED',
          message: 'Authentication required. Provide a valid Bearer token.',
          status_code: 401,
          details: [],
        },
      }),
    });
    globalThis.fetch = mockFetch;

    const client = new WearWiseApiClient('http://localhost:8000', devAuthHeaderProvider);

    await expect(client.listProfiles()).rejects.toThrow('Authentication required. Provide a valid Bearer token.');
  });

  it('correctly maps 403 Forbidden ownership violation error', async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 403,
      json: async () => ({
        error: {
          code: 'OWNERSHIP_VIOLATION',
          message: 'Access denied: You do not own this profile.',
          status_code: 403,
        },
      }),
    });
    globalThis.fetch = mockFetch;

    const client = new WearWiseApiClient('http://localhost:8000', devAuthHeaderProvider);

    try {
      await client.getProfile('11111111-2222-3333-4444-555555555555');
      expect.fail('Should have thrown ApiClientError');
    } catch (err: any) {
      expect(err).toBeInstanceOf(ApiClientError);
      expect(err.code).toBe('OWNERSHIP_VIOLATION');
      expect(err.statusCode).toBe(403);
    }
  });
});
