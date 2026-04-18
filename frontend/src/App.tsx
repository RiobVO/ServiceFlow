import { useState } from 'react';
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { Sidebar } from './components/Sidebar';
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

  const connect = async () => {
    if (!key.trim()) {
      setLocalError('Введите API-ключ');
      return;
    }
    setLoading(true);
    setLocalError(null);
    try {
      await login(key.trim());
    } catch (err) {
      const msg =
        err instanceof ApiError ? err.problem.detail : (err as Error).message;
      setLocalError(msg);
    } finally {
      setLoading(false);
    }
  };

  const shownError = localError ?? error;

  return (
    <div className="connect-screen">
      <div className="connect-card">
        <div className="connect-logo">
          <div className="connect-logo-icon">⚡</div>
          <div>
            <h1>ServiceFlow</h1>
            <p>Система управления заявками</p>
          </div>
        </div>
        <div className="connect-form">
          <label>API-ключ</label>
          <input
            className="input"
            placeholder="Вставьте ваш API-ключ…"
            value={key}
            onChange={(e) => setKey(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && connect()}
            autoFocus
          />
          {shownError && <div className="error-msg">⚠ {shownError}</div>}
          <button
            className="btn btn-primary btn-full"
            onClick={connect}
            disabled={loading}
          >
            {loading ? 'Подключение…' : '⚡ Подключиться'}
          </button>
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
          background: 'var(--bg)',
          color: 'var(--text-3)',
        }}
      >
        Загрузка…
      </div>
    );
  }

  if (status !== 'authenticated' || !user || !apiKey) {
    return <ConnectScreen />;
  }

  return (
    <BrowserRouter>
      <div className="layout">
        <Sidebar user={user} onLogout={logout} />
        <main className="main">
          <header className="topbar">
            <div className="topbar-title">
              {user.role === 'admin'
                ? 'Admin Console'
                : user.role === 'agent'
                  ? 'Agent Panel'
                  : 'Employee Portal'}
            </div>
            <div className="topbar-status">
              <div className="status-dot" />
              API подключён
            </div>
          </header>
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
        </main>
      </div>
    </BrowserRouter>
  );
}
