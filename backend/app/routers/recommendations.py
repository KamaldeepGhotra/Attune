import logging

import httpx
from fastapi import APIRouter, Cookie, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.llm.client import suggest_search_queries
from app.models import User
from app.sessions import SESSION_COOKIE_NAME, read_session_token
from app.spotify.client import get_top_tracks, search_tracks

router = APIRouter(prefix="/recommendations", tags=["recommendations"])
logger = logging.getLogger(__name__)


@router.get("")
def get_recommendations(
    db: Session = Depends(get_db),
    attune_session: str | None = Cookie(default=None, alias=SESSION_COOKIE_NAME),
) -> dict:
    if attune_session is None:
        raise HTTPException(status_code=401, detail="Not logged in")

    spotify_user_id = read_session_token(attune_session)
    if spotify_user_id is None:
        raise HTTPException(status_code=401, detail="Invalid session")

    user = db.query(User).filter_by(spotify_user_id=spotify_user_id).one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    top_tracks = get_top_tracks(user.access_token)

    try:
        queries = suggest_search_queries(top_tracks)
    except Exception:
        logger.warning("candidate discovery failed; falling back to top tracks", exc_info=True)
        queries = []

    known_track_ids = {track["id"] for track in top_tracks}
    seen_ids = set(known_track_ids)
    candidates = []
    for query in queries:
        try:
            results = search_tracks(user.access_token, query)
        except httpx.HTTPError:
            continue
        for track in results:
            if track["id"] not in seen_ids:
                candidates.append(track)
                seen_ids.add(track["id"])

    return {"tracks": candidates if queries else top_tracks}
