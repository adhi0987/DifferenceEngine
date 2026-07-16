# AttendIQ COA — Backend (Phase 1 MVP)

FastAPI implementation of the AttendIQ COA platform described in
[`README_AttendIQ_COA_System_Design_v3_Full.md`](../README_AttendIQ_COA_System_Design_v3_Full.md).

This service covers the **Phase 1 MVP**: authentication, course/enrollment
management, class sessions, rotating-QR attendance with a verification engine,
in-class quizzes and participation scoring, tiered resource unlocking, reward
computation, faculty analytics, and audit logging. (Phase 2 AI/OCR is out of
scope.)

## Tech stack

| Layer | Choice |
|---|---|
| Framework | FastAPI |
| ORM | SQLAlchemy 2.x |
| Database | SQLite by default (zero-config); PostgreSQL-ready via `DATABASE_URL` |
| Auth | Custom JWT (PyJWT) + PBKDF2 password hashing (stdlib) |
| Tests | pytest + Starlette TestClient |

The design recommends PostgreSQL in production. The models are portable —
point `DATABASE_URL` at `postgresql+psycopg://...` and run against the schema in
[`../database/schema.sql`](../database/schema.sql).

## Quick start

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Seed demo data (creates ./attendiq.db)
python -m app.seed

# Run the API
uvicorn app.main:app --reload
```

Open interactive docs at http://localhost:8000/docs.

### Demo accounts (password: `Password@123`)

| Role | Email |
|---|---|
| Admin | `admin@attendiq.edu` |
| Faculty | `faculty@attendiq.edu` |
| Student | `student1@attendiq.edu` … `student5@attendiq.edu` |

## Configuration (environment variables)

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./attendiq.db` | SQLAlchemy connection URL |
| `JWT_SECRET` | `dev-secret-change-me` | JWT + QR signing secret (set a strong value in prod) |
| `ACCESS_TOKEN_TTL_SECONDS` | `3600` | Access token lifetime |
| `QR_ROTATION_SECONDS` | `30` | Rotating QR token window |
| `ALLOW_OPEN_REGISTRATION` | `true` | Allow self-registration of any role (demo) |
| `API_PREFIX` | `/api/v1` | Base path for all endpoints |

## API overview (`/api/v1`)

- **Auth:** `POST /auth/register`, `POST /auth/login`, `POST /auth/logout`
- **Courses:** `GET /courses`, `POST /admin/courses`, `POST /admin/enrollments`
- **Sessions:** `POST /faculty/sessions`, `.../start`, `.../close`, `.../live`
- **Attendance:** `GET /faculty/sessions/{id}/qr`,
  `POST /student/attendance/check-in`, `GET /student/attendance/summary`,
  `POST /faculty/attendance/{id}/override`
- **Quizzes:** `POST /faculty/sessions/{id}/quizzes`,
  `GET /student/sessions/{id}/active-quiz`,
  `POST /student/quizzes/{id}/responses`,
  `GET /faculty/sessions/{id}/quiz-analytics`
- **Resources & rewards:** `POST /faculty/resources`,
  `GET /student/resources`, `GET /student/rewards`
- **Analytics & audit:** `GET /faculty/analytics/course/{id}`,
  `GET /admin/audit-logs`

All responses use a standard envelope:

```json
{ "success": true, "message": "...", "data": { }, "error": null }
```

## Verification engine

`POST /student/attendance/check-in` validates the signed, short-lived QR payload
(HMAC-signed, rotating every `QR_ROTATION_SECONDS` with a one-window grace
period), the device session, and optional classroom proximity signal. It
computes a `risk_score` (0–100); low risk is auto-`verified`, higher risk is
flagged `pending_review` for faculty override.

## Reward tiers

Reward status is recomputed on check-in, quiz submission, and summary/reward
reads. Attendance percentage + participation score are matched against
per-course `reward_policies` to resolve `bronze → silver → gold → platinum`.
Resource visibility is gated by the student's current tier.

## Tests

```bash
cd backend
pytest
```

The suite spins up an isolated SQLite database, seeds demo data, and exercises
the full flows: auth, RBAC, session lifecycle, QR check-in (valid/invalid/
duplicate), quizzes, resource gating, override, audit, and analytics.

## Project layout

```
backend/
├── app/
│   ├── main.py          # FastAPI app + error envelope + router wiring
│   ├── config.py        # Env-driven settings
│   ├── database.py      # Engine, session, Base
│   ├── models.py        # SQLAlchemy models (design section 8)
│   ├── schemas.py       # Pydantic request/response models
│   ├── security.py      # Password hashing + JWT
│   ├── deps.py          # Auth + role-based access dependencies
│   ├── seed.py          # Demo data seeding
│   ├── routers/         # auth, courses, sessions, attendance, quizzes,
│   │                    #   resources, analytics
│   └── services/        # qr, rewards, audit
└── tests/
```
