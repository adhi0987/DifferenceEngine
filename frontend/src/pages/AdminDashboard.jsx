import { useState } from "react";
import { api } from "../lib/api.js";
import { Alert, Tabs, useAsync } from "../components/ui.jsx";

const TABS = [
  { key: "courses", label: "Courses" },
  { key: "enroll", label: "Enrollments" },
  { key: "audit", label: "Audit logs" },
];

export default function AdminDashboard() {
  const [tab, setTab] = useState("courses");
  return (
    <>
      <Tabs tabs={TABS} active={tab} onChange={setTab} />
      {tab === "courses" && <CreateCourse />}
      {tab === "enroll" && <Enroll />}
      {tab === "audit" && <AuditLogs />}
    </>
  );
}

function CreateCourse() {
  const [form, setForm] = useState({
    courseCode: "",
    courseName: "",
    sectionName: "",
    academicTerm: "Semester 3",
    facultyId: "",
  });
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);

  async function submit(e) {
    e.preventDefault();
    setError(null);
    setResult(null);
    try {
      const payload = { ...form };
      if (!payload.facultyId) delete payload.facultyId;
      const data = await api.createCourse(payload);
      setResult(data);
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="card">
      <h3>Create course & section</h3>
      <Alert error={error} />
      <form onSubmit={submit}>
        <div className="row">
          <div style={{ flex: 1 }}>
            <label>Course code</label>
            <input
              value={form.courseCode}
              onChange={(e) => setForm({ ...form, courseCode: e.target.value })}
              required
            />
          </div>
          <div style={{ flex: 2 }}>
            <label>Course name</label>
            <input
              value={form.courseName}
              onChange={(e) => setForm({ ...form, courseName: e.target.value })}
              required
            />
          </div>
        </div>
        <div className="row">
          <div style={{ flex: 1 }}>
            <label>Section name</label>
            <input
              value={form.sectionName}
              onChange={(e) => setForm({ ...form, sectionName: e.target.value })}
              required
            />
          </div>
          <div style={{ flex: 1 }}>
            <label>Academic term</label>
            <input
              value={form.academicTerm}
              onChange={(e) => setForm({ ...form, academicTerm: e.target.value })}
              required
            />
          </div>
        </div>
        <label>Faculty ID (optional)</label>
        <input
          value={form.facultyId}
          onChange={(e) => setForm({ ...form, facultyId: e.target.value })}
          placeholder="User UUID of assigned faculty"
        />
        <button>Create</button>
      </form>
      {result && (
        <div className="alert success" style={{ marginTop: 12 }}>
          Created. Course ID <code>{result.courseId}</code>, Section ID{" "}
          <code>{result.sectionId}</code>
        </div>
      )}
    </div>
  );
}

function Enroll() {
  const [studentId, setStudentId] = useState("");
  const [sectionId, setSectionId] = useState("");
  const [error, setError] = useState(null);
  const [msg, setMsg] = useState(null);

  async function submit(e) {
    e.preventDefault();
    setError(null);
    setMsg(null);
    try {
      const data = await api.enroll(studentId, sectionId);
      setMsg(`Enrolled (status: ${data.enrollmentStatus}).`);
      setStudentId("");
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="card">
      <h3>Enroll student into section</h3>
      <p className="muted">Use the user UUID and section UUID.</p>
      <Alert error={error} success={msg} />
      <form onSubmit={submit}>
        <label>Student ID</label>
        <input value={studentId} onChange={(e) => setStudentId(e.target.value)} required />
        <label>Section ID</label>
        <input value={sectionId} onChange={(e) => setSectionId(e.target.value)} required />
        <button>Enroll</button>
      </form>
    </div>
  );
}

function AuditLogs() {
  const { data, loading, error, reload } = useAsync(() => api.auditLogs(), []);
  return (
    <div className="card">
      <div className="row" style={{ justifyContent: "space-between" }}>
        <h3>Audit logs</h3>
        <button className="ghost small" onClick={reload}>
          Refresh
        </button>
      </div>
      {loading && <p className="muted">Loading…</p>}
      <Alert error={error} />
      {data && (
        <table>
          <thead>
            <tr>
              <th>Time</th>
              <th>Action</th>
              <th>Entity</th>
            </tr>
          </thead>
          <tbody>
            {data.map((e) => (
              <tr key={e.id}>
                <td>{new Date(e.createdAt).toLocaleString()}</td>
                <td>{e.action}</td>
                <td>{e.entityType}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
