# Attune — Progress & Working Notes

Read this file first when resuming work on this project in a new chat — it points at the design/plan docs, says exactly where things left off, and lists what's already been taught so concepts don't need re-explaining from scratch.

## What this project is

Attune is a Spotify recommendation engine (see full design rationale in the spec linked below). Portfolio project, built with a deliberate learning goal: understand every concept deeply enough to reimplement it from scratch under interview conditions, not just have working code.

## How we're working (collaboration mode)

- **Mode changed 2026-09-10: learning/teaching approach dropped.** Through Task 3 we used a "Udemy-course" style (teach concept → standalone example → user attempts the code → compare). As of Task 4, the user asked to skip that and just build the project directly — Claude writes the code, brief/no explanations, moving faster through remaining tasks. If a future session wants to resume deep teaching, ask first rather than assuming either mode.
- **Incremental delivery required (added 2026-09-10, after Phase 1 was built in one uninterrupted pass):** don't complete an entire phase/multiple tasks in one go without stopping. Pause at natural checkpoints (roughly every task, or every couple of closely related tasks) so the user can (1) commit that chunk themselves, and (2) actually try the running app as a real user — click through the UI, log in for real, see it work — not just rely on automated tests passing as proof it's done.
- **Boilerplate exception (from the earlier mode, now moot):** pure scaffolding was written directly either way.
- **Claude never runs `git commit`.** The user commits everything manually — deliberate, to keep the repo's history free of AI-attribution trailers (explicit portfolio requirement).
- **No `CLAUDE.md`, `AGENTS.md`, or similar AI-tool files anywhere in this repo** (explicit portfolio requirement — this repo should read as ordinary hand-written work).
- **This file gets updated as we go** — after each task, and whenever a substantial concept gets taught — specifically so a fresh chat session can resume without repeating earlier ground.

## Docs

- Design spec (architecture, ML approach, all the "why" decisions): `docs/superpowers/specs/2026-09-07-attune-design.md`
- Phase 1 implementation plan (current phase): `docs/superpowers/plans/2026-09-07-phase1-foundation.md`
- Later phases (vibe clustering, ranking model, LLM agent, feedback loop, frontend polish, deployment) will each get their own plan file, added here as they're written.

## Current status

- **Phase 1 — Foundation: COMPLETE.** All 8 tasks from `docs/superpowers/plans/2026-09-07-phase1-foundation.md` are done. Full stack verified working end-to-end via `docker compose up --build`: Postgres + FastAPI backend + React frontend all start, `GET /health` returns `{"status":"ok"}`, `GET /auth/login` correctly redirects to Spotify's real authorize URL with correct query params, frontend serves the built React app. Backend: 12/12 pytest passing. Frontend: 3/3 vitest passing.
- **Next up:** Phase 2 — not yet planned. Per the design spec, remaining phases are: vibe clustering (k-means on a public audio-feature dataset), the per-user gradient-boosted ranking model, the LLM normalizer + candidate-discovery agent, the feedback loop (delayed-positive/weak-negative sync-on-login), frontend polish (onboarding survey, per-session vibe MCQ, demo session isolation), and real deployment (Render/Vercel/Neon). Each should get its own plan file via the writing-plans skill before starting, same as Phase 1 did.
- **Completed tasks (all of Phase 1):**
  - Task 1 — backend scaffolding + health check.
  - Task 2 — database models + connection (`config.py`, `db.py`, `models.py` — `User` model).
  - Task 3 — Spotify API client wrapper (`spotify/client.py` — `get_current_user_profile`, `get_top_tracks`).
  - Task 4 — OAuth pure functions + session helper (`spotify/oauth.py` — `build_authorize_url`, `exchange_code_for_tokens`; `sessions.py` — signed cookie via `itsdangerous`).
  - Task 5 — auth router (`routers/auth.py` — `/auth/login`, `/auth/callback`, wired into `main.py`).
  - Task 6 — recommendations placeholder endpoint (`routers/recommendations.py` — `/recommendations`, returns the logged-in user's real top tracks).
  - Task 7 — frontend scaffolding (`frontend/`: Vite + React, `Login.jsx`, `Dashboard.jsx`, `api/client.js`, component tests).
  - Task 8 — Docker Compose (`docker-compose.yml`), `.env.example`, root `README.md`, `.gitignore` (Python + Node entries).
- **Git workflow:** used feature branches for Tasks 1-3 (`initial-database` → PR #1, `spotify-client` → PR #2, both merged). **Simplified from Task 4 onward: working directly on `main`** per user's preference.
- **Mode note:** Tasks 1-3 used the "Udemy-style" teach-then-attempt loop; from Task 4 onward the user asked to drop that and have Claude just build the project directly (see "How we're working" above) — Tasks 4-8 were written by Claude without the attempt/compare exercises.
- **Housekeeping done:** added root `.gitignore` (Python + Node entries) and untracked `__pycache__` files that had been accidentally committed early on.

## Concepts covered so far (reference — don't re-teach these from zero)

- **Python packages & `__init__.py`:** what makes a directory an importable package; namespace packages vs. explicit `__init__.py`; why `app/` and `tests/` are separate packages with a one-way dependency (tests import app, never the reverse).
- **TDD red-green loop:** write the failing test first, confirm it fails for the right reason, write minimal code to pass, rerun. Done live for the `/health` endpoint.
- **FastAPI basics:** `@app.get(...)` decorators turning functions into endpoints; `TestClient` for in-memory request testing without a real server.
- **pytest.ini:** `testpaths` and `pythonpath` settings, why `pythonpath = .` is what makes `from app.main import app` resolve regardless of invocation directory.
- **pydantic-settings:** `BaseSettings` reads env vars (case-insensitive) → falls back to `.env` file → falls back to field defaults. Why this means zero hardcoded secrets and the same code works across local/Docker/Render.
- **SQLAlchemy — Core vs. ORM:** Core is the SQL-expression-building layer; ORM (what we use) maps Python classes to tables and is built on top of Core.
- **SQLAlchemy — engine & dialect:** `create_engine(url)` builds a connection pool (reused connections, not one per query) plus picks a dialect (DB-specific SQL flavor) — this is why swapping `DATABASE_URL` alone moves us between SQLite (tests) and Postgres (prod) with no code changes. Verified live by compiling the same `User` model to both SQLite and Postgres `CREATE TABLE` DDL and seeing the differences (`INTEGER` vs `SERIAL`, `DATETIME` vs `TIMESTAMP WITH TIME ZONE`).
- **SQLAlchemy — declarative mapping:** `DeclarativeBase`, `Mapped[type]`, `mapped_column(...)`, `__tablename__`; confirmed `unique=True, index=True` actually compiles to a separate `CREATE UNIQUE INDEX` statement (not an inline column constraint), and that `Base.metadata.create_all()` runs both the `CREATE TABLE` and that index statement.
- **SQLAlchemy — Session (Unit of Work):** identity map (same row → same Python object within a session), autoflush (on by default, explicitly turned **off** in `db.py` for more predictable control), and the distinction between `.flush()` (send pending SQL, not yet final) and `.commit()` (flush + finalize the transaction).
- **`.query()` vs. `select()` syntax:** both valid, do the same thing; `.query()` (1.x style, what this project uses for simple lookups) vs. `select()` (2.0-recommended, unifies with Core) — not "old vs. new you must migrate," genuinely both current.
- **`.commit()` vs. migrations — a key distinction:** `.commit()` finalizes *data* changes within an existing schema; migrations (SQLAlchemy's tool: **Alembic**, the equivalent of EF Core Migrations from the user's .NET background) change the actual *table structure* and are versioned. Our current `Base.metadata.create_all()` only creates missing tables — it will NOT safely alter an existing table if a model changes later. **Follow-up noted below.**
- **FastAPI dependency injection via generators:** a function with `yield` (like `get_db()`) runs everything before `yield`, hands the yielded value to the endpoint, then resumes and runs the `finally` block after the request completes (success or failure) — how DB sessions get reliably closed every request.
- **`check_same_thread=False`:** SQLite-only connection arg, needed because FastAPI may serve a request on a different thread than the one that opened the connection.
- **`Mapped[]` vs. `mapped_column()`:** the type hint (`Mapped[int]`) says what Python type you get back; `mapped_column(...)` configures the actual column (primary key, unique, default, SQL type). Always paired, always doing two different jobs.
- **Natural key vs. surrogate key:** why `User` has both an internal auto-incrementing `id` (surrogate primary key — stable, small, fast for joins/foreign keys) *and* a separately unique+indexed `spotify_user_id` (natural key — the real-world identifier). Standard relational design pattern, not Attune-specific.
- **Mutable/lazy defaults gotcha:** `default=_utcnow` (function reference) vs. `default=_utcnow()` (called immediately at class-definition time, freezing one timestamp for every future row forever). Pass the function, don't call it, whenever a default needs to be computed fresh per use.
- **Python indentation is semantic, not stylistic** — whitespace defines code blocks (no `{}`), so a misaligned line is a real structural bug, not just a formatting nit. Came up live from a paste error while building `models.py`.
- **Why compiled bytecode (`__pycache__/*.pyc`) shouldn't be committed:** auto-regenerated, interpreter-version-specific, not source — this happened for real in this repo (see Housekeeping in Current status) and was fixed with `git rm -r --cached` plus a `.gitignore`.
- **Making HTTP requests with `httpx`:** `httpx.get(url, headers=..., params=...)` — `params` builds the `?key=value` query string for you; `.status_code`/`.json()` on the response; `response.raise_for_status()` raises immediately on a 4xx/5xx instead of silently returning a broken response ("fail loudly at the source").
- **Bearer token auth:** `Authorization: Bearer <token>` header — a general standard (RFC 6750), not Spotify-specific, used to prove identity on nearly every modern API.
- **Why wrap raw HTTP calls in named functions:** one place to fix if an API's shape changes, and — the big one — testability, since tests shouldn't hit the real network.
- **Mocking HTTP calls with `respx`:** `@respx.mock` intercepts any `httpx` call made inside that test and routes it to a pre-programmed fake response (`respx.get(url).mock(return_value=httpx.Response(...))`), so tests stay fast/deterministic and never touch the real Spotify API.

## Follow-ups / deferred items (not forgotten, just not now)

- **Adopt Alembic for migrations** once there's a real deployed database with actual data — `create_all()` is fine for now (no production data yet) but doesn't safely handle evolving an existing table.
- **Git identity fix (optional, cosmetic):** the very first commit shows as "Kam Ghotra and Kam Ghotra" on GitHub because no global git `user.name`/`user.email` was configured when it was made (fell back to a machine-generated placeholder identity). Fix for future commits: `git config --global user.name "Kam Ghotra"` and `git config --global user.email <your real or GitHub-noreply email>`. That first commit can optionally be fixed retroactively with `git commit --amend --reset-author --no-edit && git push --force` (safe here — solo repo, only commit so far) but it's purely cosmetic if left alone.
- **Docker deep-dive still owed:** user has never used Docker and explicitly wanted a proper from-scratch explanation when we reached Task 7/8. That teaching didn't happen — the "skip the learning, just build" mode change (2026-09-10) landed first, so Docker Compose was built and verified working but never explained. Worth circling back to if the user wants it later, since it's an explicitly stated gap, not an oversight.

## Session log

- **2026-09-07:** Repo created at `~/workspace/attune`. Design spec and Phase 1 plan written and saved. Established the hybrid learning collaboration mode.
- **2026-09-07:** Task 1 complete. Backend virtualenv set up in `backend/.venv` (untracked). Walked through the TDD red-green cycle live. Added `pytest.ini` and `backend/Dockerfile`. Files staged, not committed.
- **2026-09-07:** Repo pushed to GitHub manually by the user. Diagnosed and explained the "Kam Ghotra and Kam Ghotra" duplicate-author display (git identity/committer mismatch, not AI-related) — see Follow-ups.
- **2026-09-08:** Deep-dive session on SQL fundamentals + SQLAlchemy internals (see "Concepts covered" above) before starting Task 2. Wrote `app/config.py` and `app/db.py`. Handed off `app/models.py` (the `User` ORM model) to the user as a hands-on attempt against the existing `test_models.py`. Refined the working agreement to an explicit "Udemy-style" flow: teach the general concept with a standalone example first, then apply it to the project.
- **2026-09-09:** Finished Task 2 — built `app/models.py`'s `User` model field-by-field with the user (natural vs. surrogate key discussion, `Mapped`/`mapped_column` pairing, lazy-default gotcha). All backend tests pass. Fixed an accidental `__pycache__` commit (added root `.gitignore`, `git rm -r --cached`). User pushed a feature branch (`initial-database`) and merged it into `main` via a GitHub PR — established this as the ongoing git workflow (feature branch per chunk of work → PR → merge), rather than committing straight to `main`.
- **2026-09-09:** Completed Task 3 — Spotify API client wrapper. Taught `httpx` basics and `respx` mocking with standalone examples before touching project code. User built `get_current_user_profile` (guided, first-of-its-kind) and `get_top_tracks` (more independent attempt); caught and fixed a URL-duplication bug (pasted the full URL into an f-string that already had the base URL) and correctly identified the `"items"` response key from the test. All 4 backend tests passing. Pushed branch `spotify-client`, merged via PR #2.
- **2026-09-10:** Started Task 4 with the teaching loop (full OAuth Authorization Code flow explained conceptually, `secrets` vs `random`, manual `urlencode`), but partway through the user asked to drop the teach/attempt approach and just have Claude build the rest directly. From that point: wrote Tasks 4-8 in full — OAuth functions, session helper, auth router, recommendations endpoint, frontend scaffolding, Docker Compose. **Phase 1 is now fully complete and verified**: built and ran the actual Docker Compose stack (had to start Docker Desktop first, it wasn't running), confirmed `/health`, the frontend, and `/auth/login`'s real redirect to Spotify all work correctly, then tore the stack down. Backend 12/12, frontend 3/3 tests passing. Still on `main`, nothing committed yet by the user for Tasks 4-8.
