import { useState } from "react";
import { useAuth } from "../lib/auth.jsx";
import { api } from "../lib/api.js";
import { Alert } from "../components/ui.jsx";

const DEMO = [
  ["Faculty", "faculty@attendiq.edu"],
  ["Student", "student1@attendiq.edu"],
  ["Admin", "admin@attendiq.edu"],
];

export default function Login() {
  const { login } = useAuth();
  const [mode, setMode] = useState("login");
  const [email, setEmail] = useState("faculty@attendiq.edu");
  const [password, setPassword] = useState("Password@123");
  const [reg, setReg] = useState({
    institutionalId: "",
    fullName: "",
    email: "",
    password: "",
    role: "student",
  });
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);

  async function submitLogin(e) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await login(email, password);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  async function submitRegister(e) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await api.register(reg);
      await login(reg.email, reg.password);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="app">
      <div className="login-wrap">
        <h1 className="center brand">
          Attend<span>IQ</span> COA
        </h1>
        <p className="center muted">
          Smart Attendance, Engagement & Learning Rewards
        </p>

        <div className="tabs" style={{ justifyContent: "center" }}>
          <button
            className={`tab ${mode === "login" ? "active" : ""}`}
            onClick={() => setMode("login")}
          >
            Log in
          </button>
          <button
            className={`tab ${mode === "register" ? "active" : ""}`}
            onClick={() => setMode("register")}
          >
            Register
          </button>
        </div>

        <div className="card">
          <Alert error={error} />

          {mode === "login" ? (
            <form onSubmit={submitLogin}>
              <label>Email</label>
              <input
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                type="email"
                required
              />
              <label>Password</label>
              <input
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                type="password"
                required
              />
              <button disabled={busy} style={{ width: "100%" }}>
                {busy ? "Signing in…" : "Sign in"}
              </button>

              <p className="muted" style={{ marginTop: 14 }}>
                Demo accounts (password <code>Password@123</code>):
              </p>
              <div className="row">
                {DEMO.map(([label, mail]) => (
                  <button
                    type="button"
                    key={mail}
                    className="ghost small"
                    onClick={() => {
                      setEmail(mail);
                      setPassword("Password@123");
                    }}
                  >
                    {label}
                  </button>
                ))}
              </div>
            </form>
          ) : (
            <form onSubmit={submitRegister}>
              <label>Institutional ID</label>
              <input
                value={reg.institutionalId}
                onChange={(e) =>
                  setReg({ ...reg, institutionalId: e.target.value })
                }
                required
              />
              <label>Full name</label>
              <input
                value={reg.fullName}
                onChange={(e) => setReg({ ...reg, fullName: e.target.value })}
                required
              />
              <label>Email</label>
              <input
                type="email"
                value={reg.email}
                onChange={(e) => setReg({ ...reg, email: e.target.value })}
                required
              />
              <label>Password</label>
              <input
                type="password"
                value={reg.password}
                onChange={(e) => setReg({ ...reg, password: e.target.value })}
                required
              />
              <label>Role</label>
              <select
                value={reg.role}
                onChange={(e) => setReg({ ...reg, role: e.target.value })}
              >
                <option value="student">Student</option>
                <option value="faculty">Faculty</option>
                <option value="admin">Admin</option>
              </select>
              <button disabled={busy} style={{ width: "100%" }}>
                {busy ? "Creating…" : "Create account"}
              </button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
