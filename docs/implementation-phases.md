# Implementation Phases

## Phase 1: Dependency Pinning and Environment Template

Status: complete.

Changes:

* Pinned the original dependency list to versions installed in the project virtual environment.
* Added `.env.example` with placeholder values only.

Notes:

* The project venv launcher required elevated execution on this machine, so installed versions were verified with the venv after approval.

## Phase 2: JWT Authentication

Status: complete.

Changes:

* Added a `User` SQLAlchemy model with Passlib-hashed passwords.
* Added `/auth/login` to issue JWT Bearer tokens.
* Added `get_current_user` to validate JWTs and load active users.
* Protected all current prompt endpoints under `/prompts`.
* Protected all current analytics endpoints under `/analytics` because they are active API routes used by the app.
* Added startup bootstrap-user creation from environment variables.
* Added one integration test confirming an unauthenticated protected request returns `401`.

Route reality check:

* The repository does not currently contain `/responses` or `/evaluations` route files.
* Existing public endpoints are `/`, `/health`, and `/auth/login`.

## Phase 3: Frontend Authentication Integration

Status: complete.

Changes:

* Added a Streamlit login form.
* Stores the JWT in `st.session_state`, not browser `localStorage`.
* Adds the Bearer token to all existing Streamlit API requests.
* Stops unauthenticated page rendering and shows the login form instead.

Route reality check:

* The ticket requested React, but the current frontend is Streamlit. The implementation follows the same auth behavior in the existing frontend stack.

## Phase 4: Backend Dockerfile

Status: complete.

Changes:

* Added a multi-stage `Dockerfile` for the FastAPI backend.
* Runs the backend as a non-root `app` user.
* Reads runtime configuration from environment variables.
* Added `.dockerignore` to keep local env files, venvs, frontend assets, and Git data out of the build context.

## Phase 5: README Correction

Status: complete.

Changes:

* Removed authentication from future enhancements.
* Added a real Getting Started flow.
* Added Security Notes covering JWT requirements and token handling.
* Documented the setup flow, including environment configuration and backend startup.

## Phase 6: Alembic Migration Workflow

Status: complete.

Changes:

* Added Alembic configuration at `alembic.ini`.
* Added migration environment code in `migrations/env.py`.
* Added initial schema migration for `prompts` and `users`.
* Removed `Base.metadata.create_all` from backend startup.
* Kept bootstrap user creation separate from schema creation.
* Updated the auth integration test to run migrations before exercising the app.

## Phase 7: Follow-Up Queue Cleanup

Status: in progress.

Completed:

* Removed unreachable duplicate code in `backend/services/prompt_service.py`.
* Normalized Streamlit display text that previously rendered as mojibake.
* Split dependencies into `requirements-backend.txt` and `requirements-frontend.txt`.
* Updated the backend Dockerfile to install backend dependencies only.
* Included Alembic files in the backend Docker image so migrations can run from the same image.

Blocked:

* `/responses` and `/evaluations` route modules still need product requirements before implementation.

Tracked:

* FastAPI TestClient currently emits a Starlette/httpx deprecation warning. The test still passes; address during a future dependency-stack update.

## Verification

Completed:

* `python -m unittest tests.test_auth_integration`
* `python -m compileall backend frontend tests`
* Login smoke check with bootstrap user and authenticated `/prompts/` access
* Alembic-backed auth integration test after removing startup `create_all`

## Follow-Up Queue

1. Add route modules for `/responses` and `/evaluations` when those product areas are implemented.
2. Address the FastAPI TestClient dependency warning during the next dependency-stack update.
