# Security Review

## Scope

This review covers the current authentication, environment handling, frontend token storage, Docker packaging, and migration setup.

## Checks Completed

* Confirmed `.env` is ignored by Git and not staged.
* Confirmed `.env.example` contains placeholders only.
* Confirmed protected routers use `Depends(get_current_user)`.
* Confirmed `/auth/login`, `/`, and `/health` are the only intended public endpoints.
* Confirmed the frontend stores JWTs in Streamlit `session_state`, not browser storage.
* Confirmed frontend API calls attach `Authorization: Bearer <token>`.
* Searched for common high-risk patterns such as `verify=False`, `eval`, `exec`, `pickle`, `subprocess`, `shell=True`, and browser `localStorage`.
* Confirmed the Docker runtime uses a non-root user.
* Added a minimum 32-byte requirement for `JWT_SECRET_KEY`.

## Current Threat Notes

* JWTs are bearer tokens. Anyone who obtains a token can use it until it expires.
* Use HTTPS in any deployed environment so tokens are not exposed in transit.
* Rotate `JWT_SECRET_KEY` if it is exposed. Rotation invalidates existing tokens.
* Keep `AUTH_BOOTSTRAP_PASSWORD` strong and private. It creates the initial login user when the app starts.
* The app has no role-based authorization yet; any authenticated user can access protected endpoints.
* There is no login rate limiting yet. Add it before internet-facing deployment.
* The dependency vulnerability check is limited to local dependency consistency in this pass; run a vulnerability scanner such as `pip-audit` in CI when network access is available.
