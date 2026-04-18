import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api, ApiError } from '../services/api';
import { useAuth } from '../context/AuthContext';
import type { RequestStatus } from '../types';

const KEYS = {
  me: ['me'] as const,
  users: () => ['users'] as const,
  requests: (scope: string, q: object = {}) => ['requests', scope, q] as const,
};

function requireKey(apiKey: string | null): string {
  if (!apiKey) throw new ApiError(401, {
    type: 'about:blank',
    title: 'Unauthorized',
    status: 401,
    detail: 'Нет API-ключа — залогинься заново.',
    instance: '',
    code: 'missing_api_key',
  });
  return apiKey;
}

// ---------------- users ----------------

export function useMe() {
  const { apiKey } = useAuth();
  return useQuery({
    queryKey: KEYS.me,
    queryFn: () => api.getMe(requireKey(apiKey)),
    enabled: !!apiKey,
    staleTime: 60_000,
  });
}

export function useUsers() {
  const { apiKey } = useAuth();
  return useQuery({
    queryKey: KEYS.users(),
    queryFn: () => api.listUsers(requireKey(apiKey)),
    enabled: !!apiKey,
  });
}

// ---------------- requests ----------------

export function useMyRequests() {
  const { apiKey } = useAuth();
  return useQuery({
    queryKey: KEYS.requests('my'),
    queryFn: () => api.listMyRequests(requireKey(apiKey)),
    enabled: !!apiKey,
  });
}

export function useAllRequests(query: Record<string, string | number | undefined> = {}) {
  const { apiKey } = useAuth();
  return useQuery({
    queryKey: KEYS.requests('all', query),
    queryFn: () => api.listRequests(requireKey(apiKey), query),
    enabled: !!apiKey,
  });
}

export function useQueue() {
  const { apiKey } = useAuth();
  return useQuery({
    queryKey: KEYS.requests('queue'),
    queryFn: () => api.listQueue(requireKey(apiKey)),
    enabled: !!apiKey,
  });
}

export function useCreateRequest() {
  const { apiKey } = useAuth();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: { title: string; description?: string }) =>
      api.createRequest(requireKey(apiKey), payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['requests'] });
    },
  });
}

export function useUpdateStatus() {
  const { apiKey } = useAuth();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (args: {
      id: number;
      status: RequestStatus;
      assignee_id?: number;
      comment?: string;
    }) =>
      api.updateStatus(requireKey(apiKey), args.id, {
        status: args.status,
        assignee_id: args.assignee_id,
        comment: args.comment,
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['requests'] });
    },
  });
}
