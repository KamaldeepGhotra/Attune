from unittest.mock import patch

import httpx
from fastapi.testclient import TestClient

from app.main import app
from app.models import User
from app.sessions import create_session_token


def test_recommendations_requires_session_cookie():
    client = TestClient(app)

    response = client.get("/recommendations")

    assert response.status_code == 401


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
    mock_suggest_queries.assert_called_once_with(mock_get_top_tracks.return_value)
    mock_search_tracks.assert_called_once_with("abc", "dream pop")


@patch("app.routers.recommendations.search_tracks")
@patch("app.routers.recommendations.suggest_search_queries")
@patch("app.routers.recommendations.get_top_tracks")
def test_recommendations_falls_back_to_top_tracks_when_llm_call_fails(
    mock_get_top_tracks, mock_suggest_queries, mock_search_tracks, test_db_session
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
    mock_search_tracks.assert_not_called()


@patch("app.routers.recommendations.search_tracks")
@patch("app.routers.recommendations.suggest_search_queries")
@patch("app.routers.recommendations.get_top_tracks")
def test_recommendations_dedupes_candidates_found_across_multiple_queries(
    mock_get_top_tracks, mock_suggest_queries, mock_search_tracks, test_db_session
):
    mock_get_top_tracks.return_value = [{"id": "known1", "name": "Known Song", "artists": [{"name": "Known Artist"}]}]
    mock_suggest_queries.return_value = ["dream pop", "shoegaze"]
    mock_search_tracks.side_effect = [
        [{"id": "shared1", "name": "Shared Song", "artists": [{"name": "Shared Artist"}]}],
        [{"id": "shared1", "name": "Shared Song", "artists": [{"name": "Shared Artist"}]}],
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
    assert tracks[0]["id"] == "shared1"


@patch("app.routers.recommendations.search_tracks")
@patch("app.routers.recommendations.suggest_search_queries")
@patch("app.routers.recommendations.get_top_tracks")
def test_recommendations_skips_failed_search_query_and_keeps_others(
    mock_get_top_tracks, mock_suggest_queries, mock_search_tracks, test_db_session
):
    mock_get_top_tracks.return_value = [{"id": "known1", "name": "Known Song", "artists": [{"name": "Known Artist"}]}]
    mock_suggest_queries.return_value = ["dream pop", "shoegaze"]
    failing_request = httpx.Request("GET", "https://api.spotify.com/v1/search")
    failing_response = httpx.Response(429, request=failing_request)
    mock_search_tracks.side_effect = [
        httpx.HTTPStatusError("rate limited", request=failing_request, response=failing_response),
        [{"id": "new1", "name": "New Song", "artists": [{"name": "New Artist"}]}],
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
