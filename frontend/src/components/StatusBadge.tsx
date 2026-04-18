import type { RequestStatus, UserRole } from '../types';

const statusMap: Record<RequestStatus, { label: string; cls: string }> = {
  NEW:         { label: 'Новая',     cls: 'badge badge-new' },
  IN_PROGRESS: { label: 'В работе', cls: 'badge badge-progress' },
  DONE:        { label: 'Готово',   cls: 'badge badge-done' },
  CANCELED:    { label: 'Отменена', cls: 'badge badge-canceled' },
};

const roleMap: Record<UserRole, { label: string; cls: string }> = {
  admin:    { label: 'Admin',    cls: 'badge badge-admin' },
  agent:    { label: 'Agent',    cls: 'badge badge-agent' },
  employee: { label: 'Employee', cls: 'badge badge-employee' },
};

export function StatusBadge({ status }: { status: RequestStatus }) {
  const { label, cls } = statusMap[status] ?? { label: status, cls: 'badge' };
  return <span className={cls}>{label}</span>;
}

export function RoleBadge({ role }: { role: UserRole }) {
  const { label, cls } = roleMap[role] ?? { label: role, cls: 'badge' };
  return <span className={cls}>{label}</span>;
}
