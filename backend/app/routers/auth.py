from fastapi import APIRouter, Depends, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import User
from app.sessions import SESSION_COOKIE_NAME, create_session_token
from app.spotify.client import get_current_user_profile
from app.spotify.oauth import build_authorize_url, exchange_code_for_tokens

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/login")
def login() -> RedirectResponse:
    return RedirectResponse(build_authorize_url())


@router.get("/callback")
def callback(code: str, response: Response, db: Session = Depends(get_db)) -> dict:
    tokens = exchange_code_for_tokens(code)
    profile = get_current_user_profile(tokens["access_token"])

    user = db.query(User).filter_by(spotify_user_id=profile["id"]).one_or_none()
    if user is None:
        user = User(
            spotify_user_id=profile["id"],
            access_token=tokens["access_token"],
            refresh_token=tokens.get("refresh_token", ""),
        )
        db.add(user)
    else:
        user.access_token = tokens["access_token"]
        user.refresh_token = tokens.get("refresh_token", user.refresh_token)
    db.commit()

    session_token = create_session_token(profile["id"])
    response.set_cookie(SESSION_COOKIE_NAME, session_token, httponly=True)

    return {"status": "connected", "spotify_user_id": profile["id"]}
