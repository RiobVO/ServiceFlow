import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { api, ApiError } from '../services/api';

describe('api client', () => {
  const originalFetch = globalThis.fetch;

  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn());
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    globalThis.fetch = originalFetch;
  });

  it('parses User response with zod', async () => {
    (fetch as unknown as ReturnType<typeof vi.fn>).mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          id: 1,
          full_name: 'X',
          email: 'x@example.com',
          is_active: true,
          role: 'admin',
          created_at: '2026-04-18T00:00:00',
          api_key_last4: 'abcd',
        }),
        { status: 200, headers: { 'Content-Type': 'application/json' } },
      ),
    );
    const u = await api.getMe('key');
    expect(u.email).toBe('x@example.com');
  });

  it('throws ApiError with parsed problem details on 4xx', async () => {
    (fetch as unknown as ReturnType<typeof vi.fn>).mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          type: 'https://example/errors/missing_api_key',
          title: 'Unauthorized',
          status: 401,
          detail: 'Требуется API-ключ',
          instance: '/users/me',
          code: 'missing_api_key',
          request_id: 'rid-1',
        }),
        { status: 401, headers: { 'Content-Type': 'application/problem+json' } },
      ),
    );
    try {
      await api.getMe('');
      expect.fail('should have thrown');
    } catch (err) {
      expect(err).toBeInstanceOf(ApiError);
      if (err instanceof ApiError) {
        expect(err.status).toBe(401);
        expect(err.code).toBe('missing_api_key');
        expect(err.requestId).toBe('rid-1');
      }
    }
  });

  it('falls back to synthetic problem on non-JSON errors', async () => {
    (fetch as unknown as ReturnType<typeof vi.fn>).mockResolvedValueOnce(
      new Response('not json', { status: 500 }),
    );
    try {
      await api.getMe('x');
      expect.fail('should have thrown');
    } catch (err) {
      expect(err).toBeInstanceOf(ApiError);
      if (err instanceof ApiError) {
        expect(err.status).toBe(500);
        expect(err.code).toBe('unknown_error');
      }
    }
  });
});
