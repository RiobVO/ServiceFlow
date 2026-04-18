import { useEffect, useState } from 'react';
import { Check, RefreshCw } from 'lucide-react';
import { StatusBadge } from '../components/StatusBadge';
import {
  Button,
  Card,
  Empty,
  PageHeader,
  formatTime,
} from '../components/primitives';
import { api } from '../services/api';
import type { ServiceRequest, User } from '../types';

interface Props {
  apiKey: string;
  user: User | null;
}

export function Queue({ apiKey, user }: Props) {
  const [queue, setQueue] = useState<ServiceRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [taking, setTaking] = useState<number | null>(null);

  const load = () => {
    setLoading(true);
    api
      .listQueue(apiKey)
      .then((page) => setQueue(page.items))
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    if (apiKey) load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [apiKey]);

  const takeRequest = async (r: ServiceRequest) => {
    if (!user) return;
    setTaking(r.id);
    try {
      const updated = await api.updateStatus(apiKey, r.id, {
        status: 'IN_PROGRESS',
        assignee_id: user.id,
        comment: 'Взято в работу',
      });
      setQueue((prev) => prev.filter((x) => x.id !== updated.id));
    } finally {
      setTaking(null);
    }
  };

  return (
    <div className="sf-page">
      <PageHeader
        title="Очередь"
        subtitle={`${queue.length} заявок ожидают обработки`}
        right={
          <Button variant="ghost" size="sm" icon={RefreshCw} onClick={load}>
            Обновить
          </Button>
        }
      />

      <Card>
        {loading ? (
          <Empty>Загрузка…</Empty>
        ) : queue.length === 0 ? (
          <Empty icon={Check}>Очередь пуста. Хороший день.</Empty>
        ) : (
          <table className="sf-table">
            <thead>
              <tr>
                <th style={{ width: 76 }}>ID</th>
                <th>Название</th>
                <th style={{ width: 130 }}>Статус</th>
                <th style={{ width: 130 }}>Создана</th>
                <th style={{ width: 110 }}>Действие</th>
              </tr>
            </thead>
            <tbody>
              {queue.map((r) => (
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
                  <td>
                    <Button
                      size="sm"
                      disabled={taking === r.id}
                      onClick={() => takeRequest(r)}
                    >
                      {taking === r.id ? '…' : 'Взять'}
                    </Button>
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
