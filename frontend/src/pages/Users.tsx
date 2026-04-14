import { useEffect, useState } from 'react';
import { api } from '../services/api';
import { RoleBadge } from '../components/StatusBadge';
import type { User, UserRole } from '../types';

interface Props { apiKey: string; }

export function Users({ apiKey }: Props) {
  const [users, setUsers]     = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [name, setName]       = useState('');
  const [email, setEmail]     = useState('');
  const [creating, setCreating] = useState(false);
  const [error, setError]     = useState('');
  const [newUserKey, setNewUserKey] = useState<string | null>(null);

  const load = () => {
    setLoading(true);
    api.listUsers(apiKey)
      .then((page) => setUsers(page.items))
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(() => { if (apiKey) load(); }, [apiKey]);

  const createUser = async () => {
    if (!name.trim() || !email.trim()) { setError('Заполните все поля'); return; }
    setCreating(true);
    setError('');
    setNewUserKey(null);
    try {
      const u = await api.createUser(apiKey, { full_name: name.trim(), email: email.trim() });
      setUsers(prev => [...prev, u]);
      setNewUserKey(u.api_key ?? null);
      setName('');
      setEmail('');
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Ошибка');
    } finally {
      setCreating(false);
    }
  };

  const changeRole = async (userId: number, role: UserRole) => {
    try {
      const updated = await api.updateUserRole(apiKey, userId, role);
      setUsers(prev => prev.map(u => u.id === userId ? updated : u));
    } catch {}
  };

  return (
    <div className="page fade-in">
      <div className="page-header">
        <div>
          <div className="page-title">Пользователи</div>
          <div className="page-subtitle">{users.length} в системе</div>
        </div>
      </div>

      <div className="panel">
        <div className="panel-title">Добавить пользователя</div>
        <div className="row">
          <div className="form-group">
            <label className="form-label">Имя</label>
            <input className="input" placeholder="Иван Иванов" value={name} onChange={e => setName(e.target.value)} />
          </div>
          <div className="form-group">
            <label className="form-label">Email</label>
            <input className="input" type="email" placeholder="user@company.com" value={email} onChange={e => setEmail(e.target.value)} />
          </div>
          <div style={{ display: 'flex', alignItems: 'flex-end' }}>
            <button className="btn btn-primary" onClick={createUser} disabled={creating}>
              {creating ? '…' : '+ Добавить'}
            </button>
          </div>
        </div>
        {error && <div className="error-msg">⚠ {error}</div>}
        {newUserKey && (
          <div style={{ background: 'rgba(16,185,129,0.1)', border: '1px solid rgba(16,185,129,0.3)', borderRadius: 8, padding: '12px 16px' }}>
            <div style={{ fontSize: 12, color: 'var(--green)', fontWeight: 600, marginBottom: 6 }}>✓ Пользователь создан. Сохрани API-ключ:</div>
            <code style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 12, color: 'var(--text)', wordBreak: 'break-all' }}>{newUserKey}</code>
          </div>
        )}
      </div>

      <div className="card">
        {loading ? (
          <div className="empty"><div className="text-muted">Загрузка…</div></div>
        ) : (
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Имя</th>
                <th>Email</th>
                <th>Роль</th>
                <th>Статус</th>
                <th>Изменить роль</th>
              </tr>
            </thead>
            <tbody>
              {users.map(u => (
                <tr key={u.id}>
                  <td className="td-mono">#{u.id}</td>
                  <td className="td-bold">{u.full_name}</td>
                  <td className="text-muted text-sm">{u.email}</td>
                  <td><RoleBadge role={u.role} /></td>
                  <td>
                    <span className={`badge ${u.is_active ? 'badge-done' : 'badge-canceled'}`}>
                      {u.is_active ? 'Активен' : 'Отключён'}
                    </span>
                  </td>
                  <td>
                    <select
                      className="input"
                      style={{ padding: '5px 10px', fontSize: 12 }}
                      value={u.role}
                      onChange={e => changeRole(u.id, e.target.value as UserRole)}
                    >
                      <option value="admin">Admin</option>
                      <option value="agent">Agent</option>
                      <option value="employee">Employee</option>
                    </select>
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
