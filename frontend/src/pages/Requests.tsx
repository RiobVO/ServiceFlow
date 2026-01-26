import { useEffect, useState } from "react";
import { api } from "../services/api";
import { RequestItem, RequestStatus } from "../types";
import { useAppContext } from "../utils/useAppContext";

const statusOptions: Array<{ label: string; value: RequestStatus | "" }> = [
  { label: "Все", value: "" },
  { label: "OPEN", value: "OPEN" },
  { label: "IN_PROGRESS", value: "IN_PROGRESS" },
  { label: "ON_HOLD", value: "ON_HOLD" },
  { label: "RESOLVED", value: "RESOLVED" },
  { label: "CLOSED", value: "CLOSED" },
  { label: "CANCEL", value: "CANCEL" }
];

const Requests = () => {
  const { apiKey } = useAppContext();
  const [requests, setRequests] = useState<RequestItem[]>([]);
  const [statusFilter, setStatusFilter] = useState<RequestStatus | "">("");
  const [error, setError] = useState<string>("");

  useEffect(() => {
    const load = async () => {
      if (!apiKey) {
        return;
      }

      try {
        const query = statusFilter ? `?request_status=${statusFilter}` : "";
        const data = await api.listRequests(apiKey, query);
        setRequests(data);
        setError("");
      } catch (err) {
        setError((err as Error).message);
      }
    };

    void load();
  }, [apiKey, statusFilter]);

  return (
    <section className="section">
      <h2>Все заявки</h2>
      <p className="helper">Фильтрация и просмотр заявок для роли Agent/Admin.</p>
      <div className="form" style={{ marginBottom: "16px" }}>
        <select
          value={statusFilter}
          onChange={(event) => setStatusFilter(event.target.value as RequestStatus | "")}
        >
          {statusOptions.map((option) => (
            <option key={option.label} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </div>
      {error && <p className="helper">Ошибка загрузки: {error}</p>}
      {!apiKey && <p className="helper">Введите API-ключ, чтобы загрузить список.</p>}
      <table className="table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Название</th>
            <th>Статус</th>
            <th>Создана</th>
            <th>Исполнитель</th>
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
              <td>{new Date(request.created_at).toLocaleDateString()}</td>
              <td>{request.assigned_to_user_id ?? "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
};

export default Requests;
