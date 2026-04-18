import { useEffect, useState } from 'react';
import { api } from '../services/api';
import { StatusBadge } from '../components/StatusBadge';
import type { ServiceRequest, RequestStatus, User } from '../types';

interface Props { apiKey: string; user: User | null; }

const STATUSES: { value: RequestStatus | ''; label: string }[] = [
  { value: '',            label: 'Все' },
  { value: 'NEW',         label: 'Новые' },
  { value: 'IN_PROGRESS', label: 'В работе' },
  { value: 'DONE',        label: 'Готово' },
  { value: 'CANCELED',    label: 'Отменены' },
];

export function Requests({ apiKey, user }: Props) {
  const [requests, setRequests] = useState<ServiceRequest[]>([]);
  const [filter, setFilter]     = useState<RequestStatus | ''>('');
  const [loading, setLoading]   = useState(true);
  const [updating, setUpdating] = useState<number | null>(null);

  const load = () => {
    setLoading(true);
    const q = filter ? { request_status: filter } : {};
    api.listRequests(apiKey, q)
      .then((page) => setRequests(page.items))
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(() => { if (apiKey) load(); }, [apiKey, filter]);

  const changeStatus = async (r: ServiceRequest, status: RequestStatus) => {
    setUpdating(r.id);
    try {
      const updated = await api.updateStatus(apiKey, r.id, { status });
      setRequests(prev => prev.map(x => x.id === r.id ? updated : x));
    } finally {
      setUpdating(null);
    }
  };

  const canChange = user?.role === 'admin' || user?.role === 'agent';

  return (
    <div className="page fade-in">
      <div className="page-header">
        <div>
          <div className="page-title">Все заявки</div>
          <div className="page-subtitle">{requests.length} заявок</div>
        </div>
      </div>

      <div className="filter-bar">
        {STATUSES.map(s => (
          <button
            key={s.value}
            className={`filter-btn${filter === s.value ? ' active' : ''}`}
            onClick={() => setFilter(s.value)}
          >
            {s.label}
          </button>
        ))}
      </div>

      <div className="card">
        {loading ? (
          <div className="empty"><div className="text-muted">Загрузка…</div></div>
        ) : requests.length === 0 ? (
          <div className="empty">
            <div className="empty-icon">◈</div>
            Заявок нет
          </div>
        ) : (
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Название</th>
                <th>Статус</th>
                <th>Создана</th>
                {canChange && <th>Действие</th>}
              </tr>
            </thead>
            <tbody>
              {requests.map(r => (
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
                  {canChange && (
                    <td>
                      <select
                        className="input"
                        style={{ padding: '5px 10px', fontSize: 12 }}
                        value={r.status}
                        disabled={updating === r.id}
                        onChange={e => changeStatus(r, e.target.value as RequestStatus)}
                      >
                        <option value="NEW">Новая</option>
                        <option value="IN_PROGRESS">В работе</option>
                        <option value="DONE">Готово</option>
                        <option value="CANCELED">Отменена</option>
                      </select>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
