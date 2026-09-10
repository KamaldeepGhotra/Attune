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
