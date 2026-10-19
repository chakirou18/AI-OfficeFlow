from unittest.mock import MagicMock

from fastapi.testclient import TestClient
from sqlalchemy import Engine
from sqlalchemy.exc import OperationalError

from app.api import create_app


def test_liveness_does_not_require_database():
    engine = MagicMock(spec=Engine)
    with TestClient(create_app(engine)) as client:
        response = client.get("/api/v1/health/live")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    engine.connect.assert_not_called()


def test_readiness_failure_is_503_without_driver_details():
    engine = MagicMock(spec=Engine)
    engine.connect.side_effect = OperationalError(
        "sensitive SQL", {}, Exception("credential-like driver detail")
    )
    with TestClient(create_app(engine)) as client:
        response = client.get("/api/v1/health/ready")
    assert response.status_code == 503
    assert response.json() == {"detail": "Database unavailable"}
    assert "sensitive" not in response.text
    assert "credential" not in response.text
