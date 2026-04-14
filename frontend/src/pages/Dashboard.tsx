import { useEffect, useState } from 'react';
import { api } from '../services/api';
import { StatusBadge } from '../components/StatusBadge';
import type { ServiceRequest, User } from '../types';

interface Props { apiKey: string; user: User | null; }

export function Dashboard({ apiKey, user }: Props) {
  const [requests, setRequests] = useState<ServiceRequest[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!apiKey) return;
    const endpoint = user?.role === 'employee'
      ? api.listMyRequests(apiKey)
      : api.listRequests(apiKey);
    endpoint
      .then((page) => setRequests(page.items))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [apiKey, user]);

  const total      = requests.length;
  const newCount   = requests.filter(r => r.status === 'NEW').length;
  const inProgress = requests.filter(r => r.status === 'IN_PROGRESS').length;
  const done       = requests.filter(r => r.status === 'DONE').length;

  const recent = [...requests]
    .sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime())
    .slice(0, 8);

  return (
    <div className="page fade-in">
      <div className="page-header">
        <div>
          <div className="page-title">Обзор</div>
          <div className="page-subtitle">
            Привет, {user?.full_name ?? '—'} · {new Date().toLocaleDateString('ru-RU', { weekday: 'long', day: 'numeric', month: 'long' })}
          </div>
        </div>
      </div>

      <div className="stats-grid">
        <div className="stat-card violet">
          <div className="stat-icon">◈</div>
          <div className="stat-value">{loading ? '…' : total}</div>
          <div className="stat-label">Всего заявок</div>
        </div>
        <div className="stat-card cyan">
          <div className="stat-icon">◎</div>
          <div className="stat-value">{loading ? '…' : newCount}</div>
          <div className="stat-label">Новые</div>
        </div>
        <div className="stat-card yellow">
          <div className="stat-icon">⟳</div>
          <div className="stat-value">{loading ? '…' : inProgress}</div>
          <div className="stat-label">В работе</div>
        </div>
        <div className="stat-card green">
          <div className="stat-icon">✓</div>
          <div className="stat-value">{loading ? '…' : done}</div>
          <div className="stat-label">Завершены</div>
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <div>
            <div className="card-title">Последние заявки</div>
            <div className="card-subtitle">Обновлено только что</div>
          </div>
        </div>
        {loading ? (
          <div className="empty"><div className="text-muted">Загрузка…</div></div>
        ) : recent.length === 0 ? (
          <div className="empty">
            <div className="empty-icon">◈</div>
            Заявок пока нет
          </div>
        ) : (
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Название</th>
                <th>Статус</th>
                <th>Обновлена</th>
              </tr>
            </thead>
            <tbody>
              {recent.map(r => (
                <tr key={r.id}>
                  <td className="td-mono">#{r.id}</td>
                  <td className="td-bold">{r.title}</td>
                  <td><StatusBadge status={r.status} /></td>
                  <td className="text-muted text-sm">
                    {new Date(r.updated_at).toLocaleString('ru-RU', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' })}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
