# LLM Candidate Discovery Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace `/recommendations`' current "just return the user's own top tracks" behavior with real candidate discovery — an LLM (Gemini) suggests artists/styles beyond the user's existing top artists, and Spotify's Search API finds real tracks matching those suggestions.

**Architecture:** A new Spotify Search wrapper (`spotify/client.py`) and a new `app/llm/` package wrapping Gemini's structured-output API get combined inside `/recommendations`: fetch top tracks → ask the LLM for search-worthy artists/styles not already in the user's top artists → search Spotify for each → dedupe against what the user already has → return the combined list. No ranking/scoring model yet (that's the next sub-phase) — this plan's job is purely to make genuinely different songs start appearing. Single search round, not the spec's fancier iterative refine-and-search-again loop — ship the simpler version first.

**Tech Stack:** Python, `google-genai` (official Gemini SDK, verified directly against the installed package — not scraped docs), Pydantic (already a transitive dependency via FastAPI), httpx (existing).

**Spec:** `docs/superpowers/specs/2026-09-07-attune-design.md` (see "The LLM's role — two narrow, well-defined jobs" — this plan implements the "candidate-discovery agent" half, single-round rather than multi-round)

## Global Constraints

- LLM: Gemini API, model `gemini-flash-latest` (a stable alias, avoids hardcoding a dated version string), via the `google-genai` Python package (confirmed installed version `2.25.0`; pin `google-genai>=2.25,<2.26`).
- Use `client.models.generate_content(model=..., contents=..., config=types.GenerateContentConfig(response_mime_type="application/json", response_schema=SomeSchema))` — verified directly against the installed SDK's real method signature and `GenerateContentConfig`/`GenerateContentResponse` fields. `response.parsed` returns an already-validated instance of the given Pydantic schema.
- `google-genai` is a **runtime** dependency (goes in `backend/requirements.txt`, unlike the clustering plan's pandas/scikit-learn) — `/recommendations` calls it on every live request.
- API key: `GEMINI_API_KEY` env var, read via a new `gemini_api_key: str = ""` field on `Settings` (matches the existing `spotify_client_id`-style empty-string default pattern in `backend/app/config.py`).
- No real Gemini API key exists yet — every task's tests must pass via mocks alone. Live end-to-end verification against the real API happens later, once the user has a key (same pattern as Spotify credentials).
- Claude does not run `git commit` — the project owner commits manually, OR (if executed via subagent-driven-development) implementer/fix subagents may commit per that skill's own process, with plain factual messages and no AI-attribution trailers.
- No `CLAUDE.md`/`AGENTS.md` or similar AI-tool files in this repo.

---

## Task 1: Spotify Search API wrapper

**Files:**
- Modify: `backend/app/spotify/client.py`
- Modify: `backend/tests/test_spotify_client.py`

**Interfaces:**
- Produces: `app.spotify.client.search_tracks(access_token: str, query: str, limit: int = 5) -> list[dict]` — calls Spotify's `/v1/search` endpoint with `type=track`, returns the list of track objects from `response.json()["tracks"]["items"]`.

- [ ] **Step 1: Write the failing test**

Add to `backend/tests/test_spotify_client.py` (alongside the existing tests, same file):
```python
@respx.mock
def test_search_tracks_returns_items_list():
    respx.get("https://api.spotify.com/v1/search").mock(
        return_value=httpx.Response(
            200,
            json={
                "tracks": {
                    "items": [
                        {"id": "track1", "name": "Song One", "artists": [{"name": "Artist One"}]},
                        {"id": "track2", "name": "Song Two", "artists": [{"name": "Artist Two"}]},
                    ]
                }
            },
        )
    )

    tracks = search_tracks("fake-token", "dream pop", limit=2)

    assert len(tracks) == 2
    assert tracks[0]["id"] == "track1"
```
Add `search_tracks` to the existing `from app.spotify.client import ...` import line at the top of the file.

- [ ] **Step 2: Run the test to verify it fails**

Run (from `backend/`): `pytest tests/test_spotify_client.py -v`
Expected: FAIL with `ImportError: cannot import name 'search_tracks'`

- [ ] **Step 3: Write the minimal implementation**

Add to `backend/app/spotify/client.py` (below the existing `get_top_tracks` function):
```python
def search_tracks(access_token: str, query: str, limit: int = 5) -> list[dict]:
    response = httpx.get(
        f"{SPOTIFY_API_BASE}/search",
        headers={"Authorization": f"Bearer {access_token}"},
        params={"q": query, "type": "track", "limit": limit},
    )
    response.raise_for_status()
    return response.json()["tracks"]["items"]
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `pytest tests/test_spotify_client.py -v`
Expected: PASS (3/3 in this file)

- [ ] **Step 5: Stage changes**

```bash
git add backend/app/spotify/client.py backend/tests/test_spotify_client.py
```

---

## Task 2: Gemini-powered search-query suggestion

**Files:**
- Create: `backend/app/llm/__init__.py`
- Create: `backend/app/llm/client.py`
- Test: `backend/tests/test_llm_client.py`
- Modify: `backend/app/config.py`
- Modify: `backend/requirements.txt`

**Interfaces:**
- Consumes: `app.config.settings` (existing).
- Produces: `app.llm.client.SearchSuggestions` (Pydantic model, one field `queries: list[str]`); `app.llm.client.suggest_search_queries(top_tracks: list[dict], count: int = 5) -> list[str]` — given a list of Spotify track objects (each with `name` and `artists: list[{"name": str}]`), returns a list of LLM-suggested search query strings (artist names or genre/style phrases) that exclude the artists already present in `top_tracks`.

- [ ] **Step 1: Add the Gemini API key setting**

Modify `backend/app/config.py` — add this field to the `Settings` class, alongside the other string settings:
```python
    gemini_api_key: str = ""
```

- [ ] **Step 2: Add the runtime dependency**

Add to `backend/requirements.txt`:
```
google-genai>=2.25,<2.26
```

Install it:
```bash
cd backend
source .venv/bin/activate
pip install -r requirements.txt
```

- [ ] **Step 3: Write the failing test**

`backend/tests/test_llm_client.py`:
```python
from unittest.mock import MagicMock, patch

from app.llm.client import SearchSuggestions, suggest_search_queries


@patch("app.llm.client.genai.Client")
def test_suggest_search_queries_returns_llm_suggestions(mock_client_class):
    mock_client = MagicMock()
    mock_client_class.return_value = mock_client
    mock_response = MagicMock()
    mock_response.parsed = SearchSuggestions(queries=["Beach House", "dream pop"])
    mock_client.models.generate_content.return_value = mock_response

    top_tracks = [
        {"name": "Song A", "artists": [{"name": "Artist A"}]},
        {"name": "Song B", "artists": [{"name": "Artist B"}]},
    ]

    queries = suggest_search_queries(top_tracks, count=2)

    assert queries == ["Beach House", "dream pop"]
    mock_client.models.generate_content.assert_called_once()
    call_kwargs = mock_client.models.generate_content.call_args.kwargs
    assert call_kwargs["model"] == "gemini-flash-latest"
    assert "Artist A" in call_kwargs["contents"]
    assert "Artist B" in call_kwargs["contents"]


@patch("app.llm.client.genai.Client")
def test_suggest_search_queries_excludes_known_artists_from_prompt_instructions(mock_client_class):
    mock_client = MagicMock()
    mock_client_class.return_value = mock_client
    mock_response = MagicMock()
    mock_response.parsed = SearchSuggestions(queries=[])
    mock_client.models.generate_content.return_value = mock_response

    top_tracks = [{"name": "Song A", "artists": [{"name": "Tame Impala"}]}]

    suggest_search_queries(top_tracks)

    call_kwargs = mock_client.models.generate_content.call_args.kwargs
    assert "Tame Impala" in call_kwargs["contents"]
    assert "NOT" in call_kwargs["contents"] or "not already" in call_kwargs["contents"].lower()
```

- [ ] **Step 4: Run the tests to verify they fail**

Run: `pytest tests/test_llm_client.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.llm'`

- [ ] **Step 5: Write the minimal implementation**

`backend/app/llm/__init__.py`: (empty file)

`backend/app/llm/client.py`:
```python
from google import genai
from google.genai import types
from pydantic import BaseModel

from app.config import settings


class SearchSuggestions(BaseModel):
    queries: list[str]


def suggest_search_queries(top_tracks: list[dict], count: int = 5) -> list[str]:
    artist_names = sorted({artist["name"] for track in top_tracks for artist in track.get("artists", [])})
    track_names = [track["name"] for track in top_tracks]

    prompt = (
        f"A music listener's top tracks are: {', '.join(track_names)}.\n"
        f"Their most-listened artists are: {', '.join(artist_names)}.\n"
        f"Suggest {count} search queries (artist names or music genres/styles) for songs "
        f"this listener would likely enjoy but is NOT already listening to. "
        f"Do not suggest any artist already in their most-listened list."
    )

    client = genai.Client(api_key=settings.gemini_api_key)
    response = client.models.generate_content(
        model="gemini-flash-latest",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=SearchSuggestions,
        ),
    )
    return response.parsed.queries
```

- [ ] **Step 6: Run the tests to verify they pass**

Run: `pytest tests/test_llm_client.py -v`
Expected: PASS (2/2)

- [ ] **Step 7: Run the full backend test suite**

Run: `pytest -v` (from `backend/`)
Expected: all tests pass (existing 22 + this task's 2 new ones = 24)

- [ ] **Step 8: Stage changes**

```bash
git add backend/app/llm/__init__.py backend/app/llm/client.py backend/tests/test_llm_client.py backend/app/config.py backend/requirements.txt
```

---

## Task 3: Wire candidate discovery into `/recommendations`

**Files:**
- Modify: `backend/app/routers/recommendations.py`
- Modify: `backend/tests/test_recommendations.py`
- Modify: `.env.example`
- Modify: `.env`
- Modify: `docker-compose.yml`

**Interfaces:**
- Consumes: `app.spotify.client.search_tracks` (Task 1), `app.llm.client.suggest_search_queries` (Task 2), `app.spotify.client.get_top_tracks` (existing).
- Produces: `GET /recommendations` now returns `{"tracks": list[dict]}` where the list is genuinely new tracks (found via LLM-suggested searches), excluding anything already in the user's top tracks — not just a passthrough of `get_top_tracks` anymore.

- [ ] **Step 1: Write the failing tests**

Replace the existing test in `backend/tests/test_recommendations.py` that checks the logged-in-user path (keep the `test_recommendations_requires_session_cookie` test as-is) — replace `test_recommendations_returns_top_tracks_for_logged_in_user` with:

```python
@patch("app.routers.recommendations.search_tracks")
@patch("app.routers.recommendations.suggest_search_queries")
@patch("app.routers.recommendations.get_top_tracks")
def test_recommendations_returns_new_tracks_excluding_known_ones(
    mock_get_top_tracks, mock_suggest_queries, mock_search_tracks, test_db_session
):
    mock_get_top_tracks.return_value = [{"id": "known1", "name": "Known Song", "artists": [{"name": "Known Artist"}]}]
    mock_suggest_queries.return_value = ["dream pop"]
    mock_search_tracks.return_value = [
        {"id": "known1", "name": "Known Song", "artists": [{"name": "Known Artist"}]},
        {"id": "new1", "name": "New Song", "artists": [{"name": "New Artist"}]},
    ]

    user = User(spotify_user_id="spotify_abc123", access_token="abc", refresh_token="xyz")
    test_db_session.add(user)
    test_db_session.commit()

    client = TestClient(app)
    client.cookies.set("attune_session", create_session_token("spotify_abc123"))

    response = client.get("/recommendations")

    assert response.status_code == 200
    tracks = response.json()["tracks"]
    assert len(tracks) == 1
    assert tracks[0]["id"] == "new1"


@patch("app.routers.recommendations.suggest_search_queries")
@patch("app.routers.recommendations.get_top_tracks")
def test_recommendations_falls_back_to_top_tracks_when_llm_call_fails(
    mock_get_top_tracks, mock_suggest_queries, test_db_session
):
    mock_get_top_tracks.return_value = [{"id": "known1", "name": "Known Song", "artists": [{"name": "Known Artist"}]}]
    mock_suggest_queries.side_effect = Exception("LLM API unavailable")

    user = User(spotify_user_id="spotify_abc123", access_token="abc", refresh_token="xyz")
    test_db_session.add(user)
    test_db_session.commit()

    client = TestClient(app)
    client.cookies.set("attune_session", create_session_token("spotify_abc123"))

    response = client.get("/recommendations")

    assert response.status_code == 200
    assert response.json() == {"tracks": [{"id": "known1", "name": "Known Song", "artists": [{"name": "Known Artist"}]}]}
```

Add `search_tracks` and `suggest_search_queries` are patched by target path (`app.routers.recommendations.search_tracks` / `.suggest_search_queries`), so `recommendations.py` must import them by name (`from app.spotify.client import get_top_tracks, search_tracks` and `from app.llm.client import suggest_search_queries`) for the patches to attach correctly — this matches the existing pattern already used for `get_top_tracks` in this file.

- [ ] **Step 2: Run the tests to verify they fail**

Run: `pytest tests/test_recommendations.py -v`
Expected: FAIL — `test_recommendations_returns_new_tracks_excluding_known_ones` fails because the current endpoint just returns `get_top_tracks`'s output unchanged (would return the "known1" track, not filter it, and wouldn't call `search_tracks`/`suggest_search_queries` at all); `test_recommendations_falls_back_to_top_tracks_when_llm_call_fails` fails because there's no try/except around an LLM call yet

- [ ] **Step 3: Write the minimal implementation**

Replace `backend/app/routers/recommendations.py`'s contents with:
```python
from fastapi import APIRouter, Cookie, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.llm.client import suggest_search_queries
from app.models import User
from app.sessions import SESSION_COOKIE_NAME, read_session_token
from app.spotify.client import get_top_tracks, search_tracks

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.get("")
def get_recommendations(
    db: Session = Depends(get_db),
    attune_session: str | None = Cookie(default=None, alias=SESSION_COOKIE_NAME),
) -> dict:
    if attune_session is None:
        raise HTTPException(status_code=401, detail="Not logged in")

    spotify_user_id = read_session_token(attune_session)
    if spotify_user_id is None:
        raise HTTPException(status_code=401, detail="Invalid session")

    user = db.query(User).filter_by(spotify_user_id=spotify_user_id).one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    top_tracks = get_top_tracks(user.access_token)

    try:
        queries = suggest_search_queries(top_tracks)
    except Exception:
        queries = []

    known_track_ids = {track["id"] for track in top_tracks}
    seen_ids = set(known_track_ids)
    candidates = []
    for query in queries:
        for track in search_tracks(user.access_token, query):
            if track["id"] not in seen_ids:
                candidates.append(track)
                seen_ids.add(track["id"])

    return {"tracks": candidates if queries else top_tracks}
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `pytest tests/test_recommendations.py -v`
Expected: PASS (3/3 — the unchanged session-cookie test plus the 2 new ones)

- [ ] **Step 5: Run the full backend test suite**

Run: `pytest -v` (from `backend/`)
Expected: all tests pass (22 existing + 2 from Task 2 + 2 net-new from this task, replacing 1 = 25 total)

- [ ] **Step 6: Add GEMINI_API_KEY to the env templates and Docker Compose**

Add to `.env.example`:
```
GEMINI_API_KEY=
```

Add to `.env` (if you have a real Gemini API key from https://aistudio.google.com/apikey, paste it here; otherwise leave blank — candidate discovery will fail closed to the top-tracks fallback):
```
GEMINI_API_KEY=
```

Add to `docker-compose.yml`'s `backend` service `environment:` block, alongside the existing `SESSION_SECRET`/`FRONTEND_URL` lines:
```yaml
      GEMINI_API_KEY: ${GEMINI_API_KEY}
```

- [ ] **Step 7: Stage changes**

```bash
git add backend/app/routers/recommendations.py backend/tests/test_recommendations.py .env.example docker-compose.yml
```
(`.env` is git-ignored — no need to stage it, but make sure your real key is in there if you have one.)

---

## Self-review notes

- Spec coverage: "candidate-discovery agent" from the design spec ✅ (single search round rather than the spec's fancier multi-round refine loop — explicitly descoped in this plan's Architecture section, not silently dropped). The spec's other LLM role — the free-text vibe *normalizer* — is explicitly out of scope for this plan; there's no free-text vibe input UI yet (that's frontend work + its own future plan). The ranking/scoring model (Problem B) is also explicitly out of scope — this plan only gets new candidates showing up, not smart ranking of them.
- Interface consistency checked: Task 1's `search_tracks(access_token, query, limit=5)` signature matches how Task 3 calls it (`search_tracks(user.access_token, query)`, using the default limit). Task 2's `suggest_search_queries(top_tracks, count=5)` matches Task 3's call (`suggest_search_queries(top_tracks)`, default count). Both patched-by-name in Task 3's tests at the exact import path Task 3's implementation uses.
- No placeholders — every step has real, runnable code. The Gemini SDK usage (`client.models.generate_content`, `GenerateContentConfig`, `response.parsed`) was verified directly against the installed `google-genai==2.25.0` package's real signatures and Pydantic field definitions, not assumed from documentation alone.
- Graceful degradation: if the LLM call fails for any reason (bad/missing API key, rate limit, network issue), `/recommendations` falls back to the pre-existing top-tracks behavior rather than 500ing — covered by its own test in Task 3.
- **Known deviation from the spec (flagged during final review, not caught at plan-writing time):** the design spec's error-handling section calls for LLM failures to fall back to "a hardcoded set of genre-adjacent search terms," but this plan's fallback is plain top-tracks passthrough instead — simpler, but loses the "still show something vibe-adjacent" property the spec intended. Worth revisiting in a future plan once the ranking model exists (a hardcoded fallback is more useful once there's something to rank it against).
