import { useEffect, useMemo, useState } from 'react';
import { StatusBadge } from '../components/StatusBadge';
import {
  Card,
  CardHeader,
  Empty,
  Eyebrow,
  PageHeader,
  formatTime,
} from '../components/primitives';
import { api } from '../services/api';
import type { ServiceRequest, User } from '../types';

interface Props {
  apiKey: string;
  user: User | null;
}

export function Dashboard({ apiKey, user }: Props) {
  const [requests, setRequests] = useState<ServiceRequest[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!apiKey) return;
    const endpoint =
      user?.role === 'employee'
        ? api.listMyRequests(apiKey)
        : api.listRequests(apiKey);
    endpoint
      .then((page) => setRequests(page.items))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [apiKey, user]);

  const total = requests.length;
  const newCount = requests.filter((r) => r.status === 'NEW').length;
  const inProgress = requests.filter((r) => r.status === 'IN_PROGRESS').length;
  const done = requests.filter((r) => r.status === 'DONE').length;

  const recent = useMemo(
    () =>
      [...requests]
        .sort(
          (a, b) =>
            new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime(),
        )
        .slice(0, 6),
    [requests],
  );

  const today = new Date().toLocaleDateString('ru-RU', {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
  });
  const firstName = user?.full_name?.split(' ')[0] ?? '';

  return (
    <div className="sf-page">
      <PageHeader
        title="Обзор"
        subtitle={
          <>
            Привет, {firstName} · {today}
          </>
        }
      />

      <div className="sf-stats">
        <StatCard label="Всего" value={loading ? '…' : total} />
        <StatCard label="Новые" value={loading ? '…' : newCount} />
        <StatCard label="В работе" value={loading ? '…' : inProgress} />
        <StatCard label="Завершены" value={loading ? '…' : done} />
      </div>

      <Card>
        <CardHeader title="Последние заявки" subtitle="Обновлено только что" />
        {loading ? (
          <Empty>Загрузка…</Empty>
        ) : recent.length === 0 ? (
          <Empty>Заявок пока нет — всё спокойно.</Empty>
        ) : (
          <RequestTable rows={recent} />
        )}
      </Card>
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: number | string }) {
  return (
    <div className="sf-stat">
      <Eyebrow>{label}</Eyebrow>
      <div className="sf-stat__value">{value}</div>
    </div>
  );
}

export function RequestTable({ rows }: { rows: ServiceRequest[] }) {
  return (
    <table className="sf-table">
      <thead>
        <tr>
          <th style={{ width: 76 }}>ID</th>
          <th>Название</th>
          <th style={{ width: 130 }}>Статус</th>
          <th style={{ width: 140 }}>Обновлена</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((r) => (
          <tr key={r.id}>
            <td className="sf-td--mono">#{r.id}</td>
            <td>
              <div className="sf-row-title">{r.title}</div>
              {r.description ? (
                <div className="sf-row-sub">{r.description}</div>
              ) : null}
            </td>
            <td>
              <StatusBadge status={r.status} />
            </td>
            <td className="sf-td--muted">{formatTime(r.updated_at)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
