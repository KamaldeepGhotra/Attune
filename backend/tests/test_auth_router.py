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
