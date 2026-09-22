from fastapi.testclient import TestClient

from app.config import settings
from app.main import app


def test_cors_allows_frontend_origin_with_credentials():
    client = TestClient(app)

    response = client.get("/health", headers={"Origin": settings.frontend_url})

    assert response.headers["access-control-allow-origin"] == settings.frontend_url
    assert response.headers["access-control-allow-credentials"] == "true"
