# AttendIQ COA — Frontend (React PWA)

Phone-first single-page app for the AttendIQ COA platform. It provides the
student, faculty, and admin experiences described in the design document,
talking to the FastAPI backend over `/api/v1`.

> **Stack note:** the design suggests React + Next.js. This implementation uses
> **Vite + React** for a lightweight, fully self-contained SPA (installable as a
> PWA via `manifest.webmanifest`). The API client is framework-agnostic, so it
> ports cleanly to Next.js if server rendering is later required.

## Tech stack

- React 18 + React Router
- Vite 5 build tooling
- Plain CSS (dark, mobile-first) — no UI framework dependency
- PWA manifest + SVG icon for installability

## Run

The backend must be running first (see [`../backend/README.md`](../backend/README.md)):

```bash
cd backend && uvicorn app.main:app --reload   # http://localhost:8000
```

Then, in another terminal:

```bash
cd frontend
npm install
npm run dev        # http://localhost:5173 (proxies /api -> :8000)
```

Log in with a demo account (password `Password@123`):

| Role | Email |
|---|---|
| Student | `student1@attendiq.edu` |
| Faculty | `faculty@attendiq.edu` |
| Admin | `admin@attendiq.edu` |

### Production build

```bash
npm run build      # outputs to dist/
npm run preview    # serve the built app
```

Set `VITE_API_BASE` to point at a non-default API origin when building for
deployment (defaults to `/api/v1`).

## Features by role

**Student**
- Course selector
- QR check-in (session ID + rotating QR payload)
- Live concept-check quiz answering
- Attendance summary and reward-tier progress
- Tiered resource list (locked/unlocked by tier)
- **AI concept feedback** — upload a handwritten answer image or `.txt`
  transcript; view OCR text, detected/missing COA concepts, coverage score, and
  recommended resources (Phase 2)

**Faculty**
- Create + start a session, display the rotating QR, live attendance counters
- Launch concept-check quizzes and view quiz analytics
- Upload resources and map them to reward tiers
- Course analytics with weak-topic detection

**Admin**
- Create courses/sections, enroll students
- Browse audit logs

## Structure

```
frontend/
├── index.html
├── vite.config.js          # dev proxy to the backend
├── public/                 # PWA manifest + icon
└── src/
    ├── main.jsx            # app bootstrap
    ├── App.jsx             # role-based shell
    ├── styles.css
    ├── lib/
    │   ├── api.js          # API client (envelope-aware, JWT)
    │   └── auth.jsx        # auth context
    ├── components/ui.jsx   # shared UI helpers
    └── pages/              # Login, Student/Faculty/Admin dashboards
```
