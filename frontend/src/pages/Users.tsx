import { useEffect, useState } from 'react';
import { Check, Plus } from 'lucide-react';
import { RoleBadge } from '../components/StatusBadge';
import {
  Avatar,
  Button,
  Card,
  ErrorMessage,
  Field,
  Input,
  PageHeader,
  Select,
} from '../components/primitives';
import { api, ApiError } from '../services/api';
import type { User, UserRole } from '../types';

interface Props {
  apiKey: string;
}

export function Users({ apiKey }: Props) {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [newUserKey, setNewUserKey] = useState<string | null>(null);

  const load = () => {
    setLoading(true);
    api
      .listUsers(apiKey)
      .then((page) => setUsers(page.items))
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    if (apiKey) load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [apiKey]);

  const createUser = async () => {
    if (!name.trim() || !email.trim()) {
      setError('Заполните все поля.');
      return;
    }
    setCreating(true);
    setError(null);
    setNewUserKey(null);
    try {
      const u = await api.createUser(apiKey, {
        full_name: name.trim(),
        email: email.trim(),
      });
      setUsers((prev) => [...prev, u]);
      setNewUserKey(u.api_key);
      setName('');
      setEmail('');
    } catch (err) {
      const msg = err instanceof ApiError ? err.problem.detail : 'Не удалось создать пользователя.';
      setError(msg);
    } finally {
      setCreating(false);
    }
  };

  const changeRole = async (userId: number, role: UserRole) => {
    try {
      const updated = await api.updateUserRole(apiKey, userId, role);
      setUsers((prev) => prev.map((u) => (u.id === userId ? updated : u)));
    } catch {
      /* no-op */
    }
  };

  return (
    <div className="sf-page">
      <PageHeader title="Пользователи" subtitle={`${users.length} в системе`} />

      <Card elevated>
        <div className="sf-card__body">
          <div
            className="sf-serif"
            style={{
              fontSize: 18,
              fontWeight: 500,
              color: 'var(--sf-ink)',
              letterSpacing: '-0.005em',
              marginBottom: 14,
            }}
          >
            Добавить пользователя
          </div>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: '1fr 1fr auto',
              gap: 12,
              alignItems: 'flex-end',
            }}
          >
            <Field label="Имя">
              <Input
                placeholder="Иван Иванов"
                value={name}
                onChange={(e) => setName(e.target.value)}
              />
            </Field>
            <Field label="Email">
              <Input
                type="email"
                placeholder="user@company.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </Field>
            <Button icon={Plus} onClick={createUser} disabled={creating}>
              {creating ? '…' : 'Добавить'}
            </Button>
          </div>
          {error ? (
            <div style={{ marginTop: 12 }}>
              <ErrorMessage>{error}</ErrorMessage>
            </div>
          ) : null}
          {newUserKey ? (
            <div className="sf-callout sf-callout--success">
              <div className="sf-callout__title">
                <Check size={14} strokeWidth={1.5} />
                Пользователь создан. Сохраните API-ключ — больше он не покажется.
              </div>
              <code className="sf-callout__code">{newUserKey}</code>
            </div>
          ) : null}
        </div>
      </Card>

      <Card>
        {loading ? (
          <div className="sf-empty">
            <div className="sf-empty__text">Загрузка…</div>
          </div>
        ) : (
          <table className="sf-table">
            <thead>
              <tr>
                <th style={{ width: 60 }}>ID</th>
                <th>Имя</th>
                <th>Email</th>
                <th style={{ width: 110 }}>Роль</th>
                <th style={{ width: 110 }}>Статус</th>
                <th style={{ width: 140 }}>Изменить роль</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id}>
                  <td className="sf-td--mono">#{u.id}</td>
                  <td>
                    <div
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 10,
                      }}
                    >
                      <Avatar name={u.full_name} size={26} />
                      <span className="sf-row-title">{u.full_name}</span>
                    </div>
                  </td>
                  <td className="sf-td--muted">{u.email}</td>
                  <td>
                    <RoleBadge role={u.role} />
                  </td>
                  <td>
                    <span
                      className={`sf-badge ${
                        u.is_active
                          ? 'sf-badge--status-done'
                          : 'sf-badge--status-canceled'
                      }`}
                    >
                      {u.is_active ? 'Активен' : 'Отключён'}
                    </span>
                  </td>
                  <td>
                    <Select
                      value={u.role}
                      onChange={(e) =>
                        changeRole(u.id, e.target.value as UserRole)
                      }
                      style={{ padding: '5px 10px', fontSize: 12.5 }}
                    >
                      <option value="admin">Admin</option>
                      <option value="agent">Agent</option>
                      <option value="employee">Employee</option>
                    </Select>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>
    </div>
  );
}
