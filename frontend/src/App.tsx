import { useState } from 'react';
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { Sidebar } from './components/Sidebar';
import {
  BrandMark,
  Button,
  ErrorMessage,
  Field,
  Input,
} from './components/primitives';
import { useAuth } from './context/AuthContext';
import { Dashboard } from './pages/Dashboard';
import { MyRequests } from './pages/MyRequests';
import { Queue } from './pages/Queue';
import { Requests } from './pages/Requests';
import { Users } from './pages/Users';
import { ApiError } from './services/api';
import './styles/global.css';

function ConnectScreen() {
  const { login, error } = useAuth();
  const [key, setKey] = useState('');
  const [loading, setLoading] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);

  const submit = async () => {
    if (!key.trim()) {
      setLocalError('Нужен API-ключ.');
      return;
    }
    setLoading(true);
    setLocalError(null);
    try {
      await login(key.trim());
    } catch (err) {
      const msg = err instanceof ApiError ? err.problem.detail : (err as Error).message;
      setLocalError(msg);
    } finally {
      setLoading(false);
    }
  };

  const shownError = localError ?? error;

  return (
    <div className="sf-connect">
      <div className="sf-connect__card">
        <div className="sf-connect__brand">
          <BrandMark size={36} />
          <div>
            <div className="sf-connect__brand-title">ServiceFlow</div>
            <div className="sf-connect__brand-subtitle">Заявки и сервис-деск</div>
          </div>
        </div>

        <h1 className="sf-connect__h1">Подключение</h1>
        <p className="sf-connect__lead">
          Введите API-ключ, который выдал администратор.
        </p>

        <div className="sf-form">
          <Field label="API-ключ">
            <Input
              mono
              placeholder="sk_…"
              value={key}
              onChange={(e) => setKey(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && submit()}
              autoFocus
            />
          </Field>
          {shownError ? <ErrorMessage>{shownError}</ErrorMessage> : null}
          <Button onClick={submit} disabled={loading} fullWidth>
            {loading ? 'Подключение…' : 'Подключиться'}
          </Button>
        </div>
      </div>
    </div>
  );
}

export default function App() {
  const { status, user, apiKey, logout } = useAuth();

  if (status === 'loading') {
    return (
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          height: '100vh',
          background: 'var(--sf-paper)',
          color: 'var(--sf-ink-3)',
          fontFamily: 'var(--sf-font-sans)',
        }}
      >
        Загрузка…
      </div>
    );
  }

  if (status !== 'authenticated' || !user || !apiKey) {
    return <ConnectScreen />;
  }

  const portalTitle =
    user.role === 'admin' ? 'Admin Console' : user.role === 'agent' ? 'Agent Panel' : 'Employee Portal';

  return (
    <BrowserRouter>
      <div className="sf-layout">
        <Sidebar user={user} onLogout={logout} />
        <main className="sf-main">
          <header className="sf-topbar">
            <div className="sf-topbar__title">{portalTitle}</div>
            <div className="sf-topbar__status">
              <span className="sf-topbar__dot" />
              API подключён
            </div>
          </header>
          <div className="sf-content sf-fade-in">
            <Routes>
              <Route path="/" element={<Dashboard apiKey={apiKey} user={user} />} />
              {(user.role === 'admin' || user.role === 'agent') && (
                <>
                  <Route
                    path="/requests"
                    element={<Requests apiKey={apiKey} user={user} />}
                  />
                  <Route
                    path="/queue"
                    element={<Queue apiKey={apiKey} user={user} />}
                  />
                </>
              )}
              {user.role === 'admin' && (
                <Route path="/users" element={<Users apiKey={apiKey} />} />
              )}
              {user.role === 'employee' && (
                <Route
                  path="/my"
                  element={<MyRequests apiKey={apiKey} user={user} />}
                />
              )}
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </div>
        </main>
      </div>
    </BrowserRouter>
  );
}
