import { useEffect, useState } from 'react';
import { StatusBadge } from '../components/StatusBadge';
import {
  Card,
  Empty,
  PageHeader,
  Select,
  formatTime,
} from '../components/primitives';
import { api } from '../services/api';
import type { RequestStatus, ServiceRequest, User } from '../types';

interface Props {
  apiKey: string;
  user: User | null;
}

const STATUSES: { value: RequestStatus | ''; label: string }[] = [
  { value: '', label: 'Все' },
  { value: 'NEW', label: 'Новые' },
  { value: 'IN_PROGRESS', label: 'В работе' },
  { value: 'DONE', label: 'Готово' },
  { value: 'CANCELED', label: 'Отменены' },
];

export function Requests({ apiKey, user }: Props) {
  const [requests, setRequests] = useState<ServiceRequest[]>([]);
  const [filter, setFilter] = useState<RequestStatus | ''>('');
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState<number | null>(null);

  const load = () => {
    setLoading(true);
    const q = filter ? { request_status: filter } : {};
    api
      .listRequests(apiKey, q)
      .then((page) => setRequests(page.items))
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    if (apiKey) load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [apiKey, filter]);

  const changeStatus = async (r: ServiceRequest, status: RequestStatus) => {
    setUpdating(r.id);
    try {
      const updated = await api.updateStatus(apiKey, r.id, { status });
      setRequests((prev) => prev.map((x) => (x.id === r.id ? updated : x)));
    } finally {
      setUpdating(null);
    }
  };

  const canChange = user?.role === 'admin' || user?.role === 'agent';

  return (
    <div className="sf-page">
      <PageHeader title="Все заявки" subtitle={`${requests.length} заявок`} />

      <div className="sf-chips">
        {STATUSES.map((s) => (
          <button
            key={s.value}
            type="button"
            onClick={() => setFilter(s.value)}
            className={`sf-chip ${filter === s.value ? 'is-active' : ''}`}
          >
            {s.label}
          </button>
        ))}
      </div>

      <Card>
        {loading ? (
          <Empty>Загрузка…</Empty>
        ) : requests.length === 0 ? (
          <Empty>Ничего не найдено.</Empty>
        ) : (
          <table className="sf-table">
            <thead>
              <tr>
                <th style={{ width: 76 }}>ID</th>
                <th>Название</th>
                <th style={{ width: 130 }}>Статус</th>
                <th style={{ width: 120 }}>Создана</th>
                {canChange ? <th style={{ width: 160 }}>Действие</th> : null}
              </tr>
            </thead>
            <tbody>
              {requests.map((r) => (
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
                  <td className="sf-td--muted">{formatTime(r.created_at)}</td>
                  {canChange ? (
                    <td>
                      <Select
                        value={r.status}
                        disabled={updating === r.id}
                        onChange={(e) =>
                          changeStatus(r, e.target.value as RequestStatus)
                        }
                        style={{ padding: '5px 10px', fontSize: 12.5 }}
                      >
                        <option value="NEW">Новая</option>
                        <option value="IN_PROGRESS">В работе</option>
                        <option value="DONE">Готово</option>
                        <option value="CANCELED">Отменена</option>
                      </Select>
                    </td>
                  ) : null}
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>
    </div>
  );
}
