import { Navigate, Route, Routes } from "react-router-dom";
import AppShell from "./components/AppShell";
import Dashboard from "./pages/Dashboard";
import MyRequests from "./pages/MyRequests";
import Queue from "./pages/Queue";
import Requests from "./pages/Requests";
import Users from "./pages/Users";

const App = () => {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route index element={<Dashboard />} />
        <Route path="/requests" element={<Requests />} />
        <Route path="/requests/my" element={<MyRequests />} />
        <Route path="/requests/queue" element={<Queue />} />
        <Route path="/users" element={<Users />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
};

export default App;
