// Small shared UI helpers used across dashboards.
import { useEffect, useState } from "react";

export function Alert({ error, success }) {
  if (error) return <div className="alert error">{error}</div>;
  if (success) return <div className="alert success">{success}</div>;
  return null;
}

export function Tabs({ tabs, active, onChange }) {
  return (
    <div className="tabs">
      {tabs.map((t) => (
        <button
          key={t.key}
          className={`tab ${active === t.key ? "active" : ""}`}
          onClick={() => onChange(t.key)}
        >
          {t.label}
        </button>
      ))}
    </div>
  );
}

export function Badge({ value }) {
  const cls = (value || "none").toLowerCase();
  return <span className={`badge ${cls}`}>{value || "none"}</span>;
}

// Simple async loader wrapper.
export function useAsync(fn, deps = []) {
  const [state, setState] = useState({ loading: true, data: null, error: null });
  const [nonce, setNonce] = useState(0);

  useEffect(() => {
    let alive = true;
    setState((s) => ({ ...s, loading: true, error: null }));
    fn()
      .then((data) => alive && setState({ loading: false, data, error: null }))
      .catch((e) => alive && setState({ loading: false, data: null, error: e.message }));
    return () => {
      alive = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, nonce]);

  return { ...state, reload: () => setNonce((n) => n + 1) };
}

export function CourseSelect({ courses, value, onChange }) {
  return (
    <select value={value || ""} onChange={(e) => onChange(e.target.value)}>
      <option value="" disabled>
        Select a course…
      </option>
      {courses.map((c) => (
        <option key={c.sectionId} value={c.sectionId}>
          {c.courseCode} — {c.sectionName}
        </option>
      ))}
    </select>
  );
}
