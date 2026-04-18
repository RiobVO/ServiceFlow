import type { RequestStatus, UserRole } from '../types';

const statusMap: Record<RequestStatus, { label: string; cls: string }> = {
  NEW: { label: 'Новая', cls: 'sf-badge sf-badge--status-new' },
  IN_PROGRESS: { label: 'В работе', cls: 'sf-badge sf-badge--status-progress' },
  DONE: { label: 'Готово', cls: 'sf-badge sf-badge--status-done' },
  CANCELED: { label: 'Отменена', cls: 'sf-badge sf-badge--status-canceled' },
};

const roleMap: Record<UserRole, { label: string; cls: string }> = {
  admin: { label: 'Admin', cls: 'sf-badge sf-badge--role-admin' },
  agent: { label: 'Agent', cls: 'sf-badge sf-badge--role-agent' },
  employee: { label: 'Employee', cls: 'sf-badge sf-badge--role-employee' },
};

export function StatusBadge({ status }: { status: RequestStatus }) {
  const entry = statusMap[status];
  if (!entry) return null;
  return (
    <span className={entry.cls}>
      <span className="sf-badge__dot" aria-hidden />
      {entry.label}
    </span>
  );
}

export function RoleBadge({ role }: { role: UserRole }) {
  const entry = roleMap[role];
  if (!entry) return null;
  return <span className={entry.cls}>{entry.label}</span>;
}
