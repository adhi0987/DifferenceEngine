# DifferenceEngine — AttendIQ COA

Privacy-first classroom engagement platform for **Computer Organization and
Architecture (COA)** classes. Attendance is the entry point to unlock learning
value: presence verification → participation checkpoints → reward-based resource
unlocking → faculty analytics.

The full system design lives in
[`README_AttendIQ_COA_System_Design_v3_Full.md`](./README_AttendIQ_COA_System_Design_v3_Full.md).

## What's built

Two runnable pieces plus the reference database schema:

### Backend — [`backend/`](./backend) (FastAPI + SQLAlchemy)

**Phase 1 MVP:**
- Authentication with JWT and role-based access (student / faculty / admin)
- Course, section, classroom, and enrollment management
- Class session lifecycle (create → start → close → live monitoring)
- Rotating-QR attendance with a verification engine and risk scoring
- In-class quizzes, participation scoring, and quiz analytics
- Tiered resource unlocking and reward computation (bronze → platinum)
- Faculty course analytics (attendance, weak topics) and audit logging

**Phase 2 Edge AI:**
- Note-image upload → object storage → OCR → COA concept extraction →
  coverage scoring → resource recommendations, persisted as feedback
- Runs with zero heavy ML dependencies via graceful fallbacks; upgrades to a
  fine-tuned **T5 + LoRA** model and Tesseract OCR when configured

### Frontend — [`frontend/`](./frontend) (Vite + React PWA)

Phone-first, installable PWA with role-based dashboards for students
(check-in, quizzes, attendance, rewards, resources, AI feedback), faculty
(sessions, live QR, quiz launch/analytics, resources), and admins (courses,
enrollments, audit).

## Getting started

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m app.seed          # demo data
uvicorn app.main:app --reload
```

Interactive API docs: http://localhost:8000/docs — see
[`backend/README.md`](./backend/README.md) for endpoints, config, and demo
accounts.

### Frontend

```bash
cd frontend
npm install
npm run dev                 # proxies /api and /health to the backend
```

See [`frontend/README.md`](./frontend/README.md) for details.

## Repository layout

```
.
├── backend/                # FastAPI backend (Phase 1 MVP + Phase 2 AI)
├── frontend/               # Vite + React PWA (role-based dashboards)
├── database/schema.sql     # PostgreSQL reference schema
└── README_AttendIQ_COA_System_Design_v3_Full.md   # Full system design + SRS
```

## Tests

```bash
cd backend && pytest
```
