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