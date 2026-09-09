from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import Base
from app.models import User


def test_create_and_query_user():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()

    user = User(
        spotify_user_id="spotify_abc123",
        access_token="token",
        refresh_token="refresh",
        is_demo=True,
    )
    session.add(user)
    session.commit()

    fetched = session.query(User).filter_by(spotify_user_id="spotify_abc123").one()

    assert fetched.is_demo is True
    assert fetched.access_token == "token"
    assert fetched.connected_at is not None
