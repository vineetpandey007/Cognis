# Cognis — LMS, Placement CRM & Data Analytics Suite

**Cognis** is a full-stack, analytics-first Learning Management System (LMS), Placement Readiness CRM, and Business Intelligence (BI) Telemetry Dashboard built entirely with permissive open-source technologies (**FastAPI, SQLAlchemy, Pandas, React, Vite, Tailwind CSS, and Recharts**).

Instead of treating course delivery and career analytics as disconnected silos, Cognis writes every learner action to a normalized telemetry stream that powers live cohort health KPIs, automated placement-stage promotions, at-risk learner alerts, and one-click CSV data exports.

---

## Key Capabilities (Modules 0–7)

- **Role-Based Access Control (RBAC):** Isolated `student` and `analyst_admin` portals protected by salted `PBKDF2-SHA256` password hashing and `HS256` JWT Bearer authentication.
- **Learner Portal (`/learn`):** Interactive course progress tracking, module completion controls, assessment quiz submission, and automatic CRM stage promotion (`Enrolled` -> `Screening` at `>=40%` completion; `Interview_Ready` at `>=80%` completion and `>=75%` quiz average).
- **BI Command Center (`/analytics`):** Pandas-powered executive dashboard displaying total learners, average completion rate, average quiz score, placement pipeline funnel chart, cohort completion vs. quiz score comparison chart, at-risk learner alerts (`>5 days` inactive or `<60%` quiz average), and one-click CSV telemetry export (`cognis_cohort_telemetry.csv`).
- **Placement CRM Pipeline (`/crm`):** Stage-filterable candidate management (`Enrolled` -> `Screening` -> `Interview_Ready` -> `Placed`) where every manual stage override is recorded in an immutable `audit_logs` table.
- **Synthetic Cohort Seeder:** Idempotent Python seeder (`seed.py`) pre-populating 50 realistic learners across 3 cohorts (`COG-DA-2026-Q4`, `COG-AI-2026-Q4`, `COG-NT-2026-Q4`), 2 tracks, and historical telemetry events.

---

## Tech Stack (100% Open Source)

| Layer | Technologies |
| :--- | :--- |
| **Backend API** | Python 3, FastAPI, Uvicorn, Pydantic v2, pydantic-settings |
| **Database & ORM** | SQLAlchemy 2.0, SQLite (local) / PostgreSQL-compatible |
| **Analytics & Auth** | Pandas, PyJWT (`HS256`), Python `hashlib` (`PBKDF2-SHA256`) |
| **Frontend UI** | React 18, Vite 5, React Router v6, Axios, Tailwind CSS v3, Recharts |
| **Testing** | Pytest, Starlette/HTTPX `TestClient` |

---

## Project Structure

```text
lms-analytics-portal/
├── backend/
│   ├── requirements.txt
│   ├── .env.example
│   ├── seed.py
│   ├── app/
│   │   ├── main.py
│   │   ├── core/          # Config, SQLAlchemy engine, PBKDF2/JWT security
│   │   ├── models/        # Normalized 5-table ORM schema
│   │   ├── schemas/       # Pydantic v2 request/response contracts
│   │   ├── services/      # LMS auto-promotion, CRM audit log, Pandas BI
│   │   └── api/           # RBAC dependencies & /api/v1 routers
│   └── tests/             # End-to-end Pytest suite
├── frontend/
│   ├── package.json
│   ├── vercel.json        # SPA routing rewrites
│   └── src/
│       ├── api/           # Axios JWT interceptor
│       ├── context/       # AuthContext session provider
│       ├── components/    # Navbar & KPI cards
│       └── pages/         # Login, Learner Portal, BI Dashboard, CRM Pipeline
├── docs/
│   └── ARCHITECTURE.md    # Schema, API reference & deployment guide
├── LICENSE
└── README.md
```

---

## Local Quick Start (Windows Command Prompt)

### 1. Backend API
```cmd
cd backend
python -m venv venv
venv\Scripts\activate.bat
pip install -r requirements.txt
copy .env.example .env
python seed.py
pytest -v
uvicorn app.main:app --reload --port 8000
```
- Health Check: `http://localhost:8000/health`
- Interactive Swagger Docs: `http://localhost:8000/docs`

### 2. Frontend UI (Open a second Command Prompt)
```cmd
cd frontend
npm install
copy .env.example .env
npm run dev
```
- Web Portal: `http://localhost:5173`

---

## Demo Credentials

Seeded automatically by `python seed.py`:

| Role | Email | Password | Default Route |
| :--- | :--- | :--- | :--- |
| **Analyst / Admin** | `admin@cognis.dev` | `Admin@1234` | `/analytics` & `/crm` |
| **Learner** | `student@cognis.dev` | `Student@1234` | `/learn` |

---

## Documentation & License

- Detailed relational schema, REST API reference, and Render/Vercel deployment instructions are available in [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).
- Released under the [MIT License](LICENSE).
