# Attune — Progress & Working Notes

Read this file first when resuming work on this project in a new chat — it points at the design/plan docs, says exactly where things left off, and lists what's already been taught so concepts don't need re-explaining from scratch.

## What this project is

Attune is a Spotify recommendation engine (see full design rationale in the spec linked below). Portfolio project, built with a deliberate learning goal: understand every concept deeply enough to reimplement it from scratch under interview conditions, not just have working code.

## How we're working (collaboration mode)

- **Learning-focused, "Udemy-course" style.** For each new concept: (1) teach the general topic on its own first, with a standalone example decoupled from Attune's code — same way a course would introduce it; (2) a syntax/library primer for anything new (decorators, ORM typing, dependency injection, React hooks, etc.); (3) only then apply it into the actual project code; (4) the user attempts the real implementation themselves in their own editor; (5) compare against a reference implementation together and discuss gaps.
- **Boilerplate exception:** pure scaffolding (Dockerfiles, config skeletons, repetitive setup) is written directly with brief explanation — not turned into a practice exercise. Concept-heavy pieces (OAuth flow, signed sessions, ORM modeling, the ML pipeline later) get the full loop above.
- **Claude never runs `git commit`.** The user commits everything manually — deliberate, to keep the repo's history free of AI-attribution trailers (explicit portfolio requirement).
- **No `CLAUDE.md`, `AGENTS.md`, or similar AI-tool files anywhere in this repo** (explicit portfolio requirement — this repo should read as ordinary hand-written work).
- **This file gets updated as we go** — after each task, and whenever a substantial concept gets taught — specifically so a fresh chat session can resume without repeating earlier ground.

## Docs

- Design spec (architecture, ML approach, all the "why" decisions): `docs/superpowers/specs/2026-09-07-attune-design.md`
- Phase 1 implementation plan (current phase): `docs/superpowers/plans/2026-09-07-phase1-foundation.md`
- Later phases (vibe clustering, ranking model, LLM agent, feedback loop, frontend polish, deployment) will each get their own plan file, added here as they're written.

## Current status

- **Phase:** 1 — Foundation (walking skeleton: FastAPI + React + Postgres, Spotify OAuth, placeholder recommendations endpoint)
- **In progress:** Task 2 — database models + connection.
  - `backend/app/config.py` — done (pydantic-settings `Settings` class).
  - `backend/app/db.py` — done (SQLAlchemy `Base`, `engine`, `SessionLocal`, `get_db` dependency).
  - `backend/app/models.py` — **not yet written**. User is attempting the `User` model themselves against `backend/tests/test_models.py` (already written, defines the required fields: `spotify_user_id`, `access_token`, `refresh_token`, `is_demo`, `connected_at`; spec also calls for `last_active_at` which the test doesn't directly exercise but should be included). Next step when resuming: check whether the user has a draft, review it together, run the test.
- **Completed tasks:** Task 1 — backend scaffolding + health check (`backend/app/main.py`, `GET /health` returns `{"status": "ok"}`, test in `backend/tests/test_health.py`).
- **Git:** repo pushed to GitHub, one commit so far ("Starting off, progress file") containing only `docs/`. Task 1's backend files are staged (`git add`) but not committed — user commits manually per the working agreement above.

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

## Follow-ups / deferred items (not forgotten, just not now)

- **Adopt Alembic for migrations** once there's a real deployed database with actual data — `create_all()` is fine for now (no production data yet) but doesn't safely handle evolving an existing table.
- **Git identity fix (optional, cosmetic):** the very first commit shows as "Kam Ghotra and Kam Ghotra" on GitHub because no global git `user.name`/`user.email` was configured when it was made (fell back to a machine-generated placeholder identity). Fix for future commits: `git config --global user.name "Kam Ghotra"` and `git config --global user.email <your real or GitHub-noreply email>`. That first commit can optionally be fixed retroactively with `git commit --amend --reset-author --no-edit && git push --force` (safe here — solo repo, only commit so far) but it's purely cosmetic if left alone.
- **Docker deep-dive:** user has never used Docker — explicitly wants a proper from-scratch explanation when we reach Task 7/8 (docker-compose), not before. A `backend/Dockerfile` already exists from Task 1 but hasn't been explained or used yet.

## Session log

- **2026-09-07:** Repo created at `~/workspace/attune`. Design spec and Phase 1 plan written and saved. Established the hybrid learning collaboration mode.
- **2026-09-07:** Task 1 complete. Backend virtualenv set up in `backend/.venv` (untracked). Walked through the TDD red-green cycle live. Added `pytest.ini` and `backend/Dockerfile`. Files staged, not committed.
- **2026-09-07:** Repo pushed to GitHub manually by the user. Diagnosed and explained the "Kam Ghotra and Kam Ghotra" duplicate-author display (git identity/committer mismatch, not AI-related) — see Follow-ups.
- **2026-09-08:** Deep-dive session on SQL fundamentals + SQLAlchemy internals (see "Concepts covered" above) before starting Task 2. Wrote `app/config.py` and `app/db.py`. Handed off `app/models.py` (the `User` ORM model) to the user as a hands-on attempt against the existing `test_models.py`. Refined the working agreement to an explicit "Udemy-style" flow: teach the general concept with a standalone example first, then apply it to the project.
