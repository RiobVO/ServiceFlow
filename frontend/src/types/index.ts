import { z } from 'zod';

// ============================================================================
// Базовые enum'ы — синхронизированы с Pydantic-схемами бэка.
// При несоответствии — Zod упадёт с понятной ошибкой, а не отдаст мусор наверх.
// ============================================================================

export const UserRoleSchema = z.enum(['admin', 'agent', 'employee']);
export type UserRole = z.infer<typeof UserRoleSchema>;

export const RequestStatusSchema = z.enum(['NEW', 'IN_PROGRESS', 'DONE', 'CANCELED']);
export type RequestStatus = z.infer<typeof RequestStatusSchema>;

// ============================================================================
// Users
// ============================================================================

export const UserSchema = z.object({
  id: z.number().int(),
  full_name: z.string(),
  email: z.string().email(),
  is_active: z.boolean(),
  role: UserRoleSchema,
  created_at: z.string(),
  api_key_last4: z.string().nullable().optional(),
});
export type User = z.infer<typeof UserSchema>;

export const UserCreatedSchema = UserSchema.extend({
  api_key: z.string(),
});
export type UserCreated = z.infer<typeof UserCreatedSchema>;

export const ApiKeyRotatedSchema = z.object({
  api_key: z.string(),
  api_key_last4: z.string(),
});
export type ApiKeyRotated = z.infer<typeof ApiKeyRotatedSchema>;

// ============================================================================
// Requests
// ============================================================================

export const ServiceRequestSchema = z.object({
  id: z.number().int(),
  public_id: z.string(),
  title: z.string(),
  description: z.string().nullable().optional(),
  status: RequestStatusSchema,
  created_by_user_id: z.number().int(),
  assigned_to_user_id: z.number().int().nullable().optional(),
  created_at: z.string(),
  updated_at: z.string(),
});
export type ServiceRequest = z.infer<typeof ServiceRequestSchema>;

// ============================================================================
// Pagination envelope
// ============================================================================

export function pageSchemaOf<T extends z.ZodTypeAny>(item: T) {
  return z.object({
    items: z.array(item),
    total: z.number().int().nonnegative(),
    limit: z.number().int().positive(),
    offset: z.number().int().nonnegative(),
    has_next: z.boolean(),
  });
}

export type Page<T> = {
  items: T[];
  total: number;
  limit: number;
  offset: number;
  has_next: boolean;
};

// ============================================================================
// RFC 7807 Problem Details
// ============================================================================

export const ProblemDetailsSchema = z.object({
  type: z.string(),
  title: z.string(),
  status: z.number().int(),
  detail: z.string(),
  instance: z.string(),
  code: z.string(),
  request_id: z.string().optional(),
  errors: z.unknown().optional(),
});
export type ProblemDetails = z.infer<typeof ProblemDetailsSchema>;
