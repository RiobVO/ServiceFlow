import { useOutletContext } from "react-router-dom";
import { User } from "../types";

export type AppContext = {
  apiKey: string;
  user: User | null;
};

export const useAppContext = () => useOutletContext<AppContext>();
