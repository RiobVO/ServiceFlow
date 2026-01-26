import { RequestItem, User } from "../types";

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

const buildHeaders = (apiKey?: string) => {
  const headers: Record<string, string> = {
    "Content-Type": "application/json"
  };

  if (apiKey) {
    headers["X-API-Key"] = apiKey;
  }

  return headers;
};

const handleResponse = async <T>(response: Response): Promise<T> => {
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    const detail = (body as { detail?: string }).detail ?? response.statusText;
    throw new Error(detail);
  }

  return response.json() as Promise<T>;
};

export const api = {
  async getMe(apiKey: string) {
    const response = await fetch(`${API_URL}/users/me`, {
      headers: buildHeaders(apiKey)
    });
    return handleResponse<User>(response);
  },

  async listRequests(apiKey: string, query = "") {
    const response = await fetch(`${API_URL}/requests${query}`, {
      headers: buildHeaders(apiKey)
    });
    return handleResponse<RequestItem[]>(response);
  },

  async listQueue(apiKey: string) {
    const response = await fetch(`${API_URL}/requests/queue`, {
      headers: buildHeaders(apiKey)
    });
    return handleResponse<RequestItem[]>(response);
  },

  async listMyRequests(apiKey: string) {
    const response = await fetch(`${API_URL}/requests/my`, {
      headers: buildHeaders(apiKey)
    });
    return handleResponse<RequestItem[]>(response);
  },

  async listUsers(apiKey: string) {
    const response = await fetch(`${API_URL}/users`, {
      headers: buildHeaders(apiKey)
    });
    return handleResponse<User[]>(response);
  },

  async createRequest(apiKey: string, payload: { title: string; description?: string }) {
    const response = await fetch(`${API_URL}/requests`, {
      method: "POST",
      headers: buildHeaders(apiKey),
      body: JSON.stringify(payload)
    });
    return handleResponse<RequestItem>(response);
  }
};
