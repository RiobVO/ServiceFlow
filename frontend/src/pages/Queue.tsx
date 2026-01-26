import { useEffect, useState } from "react";
import { api } from "../services/api";
import { RequestItem } from "../types";
import { useAppContext } from "../utils/useAppContext";

const Queue = () => {
  const { apiKey } = useAppContext();
  const [requests, setRequests] = useState<RequestItem[]>([]);
  const [error, setError] = useState<string>("");

  useEffect(() => {
    const load = async () => {
      if (!apiKey) {
        return;
      }

      try {
        const data = await api.listQueue(apiKey);
        setRequests(data);
        setError("");
      } catch (err) {
        setError((err as Error).message);
      }
    };

    void load();
  }, [apiKey]);

  return (
    <section className="section">
      <h2>Очередь заявок</h2>
      <p className="helper">Заявки без исполнителя для агентских команд.</p>
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
  );
};

export default Queue;
