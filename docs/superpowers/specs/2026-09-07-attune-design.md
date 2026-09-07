# Attune — Design Spec

## Context

Attune is a portfolio side project: a Spotify recommendation engine that logs into a user's account, builds a taste profile from their real listening history, asks them a couple of questions about the vibe they want (multiple choice + free text), and returns song suggestions that are both personalized and deliberately more exploratory than Spotify's own recommendations (which tend to stick to artists the user already knows).

Two hard external constraints shaped this design:

1. **Spotify permanently deprecated `audio-features`, `audio-analysis`, `recommendations`, and `related-artists`** for any app created after Nov 27, 2024. No BPM, energy, valence, or danceability from the live API, and no seed-based recommendation endpoint. No waitlist, no announced reversal.
2. **New Spotify apps are capped in "Development Mode"**: as of a February 2026 platform change, only 5 users total can be allowlisted, and that allowlist can only be edited manually in Spotify's dashboard — no API exists to add or remove testers.

## Product shape

- **Hosted demo site**: powered entirely by one pre-authorized demo Spotify account (the developer's own). Any visitor sees the full flow — taste profile, vibe questions, recommendations — with zero login required. This is the only mode the hosted site offers; it never asks a stranger to log in with their own Spotify account.
- **Local self-hosted setup, for real personal use**: anyone who wants recommendations from their *own* Spotify account clones the repo, registers their own free Spotify Developer app (instant, gives them their own separate 5-user allowlist), and runs the stack locally via Docker Compose. This fully sidesteps the Development Mode cap — no request queue, no manual approval needed from the original developer, since each local runner is the sole tester of their own app registration.
- **Demo session isolation**: the demo account's underlying Spotify data is the same for every visitor (intentional — it's the developer's own public sample data). The *interactive* part (vibe answers, generated recommendations) is scoped to a per-visitor anonymous session ID, never shared global state — this prevents both stale leftover results and concurrent visitors clobbering each other.

## Architecture

**Stack**: Python (FastAPI) backend, React frontend, PostgreSQL database.

**Hosting (fully free at portfolio-scale traffic)**:
- Backend: Render free web service.
- Database: Neon Postgres (chosen over Render's own Postgres, which auto-deletes free databases after 30 days).
- Frontend: Vercel free tier.
- No cron/scheduled jobs anywhere (not free on Render) — anything periodic-shaped is instead triggered by user activity (login).

**Local setup**: Docker Compose running Postgres + backend + frontend together, using the local runner's own Spotify Client ID/Secret and (optionally) their own LLM API key.

## Recommendation engine

Two genuinely different sub-problems, each solved with the tool suited to it.

### Problem A — grouping songs into vibe clusters (unsupervised)

Built from a static public dataset containing pre-2024-deprecation audio features (tempo, energy, valence, danceability) — e.g. Kaggle's "Spotify Tracks Dataset." **License must be verified before this dataset ships in the repo**; if unclear, fall back to an alternative CC0 tabular Spotify dataset or the Hugging Face mirror.

Run k-means clustering offline on the dataset's numeric feature vectors to produce a fixed set of named vibe clusters (e.g. "high-energy," "chill acoustic," "melancholic indie"). Unsupervised — no labels needed.

A candidate track is matched to this dataset by track ID / artist+title to inherit its real historical cluster. Tracks not in the dataset fall through to the tiered fallback below.

### Problem B — will *this* user like *this* song (supervised, per-user)

A gradient-boosted tree model (LightGBM or XGBoost), trained **per user, at request time** — not one global model.

- Chosen over random forest (lower accuracy ceiling on tabular ranking), a neural network (needs more data to beat trees on structured input; its unstructured-input strength is already covered by the LLM), and matrix factorization (needs cross-user interaction history this project doesn't have yet).
- **Cold-start bootstrap, no separate dataset needed**: positives = the user's own top/saved tracks (real, known-liked). Negatives = tracks randomly sampled from the public dataset that clearly fall outside the user's taste profile (different genre/cluster/era).
- **Features** per (user, candidate song): genre match score, vibe-cluster match, era difference, popularity, artist familiarity, plus the LLM-normalized vibe features (below).
- **Tiered confidence fallback** (weights renormalize onto whatever signals actually exist, rather than guessing missing ones):
  - Tier 1 (rich): dataset-matched cluster + genre + popularity + era + LLM-inferred descriptors → full weighted score.
  - Tier 2 (thin): only genre + artist known → weights renormalize onto those two.
  - Tier 3 (minimal): genre only → single-signal weight, flagged low-confidence.
- Tempo/energy expressed as coarse buckets (slow/medium/fast) — never a fabricated precise BPM number.

### The LLM's role — two narrow, well-defined jobs

Deliberately scoped to avoid "GPT wrapper" territory — the LLM never makes the ranking decision, only supplies inputs to it:

1. **Normalizer**: maps free-text vibe input into a fixed taxonomy (`energy: low/medium/high`, `mood: chill/happy/melancholic/aggressive/romantic/energetic`, `context: workout/study/relax/party/commute`) via schema-enforced structured output. Solves the problem that raw text ("chill music" vs "calm-chill music") is inconsistent as a model feature — normalized output feeds directly into Problem B as input features.
2. **Candidate-discovery agent**: given the taste profile + normalized vibe, runs a few rounds of Spotify Search API calls to find artists/genres beyond the user's existing top artists — this is what fixes the "too linear" complaint. Multi-round (search → judge diversity → refine → search again), not a single one-shot call.

Both calls are cheap/infrequent, cheap model tier, server-side API key with per-IP rate limit + monthly spend cap (hosted demo only — local runners supply their own key).

## Feedback loop

Two independent signals, both feed retraining, weighted differently:

- **Delayed positive** (strong): on login, check the user's current Spotify library against the app's log of previously-recommended tracks. Any match is a positive label — even a month later, even overriding an earlier "don't like this" answer.
- **Weak negative** (soft): a recommended track not added after **30 days** is a low-confidence negative — still used, weighted below a real add or explicit dislike.

Both checks run on login, not on a schedule (no free cron on Render; nothing useful to check for an inactive user anyway).

## Vibe input UX

- **Onboarding** (once, at first connect): short survey establishing baseline taste, feeding the cold-start model.
- **Per-session** (optional, each recommendation request): quick MCQ + free-text refinement layered on the baseline.

## Data model (high-level)

- `users` — Spotify user ID, OAuth tokens (encrypted at rest), connected_at, last_active_at, is_demo flag.
- `taste_profiles` — per-user baseline profile from onboarding + listening history.
- `recommendations` — user_id (or anonymous session_id for demo), track_id, shown_at, vibe_context.
- `feedback` — user_id, track_id, label (positive/weak_negative), resolved_at, source.

## Error handling

- Spotify API failures/rate limits: exponential backoff + graceful degradation (serve cached data rather than hard failure).
- OAuth token expiry: standard refresh-token flow; if refresh fails, prompt re-login.
- LLM API failures/timeouts: candidate-discovery agent falls back to a hardcoded set of genre-adjacent search terms; normalizer failure falls back to Tier 3 confidence rather than blocking the request.

## Testing approach

- Unit tests for the scoring/ranking logic and tiered-fallback weighting (the core custom-model code — most thoroughly tested part).
- Unit tests for k-means clustering against fixture data.
- Integration tests for API endpoints with Spotify and LLM calls mocked — never hit real external APIs in tests.
- End-to-end smoke tests against the demo-mode path, since every visitor depends on it.

## Repo hygiene (explicit requirement)

- No CLAUDE.md, AGENTS.md, or similar AI-tool files committed.
- No AI attribution in commits or PR descriptions — the developer makes all commits themselves.
- Standard OSS layout: README explaining the architecture/motivation, LICENSE (MIT), `.env.example`, real secrets never committed.
