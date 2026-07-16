import { useEffect, useState } from "react";
import { api } from "../lib/api.js";
import { Alert, Badge, CourseSelect, Tabs, useAsync } from "../components/ui.jsx";

const TABS = [
  { key: "checkin", label: "Check-in" },
  { key: "quiz", label: "Quiz" },
  { key: "attendance", label: "Attendance" },
  { key: "rewards", label: "Rewards" },
  { key: "resources", label: "Resources" },
  { key: "ai", label: "AI Feedback" },
];

export default function StudentDashboard() {
  const { data: courses, loading } = useAsync(() => api.courses(), []);
  const [section, setSection] = useState("");
  const [tab, setTab] = useState("checkin");

  useEffect(() => {
    if (courses && courses.length && !section) setSection(courses[0].sectionId);
  }, [courses, section]);

  const course = (courses || []).find((c) => c.sectionId === section);

  if (loading) return <p className="muted">Loading…</p>;
  if (!courses || !courses.length)
    return <p className="muted">You are not enrolled in any course yet.</p>;

  return (
    <>
      <div className="card">
        <label>Course</label>
        <CourseSelect courses={courses} value={section} onChange={setSection} />
      </div>

      <Tabs tabs={TABS} active={tab} onChange={setTab} />

      {tab === "checkin" && <CheckIn />}
      {tab === "quiz" && <Quiz />}
      {tab === "attendance" && course && <AttendanceSummary courseId={course.courseId} />}
      {tab === "rewards" && course && <Rewards courseId={course.courseId} />}
      {tab === "resources" && course && <Resources courseId={course.courseId} />}
      {tab === "ai" && course && <AiFeedback courseId={course.courseId} />}
    </>
  );
}

function CheckIn() {
  const [sessionId, setSessionId] = useState("");
  const [qr, setQr] = useState("");
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);

  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    setResult(null);
    try {
      const data = await api.checkIn({ sessionId, qrPayload: qr });
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="card">
      <h3>Scan / enter QR to check in</h3>
      <p className="muted">
        Enter the active session ID and the QR payload shown by your faculty.
      </p>
      <form onSubmit={submit}>
        <label>Session ID</label>
        <input value={sessionId} onChange={(e) => setSessionId(e.target.value)} required />
        <label>QR payload</label>
        <textarea
          rows={3}
          value={qr}
          onChange={(e) => setQr(e.target.value)}
          placeholder="Paste the QR payload…"
          required
        />
        <button disabled={busy}>{busy ? "Checking in…" : "Check in"}</button>
      </form>
      <Alert error={error} />
      {result && (
        <div className="alert success" style={{ marginTop: 12 }}>
          <b>{result.verificationStatus.replace("_", " ")}</b> — risk score{" "}
          {result.riskScore}
          {result.reason ? ` (${result.reason})` : ""}
        </div>
      )}
    </div>
  );
}

function Quiz() {
  const [sessionId, setSessionId] = useState("");
  const [quiz, setQuiz] = useState(null);
  const [error, setError] = useState(null);
  const [msg, setMsg] = useState(null);

  async function load() {
    setError(null);
    setMsg(null);
    setQuiz(null);
    try {
      setQuiz(await api.activeQuiz(sessionId));
    } catch (err) {
      setError(err.message);
    }
  }

  async function answer(option) {
    try {
      const res = await api.answerQuiz(quiz.sessionQuizId, option);
      setMsg(
        res.isCorrect === null
          ? "Answer recorded."
          : res.isCorrect
          ? "Correct! 🎉"
          : "Recorded — not correct this time."
      );
      setQuiz(null);
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="card">
      <h3>Live concept check</h3>
      <div className="row">
        <input
          value={sessionId}
          onChange={(e) => setSessionId(e.target.value)}
          placeholder="Active session ID"
        />
        <button className="small" onClick={load} disabled={!sessionId}>
          Load quiz
        </button>
      </div>
      <Alert error={error} success={msg} />
      {quiz && (
        <div style={{ marginTop: 12 }}>
          <p className="muted">{quiz.topic}</p>
          <p>
            <b>{quiz.questionText}</b>
          </p>
          <div className="grid">
            {["A", "B", "C", "D"].map((opt) => {
              const text = quiz[`option${opt}`];
              if (!text) return null;
              return (
                <button key={opt} className="ghost" onClick={() => answer(opt)}>
                  {opt}. {text}
                </button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

function AttendanceSummary({ courseId }) {
  const { data, loading, error } = useAsync(
    () => api.attendanceSummary(courseId),
    [courseId]
  );
  if (loading) return <p className="muted">Loading…</p>;
  if (error) return <Alert error={error} />;
  return (
    <div className="card">
      <h3>Attendance summary</h3>
      <div className="row" style={{ justifyContent: "space-between" }}>
        <div>
          <div className="stat">{data.attendancePercentage}%</div>
          <div className="muted">
            {data.attendedSessions} / {data.totalSessions} sessions
          </div>
        </div>
        <div className="center">
          <div className="muted">Current tier</div>
          <Badge value={data.currentTier} />
        </div>
      </div>
    </div>
  );
}

function Rewards({ courseId }) {
  const { data, loading, error } = useAsync(() => api.rewards(courseId), [courseId]);
  if (loading) return <p className="muted">Loading…</p>;
  if (error) return <Alert error={error} />;
  return (
    <div className="card">
      <h3>Reward progress</h3>
      <div className="row" style={{ justifyContent: "space-between" }}>
        <div>
          <div className="muted">Current tier</div>
          <Badge value={data.currentTier} />
        </div>
        <div className="center">
          <div className="muted">Participation</div>
          <div className="stat">{data.participationScore}</div>
        </div>
        <div className="center">
          <div className="muted">Next tier</div>
          <Badge value={data.nextTier || "max"} />
        </div>
      </div>
      <table style={{ marginTop: 16 }}>
        <thead>
          <tr>
            <th>Tier</th>
            <th>Min attendance</th>
            <th>Min participation</th>
          </tr>
        </thead>
        <tbody>
          {data.tiers.map((t) => (
            <tr key={t.tier}>
              <td>
                <Badge value={t.tier} />
              </td>
              <td>{t.minAttendancePercentage}%</td>
              <td>{t.minParticipationScore}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Resources({ courseId }) {
  const { data, loading, error } = useAsync(
    () => api.studentResources(courseId),
    [courseId]
  );
  if (loading) return <p className="muted">Loading…</p>;
  if (error) return <Alert error={error} />;
  return (
    <div className="card">
      <h3>Learning resources</h3>
      {data.map((r) => (
        <div key={r.resourceId} className={`list-item ${r.locked ? "locked" : ""}`}>
          <div>
            <div>
              <b>{r.title}</b>
            </div>
            <div className="muted">
              {r.resourceType} · {r.topic || "general"}
            </div>
          </div>
          <div className="center">
            <Badge value={r.requiredTier} />
            <div style={{ marginTop: 6 }}>
              {r.locked ? (
                <span className="muted">🔒 Locked</span>
              ) : (
                <a href={r.fileUrl} target="_blank" rel="noreferrer">
                  Open
                </a>
              )}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

function AiFeedback({ courseId }) {
  const [file, setFile] = useState(null);
  const [status, setStatus] = useState(null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);

  async function submit(e) {
    e.preventDefault();
    if (!file) return;
    setBusy(true);
    setError(null);
    setResult(null);
    setStatus("Uploading…");
    try {
      const up = await api.aiUpload(file);
      setStatus("Submitting for analysis…");
      const sub = await api.aiSubmit(courseId, up.imageFileUrl);
      // Poll for completion.
      let res = await api.aiResult(sub.submissionId);
      for (let i = 0; i < 20 && res.processingStatus !== "completed"; i++) {
        if (res.processingStatus === "failed") break;
        await new Promise((r) => setTimeout(r, 400));
        res = await api.aiResult(sub.submissionId);
      }
      setResult(res);
      setStatus(null);
    } catch (err) {
      setError(err.message);
      setStatus(null);
    } finally {
      setBusy(false);
    }
  }

  const fb = result && result.modelFeedback;

  return (
    <div className="card">
      <h3>AI concept feedback (Phase 2)</h3>
      <p className="muted">
        Upload a handwritten answer image or a <code>.txt</code> transcript. OCR
        extracts the text, then the COA model detects concept coverage and
        recommends resources.
      </p>
      <form onSubmit={submit}>
        <input
          type="file"
          accept="image/*,.txt,.md"
          onChange={(e) => setFile(e.target.files[0])}
        />
        <button disabled={busy || !file}>{busy ? "Working…" : "Analyze"}</button>
      </form>
      {status && <p className="muted">{status}</p>}
      <Alert error={error} />
      {fb && (
        <div style={{ marginTop: 14 }}>
          <div className="row" style={{ justifyContent: "space-between" }}>
            <div>
              <div className="muted">Inferred topic</div>
              <b>{fb.inferredTopic || "—"}</b>
            </div>
            <div className="center">
              <div className="muted">Coverage</div>
              <div className="stat">{fb.conceptCoverageScore}%</div>
            </div>
          </div>
          <p className="muted" style={{ marginTop: 10 }}>Detected concepts</p>
          <div className="row">
            {fb.detectedConcepts.length ? (
              fb.detectedConcepts.map((c) => (
                <span key={c} className="badge verified">
                  {c}
                </span>
              ))
            ) : (
              <span className="muted">none detected</span>
            )}
          </div>
          <p className="muted" style={{ marginTop: 10 }}>Missing concepts</p>
          <div className="row">
            {fb.missingConcepts.length ? (
              fb.missingConcepts.map((c) => (
                <span key={c} className="badge pending_review">
                  {c}
                </span>
              ))
            ) : (
              <span className="muted">none — great coverage!</span>
            )}
          </div>
          {fb.recommendedResources && fb.recommendedResources.length > 0 && (
            <>
              <p className="muted" style={{ marginTop: 10 }}>
                Recommended resources
              </p>
              {fb.recommendedResources.map((r) => (
                <div key={r.resourceId} className="list-item">
                  <span>{r.title}</span>
                  <Badge value={r.requiredTier} />
                </div>
              ))}
            </>
          )}
          <details style={{ marginTop: 12 }}>
            <summary className="muted">Extracted text (OCR: {fb.ocrEngine})</summary>
            <p style={{ whiteSpace: "pre-wrap" }}>{result.extractedText}</p>
          </details>
        </div>
      )}
    </div>
  );
}
