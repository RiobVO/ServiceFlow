export type UserRole = "ADMIN" | "AGENT" | "EMPLOYEE";

export type User = {
  id: number;
  full_name: string;
  email: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
};

export type RequestStatus =
  | "OPEN"
  | "IN_PROGRESS"
  | "ON_HOLD"
  | "RESOLVED"
  | "CLOSED"
  | "CANCEL";

export type RequestItem = {
  id: number;
  public_id: string;
  title: string;
  description: string | null;
  status: RequestStatus;
  created_by_user_id: number;
  assigned_to_user_id: number | null;
  created_at: string;
  updated_at: string;
};
