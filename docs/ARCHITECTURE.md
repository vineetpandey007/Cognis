# Cognis — System Architecture, Schema & API Reference

This document details the backend data model, service architecture, REST API endpoints, and cloud deployment workflow for **Cognis (Modules 0–7)**.

---

## 1. Modular Architecture & Data Flow

```text
[React + Vite UI] --(JWT Bearer)--> [FastAPI /api/v1 Routers]
                                           |
            +------------------------------+------------------------------+
            |                              |                              |
     [LMS Service]                   [CRM Service]               [Analytics Service]
  - Module completion             - Candidate listing           - Pandas DataFrame
  - Quiz score averaging          - Stage override              - Cohort aggregations
  - Auto-promotion rules          - Immutable AuditLog          - At-risk alerts (>5d / <60%)
            |                              |                    - CSV export stream
            +------------------------------+------------------------------+
                                           |
                           [SQLAlchemy ORM -> SQLite / PostgreSQL]
```

### Automated Placement Promotion Rules
1. **`Enrolled` -> `Screening`**: Triggered automatically when a learner reaches `>= 40%` module completion.
2. **`Screening` -> `Interview_Ready`**: Triggered automatically when a learner reaches `>= 80%` module completion **and** maintains `>= 75%` average quiz score.
3. **`Placed` (or Manual Overrides)**: Updated by `analyst_admin` users via the Placement CRM, writing both a `TelemetryEvent` and an immutable `AuditLog` entry (`actor_user_id`, `old_value`, `new_value`, `created_at`).

---

## 2. Normalized Database Schema

| Table | Primary Key | Key Columns & Relationships |
| :--- | :--- | :--- |
| `users` | `user_id` | `full_name`, `email` (unique), `password_hash`, `role` (`student` / `analyst_admin`), `cohort`, `created_at` |
| `courses` | `course_id` | `title`, `domain`, `description`, `total_modules` |
| `enrollments` | `enrollment_id` | `user_id` (FK), `course_id` (FK), `modules_completed`, `quizzes_taken`, `avg_quiz_score`, `crm_stage`, `last_active` |
| `telemetry_events` | `event_id` | `user_id` (FK), `course_id` (FK), `event_type` (`module_complete`, `quiz_submit`, `crm_stage_change`), `metric_value`, `recorded_at` |
| `audit_logs` | `audit_id` | `actor_user_id` (FK), `target_enrollment_id` (FK), `action`, `old_value`, `new_value`, `created_at` |

---

## 3. REST API Reference (`/api/v1`)

### System & Auth
| Method | Endpoint | Access | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/health` | Public | Service health check |
| `POST` | `/api/v1/auth/register` | Public | Register user (`student` auto-enrolled into courses) & return JWT |
| `POST` | `/api/v1/auth/login` | Public | Authenticate credentials & return `HS256` Bearer JWT |
| `GET` | `/api/v1/auth/me` | Authenticated | Return current user profile |

### LMS Portal
| Method | Endpoint | Access | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/lms/my-courses` | Authenticated | Fetch enrolled courses, completion %, quiz avg & CRM stage |
| `POST` | `/api/v1/lms/complete-module` | Authenticated | Record module completion, log telemetry & evaluate auto-promotion |
| `POST` | `/api/v1/lms/submit-quiz` | Authenticated | Update running quiz average, log telemetry & evaluate auto-promotion |

### Placement CRM & BI Analytics
| Method | Endpoint | Access | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/crm/candidates` | `analyst_admin` | List all learner enrollments with completion, quiz avg & CRM stage |
| `PATCH` | `/api/v1/crm/candidates/{enrollment_id}/stage` | `analyst_admin` | Update candidate stage & write immutable `audit_logs` record |
| `GET` | `/api/v1/analytics/summary` | `analyst_admin` | Pandas cohort KPIs, stage funnel, cohort breakdown & at-risk learners |
| `GET` | `/api/v1/analytics/export/csv` | `analyst_admin` | Download clean CSV telemetry snapshot (`cognis_cohort_telemetry.csv`) |

---

## 4. Security & Data Hygiene Safeguards

- **Password Storage:** Per-user 16-byte random salt with `PBKDF2-HMAC-SHA256` (120,000 iterations) and constant-time comparison (`hmac.compare_digest`).
- **Role Enforcement:** Admin analytics and CRM endpoints enforce `require_analyst_admin` (returning `403 Forbidden` to non-admin tokens).
- **Schema Validation:** All inbound payloads are strictly validated via Pydantic v2 (`EmailStr`, bounded quiz scores `0-100`, literal stage enums).
- **Repository Hygiene:** `.gitignore` excludes `.env`, `*.db`, `venv/`, `node_modules/`, and `dist/` so local credentials and databases are never pushed to version control.

---

## 5. Production Deployment (Render + Vercel)

1. **Backend (Render Web Service):**
   - Root Directory: `backend`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python seed.py && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - Env Vars: `SECRET_KEY` (32+ random characters), `CORS_ORIGINS` (your Vercel URL, no trailing slash)
2. **Frontend (Vercel):**
   - Root Directory: `frontend` (Vite preset; `vercel.json` handles SPA rewrites)
   - Env Var: `VITE_API_BASE_URL=https://<your-render-service>.onrender.com/api/v1`
