# AI Governance Dashboard

[![CI](https://github.com/teja2704/AI-Governance-Dashboard/actions/workflows/ci.yml/badge.svg)](https://github.com/teja2704/AI-Governance-Dashboard/actions/workflows/ci.yml)

## Overview

AI Governance Dashboard is a full-stack AI monitoring and governance platform built with FastAPI, PostgreSQL, Streamlit, and Google's Gemini API.

The platform lets authenticated users generate AI responses, store interactions, monitor model performance, analyze prompt history, and track governance metrics through an interactive dashboard.

## Features

### Authentication

* JWT login endpoint for backend access
* Password hashing with Passlib
* Protected API routers for prompts and analytics
* Streamlit login form with in-memory token storage

### AI Response Generation

* Gemini 2.5 Flash integration
* Prompt and response storage
* Response tracking and monitoring

### Prompt History

* Search functionality
* Date filtering
* Detailed prompt inspection
* CSV export

### Analytics

* Request monitoring
* Success and failure tracking
* Average prompt length
* Average response length
* Model usage analytics

### Response Evaluations

* First-class response records tied to prompts
* Automated response checks after each generated response is saved
* Human evaluation endpoint with JWT-based evaluator attribution
* Evaluation filtering by response and evaluation type

## Tech Stack

### Backend

* FastAPI
* SQLAlchemy
* PostgreSQL
* Passlib
* PyJWT
* Gemini API

### Frontend

* Streamlit

### Database

* PostgreSQL

## Project Structure

```text
AI-Governance-Dashboard/
|-- backend/
|   |-- database/
|   |-- routes/
|   |-- schemas/
|   `-- services/
|-- frontend/
|   |-- app.py
|   `-- pages/
|-- assets/
|-- docs/
|-- migrations/
|-- Dockerfile
|-- alembic.ini
|-- requirements-backend.txt
|-- requirements-frontend.txt
|-- requirements.txt
`-- README.md
```

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/teja2704/AI-Governance-Dashboard.git
cd AI-Governance-Dashboard
```

### 2. Create environment configuration

```bash
cp .env.example .env
```

Edit `.env` and set real values for:

* `DATABASE_URL`
* `GEMINI_API_KEY`
* `JWT_SECRET_KEY`
* `AUTH_BOOTSTRAP_USERNAME`
* `AUTH_BOOTSTRAP_PASSWORD`

### 3. Create and activate a virtual environment

```bash
python -m venv venv
venv\Scripts\activate
```

### 4. Install dependencies

For local development with both backend and frontend:

```bash
pip install -r requirements.txt
```

Backend-only and frontend-only dependency sets are also available:

```bash
pip install -r requirements-backend.txt
pip install -r requirements-frontend.txt
```

### 5. Run database migrations

Initialize the database schema with Alembic:

```bash
alembic upgrade head
```

If you are pointing at an older database that was already initialized before Alembic was added, inspect the schema first. If it already matches the initial migration, stamp it instead of recreating tables:

```bash
alembic stamp head
```

### 6. Start the FastAPI backend

```bash
uvicorn backend.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.

On startup, the backend creates the bootstrap user from `AUTH_BOOTSTRAP_USERNAME` and `AUTH_BOOTSTRAP_PASSWORD` if that user does not already exist. The database schema must already be migrated before startup.

### 7. Start the Streamlit frontend

```bash
streamlit run frontend/app.py
```

Sign in with the bootstrap credentials configured in `.env`.

## Docker Backend

Build the backend image:

```bash
docker build -t ai-governance-backend .
```

Run the backend container with configuration supplied through environment variables:

```bash
docker run --env-file .env ai-governance-backend alembic upgrade head
docker run --env-file .env -p 8000:8000 ai-governance-backend
```

PostgreSQL is not included in this Dockerfile. A database host must already be reachable through `DATABASE_URL`.

## Security Notes

JWT authentication is required on all protected API routers as of this version. The `/auth/login`, `/health`, and `/` endpoints remain public for login and service checks.

Passwords are stored as Passlib hashes in the `users` table. JWT signing uses `JWT_SECRET_KEY` from the environment; use a long random value and rotate it if it is exposed.

The Streamlit frontend stores the JWT only in server-side session memory and sends it as a Bearer token on API requests. It does not write the token to `localStorage`.

**Rate limiting** is active on the `/auth/login` endpoint: a maximum of **5 requests per minute** is allowed per remote IP address. Requests that exceed this limit receive a `429 Too Many Requests` JSON response. This limit is enforced by [slowapi](https://github.com/laurents/slowapi) using an in-process memory store (no external cache required). The limiter uses the direct connecting IP (`get_remote_address`); if deployed behind a reverse proxy or load balancer, this will need updating to parse `X-Forwarded-For` correctly.

See [docs/security-review.md](docs/security-review.md) for the current security check notes and remaining threat considerations.

## API Notes

Authenticated API routers include:

* `/prompts`
* `/responses`
* `/evaluations`
* `/analytics`

Generated Gemini responses are saved automatically as response records tied to the prompt that produced them. Automated evaluations run immediately after each generated response is saved.

## Implementation Documentation

Phase notes and the follow-up issue queue are maintained in [docs/implementation-phases.md](docs/implementation-phases.md).

## Future Enhancements

* PDF report generation
* Full Docker Compose stack with PostgreSQL
* Cloud deployment
* Multi-model support
