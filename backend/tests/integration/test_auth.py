from datetime import datetime, timedelta, timezone
import secrets

from fastapi.testclient import TestClient
import pytest
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.api import create_app
from app.auth import COOKIE, digest_token
from app.models import DemoUser, LoginSession

pytestmark = pytest.mark.integration


def test_cookie_me_rotation_and_logout_revoke_database_session(auth_context):
    client, engine, _, handle, password = auth_context
    original = client.cookies.get(COOKIE)
    result = client.post("/api/v1/auth/login", json={"handle": handle, "password": password})
    cookie = result.headers["set-cookie"].lower()
    assert "httponly" in cookie and "samesite=strict" in cookie and "max-age=28800" in cookie
    assert client.cookies.get(COOKIE) != original
    with Session(engine) as db:
        assert db.get(LoginSession, digest_token(original)) is None
        assert db.get(LoginSession, digest_token(client.cookies.get(COOKIE))) is not None
    client.headers["X-CSRF-Token"] = result.json()["csrf_token"]
    assert client.get("/api/v1/auth/me").json()["handle"] == handle
    current = client.cookies.get(COOKIE)
    assert client.post("/api/v1/auth/logout").status_code == 204
    client.cookies.set(COOKIE, current)
    assert client.get("/api/v1/auth/me").status_code == 401


@pytest.mark.parametrize("mode", ["expired", "revoked", "disabled", "forged"])
def test_invalid_sessions_are_denied(auth_context, mode):
    client, engine, user_id, _, _ = auth_context
    with Session(engine) as db:
        session = db.get(LoginSession, digest_token(client.cookies.get(COOKIE)))
        if mode == "expired":
            session.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
        elif mode == "revoked":
            db.delete(session)
        elif mode == "disabled":
            db.get(DemoUser, user_id).active = False
        db.commit()
    if mode == "forged":
        client.cookies.clear()
        client.cookies.set(COOKIE, "forged")
    assert client.get("/api/v1/auth/me").status_code == 401
    assert client.post("/api/v1/foundation/checks").status_code == 401


def test_origin_csrf_and_login_failures(auth_context):
    client, _, _, handle, password = auth_context
    assert client.post("/api/v1/foundation/checks", headers={"Origin": "https://evil.invalid"}).status_code == 403
    assert client.post("/api/v1/foundation/checks", headers={"X-CSRF-Token": "wrong"}).status_code == 403
    del client.headers["X-CSRF-Token"]
    assert client.post("/api/v1/auth/logout").status_code == 403
    del client.headers["Origin"]
    assert client.post("/api/v1/auth/login", json={"handle": handle, "password": password}).status_code == 403
    for account in (handle, "nonexistent"):
        response = client.post("/api/v1/auth/login", json={"handle": account, "password": "wrong"},
                               headers={"Origin": "http://testserver"})
        assert response.status_code == 401
        assert response.json() == {"detail": "Invalid credentials"}


def test_lockout_and_secure_cookie_default(auth_context, monkeypatch):
    client, engine, user_id, handle, password = auth_context
    for _ in range(5):
        assert client.post("/api/v1/auth/login", json={"handle": handle, "password": "wrong"}).status_code == 401
    assert client.post("/api/v1/auth/login", json={"handle": handle, "password": password}).status_code == 401
    with Session(engine) as db:
        db.get(DemoUser, user_id).locked_until = datetime.now(timezone.utc) - timedelta(seconds=1)
        db.commit()
    monkeypatch.delenv("COOKIE_SECURE")
    response = client.post("/api/v1/auth/login", json={"handle": handle, "password": password})
    assert response.status_code == 200
    assert "; Secure" in response.headers["set-cookie"]


def test_private_ops_and_anonymous_access(auth_context, monkeypatch):
    client, engine, _, _, _ = auth_context
    assert client.get("/api/v1/ops/health").status_code == 403
    token = secrets.token_urlsafe(32)
    monkeypatch.setenv("OPS_TOKEN", token)
    assert client.get("/api/v1/ops/health", headers={"Authorization": "Bearer wrong"}).status_code == 403
    with TestClient(create_app(engine)) as anonymous:
        assert anonymous.get("/api/v1/auth/me").status_code == 401
        assert anonymous.post("/api/v1/foundation/checks").status_code == 401
        assert anonymous.get("/api/v1/ops/health", headers={"Authorization": f"Bearer {token}"}).status_code == 200
        assert anonymous.post("/api/v1/foundation/checks", headers={"Authorization": f"Bearer {token}"}).status_code == 401
        assert anonymous.post("/api/v1/auth/signup").status_code == 404
    with Session(engine) as db:
        assert db.scalar(select(LoginSession)) is not None
        db.execute(delete(LoginSession).where(LoginSession.expires_at < datetime.now(timezone.utc)))
        db.commit()
