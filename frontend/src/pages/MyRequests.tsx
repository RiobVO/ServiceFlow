import { useEffect, useState } from 'react';
import { Plus } from 'lucide-react';
import {
  Button,
  Card,
  CardHeader,
  Empty,
  ErrorMessage,
  Field,
  Input,
  PageHeader,
  Textarea,
} from '../components/primitives';
import { api, ApiError } from '../services/api';
import type { ServiceRequest, User } from '../types';
import { RequestTable } from './Dashboard';

interface Props {
  apiKey: string;
  user: User | null;
}

export function MyRequests({ apiKey }: Props) {
  const [requests, setRequests] = useState<ServiceRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [title, setTitle] = useState('');
  const [desc, setDesc] = useState('');
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = () => {
    setLoading(true);
    api
      .listMyRequests(apiKey)
      .then((page) => setRequests(page.items))
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    if (apiKey) load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [apiKey]);

  const submit = async () => {
    if (!title.trim()) {
      setError('Введите название.');
      return;
    }
    setCreating(true);
    setError(null);
    try {
      const r = await api.createRequest(apiKey, {
        title: title.trim(),
        description: desc.trim() || undefined,
      });
      setRequests((prev) => [r, ...prev]);
      setTitle('');
      setDesc('');
    } catch (err) {
      const msg = err instanceof ApiError ? err.problem.detail : 'Не удалось создать заявку.';
      setError(msg);
    } finally {
      setCreating(false);
    }
  };

  const clear = () => {
    setTitle('');
    setDesc('');
    setError(null);
  };

  return (
    <div className="sf-page">
      <PageHeader
        title="Мои заявки"
        subtitle="Создавайте и отслеживайте свои запросы"
      />

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
            Новая заявка
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            <Field label="Название">
              <Input
                placeholder="Опишите проблему кратко…"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
              />
            </Field>
            <Field label="Описание">
              <Textarea
                placeholder="Подробности (необязательно)…"
                value={desc}
                onChange={(e) => setDesc(e.target.value)}
              />
            </Field>
            {error ? <ErrorMessage>{error}</ErrorMessage> : null}
            <div style={{ display: 'flex', gap: 10 }}>
              <Button icon={Plus} onClick={submit} disabled={creating}>
                {creating ? 'Создание…' : 'Создать заявку'}
              </Button>
              <Button variant="ghost" onClick={clear}>
                Очистить
              </Button>
            </div>
          </div>
        </div>
      </Card>

      <Card>
        <CardHeader title="История" />
        {loading ? (
          <Empty>Загрузка…</Empty>
        ) : requests.length === 0 ? (
          <Empty>У вас пока нет заявок.</Empty>
        ) : (
          <RequestTable rows={requests} />
        )}
      </Card>
    </div>
  );
}
