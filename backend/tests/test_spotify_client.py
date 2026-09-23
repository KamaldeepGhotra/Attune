import httpx
import respx
from unittest.mock import Mock, patch

from app.spotify.client import get_current_user_profile, get_top_tracks, search_tracks


@patch("app.spotify.client.httpx.get")
def test_get_current_user_profile_returns_parsed_json(mock_get):
    mock_response = Mock()
    mock_response.json.return_value = {"id": "spotify_abc123", "display_name": "Test User"}
    mock_get.return_value = mock_response

    profile = get_current_user_profile("fake-token")

    assert profile["id"] == "spotify_abc123"


@patch("app.spotify.client.httpx.get")
def test_get_top_tracks_returns_items_list(mock_get):
    mock_response = Mock()
    mock_response.json.return_value = {"items": [{"id": "track1", "name": "Song One"}, {"id": "track2", "name": "Song Two"}]}
    mock_get.return_value = mock_response

    tracks = get_top_tracks("fake-token", limit=2)

    assert len(tracks) == 2
    assert tracks[0]["id"] == "track1"


@patch("app.spotify.client.httpx.get")
def test_search_tracks_returns_items_list(mock_get):
    mock_response = Mock()
    mock_response.json.return_value = {
        "tracks": {
            "items": [
                {"id": "track1", "name": "Song One", "artists": [{"name": "Artist One"}]},
                {"id": "track2", "name": "Song Two", "artists": [{"name": "Artist Two"}]},
            ]
        }
    }
    mock_get.return_value = mock_response

    tracks = search_tracks("fake-token", "dream pop", limit=2)

    assert len(tracks) == 2
    assert tracks[0]["id"] == "track1"
