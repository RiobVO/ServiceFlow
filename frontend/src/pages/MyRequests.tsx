import { FormEvent, useEffect, useState } from "react";
import { api } from "../services/api";
import { RequestItem } from "../types";
import { useAppContext } from "../utils/useAppContext";

const MyRequests = () => {
  const { apiKey } = useAppContext();
  const [requests, setRequests] = useState<RequestItem[]>([]);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [message, setMessage] = useState("");

  const load = async () => {
    if (!apiKey) {
      return;
    }

    const data = await api.listMyRequests(apiKey);
    setRequests(data);
  };

  useEffect(() => {
    void load();
  }, [apiKey]);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!apiKey) {
      setMessage("Нужен API-ключ.");
      return;
    }

    try {
      await api.createRequest(apiKey, { title, description });
      setTitle("");
      setDescription("");
      setMessage("Заявка создана.");
      await load();
    } catch (error) {
      setMessage(`Ошибка: ${(error as Error).message}`);
    }
  };

  return (
    <section className="section">
      <h2>Мои заявки</h2>
      <p className="helper">Создавайте заявки и отслеживайте их статус.</p>
      <form className="form" onSubmit={handleSubmit}>
        <input
          value={title}
          onChange={(event) => setTitle(event.target.value)}
          placeholder="Название заявки"
          required
        />
        <textarea
          value={description}
          onChange={(event) => setDescription(event.target.value)}
          placeholder="Описание"
          rows={4}
        />
        <button type="submit">Создать заявку</button>
        {message && <p className="helper">{message}</p>}
      </form>

      <div style={{ marginTop: "24px" }}>
        <table className="table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Название</th>
              <th>Статус</th>
              <th>Обновлена</th>
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
                <td>{new Date(request.updated_at).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
};

export default MyRequests;
