# Attune Phase 1: Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stand up a working, deployable walking skeleton — FastAPI backend + React frontend + Postgres (via Docker Compose), with real Spotify OAuth login, a session cookie, and a placeholder recommendations endpoint that returns the logged-in user's actual top tracks (no ML yet). This is the foundation every later phase (vibe clustering, ranking model, LLM agent, feedback loop) builds on top of.

**Architecture:** FastAPI backend with SQLAlchemy/Postgres, a thin Spotify API client wrapper, cookie-based sessions (no JWT library needed), and a React (Vite) frontend that logs in via the backend and displays results. Local dev runs everything through Docker Compose.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy 2.0, pydantic-settings, httpx, pytest + respx, React 18 + Vite, Vitest + React Testing Library, PostgreSQL, Docker Compose.

**Spec:** `docs/superpowers/specs/2026-09-07-attune-design.md`

## Global Constraints

- No AI attribution in commits or PR descriptions, and **do not run `git commit` at all** — the project owner commits everything manually. Every "Commit" step below stages changes only (`git add`) and stops there.
- No `CLAUDE.md`, `AGENTS.md`, or similar AI-tool files anywhere in this repo.
- Backend: Python (FastAPI). Frontend: React. Database: PostgreSQL in Docker/prod, SQLite in tests.
- Session cookie name is `attune_session`, set httponly, created via `app.sessions.create_session_token`.
- Real secrets never committed — only `.env.example` is tracked.

---

## Task 1: Backend scaffolding + health check

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/app/__init__.py`
- Create: `backend/app/main.py`
- Create: `backend/pytest.ini`
- Create: `backend/tests/__init__.py`
- Test: `backend/tests/test_health.py`
- Create: `backend/Dockerfile`

**Interfaces:**
- Produces: `app.main.app` (a `FastAPI` instance), `GET /health` → `{"status": "ok"}`.

- [ ] **Step 1: Create the backend directory and dependency list**

```bash
mkdir -p backend/app backend/tests
touch backend/app/__init__.py backend/tests/__init__.py
```

`backend/requirements.txt`:
```
fastapi>=0.115,<0.116
uvicorn[standard]>=0.32,<0.33
sqlalchemy>=2.0,<2.1
pydantic-settings>=2.6,<2.7
httpx>=0.27,<0.28
respx>=0.21,<0.22
itsdangerous>=2.2,<2.3
pytest>=8.3,<8.4
```

- [ ] **Step 2: Create a virtualenv and install dependencies**

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

- [ ] **Step 3: Write the failing test**

`backend/tests/test_health.py`:
```python
from fastapi.testclient import TestClient

from app.main import app


def test_health_check_returns_ok():
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

- [ ] **Step 4: Run the test to verify it fails**

Run (from `backend/`): `pytest tests/test_health.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.main'`

- [ ] **Step 5: Write the minimal implementation**

`backend/app/main.py`:
```python
from fastapi import FastAPI

app = FastAPI(title="Attune")


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
```

`backend/pytest.ini`:
```ini
[pytest]
testpaths = tests
pythonpath = .
```

- [ ] **Step 6: Run the test to verify it passes**

Run: `pytest tests/test_health.py -v`
Expected: PASS

- [ ] **Step 7: Add the Dockerfile**

`backend/Dockerfile`:
```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 8: Stage changes (do not commit — project owner commits manually)**

```bash
git add backend/requirements.txt backend/app/__init__.py backend/app/main.py backend/pytest.ini backend/tests/__init__.py backend/tests/test_health.py backend/Dockerfile
```

---

## Task 2: Database models + connection

**Files:**
- Create: `backend/app/config.py`
- Create: `backend/app/db.py`
- Create: `backend/app/models.py`
- Test: `backend/tests/test_models.py`

**Interfaces:**
- Consumes: nothing from Task 1 directly (independent module).
- Produces: `app.config.settings` (a `Settings` instance with `database_url`, `spotify_client_id`, `spotify_client_secret`, `spotify_redirect_uri`, `session_secret`); `app.db.Base` (SQLAlchemy `DeclarativeBase`); `app.db.get_db()` (FastAPI dependency yielding a `Session`); `app.models.User` with fields `id`, `spotify_user_id: str`, `access_token: str`, `refresh_token: str`, `is_demo: bool`, `connected_at: datetime`, `last_active_at: datetime`.

- [ ] **Step 1: Write the failing test**

`backend/tests/test_models.py`:
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import Base
from app.models import User


def test_create_and_query_user():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()

    user = User(
        spotify_user_id="spotify_abc123",
        access_token="token",
        refresh_token="refresh",
        is_demo=True,
    )
    session.add(user)
    session.commit()

    fetched = session.query(User).filter_by(spotify_user_id="spotify_abc123").one()

    assert fetched.is_demo is True
    assert fetched.access_token == "token"
    assert fetched.connected_at is not None
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `pytest tests/test_models.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.db'`

- [ ] **Step 3: Write the minimal implementation**

`backend/app/config.py`:
```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./attune.db"
    spotify_client_id: str = ""
    spotify_client_secret: str = ""
    spotify_redirect_uri: str = "http://localhost:8000/auth/callback"
    session_secret: str = "dev-secret-change-me"


settings = Settings()
```

`backend/app/db.py`:
```python
from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings


class Base(DeclarativeBase):
    pass


_connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=_connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

`backend/app/models.py`:
```python
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    spotify_user_id: Mapped[str] = mapped_column(String, unique=True, index=True)
    access_token: Mapped[str] = mapped_column(String, default="")
    refresh_token: Mapped[str] = mapped_column(String, default="")
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)
    connected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    last_active_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `pytest tests/test_models.py -v`
Expected: PASS

- [ ] **Step 5: Stage changes**

```bash
git add backend/app/config.py backend/app/db.py backend/app/models.py backend/tests/test_models.py
```

---

## Task 3: Spotify API client wrapper

**Files:**
- Create: `backend/app/spotify/__init__.py`
- Create: `backend/app/spotify/client.py`
- Test: `backend/tests/test_spotify_client.py`

**Interfaces:**
- Consumes: nothing (pure functions taking an access token string).
- Produces: `app.spotify.client.get_current_user_profile(access_token: str) -> dict`, `app.spotify.client.get_top_tracks(access_token: str, limit: int = 20) -> list[dict]`.

- [ ] **Step 1: Write the failing test**

`backend/tests/test_spotify_client.py`:
```python
import httpx
import respx

from app.spotify.client import get_current_user_profile, get_top_tracks


@respx.mock
def test_get_current_user_profile_returns_parsed_json():
    respx.get("https://api.spotify.com/v1/me").mock(
        return_value=httpx.Response(200, json={"id": "spotify_abc123", "display_name": "Test User"})
    )

    profile = get_current_user_profile("fake-token")

    assert profile["id"] == "spotify_abc123"


@respx.mock
def test_get_top_tracks_returns_items_list():
    respx.get("https://api.spotify.com/v1/me/top/tracks").mock(
        return_value=httpx.Response(
            200,
            json={"items": [{"id": "track1", "name": "Song One"}, {"id": "track2", "name": "Song Two"}]},
        )
    )

    tracks = get_top_tracks("fake-token", limit=2)

    assert len(tracks) == 2
    assert tracks[0]["id"] == "track1"
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `pytest tests/test_spotify_client.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.spotify'`

- [ ] **Step 3: Write the minimal implementation**

`backend/app/spotify/__init__.py`: (empty file)

`backend/app/spotify/client.py`:
```python
import httpx

SPOTIFY_API_BASE = "https://api.spotify.com/v1"


def get_current_user_profile(access_token: str) -> dict:
    response = httpx.get(
        f"{SPOTIFY_API_BASE}/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    response.raise_for_status()
    return response.json()


def get_top_tracks(access_token: str, limit: int = 20) -> list[dict]:
    response = httpx.get(
        f"{SPOTIFY_API_BASE}/me/top/tracks",
        headers={"Authorization": f"Bearer {access_token}"},
        params={"limit": limit},
    )
    response.raise_for_status()
    return response.json()["items"]
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `pytest tests/test_spotify_client.py -v`
Expected: PASS

- [ ] **Step 5: Stage changes**

```bash
git add backend/app/spotify/__init__.py backend/app/spotify/client.py backend/tests/test_spotify_client.py
```

---

## Task 4: OAuth pure functions + session token helper

**Files:**
- Create: `backend/app/spotify/oauth.py`
- Create: `backend/app/sessions.py`
- Test: `backend/tests/test_oauth.py`
- Test: `backend/tests/test_sessions.py`

**Interfaces:**
- Consumes: `app.config.settings` (Task 2).
- Produces: `app.spotify.oauth.build_authorize_url(state: str | None = None) -> str`, `app.spotify.oauth.exchange_code_for_tokens(code: str) -> dict`; `app.sessions.SESSION_COOKIE_NAME` (str constant, value `"attune_session"`), `app.sessions.create_session_token(spotify_user_id: str) -> str`, `app.sessions.read_session_token(token: str) -> str | None`.

- [ ] **Step 1: Write the failing tests**

`backend/tests/test_oauth.py`:
```python
import httpx
import respx

from app.config import settings
from app.spotify.oauth import build_authorize_url, exchange_code_for_tokens


def test_build_authorize_url_contains_client_id_and_state():
    url = build_authorize_url(state="teststate")

    assert settings.spotify_client_id in url
    assert "state=teststate" in url
    assert "redirect_uri=" in url


@respx.mock
def test_exchange_code_for_tokens_returns_token_payload():
    respx.post("https://accounts.spotify.com/api/token").mock(
        return_value=httpx.Response(200, json={"access_token": "abc", "refresh_token": "xyz"})
    )

    tokens = exchange_code_for_tokens("some-code")

    assert tokens["access_token"] == "abc"
    assert tokens["refresh_token"] == "xyz"
```

`backend/tests/test_sessions.py`:
```python
from app.sessions import create_session_token, read_session_token


def test_round_trips_spotify_user_id():
    token = create_session_token("spotify_abc123")

    assert read_session_token(token) == "spotify_abc123"


def test_returns_none_for_tampered_token():
    token = create_session_token("spotify_abc123")
    tampered = token[:-1] + ("a" if token[-1] != "a" else "b")

    assert read_session_token(tampered) is None
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `pytest tests/test_oauth.py tests/test_sessions.py -v`
Expected: FAIL with `ModuleNotFoundError` for both `app.spotify.oauth` and `app.sessions`

- [ ] **Step 3: Write the minimal implementation**

`backend/app/spotify/oauth.py`:
```python
import secrets
from urllib.parse import urlencode

import httpx

from app.config import settings

SPOTIFY_AUTHORIZE_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SCOPES = "user-top-read user-library-read playlist-read-private"


def build_authorize_url(state: str | None = None) -> str:
    state = state or secrets.token_urlsafe(16)
    params = {
        "client_id": settings.spotify_client_id,
        "response_type": "code",
        "redirect_uri": settings.spotify_redirect_uri,
        "scope": SCOPES,
        "state": state,
    }
    return f"{SPOTIFY_AUTHORIZE_URL}?{urlencode(params)}"


def exchange_code_for_tokens(code: str) -> dict:
    response = httpx.post(
        SPOTIFY_TOKEN_URL,
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": settings.spotify_redirect_uri,
        },
        auth=(settings.spotify_client_id, settings.spotify_client_secret),
    )
    response.raise_for_status()
    return response.json()
```

`backend/app/sessions.py`:
```python
from itsdangerous import URLSafeSerializer

from app.config import settings

SESSION_COOKIE_NAME = "attune_session"

_serializer = URLSafeSerializer(settings.session_secret, salt="attune-session")


def create_session_token(spotify_user_id: str) -> str:
    return _serializer.dumps({"spotify_user_id": spotify_user_id})


def read_session_token(token: str) -> str | None:
    try:
        data = _serializer.loads(token)
    except Exception:
        return None
    return data.get("spotify_user_id")
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `pytest tests/test_oauth.py tests/test_sessions.py -v`
Expected: PASS

- [ ] **Step 5: Stage changes**

```bash
git add backend/app/spotify/oauth.py backend/app/sessions.py backend/tests/test_oauth.py backend/tests/test_sessions.py
```

---

## Task 5: Auth router (`/auth/login`, `/auth/callback`)

**Files:**
- Create: `backend/tests/conftest.py`
- Create: `backend/app/routers/__init__.py`
- Create: `backend/app/routers/auth.py`
- Modify: `backend/app/main.py`
- Test: `backend/tests/test_auth_router.py`

**Interfaces:**
- Consumes: `app.spotify.oauth.build_authorize_url`, `app.spotify.oauth.exchange_code_for_tokens` (Task 4); `app.spotify.client.get_current_user_profile` (Task 3); `app.sessions.SESSION_COOKIE_NAME`, `app.sessions.create_session_token` (Task 4); `app.db.get_db`, `app.models.User` (Task 2).
- Produces: `app.routers.auth.router` (an `APIRouter`) mounted on `app.main.app`; `GET /auth/login` (302/307 redirect to Spotify); `GET /auth/callback?code=...` → `{"status": "connected", "spotify_user_id": str}` and sets the `attune_session` cookie. Test fixture `test_db_session` (from `conftest.py`) is reused by later tasks' integration tests.

- [ ] **Step 1: Write the shared test fixture**

`backend/tests/conftest.py`:
```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base, get_db
from app.main import app


@pytest.fixture()
def test_db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()

    def override_get_db():
        try:
            yield session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    yield session

    session.close()
    app.dependency_overrides.clear()
```

- [ ] **Step 2: Write the failing tests**

`backend/tests/test_auth_router.py`:
```python
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.models import User


def test_login_redirects_to_spotify_authorize_url():
    client = TestClient(app, follow_redirects=False)

    response = client.get("/auth/login")

    assert response.status_code in (302, 307)
    assert "accounts.spotify.com/authorize" in response.headers["location"]


@patch("app.routers.auth.get_current_user_profile")
@patch("app.routers.auth.exchange_code_for_tokens")
def test_callback_creates_user_and_sets_session_cookie(mock_exchange, mock_profile, test_db_session):
    mock_exchange.return_value = {"access_token": "abc", "refresh_token": "xyz"}
    mock_profile.return_value = {"id": "spotify_abc123", "display_name": "Test User"}

    client = TestClient(app)
    response = client.get("/auth/callback", params={"code": "some-code"})

    assert response.status_code == 200
    assert response.json() == {"status": "connected", "spotify_user_id": "spotify_abc123"}
    assert "attune_session" in response.cookies

    user = test_db_session.query(User).filter_by(spotify_user_id="spotify_abc123").one()
    assert user.access_token == "abc"
```

- [ ] **Step 3: Run the tests to verify they fail**

Run: `pytest tests/test_auth_router.py -v`
Expected: FAIL — `/auth/login` returns 404 (no router mounted yet)

- [ ] **Step 4: Write the minimal implementation**

`backend/app/routers/__init__.py`: (empty file)

`backend/app/routers/auth.py`:
```python
from fastapi import APIRouter, Depends, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import User
from app.sessions import SESSION_COOKIE_NAME, create_session_token
from app.spotify.client import get_current_user_profile
from app.spotify.oauth import build_authorize_url, exchange_code_for_tokens

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/login")
def login() -> RedirectResponse:
    return RedirectResponse(build_authorize_url())


@router.get("/callback")
def callback(code: str, response: Response, db: Session = Depends(get_db)) -> dict:
    tokens = exchange_code_for_tokens(code)
    profile = get_current_user_profile(tokens["access_token"])

    user = db.query(User).filter_by(spotify_user_id=profile["id"]).one_or_none()
    if user is None:
        user = User(
            spotify_user_id=profile["id"],
            access_token=tokens["access_token"],
            refresh_token=tokens.get("refresh_token", ""),
        )
        db.add(user)
    else:
        user.access_token = tokens["access_token"]
        user.refresh_token = tokens.get("refresh_token", user.refresh_token)
    db.commit()

    session_token = create_session_token(profile["id"])
    response.set_cookie(SESSION_COOKIE_NAME, session_token, httponly=True)

    return {"status": "connected", "spotify_user_id": profile["id"]}
```

`backend/app/main.py` (modify):
```python
from fastapi import FastAPI

from app.routers import auth

app = FastAPI(title="Attune")
app.include_router(auth.router)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `pytest tests/test_auth_router.py -v`
Expected: PASS

- [ ] **Step 6: Stage changes**

```bash
git add backend/tests/conftest.py backend/app/routers/__init__.py backend/app/routers/auth.py backend/app/main.py backend/tests/test_auth_router.py
```

---

## Task 6: Recommendations placeholder endpoint

**Files:**
- Create: `backend/app/routers/recommendations.py`
- Modify: `backend/app/main.py`
- Test: `backend/tests/test_recommendations.py`

**Interfaces:**
- Consumes: `app.sessions.SESSION_COOKIE_NAME`, `app.sessions.read_session_token` (Task 4); `app.spotify.client.get_top_tracks` (Task 3); `app.db.get_db`, `app.models.User` (Task 2).
- Produces: `app.routers.recommendations.router`; `GET /recommendations` → `{"tracks": list[dict]}` (200) or 401 if not logged in / invalid session, 404 if the session's user no longer exists.

- [ ] **Step 1: Write the failing tests**

`backend/tests/test_recommendations.py`:
```python
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.models import User
from app.sessions import create_session_token


def test_recommendations_requires_session_cookie():
    client = TestClient(app)

    response = client.get("/recommendations")

    assert response.status_code == 401


@patch("app.routers.recommendations.get_top_tracks")
def test_recommendations_returns_top_tracks_for_logged_in_user(mock_get_top_tracks, test_db_session):
    mock_get_top_tracks.return_value = [{"id": "track1", "name": "Song One"}]

    user = User(spotify_user_id="spotify_abc123", access_token="abc", refresh_token="xyz")
    test_db_session.add(user)
    test_db_session.commit()

    client = TestClient(app)
    client.cookies.set("attune_session", create_session_token("spotify_abc123"))

    response = client.get("/recommendations")

    assert response.status_code == 200
    assert response.json() == {"tracks": [{"id": "track1", "name": "Song One"}]}
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `pytest tests/test_recommendations.py -v`
Expected: FAIL — `/recommendations` returns 404 (no router mounted yet)

- [ ] **Step 3: Write the minimal implementation**

`backend/app/routers/recommendations.py`:
```python
from fastapi import APIRouter, Cookie, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import User
from app.sessions import SESSION_COOKIE_NAME, read_session_token
from app.spotify.client import get_top_tracks

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
    return {"tracks": top_tracks}
```

`backend/app/main.py` (modify):
```python
from fastapi import FastAPI

from app.routers import auth, recommendations

app = FastAPI(title="Attune")
app.include_router(auth.router)
app.include_router(recommendations.router)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `pytest tests/test_recommendations.py -v`
Expected: PASS

- [ ] **Step 5: Run the full backend test suite**

Run: `pytest -v`
Expected: all tests from Tasks 1-6 PASS

- [ ] **Step 6: Stage changes**

```bash
git add backend/app/routers/recommendations.py backend/app/main.py backend/tests/test_recommendations.py
```

---

## Task 7: Frontend scaffolding (Login + Dashboard)

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/vite.config.js`
- Create: `frontend/index.html`
- Create: `frontend/src/setupTests.js`
- Create: `frontend/src/api/client.js`
- Create: `frontend/src/pages/Login.jsx`
- Create: `frontend/src/pages/Dashboard.jsx`
- Create: `frontend/src/App.jsx`
- Create: `frontend/src/main.jsx`
- Test: `frontend/src/pages/__tests__/Login.test.jsx`
- Test: `frontend/src/pages/__tests__/Dashboard.test.jsx`
- Create: `frontend/Dockerfile`

**Interfaces:**
- Consumes: backend `GET /auth/login` and `GET /recommendations` (Tasks 5-6), via `VITE_API_BASE_URL` env var (defaults to `http://localhost:8000`).
- Produces: `getLoginUrl(): string`, `fetchRecommendations(): Promise<{tracks: Array<{id: string, name: string}>}>` from `src/api/client.js`; `<Login />` and `<Dashboard />` components.

- [ ] **Step 1: Scaffold the frontend project files**

`frontend/package.json`:
```json
{
  "name": "attune-frontend",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "test": "vitest run"
  },
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1"
  },
  "devDependencies": {
    "@testing-library/jest-dom": "^6.5.0",
    "@testing-library/react": "^16.0.1",
    "@vitejs/plugin-react": "^4.3.2",
    "jsdom": "^25.0.1",
    "vite": "^5.4.8",
    "vitest": "^2.1.2"
  }
}
```

`frontend/vite.config.js`:
```js
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    setupFiles: "./src/setupTests.js",
  },
});
```

`frontend/index.html`:
```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <title>Attune</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
```

`frontend/src/setupTests.js`:
```js
import "@testing-library/jest-dom/vitest";
```

Install dependencies:
```bash
cd frontend
npm install
```

- [ ] **Step 2: Write the failing tests**

`frontend/src/pages/__tests__/Login.test.jsx`:
```jsx
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import Login from "../Login";

describe("Login", () => {
  it("renders a link to the backend login route", () => {
    render(<Login />);

    const link = screen.getByRole("link", { name: /connect spotify/i });
    expect(link).toHaveAttribute("href", "http://localhost:8000/auth/login");
  });
});
```

`frontend/src/pages/__tests__/Dashboard.test.jsx`:
```jsx
import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import Dashboard from "../Dashboard";

describe("Dashboard", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("renders track names once recommendations load", async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ tracks: [{ id: "1", name: "Song One" }] }),
    });

    render(<Dashboard />);

    expect(await screen.findByText("Song One")).toBeInTheDocument();
  });

  it("shows an error message when the request fails", async () => {
    global.fetch = vi.fn().mockResolvedValue({ ok: false, status: 401 });

    render(<Dashboard />);

    expect(await screen.findByRole("alert")).toHaveTextContent("401");
  });
});
```

- [ ] **Step 3: Run the tests to verify they fail**

Run (from `frontend/`): `npm test`
Expected: FAIL — `../Login` and `../Dashboard` don't exist yet

- [ ] **Step 4: Write the minimal implementation**

`frontend/src/api/client.js`:
```js
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export function getLoginUrl() {
  return `${API_BASE_URL}/auth/login`;
}

export async function fetchRecommendations() {
  const response = await fetch(`${API_BASE_URL}/recommendations`, {
    credentials: "include",
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch recommendations: ${response.status}`);
  }

  return response.json();
}
```

`frontend/src/pages/Login.jsx`:
```jsx
import { getLoginUrl } from "../api/client";

export default function Login() {
  return (
    <main>
      <h1>Attune</h1>
      <a href={getLoginUrl()}>Connect Spotify</a>
    </main>
  );
}
```

`frontend/src/pages/Dashboard.jsx`:
```jsx
import { useEffect, useState } from "react";

import { fetchRecommendations } from "../api/client";

export default function Dashboard() {
  const [tracks, setTracks] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchRecommendations()
      .then((data) => setTracks(data.tracks))
      .catch((err) => setError(err.message));
  }, []);

  if (error) {
    return <p role="alert">{error}</p>;
  }

  return (
    <main>
      <h1>Your recommendations</h1>
      <ul>
        {tracks.map((track) => (
          <li key={track.id}>{track.name}</li>
        ))}
      </ul>
    </main>
  );
}
```

`frontend/src/App.jsx`:
```jsx
import Login from "./pages/Login";

export default function App() {
  return <Login />;
}
```

`frontend/src/main.jsx`:
```jsx
import React from "react";
import ReactDOM from "react-dom/client";

import App from "./App";

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `npm test`
Expected: PASS

- [ ] **Step 6: Add the frontend Dockerfile**

`frontend/Dockerfile`:
```dockerfile
FROM node:20-slim AS build
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
```

- [ ] **Step 7: Stage changes**

```bash
git add frontend/package.json frontend/vite.config.js frontend/index.html frontend/src frontend/Dockerfile
```

*(Note: `frontend/package-lock.json` will also be generated by `npm install` — stage it too if present: `git add frontend/package-lock.json`.)*

---

## Task 8: Docker Compose + env template + root README

**Files:**
- Create: `docker-compose.yml`
- Create: `.env.example`
- Create: `.gitignore`
- Create: `README.md`

**Interfaces:**
- Consumes: `backend/Dockerfile` (Task 1), `frontend/Dockerfile` (Task 7), backend env vars from `app.config.Settings` (Task 2).
- Produces: a runnable local stack via `docker compose up --build`.

- [ ] **Step 1: Write the compose file**

`docker-compose.yml`:
```yaml
services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: attune
      POSTGRES_PASSWORD: attune
      POSTGRES_DB: attune
    ports:
      - "5432:5432"
    volumes:
      - db_data:/var/lib/postgresql/data

  backend:
    build: ./backend
    environment:
      DATABASE_URL: postgresql://attune:attune@db:5432/attune
      SPOTIFY_CLIENT_ID: ${SPOTIFY_CLIENT_ID}
      SPOTIFY_CLIENT_SECRET: ${SPOTIFY_CLIENT_SECRET}
      SPOTIFY_REDIRECT_URI: ${SPOTIFY_REDIRECT_URI:-http://localhost:8000/auth/callback}
      SESSION_SECRET: ${SESSION_SECRET:-dev-secret-change-me}
    ports:
      - "8000:8000"
    depends_on:
      - db

  frontend:
    build: ./frontend
    ports:
      - "5173:80"
    depends_on:
      - backend

volumes:
  db_data:
```

Note: `postgresql://` URLs need the `psycopg2-binary` driver — add it to `backend/requirements.txt` (`psycopg2-binary>=2.9,<2.10`) since Task 2's `app/db.py` uses whatever driver `DATABASE_URL` specifies.

- [ ] **Step 2: Add the driver dependency**

Append to `backend/requirements.txt`:
```
psycopg2-binary>=2.9,<2.10
```

- [ ] **Step 3: Write the env template**

`.env.example`:
```
SPOTIFY_CLIENT_ID=
SPOTIFY_CLIENT_SECRET=
SPOTIFY_REDIRECT_URI=http://localhost:8000/auth/callback
SESSION_SECRET=change-me-to-a-random-string
```

- [ ] **Step 4: Write .gitignore**

`.gitignore`:
```
__pycache__/
*.pyc
.venv/
venv/
node_modules/
dist/
*.db
.env
.DS_Store
```

- [ ] **Step 5: Write the root README**

`README.md`:
```markdown
# Attune

A Spotify recommendation engine that builds a taste profile from your real listening history and suggests songs based on the vibe you're in — not just more of the artists you already listen to.

## Local setup

1. Create an app at https://developer.spotify.com/dashboard, add `http://localhost:8000/auth/callback` as a redirect URI, and add your own Spotify account under the app's User Management tab.
2. Copy `.env.example` to `.env` and fill in your Spotify Client ID/Secret.
3. Run `docker compose up --build`.
4. Visit http://localhost:5173.
```

- [ ] **Step 6: Verify the full stack boots**

Run: `docker compose up --build`
Expected: all three services start; `curl http://localhost:8000/health` returns `{"status":"ok"}`; visiting `http://localhost:5173` in a browser shows the "Connect Spotify" link.

- [ ] **Step 7: Stage changes**

```bash
git add docker-compose.yml .env.example .gitignore README.md backend/requirements.txt
```

---

## Self-review notes

- Spec coverage for this phase: OAuth login/callback ✅, session handling ✅, demo-account-capable data model (`is_demo` flag) ✅, local Docker setup ✅, root README pointing at local setup ✅. Vibe clustering, the ranking model, the LLM agent, the feedback loop, onboarding/per-session MCQ UX, and demo session isolation are explicitly **not** in this phase — they're separate follow-up plans, since this phase's job is only the walking skeleton.
- Every task's `Interfaces: Produces` names match what the next task's `Interfaces: Consumes` expects (checked `get_current_user_profile`, `get_top_tracks`, `SESSION_COOKIE_NAME`, `create_session_token`/`read_session_token`, `get_db`, `User` end to end).
