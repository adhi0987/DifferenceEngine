import { useAuth } from "./lib/auth.jsx";
import Login from "./pages/Login.jsx";
import StudentDashboard from "./pages/StudentDashboard.jsx";
import FacultyDashboard from "./pages/FacultyDashboard.jsx";
import AdminDashboard from "./pages/AdminDashboard.jsx";

export default function App() {
  const { user, logout } = useAuth();

  if (!user) return <Login />;

  return (
    <div className="app">
      <div className="topbar">
        <div className="brand">
          Attend<span>IQ</span> COA
          <span className="role-pill">{user.role}</span>
        </div>
        <div className="row">
          <span className="muted">{user.fullName}</span>
          <button className="ghost small" onClick={logout}>
            Log out
          </button>
        </div>
      </div>

      {user.role === "student" && <StudentDashboard />}
      {user.role === "faculty" && <FacultyDashboard />}
      {user.role === "admin" && <AdminDashboard />}
    </div>
  );
}
