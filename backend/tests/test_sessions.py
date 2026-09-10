from app.sessions import create_session_token, read_session_token


def test_round_trips_spotify_user_id():
    token = create_session_token("spotify_abc123")

    assert read_session_token(token) == "spotify_abc123"


def test_returns_none_for_tampered_token():
    token = create_session_token("spotify_abc123")
    tampered = token[:-1] + ("a" if token[-1] != "a" else "b")

    assert read_session_token(tampered) is None
