# AI Governance Dashboard

[![CI](https://github.com/teja2704/AI-Governance-Dashboard/actions/workflows/ci.yml/badge.svg)](https://github.com/teja2704/AI-Governance-Dashboard/actions/workflows/ci.yml)

## Overview

AI Governance Dashboard is a full-stack AI monitoring and governance platform. It lets authenticated users generate AI responses via Google Gemini, store and inspect interactions, monitor model performance, and track governance metrics through an interactive dashboard.

### Live Deployment

| Service | URL |
|---|---|
| **Frontend (Node.js)** | _To be updated after Railway deployment — see [Part 2 deployment steps](#deploying-the-node-frontend-to-railway)_ |
| **Backend API (FastAPI)** | [https://ai-governance-dashboard-production-4c62.up.railway.app](https://ai-governance-dashboard-production-4c62.up.railway.app) |
| **API Docs (Swagger UI)** | [https://ai-governance-dashboard-production-4c62.up.railway.app/docs](https://ai-governance-dashboard-production-4c62.up.railway.app/docs) |

> **Note — archived Streamlit frontend**: An earlier frontend at `https://ravishing-integrity-production.up.railway.app` (Streamlit) is **no longer actively deployed or maintained**. The Streamlit source code (`frontend/`) remains in the repository for historical reference but is not the active UI. It was replaced by the Node.js frontend for better control over auth flows (multi-step login, OTP, OAuth hooks), custom UI design, and a more traditional HTML/CSS/JS stack.

---

## Features

### Authentication

* Two-step email + password login (email first, then password — mirrors a modern auth UX)
* User signup with first/last name, email, and password
* Forgot password with email OTP verification (three-step: request → verify → reset)
* JWT Bearer token auth on all protected API endpoints
* Password hashing with Passlib (bcrypt)
* Rate limiting on `/auth/login` (5 requests/minute per IP)

### AI Response Generation

* Gemini 2.5 Flash integration
* Prompt submission and AI response display
* All interactions automatically stored for governance tracking

### Prompt History

* Full history table with date, time, model, status, and response length columns
* Live client-side filtering by date range and keyword (no re-fetches)
* Detail modal per record showing full prompt and response text
* CSV export of the currently-filtered view

### Analytics Dashboard

* Core KPIs: total requests, AI requests, manual requests
* Performance metrics: success rate, failed requests, longest response
* Request distribution bar chart (Chart.js)
* Model usage bar chart and table
* System health and most-used model info boxes
* Latest prompt display

### Response Evaluations

* First-class response records tied to generated prompts
* Automated response checks (near-empty, max length, sensitive words, repeated text)
* Human evaluation endpoint with JWT-based evaluator attribution
* Evaluation filtering by response and type

---

## Tech Stack

### Active Frontend

* **Node.js** + **Express** — serves static files and injects runtime config
* **Vanilla HTML / CSS / JS** — no framework, no build step
* **Chart.js** (CDN) — dashboard charts
* Deployed as a Docker container on Railway

### Backend

* **FastAPI** (Python)
* **SQLAlchemy** ORM
* **Alembic** — database migrations
* **PostgreSQL** — production database
* **Passlib** (bcrypt) — password hashing
* **PyJWT** — JWT token signing/verification
* **Resend** — transactional email for OTP delivery
* **Google Gemini API** (Gemini 2.5 Flash) — AI generation
* **slowapi** — rate limiting

### Legacy Frontend (archived, not deployed)

* **Streamlit** — source in `frontend/`, retained for reference

---

## Project Structure

```text
AI-Governance-Dashboard/
|-- backend/                        # FastAPI application
|   |-- config/
|   |-- database/
|   |-- routes/
|   |-- schemas/
|   `-- services/
|-- frontend/                       # Streamlit frontend (archived, not deployed)
|   |-- app.py
|   `-- pages/
|-- governance-dashboard-frontend/  # Node.js/Express frontend (ACTIVE)
|   |-- public/
|   |   |-- css/style.css
|   |   |-- js/                     # api.js, auth.js, dashboard.js, generate.js, history.js
|   |   |-- dashboard.html
|   |   |-- generate.html
|   |   |-- history.html
|   |   |-- login.html
|   |   |-- signup.html
|   |   `-- forgot-password.html
|   |-- server.js
|   |-- package.json
|   |-- Dockerfile                  # Used for Railway deployment
|   `-- .env.example
|-- migrations/                     # Alembic migration scripts
|-- assets/
|-- docs/
|-- .github/workflows/
|-- Dockerfile                      # Backend Docker image
|-- Dockerfile.frontend             # Legacy Streamlit Docker image (archived)
|-- docker-compose.yml              # Local full-stack dev (backend + Streamlit)
|-- entrypoint.sh
|-- alembic.ini
|-- requirements-backend.txt
|-- requirements-frontend.txt       # Legacy Streamlit deps
|-- requirements.txt
`-- README.md
```

---

## Getting Started (Local Development)

### Prerequisites

* Python 3.12+, a virtual environment tool
* Node.js 18+ and npm
* PostgreSQL (or use the Docker Compose setup which starts one automatically)

---

### Running the Backend

#### 1. Clone the repository

```bash
git clone https://github.com/teja2704/AI-Governance-Dashboard.git
cd AI-Governance-Dashboard
```

#### 2. Create environment configuration

```bash
cp .env.example .env
```

Edit `.env` and set real values for:

* `DATABASE_URL` — PostgreSQL connection string, or `sqlite:///./local.db` for local SQLite
* `GEMINI_API_KEY`
* `JWT_SECRET_KEY`
* `AUTH_BOOTSTRAP_USERNAME`
* `AUTH_BOOTSTRAP_PASSWORD`
* `RESEND_API_KEY` — required for password-reset email delivery

#### 3. Create and activate a virtual environment

```bash
python -m venv venv
venv\Scripts\activate      # Windows
# source venv/bin/activate  # macOS/Linux
```

#### 4. Install backend dependencies

```bash
pip install -r requirements-backend.txt
```

#### 5. Run database migrations

```bash
alembic upgrade head
```

If pointing at an existing database that pre-dates Alembic, stamp instead of migrating:

```bash
alembic stamp head
```

#### 6. Start the FastAPI backend

```bash
uvicorn backend.main:app --reload
```

The API is available at `http://127.0.0.1:8000`. Swagger docs at `http://127.0.0.1:8000/docs`.

On startup the backend creates the bootstrap user from `AUTH_BOOTSTRAP_USERNAME` / `AUTH_BOOTSTRAP_PASSWORD` if it doesn't already exist.

---

### Running the Node.js Frontend

```bash
cd governance-dashboard-frontend
cp .env.example .env       # sets FASTAPI_BASE_URL=http://127.0.0.1:8000
npm install
npm start                  # production server on port 3000
# -- or --
npm run dev                # nodemon with auto-restart on file changes
```

Open `http://localhost:3000`. Sign in with the bootstrap credentials set in the root `.env`.

> The `.env` inside `governance-dashboard-frontend/` only needs `FASTAPI_BASE_URL` and `PORT`. It is separate from the root `.env` used by the backend.

---

### Running with Docker Compose (Backend + PostgreSQL only)

The `docker-compose.yml` starts the FastAPI backend and a PostgreSQL database. The Node.js frontend is run separately (see above), or deployed to Railway independently.

```bash
cp .env.example .env
# Edit .env with real values
docker compose up --build
```

| Service | Port | Notes |
|---|---|---|
| `db` | 5432 | PostgreSQL 16, health-checked before backend starts |
| `backend` | 8000 | Runs `alembic upgrade head` on startup, then uvicorn |

Database migrations are applied automatically via `entrypoint.sh`.

#### Required `.env` variables for Docker Compose

```
DATABASE_URL
GEMINI_API_KEY
JWT_SECRET_KEY
JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES
AUTH_BOOTSTRAP_USERNAME
AUTH_BOOTSTRAP_PASSWORD
RESEND_API_KEY
POSTGRES_USER
POSTGRES_PASSWORD
POSTGRES_DB
```

#### Health check

```bash
curl http://localhost:8000/health
# {"status": "healthy"}
```

---

### Legacy: Running the Streamlit Frontend (optional, archived)

The Streamlit source is retained in `frontend/` but is not the active UI. To run it locally for reference:

```bash
pip install -r requirements-frontend.txt
streamlit run frontend/app.py
```

Sign in with the bootstrap credentials. Note that some auth flows (OTP reset, etc.) are only partially implemented in this version.

---

## Deploying the Node Frontend to Railway

The Node.js frontend (`governance-dashboard-frontend/`) is designed to be deployed as a separate Railway service alongside the existing backend service, within the same Railway project.

**Important — subfolder deployment**: This repository contains both the backend and frontend in subdirectories. Railway must be pointed at the correct subfolder. Follow these steps exactly:

### Step-by-step Railway deployment

**1. Open your Railway project**
Go to [railway.app](https://railway.app) and open the project that already contains your backend and PostgreSQL services.

**2. Add a new service**
Click **+ New** → **GitHub Repo** → select `teja2704/AI-Governance-Dashboard`.

**3. Set the Root Directory**
In the new service's **Settings** → **Build** section, set **Root Directory** to:
```
governance-dashboard-frontend
```
This tells Railway to treat that subfolder as the project root. Without this setting Railway would try to build from the repo root and pick up the backend `Dockerfile` instead.

**4. Confirm the Dockerfile path**
Railway should auto-detect `Dockerfile` inside `governance-dashboard-frontend/`. The **Dockerfile Path** field can stay as its default (`Dockerfile`) since it's resolved relative to the Root Directory set above.

**5. Set environment variables**
In the service's **Variables** tab, add:

| Variable | Value |
|---|---|
| `FASTAPI_BASE_URL` | `https://ai-governance-dashboard-production-4c62.up.railway.app` |

Railway injects `PORT` automatically — do **not** set it manually.

**6. Deploy**
Click **Deploy**. Railway will build the Docker image from `governance-dashboard-frontend/Dockerfile` and start the container.

**7. Generate a public domain**
In the service's **Settings** → **Networking** section, click **Generate Domain**. Railway will assign a `*.up.railway.app` URL.

**8. Update this README**
Replace the placeholder in the Live Deployment table above with the real Railway URL.

**9. Verify and retire the Streamlit service**
Once the Node.js frontend is live and working at the new URL, go to the Railway dashboard and **delete the `ravishing-integrity` Streamlit service** (this is a manual dashboard action — do not do it until the new frontend is confirmed working).

---

## Security Notes

JWT authentication is required on all protected API routers. The `/auth/login`, `/auth/signup`, `/auth/forgot-password`, `/health`, and `/` endpoints are public.

Passwords are stored as Passlib bcrypt hashes. JWT tokens are signed with `JWT_SECRET_KEY` — use a long random value and rotate if exposed.

The Node.js frontend stores the JWT in browser `localStorage` and sends it as a Bearer token on every API request. A 401 response from any protected endpoint automatically clears the token and redirects to the login page.

**Rate limiting** is active on `/auth/login`: 5 requests per minute per IP via slowapi. If deployed behind a reverse proxy, `X-Forwarded-For` parsing will need to be added for correct IP attribution.

See [docs/security-review.md](docs/security-review.md) for current security notes.

---

## API Notes

Authenticated API routers (JWT Bearer required):

* `/prompts` — prompt creation, generation, history
* `/responses` — response records
* `/evaluations` — automated and human evaluations
* `/analytics` — KPIs, model usage, dashboard metrics

Interactive API documentation is available at `/docs` (Swagger UI) and `/redoc`.

---

## CI / Continuous Integration

GitHub Actions runs on every push and pull request to `main`:

* **Tests** — `pytest` against all route and rate-limit tests
* **Dependency audit** — `pip-audit` scans for known CVEs in backend dependencies

See [`.github/workflows/ci.yml`](.github/workflows/ci.yml) for the pipeline definition.

---

## Implementation Documentation

Phase notes and the follow-up issue queue are in [docs/implementation-phases.md](docs/implementation-phases.md).

---

## Future Enhancements

* Google OAuth sign-in (placeholder exists in UI; backend endpoint stubbed)
* PDF governance report generation
* Multi-model support (currently hardcoded to Gemini 2.5 Flash)
* Rate limiter backed by Redis (for multi-instance / load-balanced deployments)
* `X-Forwarded-For` parsing for correct IP attribution behind a reverse proxy
