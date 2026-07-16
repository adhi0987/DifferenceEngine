// Thin API client for the AttendIQ COA backend (/api/v1).
// Stores the JWT in localStorage and unwraps the standard response envelope.

const BASE = import.meta.env.VITE_API_BASE || "/api/v1";
const TOKEN_KEY = "attendiq_token";
const USER_KEY = "attendiq_user";

export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function getStoredUser() {
  const raw = localStorage.getItem(USER_KEY);
  return raw ? JSON.parse(raw) : null;
}

export function setSession(token, user) {
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function clearSession() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

async function request(path, { method = "GET", body, form } = {}) {
  const headers = {};
  const token = getToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;

  let payload;
  if (form) {
    payload = form; // FormData; browser sets content-type
  } else if (body !== undefined) {
    headers["Content-Type"] = "application/json";
    payload = JSON.stringify(body);
  }

  const res = await fetch(`${BASE}${path}`, { method, headers, body: payload });
  let data = null;
  try {
    data = await res.json();
  } catch {
    /* no body */
  }

  if (!res.ok || (data && data.success === false)) {
    const message =
      (data && (data.message || (data.error && data.error.details))) ||
      `Request failed (${res.status})`;
    const err = new Error(message);
    err.status = res.status;
    err.code = data && data.error && data.error.code;
    throw err;
  }
  return data ? data.data : null;
}

export const api = {
  // Auth
  login: (email, password) =>
    request("/auth/login", { method: "POST", body: { email, password } }),
  register: (payload) =>
    request("/auth/register", { method: "POST", body: payload }),
  logout: () => request("/auth/logout", { method: "POST", body: {} }),

  // Courses / enrollment
  courses: () => request("/courses"),
  createCourse: (payload) =>
    request("/admin/courses", { method: "POST", body: payload }),
  enroll: (studentId, sectionId) =>
    request("/admin/enrollments", { method: "POST", body: { studentId, sectionId } }),

  // Sessions
  createSession: (payload) =>
    request("/faculty/sessions", { method: "POST", body: payload }),
  startSession: (id) =>
    request(`/faculty/sessions/${id}/start`, { method: "POST", body: {} }),
  closeSession: (id) =>
    request(`/faculty/sessions/${id}/close`, { method: "POST", body: {} }),
  liveSession: (id) => request(`/faculty/sessions/${id}/live`),
  sessionQr: (id) => request(`/faculty/sessions/${id}/qr`),

  // Attendance
  checkIn: (payload) =>
    request("/student/attendance/check-in", { method: "POST", body: payload }),
  attendanceSummary: (courseId) =>
    request(`/student/attendance/summary?courseId=${courseId}`),
  override: (attendanceId, payload) =>
    request(`/faculty/attendance/${attendanceId}/override`, {
      method: "POST",
      body: payload,
    }),

  // Quizzes
  launchQuiz: (sessionId, questionId, durationSeconds) =>
    request(`/faculty/sessions/${sessionId}/quizzes`, {
      method: "POST",
      body: { questionId, durationSeconds },
    }),
  activeQuiz: (sessionId) =>
    request(`/student/sessions/${sessionId}/active-quiz`),
  answerQuiz: (sessionQuizId, selectedOption) =>
    request(`/student/quizzes/${sessionQuizId}/responses`, {
      method: "POST",
      body: { selectedOption },
    }),
  quizAnalytics: (sessionId) =>
    request(`/faculty/sessions/${sessionId}/quiz-analytics`),

  // Resources / rewards
  createResource: (payload) =>
    request("/faculty/resources", { method: "POST", body: payload }),
  studentResources: (courseId) =>
    request(`/student/resources?courseId=${courseId}`),
  rewards: (courseId) => request(`/student/rewards?courseId=${courseId}`),

  // Analytics / audit
  courseAnalytics: (courseId) =>
    request(`/faculty/analytics/course/${courseId}`),
  auditLogs: (entityType) =>
    request(`/admin/audit-logs${entityType ? `?entityType=${entityType}` : ""}`),

  // AI
  aiUpload: (file) => {
    const form = new FormData();
    form.append("file", file);
    return request("/student/ai/uploads", { method: "POST", form });
  },
  aiSubmit: (courseId, imageFileUrl, sessionId) =>
    request("/student/ai/submissions", {
      method: "POST",
      body: { courseId, imageFileUrl, sessionId },
    }),
  aiResult: (submissionId) =>
    request(`/student/ai/submissions/${submissionId}`),
};
