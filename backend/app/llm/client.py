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

    client = genai.Client(
        api_key=settings.gemini_api_key,
        http_options=types.HttpOptions(timeout=10_000),
    )
    response = client.models.generate_content(
        model="gemini-flash-latest",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=SearchSuggestions,
        ),
    )
    return response.parsed.queries
