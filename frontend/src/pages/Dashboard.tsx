import { useEffect, useState } from "react";
import { api } from "../services/api";
import { RequestItem } from "../types";
import { useAppContext } from "../utils/useAppContext";

const Dashboard = () => {
  const { apiKey, user } = useAppContext();
  const [requests, setRequests] = useState<RequestItem[]>([]);
  const [error, setError] = useState<string>("");

  useEffect(() => {
    const load = async () => {
      if (!apiKey) {
        return;
      }

      try {
        const data = await api.listRequests(apiKey, "?limit=5");
        setRequests(data);
        setError("");
      } catch (err) {
        setError((err as Error).message);
      }
    };

    void load();
  }, [apiKey]);

  const openCount = requests.filter((item) => item.status === "OPEN").length;
  const inProgressCount = requests.filter((item) => item.status === "IN_PROGRESS").length;

  return (
    <>
      <section className="section">
        <h2>Добро пожаловать{user ? `, ${user.full_name}` : ""}</h2>
        <p className="helper">
          Это главная панель. Подключите API-ключ, чтобы видеть данные из FastAPI.
        </p>
      </section>

      <section className="section">
        <h2>Статистика по заявкам</h2>
        <div className="stats">
          <div className="stat-card">
            <span>Всего заявок</span>
            <strong>{requests.length}</strong>
          </div>
          <div className="stat-card">
            <span>Открытые</span>
            <strong>{openCount}</strong>
          </div>
          <div className="stat-card">
            <span>В работе</span>
            <strong>{inProgressCount}</strong>
          </div>
        </div>
      </section>

      <section className="section">
        <h2>Последние заявки</h2>
        {error && <p className="helper">Ошибка загрузки: {error}</p>}
        {!apiKey && <p className="helper">Введите API-ключ, чтобы загрузить список.</p>}
        <table className="table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Название</th>
              <th>Статус</th>
              <th>Создана</th>
            </tr>
          </thead>
          <tbody>
            {requests.map((request) => (
              <tr key={request.id}>
                <td>#{request.id}</td>
                <td>{request.title}</td>
                <td>
                  <span className={`badge ${request.status.toLowerCase()}`}>
                    {request.status}
                  </span>
                </td>
                <td>{new Date(request.created_at).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </>
  );
};

export default Dashboard;
