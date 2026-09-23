import httpx
import respx

from app.spotify.client import get_current_user_profile, get_top_tracks, search_tracks


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


@respx.mock
def test_search_tracks_returns_items_list():
    route = respx.get("https://api.spotify.com/v1/search").mock(
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
    assert route.calls.last.request.url.params["type"] == "track"
    assert route.calls.last.request.url.params["q"] == "dream pop"
    assert route.calls.last.request.url.params["limit"] == "2"
