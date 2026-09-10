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
