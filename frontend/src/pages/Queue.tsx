import { useEffect, useState } from 'react';
import { api } from '../services/api';
import { StatusBadge } from '../components/StatusBadge';
import type { ServiceRequest, User } from '../types';

interface Props { apiKey: string; user: User | null; }

export function Queue({ apiKey, user }: Props) {
  const [queue, setQueue]     = useState<ServiceRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [taking, setTaking]   = useState<number | null>(null);

  const load = () => {
    setLoading(true);
    api.listQueue(apiKey)
      .then((page) => setQueue(page.items))
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(() => { if (apiKey) load(); }, [apiKey]);

  const takeRequest = async (r: ServiceRequest) => {
    if (!user) return;
    setTaking(r.id);
    try {
      const updated = await api.updateStatus(apiKey, r.id, {
        status: 'IN_PROGRESS',
        assignee_id: user.id,
        comment: 'Взято в работу',
      });
      setQueue(prev => prev.filter(x => x.id !== updated.id));
    } finally {
      setTaking(null);
    }
  };

  return (
    <div className="page fade-in">
      <div className="page-header">
        <div>
          <div className="page-title">Очередь</div>
          <div className="page-subtitle">{queue.length} заявок ожидают обработки</div>
        </div>
        <button className="btn btn-ghost btn-sm" onClick={load}>⟳ Обновить</button>
      </div>

      <div className="card">
        {loading ? (
          <div className="empty"><div className="text-muted">Загрузка…</div></div>
        ) : queue.length === 0 ? (
          <div className="empty">
            <div className="empty-icon">✓</div>
            Очередь пуста — всё обработано
          </div>
        ) : (
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Название</th>
                <th>Статус</th>
                <th>Создана</th>
                <th>Действие</th>
              </tr>
            </thead>
            <tbody>
              {queue.map(r => (
                <tr key={r.id}>
                  <td className="td-mono">#{r.id}</td>
                  <td>
                    <div className="td-bold">{r.title}</div>
                    {r.description && <div className="text-muted text-sm">{r.description}</div>}
                  </td>
                  <td><StatusBadge status={r.status} /></td>
                  <td className="text-muted text-sm">
                    {new Date(r.created_at).toLocaleString('ru-RU', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' })}
                  </td>
                  <td>
                    <button
                      className="btn btn-primary btn-sm"
                      disabled={taking === r.id}
                      onClick={() => takeRequest(r)}
                    >
                      {taking === r.id ? '…' : 'Взять'}
                    </button>
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
