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
