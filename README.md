# DifferenceEngine — AttendIQ COA

Privacy-first classroom engagement platform for **Computer Organization and
Architecture (COA)** classes. Attendance is the entry point to unlock learning
value: presence verification → participation checkpoints → reward-based resource
unlocking → faculty analytics.

The full system design lives in
[`README_AttendIQ_COA_System_Design_v3_Full.md`](./README_AttendIQ_COA_System_Design_v3_Full.md).

## What's built

The **Phase 1 MVP backend** is implemented in [`backend/`](./backend) with
FastAPI + SQLAlchemy:

- Authentication with JWT and role-based access (student / faculty / admin)
- Course, section, classroom, and enrollment management
- Class session lifecycle (create → start → close → live monitoring)
- Rotating-QR attendance with a verification engine and risk scoring
- In-class quizzes, participation scoring, and quiz analytics
- Tiered resource unlocking and reward computation (bronze → platinum)
- Faculty course analytics (attendance, weak topics) and audit logging

> Phase 2 (Edge AI — OCR + T5/LoRA concept feedback) is described in the design
> document and is intentionally not part of this MVP.

## Getting started

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

## Repository layout

```
.
├── backend/                # FastAPI Phase 1 MVP (app, tests)
├── database/schema.sql     # PostgreSQL reference schema
└── README_AttendIQ_COA_System_Design_v3_Full.md   # Full system design + SRS
```

## Tests

```bash
cd backend && pytest
```
