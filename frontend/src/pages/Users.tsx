import { useEffect, useState } from "react";
import { api } from "../services/api";
import { User } from "../types";
import { useAppContext } from "../utils/useAppContext";

const Users = () => {
  const { apiKey } = useAppContext();
  const [users, setUsers] = useState<User[]>([]);
  const [error, setError] = useState<string>("");

  useEffect(() => {
    const load = async () => {
      if (!apiKey) {
        return;
      }

      try {
        const data = await api.listUsers(apiKey);
        setUsers(data);
        setError("");
      } catch (err) {
        setError((err as Error).message);
      }
    };

    void load();
  }, [apiKey]);

  return (
    <section className="section">
      <h2>Пользователи</h2>
      <p className="helper">Доступно только администраторам.</p>
      {error && <p className="helper">Ошибка загрузки: {error}</p>}
      {!apiKey && <p className="helper">Введите API-ключ, чтобы загрузить список.</p>}
      <table className="table">
        <thead>
          <tr>
            <th>ID</th>
            <th>ФИО</th>
            <th>Email</th>
            <th>Роль</th>
          </tr>
        </thead>
        <tbody>
          {users.map((user) => (
            <tr key={user.id}>
              <td>#{user.id}</td>
              <td>{user.full_name}</td>
              <td>{user.email}</td>
              <td>{user.role}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
};

export default Users;
