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
