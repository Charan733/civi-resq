# CIVI-RESQ — AI-Powered Urban Infrastructure Risk & Intervention Planning System

A decision-support platform for civil engineers and urban planners: identify vulnerable
urban zones, understand *why* they're at risk (explainable AI), predict flood/heat/
accessibility risk severity, and get ranked civil-engineering intervention recommendations.

Built as a multidisciplinary Civil Engineering + Computer Science final-year project,
demonstrated on a real Guntur/Vijayawada (Andhra Pradesh) demo dataset — a genuinely
flood-prone Krishna-delta region.

**Status:** AI-assisted preliminary risk assessment and decision-support tool. Not a
certified structural safety or engineering-certification system.

---

## Architecture

```
Urban Data → AI Risk Prediction → Explainable Risk Analysis → GIS Visualization
→ Civil Intervention Recommendation → Priority Ranking → What-If Simulation → Decision Support
```

| Layer | Technology |
|---|---|
| Frontend | React (Vite) + Tailwind CSS + Leaflet (GIS map) + Recharts |
| Backend | Python 3.11+ / FastAPI |
| Database | PostgreSQL 15+ with PostGIS extension |
| ML | scikit-learn / XGBoost (flood, heat, accessibility risk regressors) |
| Explainability | SHAP (per-prediction feature-importance breakdown) |
| Reports | ReportLab (downloadable PDF risk reports) |
| Auth | JWT (python-jose) + bcrypt, role-based (admin / civil_engineer / viewer) |

```
civi-resq/
├── backend/
│   ├── app/
│   │   ├── main.py                # FastAPI entrypoint
│   │   ├── config.py               # env-var settings
│   │   ├── database.py             # SQLAlchemy engine/session
│   │   ├── auth.py                 # JWT + role-based access
│   │   ├── models/db_models.py     # SQLAlchemy + PostGIS models
│   │   ├── schemas/schemas.py      # Pydantic request/response models
│   │   ├── routers/                # API endpoints (zones, simulate, analytics, assistant, reports, auth)
│   │   └── services/
│   │       ├── risk_engine.py           # ML prediction + SHAP explanation
│   │       ├── intervention_engine.py    # rule-based intervention ranking
│   │       ├── simulator.py              # what-if before/after comparison
│   │       ├── assistant.py              # data-grounded Q&A
│   │       └── report_generator.py       # PDF report generation
│   ├── ml/
│   │   ├── generate_training_data.py     # domain-formula synthetic training set
│   │   ├── train_models.py                # trains + evaluates 3 XGBoost models
│   │   └── trained_models/                # saved .joblib models + metrics.json
│   ├── scripts/
│   │   ├── generate_demo_data.py          # Guntur/Vijayawada demo zone generator
│   │   └── seed_db.py                      # creates tables + seeds DB
│   ├── data/demo_zones.json
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/       # Dashboard, RiskMap, ZoneDetail, Simulator, Assistant, Login, UploadData
│   │   ├── components/  # Shell (nav), RiskStamp (risk badge)
│   │   ├── context/     # AuthContext
│   │   └── api/client.js
│   └── package.json
└── docker-compose.yml    # PostGIS database (recommended)
```

---

## Prerequisites

- Python 3.11+
- Node.js 18+
- Docker Desktop (recommended, for PostGIS) — or a local PostgreSQL 15+ with PostGIS installed manually
- Git

---

## Setup

### 1. Start the database

**Option A — Docker (recommended):**
```bash
docker compose up -d
```

**Option B — Local PostgreSQL:**
Install PostgreSQL + PostGIS, then:
```bash
sudo -u postgres psql -c "CREATE USER civiresq WITH PASSWORD 'civiresq_pass';"
sudo -u postgres psql -c "CREATE DATABASE civiresq_db OWNER civiresq;"
sudo -u postgres psql -d civiresq_db -c "CREATE EXTENSION IF NOT EXISTS postgis;"
```
Either way, **make sure the database service is running before starting the backend** —
if you stop/restart your machine, start it again first (`docker compose up -d` or
`sudo service postgresql start`).

### 2. Backend setup

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env            # then edit SECRET_KEY, DATABASE_URL if needed
```

**Train the ML models** (only needed once, or whenever you change the training formulas):
```bash
python3 ml/generate_training_data.py
python3 ml/train_models.py
```
This trains 3 XGBoost regressors (flood/heat/accessibility risk) and saves them + evaluation
metrics (MAE/RMSE/R²) to `ml/trained_models/`.

**Generate demo data + seed the database:**
```bash
python3 scripts/generate_demo_data.py
python3 scripts/seed_db.py
```
This creates all tables, seeds 26 real Guntur/Vijayawada zones with full risk assessments,
and creates two demo users:
- `admin@civiresq.gov.in` / `Admin@12345` (full access)
- `engineer@civiresq.gov.in` / `Engineer@12345` (can upload data, run simulations)

**Run the backend:**
```bash
uvicorn app.main:app --reload
```
API docs (Swagger UI): http://localhost:8000/docs

### 3. Frontend setup

```bash
cd frontend
npm install
cp .env.example .env   # confirm VITE_API_BASE_URL points to your backend
npm run dev
```
App runs at http://localhost:5173

---

## Using the platform

1. **Dashboard** — overview stats, risk distribution, ML model performance metrics
2. **Risk Map** — color-coded zones (green/yellow/orange/red), filter by risk category, search, click a zone for details
3. **Zone Detail** — full parameters, risk scores, SHAP explainability charts, ranked interventions, downloadable PDF report
4. **What-If Simulator** — adjust drainage/green-cover/road-access/imperviousness sliders, see predicted before/after risk
5. **CIVI-AI Assistant** — ask "Why is this zone high risk?", "Which intervention should be prioritized?", "What happens if drainage improved by 30%?" — answers are generated from real system data, never fabricated
6. **Upload Data** (admin/civil_engineer only) — upload a CSV of real municipal zone data; each row is automatically assessed on upload

---

## Replacing demo data with real data

The demo dataset (`backend/data/demo_zones.json`) is synthetic but grounded in real Guntur/
Vijayawada geography and IMD monsoon rainfall averages — it exists so the app works
immediately. To connect real data:

1. Export real ward/zone boundaries + parameters (rainfall, elevation, drainage, land use,
   etc.) to CSV matching the columns listed on the **Upload Data** page.
2. Upload via the UI, or `POST /api/zones/upload-csv` directly.
3. No code changes needed — the ML models, risk engine, and intervention engine all operate
   on the same parameter schema regardless of data source.

For production-scale ML, retrain the models (`ml/train_models.py`) on real historical
flood/heat-event outcome data once available, instead of the domain-formula synthetic
training set used for this demo.

---

## Model methodology notes

- **Flood / Heat / Accessibility risk scores** are ML-predicted (XGBoost regressors),
  each explained per-prediction via SHAP.
- **Overall Vulnerability Score** is a transparent **rule-based weighted composite**
  (45% flood + 25% heat + 30% accessibility) — deliberately *not* a black-box model output,
  so engineers can audit and adjust the formula directly (`app/services/risk_engine.py`).
- **Intervention recommendations** are rule-based (if/then conditions grounded in standard
  civil-engineering practice), ranked by an auditable priority-score formula
  (`app/services/intervention_engine.py`) — not a black box either.
- Training data for the ML models is synthetic, generated from established urban-hydrology
  and urban-heat-island engineering relationships (documented in
  `ml/generate_training_data.py`), since no single public dataset already joins all these
  parameters. This is standard practice for a preliminary/demo-stage system; swap in real
  historical outcome data for production use.

## Disclaimer

CIVI-RESQ is an AI-assisted preliminary urban risk assessment and decision-support tool.
It does not constitute certified structural safety engineering, a substitute for
professional site assessment, or an official regulatory determination.

--commands to run
Terminal 1 — Start the database

cd C:\Users\LENOVO\Downloads\civi-resq\civi-resq
docker compose up -d

Terminal 2 — Start the backend

cd C:\Users\LENOVO\Downloads\civi-resq\civi-resq\backend
venv\Scripts\Activate.ps1
uvicorn app.main:app

Wait for Application startup complete and Uvicorn running on http://127.0.0.1:8000.

Terminal 3 — Start the frontend (open a new terminal, Ctrl+Shift+`)

cd C:\Users\LENOVO\Downloads\civi-resq\civi-resq\frontend
npm run dev

Then open your browser:

http://localhost:5173

Log in with:

Email: admin@civiresq.gov.in
Password: Admin@12345