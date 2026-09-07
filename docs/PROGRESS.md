# Attune — Progress & Working Notes

Read this file first when resuming work on this project in a new chat — it points at the design/plan docs and says exactly where things left off, so earlier design discussion doesn't need to be repeated.

## What this project is

Attune is a Spotify recommendation engine (see full design rationale in the spec linked below). Portfolio project, built with a deliberate learning goal: understand every concept deeply enough to reimplement it from scratch under interview conditions, not just have working code.

## How we're working (collaboration mode)

- **Learning-focused, hybrid approach.** Per concept: (1) deep explanation before any code — general concept first, then how it applies here; (2) a syntax/library primer for anything new (decorators, ORM typing, dependency injection, React hooks, etc.); (3) the user attempts the real implementation themselves in their own editor; (4) compare against a reference implementation together and discuss gaps.
- **Boilerplate exception:** pure scaffolding (Dockerfiles, config skeletons, repetitive setup) is written directly with brief explanation — not turned into a practice exercise. Concept-heavy pieces (OAuth flow, signed sessions, ORM modeling, the ML pipeline later) get the full loop above.
- **Claude never runs `git commit`.** The user commits everything manually — deliberate, to keep the repo's history free of AI-attribution trailers (explicit portfolio requirement).
- **No `CLAUDE.md`, `AGENTS.md`, or similar AI-tool files anywhere in this repo** (explicit portfolio requirement — this repo should read as ordinary hand-written work).

## Docs

- Design spec (architecture, ML approach, all the "why" decisions): `docs/superpowers/specs/2026-09-07-attune-design.md`
- Phase 1 implementation plan (current phase): `docs/superpowers/plans/2026-09-07-phase1-foundation.md`
- Later phases (vibe clustering, ranking model, LLM agent, feedback loop, frontend polish, deployment) will each get their own plan file, added here as they're written.

## Current status

- **Phase:** 1 — Foundation (walking skeleton: FastAPI + React + Postgres, Spotify OAuth, placeholder recommendations endpoint)
- **Next up:** Task 1 — backend scaffolding + health check
- **Completed tasks:** none yet

## Session log

- **2026-09-07:** Repo created at `~/workspace/attune`. Design spec and Phase 1 plan written and saved. Established the hybrid learning collaboration mode described above. About to start Task 1.
