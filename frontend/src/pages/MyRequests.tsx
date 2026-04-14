import { useEffect, useState } from 'react';
import { api } from '../services/api';
import { StatusBadge } from '../components/StatusBadge';
import type { ServiceRequest, User } from '../types';

interface Props { apiKey: string; user: User | null; }

export function MyRequests({ apiKey, user: _user }: Props) {
  const [requests, setRequests] = useState<ServiceRequest[]>([]);
  const [loading, setLoading]   = useState(true);
  const [title, setTitle]       = useState('');
  const [desc, setDesc]         = useState('');
  const [creating, setCreating] = useState(false);
  const [error, setError]       = useState('');

  const load = () => {
    setLoading(true);
    api.listMyRequests(apiKey)
      .then((page) => setRequests(page.items))
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(() => { if (apiKey) load(); }, [apiKey]);

  const submit = async () => {
    if (!title.trim()) { setError('Введите название'); return; }
    setCreating(true);
    setError('');
    try {
      const r = await api.createRequest(apiKey, { title: title.trim(), description: desc.trim() || undefined });
      setRequests(prev => [r, ...prev]);
      setTitle('');
      setDesc('');
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Ошибка');
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="page fade-in">
      <div className="page-header">
        <div>
          <div className="page-title">Мои заявки</div>
          <div className="page-subtitle">Создавайте и отслеживайте свои запросы</div>
        </div>
      </div>

      <div className="panel">
        <div className="panel-title">Новая заявка</div>
        <div className="form-group">
          <label className="form-label">Название</label>
          <input
            className="input"
            placeholder="Опишите проблему кратко…"
            value={title}
            onChange={e => setTitle(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && submit()}
          />
        </div>
        <div className="form-group">
          <label className="form-label">Описание</label>
          <textarea
            className="input"
            placeholder="Подробности (необязательно)…"
            value={desc}
            onChange={e => setDesc(e.target.value)}
          />
        </div>
        {error && <div className="error-msg">⚠ {error}</div>}
        <button className="btn btn-primary" onClick={submit} disabled={creating}>
          {creating ? 'Создание…' : '+ Создать заявку'}
        </button>
      </div>

      <div className="card">
        <div className="card-header">
          <div className="card-title">История</div>
        </div>
        {loading ? (
          <div className="empty"><div className="text-muted">Загрузка…</div></div>
        ) : requests.length === 0 ? (
          <div className="empty">
            <div className="empty-icon">◈</div>
            У вас пока нет заявок
          </div>
        ) : (
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Название</th>
                <th>Статус</th>
                <th>Создана</th>
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
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
