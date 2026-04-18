/**
 * Типизированный HTTP-клиент ServiceFlow.
 *
 *   - Единая обработка RFC 7807 Problem Details → бросает ApiError.
 *   - Валидация ответов через zod — гарантия контракта на границе.
 *   - Прокидывает X-API-Key и Idempotency-Key (когда передан).
 *   - Возвращает payload после schema.parse(..) — никаких `any` наружу.
 */

import { z } from 'zod';
import {
  ApiKeyRotatedSchema,
  ProblemDetailsSchema,
  ServiceRequestSchema,
  UserCreatedSchema,
  UserSchema,
  pageSchemaOf,
  type ApiKeyRotated,
  type Page,
  type ProblemDetails,
  type RequestStatus,
  type ServiceRequest,
  type User,
  type UserCreated,
  type UserRole,
} from '../types';

const API_BASE = (import.meta.env.VITE_API_BASE as string | undefined) ?? '/api/v1';

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly problem: ProblemDetails,
  ) {
    super(problem.detail || problem.title);
  }

  get code(): string {
    return this.problem.code;
  }

  get requestId(): string | undefined {
    return this.problem.request_id;
  }
}

interface RequestOpts {
  apiKey?: string;
  method?: string;
  body?: unknown;
  idempotencyKey?: string;
  ifMatch?: string;
}

async function fetchJson<T>(
  path: string,
  schema: z.ZodType<T>,
  opts: RequestOpts = {},
): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  };
  if (opts.apiKey) headers['X-API-Key'] = opts.apiKey;
  if (opts.idempotencyKey) headers['Idempotency-Key'] = opts.idempotencyKey;
  if (opts.ifMatch) headers['If-Match'] = opts.ifMatch;

  const res = await fetch(`${API_BASE}${path}`, {
    method: opts.method ?? 'GET',
    headers,
    body: opts.body !== undefined ? JSON.stringify(opts.body) : undefined,
  });

  if (!res.ok) {
    // Парсим Problem Details, если сервер вернул его; иначе собираем минимальный.
    const raw = await res.text();
    let problem: ProblemDetails;
    try {
      const parsed = ProblemDetailsSchema.safeParse(JSON.parse(raw));
      problem = parsed.success
        ? parsed.data
        : {
            type: 'about:blank',
            title: res.statusText || 'Error',
            status: res.status,
            detail: raw || `HTTP ${res.status}`,
            instance: path,
            code: 'unknown_error',
          };
    } catch {
      problem = {
        type: 'about:blank',
        title: res.statusText || 'Error',
        status: res.status,
        detail: raw || `HTTP ${res.status}`,
        instance: path,
        code: 'unknown_error',
      };
    }
    throw new ApiError(res.status, problem);
  }

  if (res.status === 204) {
    return undefined as unknown as T;
  }

  const data = await res.json();
  return schema.parse(data);
}

function uuid(): string {
  // Вписываемся в современные браузеры без полифилов.
  return crypto.randomUUID();
}

// ============================================================================
// Публичные методы API
// ============================================================================

export const api = {
  // -------- users --------
  getMe: (apiKey: string): Promise<User> =>
    fetchJson('/users/me', UserSchema, { apiKey }),

  listUsers: (apiKey: string, limit = 50, offset = 0): Promise<Page<User>> =>
    fetchJson(
      `/users?limit=${limit}&offset=${offset}`,
      pageSchemaOf(UserSchema),
      { apiKey },
    ),

  createUser: (
    apiKey: string,
    payload: { full_name: string; email: string },
  ): Promise<UserCreated> =>
    fetchJson('/users', UserCreatedSchema, {
      apiKey,
      method: 'POST',
      body: payload,
    }),

  updateUserRole: (apiKey: string, userId: number, role: UserRole): Promise<User> =>
    fetchJson(`/users/${userId}/role`, UserSchema, {
      apiKey,
      method: 'PATCH',
      body: { role },
    }),

  rotateMyApiKey: (apiKey: string): Promise<ApiKeyRotated> =>
    fetchJson('/users/me/api-key/rotate', ApiKeyRotatedSchema, {
      apiKey,
      method: 'POST',
    }),

  // -------- requests --------
  listRequests: (
    apiKey: string,
    query: Record<string, string | number | undefined> = {},
  ): Promise<Page<ServiceRequest>> => {
    const qs = Object.entries(query)
      .filter(([, v]) => v !== undefined && v !== '')
      .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(String(v))}`)
      .join('&');
    const path = `/requests${qs ? `?${qs}` : ''}`;
    return fetchJson(path, pageSchemaOf(ServiceRequestSchema), { apiKey });
  },

  listMyRequests: (apiKey: string): Promise<Page<ServiceRequest>> =>
    fetchJson('/requests/my', pageSchemaOf(ServiceRequestSchema), { apiKey }),

  listQueue: (apiKey: string): Promise<Page<ServiceRequest>> =>
    fetchJson('/requests/queue', pageSchemaOf(ServiceRequestSchema), { apiKey }),

  getRequest: (apiKey: string, id: number): Promise<ServiceRequest> =>
    fetchJson(`/requests/${id}`, ServiceRequestSchema, { apiKey }),

  createRequest: (
    apiKey: string,
    payload: { title: string; description?: string; assignee_id?: number },
    idempotencyKey: string = uuid(),
  ): Promise<ServiceRequest> =>
    fetchJson('/requests', ServiceRequestSchema, {
      apiKey,
      method: 'POST',
      body: payload,
      idempotencyKey,
    }),

  updateStatus: (
    apiKey: string,
    requestId: number,
    payload: { status: RequestStatus; assignee_id?: number; comment?: string },
    opts: { ifMatch?: string } = {},
  ): Promise<ServiceRequest> =>
    fetchJson(`/requests/${requestId}/status`, ServiceRequestSchema, {
      apiKey,
      method: 'PATCH',
      body: payload,
      ifMatch: opts.ifMatch,
    }),
};
