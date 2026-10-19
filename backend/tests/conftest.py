"""Isolated PostgreSQL identities, never runtime/demo credentials."""
import secrets

from fastapi.testclient import TestClient
import pytest
from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.api import create_app
from app.auth import hash_password
from app.database import build_engine, database_url
from app.models import CustomerRequest, DemoUser

ORIGIN = "http://testserver"


@pytest.fixture
def auth_context(monkeypatch):
    if not (database_url().database or "").endswith("_test"):
        pytest.fail("Tests require an isolated database ending in _test")
    monkeypatch.setenv("APP_ORIGINS", ORIGIN)
    monkeypatch.setenv("COOKIE_SECURE", "false")
    engine = build_engine()
    password = secrets.token_urlsafe(24)
    handle = "test_" + secrets.token_hex(8)
    with Session(engine) as db:
        user = DemoUser(handle=handle, password_hash=hash_password(password))
        db.add(user)
        db.commit()
        user_id = user.id
    try:
        with TestClient(create_app(engine)) as client:
            response = client.post("/api/v1/auth/login", json={"handle": handle, "password": password},
                                   headers={"Origin": ORIGIN})
            assert response.status_code == 200
            client.headers.update({"Origin": ORIGIN, "X-CSRF-Token": response.json()["csrf_token"]})
            yield client, engine, user_id, handle, password
    finally:
        with Session(engine) as db:
            db.execute(delete(CustomerRequest).where(CustomerRequest.creator_id == user_id))
            db.execute(delete(DemoUser).where(DemoUser.id == user_id))
            db.commit()
        engine.dispose()
