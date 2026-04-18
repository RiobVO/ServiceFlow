import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react';
import { api, ApiError } from '../services/api';
import type { User } from '../types';

interface AuthState {
  apiKey: string | null;
  user: User | null;
  status: 'idle' | 'loading' | 'authenticated' | 'anonymous';
  error: string | null;
}

interface AuthValue extends AuthState {
  login: (key: string) => Promise<User>;
  logout: () => void;
  rotateKey: () => Promise<string>;
}

const AuthContext = createContext<AuthValue | null>(null);
const STORAGE_KEY = 'sf_api_key';

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>({
    apiKey: null,
    user: null,
    status: 'loading',
    error: null,
  });

  // Восстановление сессии из localStorage при монтировании.
  useEffect(() => {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (!saved) {
      setState({ apiKey: null, user: null, status: 'anonymous', error: null });
      return;
    }
    api
      .getMe(saved)
      .then((user) => setState({ apiKey: saved, user, status: 'authenticated', error: null }))
      .catch(() => {
        localStorage.removeItem(STORAGE_KEY);
        setState({ apiKey: null, user: null, status: 'anonymous', error: null });
      });
  }, []);

  const login = useCallback(async (key: string) => {
    setState((s) => ({ ...s, status: 'loading', error: null }));
    try {
      const user = await api.getMe(key);
      localStorage.setItem(STORAGE_KEY, key);
      setState({ apiKey: key, user, status: 'authenticated', error: null });
      return user;
    } catch (err) {
      const message =
        err instanceof ApiError ? err.problem.detail : (err as Error).message;
      setState((s) => ({ ...s, status: 'anonymous', error: message }));
      throw err;
    }
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem(STORAGE_KEY);
    setState({ apiKey: null, user: null, status: 'anonymous', error: null });
  }, []);

  const rotateKey = useCallback(async () => {
    if (!state.apiKey) throw new Error('not authenticated');
    const res = await api.rotateMyApiKey(state.apiKey);
    localStorage.setItem(STORAGE_KEY, res.api_key);
    setState((s) => ({ ...s, apiKey: res.api_key }));
    return res.api_key;
  }, [state.apiKey]);

  const value = useMemo<AuthValue>(
    () => ({ ...state, login, logout, rotateKey }),
    [state, login, logout, rotateKey],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used inside <AuthProvider>');
  return ctx;
}
