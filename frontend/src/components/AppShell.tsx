import { NavLink, Outlet } from "react-router-dom";
import { useState } from "react";
import { api } from "../services/api";
import { useLocalStorage } from "../utils/useLocalStorage";
import { User } from "../types";

const AppShell = () => {
  const [apiKey, setApiKey] = useLocalStorage("sf_api_key", "");
  const [user, setUser] = useState<User | null>(null);
  const [status, setStatus] = useState<string>("");
  const [isLoading, setIsLoading] = useState(false);

  const handleConnect = async () => {
    if (!apiKey) {
      setStatus("Введите API-ключ для подключения.");
      return;
    }

    setIsLoading(true);
    setStatus("");
    try {
      const me = await api.getMe(apiKey);
      setUser(me);
      setStatus(`Подключено как ${me.full_name}`);
    } catch (error) {
      setUser(null);
      setStatus(`Ошибка подключения: ${(error as Error).message}`);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="app">
      <aside className="sidebar">
        <div>
          <h1>ServiceFlow</h1>
          <p className="pill">Управление заявками и пользователями.</p>
        </div>
        <nav>
          <NavLink to="/" end>
            Обзор
          </NavLink>
          <NavLink to="/requests">Все заявки</NavLink>
          <NavLink to="/requests/my">Мои заявки</NavLink>
          <NavLink to="/requests/queue">Очередь</NavLink>
          <NavLink to="/users">Пользователи</NavLink>
        </nav>
        <div className="pill">
          <strong>Текущий пользователь</strong>
          <div>{user ? user.full_name : "не подключён"}</div>
          <div className="helper">{user ? user.role : "укажите API-ключ"}</div>
        </div>
      </aside>

      <main className="content">
        <div className="topbar">
          <div>
            <h2>ServiceFlow Console</h2>
            <p className="helper">Единый интерфейс для работы с заявками.</p>
          </div>
          <div className="input-group">
            <input
              value={apiKey}
              onChange={(event) => setApiKey(event.target.value)}
              placeholder="X-API-Key"
            />
            <button type="button" onClick={handleConnect} disabled={isLoading}>
              {isLoading ? "Подключение..." : "Подключиться"}
            </button>
          </div>
        </div>
        {status && <div className="helper">{status}</div>}
        <Outlet context={{ apiKey, user }} />
      </main>
    </div>
  );
};

export default AppShell;
