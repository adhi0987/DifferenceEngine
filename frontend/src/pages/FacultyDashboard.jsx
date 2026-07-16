import { useEffect, useRef, useState } from "react";
import { api } from "../lib/api.js";
import { Alert, Badge, CourseSelect, Tabs, useAsync } from "../components/ui.jsx";

const TABS = [
  { key: "session", label: "Session & QR" },
  { key: "quiz", label: "Quiz" },
  { key: "resources", label: "Resources" },
  { key: "analytics", label: "Analytics" },
];

export default function FacultyDashboard() {
  const { data: courses, loading } = useAsync(() => api.courses(), []);
  const [section, setSection] = useState("");
  const [tab, setTab] = useState("session");
  const [activeSession, setActiveSession] = useState(null);

  useEffect(() => {
    if (courses && courses.length && !section) setSection(courses[0].sectionId);
  }, [courses, section]);

  const course = (courses || []).find((c) => c.sectionId === section);

  if (loading) return <p className="muted">Loading…</p>;
  if (!courses || !courses.length)
    return <p className="muted">No sections assigned to you.</p>;

  return (
    <>
      <div className="card">
        <label>Section</label>
        <CourseSelect courses={courses} value={section} onChange={setSection} />
      </div>
      <Tabs tabs={TABS} active={tab} onChange={setTab} />

      {tab === "session" && (
        <SessionManager
          sectionId={section}
          activeSession={activeSession}
          setActiveSession={setActiveSession}
        />
      )}
      {tab === "quiz" && (
        <QuizManager courseId={course.courseId} activeSession={activeSession} />
      )}
      {tab === "resources" && <ResourceManager courseId={course.courseId} />}
      {tab === "analytics" && <Analytics courseId={course.courseId} />}
    </>
  );
}

function SessionManager({ sectionId, activeSession, setActiveSession }) {
  const [topic, setTopic] = useState("Pipeline Hazards");
  const [error, setError] = useState(null);
  const [qr, setQr] = useState(null);
  const [live, setLive] = useState(null);
  const timer = useRef(null);

  async function create(e) {
    e.preventDefault();
    setError(null);
    try {
      const today = new Date().toISOString().slice(0, 10);
      const s = await api.createSession({
        sectionId,
        topicTitle: topic,
        sessionDate: today,
        startTime: new Date().toISOString(),
      });
      await api.startSession(s.sessionId);
      setActiveSession({ ...s, status: "active" });
      setQr(null);
      setLive(null);
    } catch (err) {
      setError(err.message);
    }
  }

  async function refreshQr() {
    if (!activeSession) return;
    try {
      setQr(await api.sessionQr(activeSession.sessionId));
      setLive(await api.liveSession(activeSession.sessionId));
    } catch (err) {
      setError(err.message);
    }
  }

  useEffect(() => {
    if (activeSession && activeSession.status === "active") {
      refreshQr();
      timer.current = setInterval(refreshQr, 5000);
      return () => clearInterval(timer.current);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeSession]);

  async function close() {
    try {
      await api.closeSession(activeSession.sessionId);
      clearInterval(timer.current);
      setActiveSession({ ...activeSession, status: "closed" });
      setQr(null);
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="card">
      <h3>Class session</h3>
      <Alert error={error} />
      {!activeSession || activeSession.status !== "active" ? (
        <form onSubmit={create}>
          <label>Topic</label>
          <input value={topic} onChange={(e) => setTopic(e.target.value)} required />
          <button>Create & start session</button>
        </form>
      ) : (
        <>
          <div className="row" style={{ justifyContent: "space-between" }}>
            <div>
              <div className="muted">Session ID (share for check-in)</div>
              <div className="qr-box">{activeSession.sessionId}</div>
            </div>
            <button className="ghost" onClick={close}>
              Close session
            </button>
          </div>

          {qr && (
            <div style={{ marginTop: 14 }}>
              <div className="muted">
                Rotating QR payload (refreshes every {qr.rotationSeconds}s)
              </div>
              <div className="qr-box">{qr.qrPayload}</div>
              <div className="muted" style={{ marginTop: 6 }}>
                Valid until {new Date(qr.validUntil).toLocaleTimeString()}
              </div>
            </div>
          )}

          {live && (
            <div className="row" style={{ marginTop: 16, justifyContent: "space-between" }}>
              <Stat label="Checked in" value={live.attendanceCount} />
              <Stat label="Verified" value={live.verifiedCount} />
              <Stat label="Pending" value={live.pendingReviewCount} />
            </div>
          )}
        </>
      )}
    </div>
  );
}

function Stat({ label, value }) {
  return (
    <div className="center">
      <div className="stat">{value}</div>
      <div className="muted">{label}</div>
    </div>
  );
}

function QuizManager({ activeSession }) {
  const [questionId, setQuestionId] = useState("");
  const [duration, setDuration] = useState(60);
  const [error, setError] = useState(null);
  const [msg, setMsg] = useState(null);
  const [analytics, setAnalytics] = useState(null);

  if (!activeSession || activeSession.status !== "active")
    return (
      <div className="card">
        <p className="muted">Start a session first to launch quizzes.</p>
      </div>
    );

  async function launch(e) {
    e.preventDefault();
    setError(null);
    setMsg(null);
    try {
      const q = await api.launchQuiz(activeSession.sessionId, questionId, Number(duration));
      setMsg(`Quiz launched (id ${q.sessionQuizId}). Closes at ${new Date(q.closesAt).toLocaleTimeString()}.`);
    } catch (err) {
      setError(err.message);
    }
  }

  async function loadAnalytics() {
    try {
      setAnalytics(await api.quizAnalytics(activeSession.sessionId));
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="card">
      <h3>Launch concept check</h3>
      <p className="muted">
        Paste a question ID from the course question bank (see the seed data or
        create questions via the API).
      </p>
      <form onSubmit={launch}>
        <label>Question ID</label>
        <input value={questionId} onChange={(e) => setQuestionId(e.target.value)} required />
        <label>Duration (seconds)</label>
        <input
          type="number"
          value={duration}
          onChange={(e) => setDuration(e.target.value)}
          min={5}
        />
        <button>Launch quiz</button>
      </form>
      <Alert error={error} success={msg} />

      <button className="ghost small" style={{ marginTop: 10 }} onClick={loadAnalytics}>
        Refresh quiz analytics
      </button>
      {analytics &&
        analytics.quizzes.map((q) => (
          <div key={q.sessionQuizId} className="card" style={{ marginTop: 12 }}>
            <b>{q.topic}</b>
            <p className="muted">{q.questionText}</p>
            <div className="row">
              <Stat label="Responses" value={q.totalResponses} />
              <Stat label="Correct" value={q.correctResponses} />
              <Stat label="Accuracy" value={`${q.accuracy}%`} />
            </div>
          </div>
        ))}
    </div>
  );
}

function ResourceManager({ courseId }) {
  const [form, setForm] = useState({
    title: "",
    resourceType: "notes",
    topic: "",
    fileUrl: "",
    requiredTier: "bronze",
  });
  const [error, setError] = useState(null);
  const [msg, setMsg] = useState(null);

  async function submit(e) {
    e.preventDefault();
    setError(null);
    setMsg(null);
    try {
      await api.createResource({ courseId, ...form });
      setMsg(`Resource "${form.title}" added.`);
      setForm({ ...form, title: "", topic: "", fileUrl: "" });
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="card">
      <h3>Add resource</h3>
      <Alert error={error} success={msg} />
      <form onSubmit={submit}>
        <label>Title</label>
        <input
          value={form.title}
          onChange={(e) => setForm({ ...form, title: e.target.value })}
          required
        />
        <div className="row">
          <div style={{ flex: 1 }}>
            <label>Type</label>
            <select
              value={form.resourceType}
              onChange={(e) => setForm({ ...form, resourceType: e.target.value })}
            >
              {["notes", "pyq", "lab_solution", "practice_test", "flashcard", "video"].map(
                (t) => (
                  <option key={t}>{t}</option>
                )
              )}
            </select>
          </div>
          <div style={{ flex: 1 }}>
            <label>Required tier</label>
            <select
              value={form.requiredTier}
              onChange={(e) => setForm({ ...form, requiredTier: e.target.value })}
            >
              {["bronze", "silver", "gold", "platinum"].map((t) => (
                <option key={t}>{t}</option>
              ))}
            </select>
          </div>
        </div>
        <label>Topic</label>
        <input
          value={form.topic}
          onChange={(e) => setForm({ ...form, topic: e.target.value })}
        />
        <label>File URL</label>
        <input
          value={form.fileUrl}
          onChange={(e) => setForm({ ...form, fileUrl: e.target.value })}
          placeholder="https://…"
          required
        />
        <button>Add resource</button>
      </form>
    </div>
  );
}

function Analytics({ courseId }) {
  const { data, loading, error, reload } = useAsync(
    () => api.courseAnalytics(courseId),
    [courseId]
  );
  if (loading) return <p className="muted">Loading…</p>;
  if (error) return <Alert error={error} />;
  return (
    <div className="card">
      <div className="row" style={{ justifyContent: "space-between" }}>
        <h3>Course analytics</h3>
        <button className="ghost small" onClick={reload}>
          Refresh
        </button>
      </div>
      <div className="row" style={{ justifyContent: "space-between" }}>
        <Stat label="Sessions" value={data.totalSessions} />
        <Stat label="Students" value={data.totalStudents} />
        <Stat label="Avg attendance" value={`${data.averageAttendancePercentage}%`} />
      </div>
      <p className="muted" style={{ marginTop: 14 }}>Weak topics (lowest quiz accuracy)</p>
      {data.weakTopics.length ? (
        <table>
          <thead>
            <tr>
              <th>Topic</th>
              <th>Responses</th>
              <th>Accuracy</th>
            </tr>
          </thead>
          <tbody>
            {data.weakTopics.map((t) => (
              <tr key={t.topic}>
                <td>{t.topic}</td>
                <td>{t.responses}</td>
                <td>{t.accuracy}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <p className="muted">No quiz data yet.</p>
      )}
    </div>
  );
}
