"""Equal-permission demo sessions; operations bearer credentials are separate."""
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import os
import secrets

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models import DemoUser, LoginSession

COOKIE = "officeflow_session"
SESSION_SECONDS = 8 * 60 * 60


def hash_password(password: str, salt: str | None = None) -> str:
    salt = salt or secrets.token_hex(16)
    # OWASP scrypt option: N=2^14, r=8, p=5 (~16 MiB per hash).
    digest = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), n=16384, r=8, p=5)
    return f"scrypt${salt}${digest.hex()}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, salt, _ = encoded.split("$")
        return algorithm == "scrypt" and hmac.compare_digest(hash_password(password, salt), encoded)
    except (ValueError, TypeError):
        return False


DUMMY_HASH = hash_password("not-an-account-password")


def digest_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def csrf_token(token: str) -> str:
    return hmac.new(token.encode(), b"officeflow-csrf", hashlib.sha256).hexdigest()


def require_origin(request: Request) -> None:
    allowed = os.environ.get("APP_ORIGINS", "http://127.0.0.1:8080,http://localhost:8080").split(",")
    if request.headers.get("origin") not in allowed:
        raise HTTPException(403, "Origin not allowed")


def current_user(request: Request) -> DemoUser:
    token = request.cookies.get(COOKIE, "")
    with Session(request.app.state.engine) as db:
        session = db.get(LoginSession, digest_token(token)) if token else None
        user = db.get(DemoUser, session.user_id) if session else None
        if not session or session.expires_at <= datetime.now(timezone.utc) or not user or not user.active:
            raise HTTPException(401, "Authentication required")
        return user


def require_mutation(request: Request, user: DemoUser = Depends(current_user)) -> DemoUser:
    require_origin(request)
    expected = csrf_token(request.cookies[COOKIE])
    if not hmac.compare_digest(request.headers.get("x-csrf-token", "").encode(), expected.encode()):
        raise HTTPException(403, "CSRF token required")
    return user


def require_ops(request: Request) -> None:
    configured = os.environ.get("OPS_TOKEN", "")
    supplied = request.headers.get("authorization", "")
    if len(configured) < 32 or not hmac.compare_digest(supplied.encode(), f"Bearer {configured}".encode()):
        raise HTTPException(403, "Operations authorization required")


class LoginInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    handle: str = Field(min_length=1, max_length=40, pattern=r"^[a-z0-9_-]+$")
    password: str = Field(min_length=1, max_length=128)


router = APIRouter(prefix="/api/v1")


@router.post("/auth/login")
def login(payload: LoginInput, request: Request, response: Response):
    require_origin(request)
    now = datetime.now(timezone.utc)
    with Session(request.app.state.engine) as db:
        user = db.scalar(select(DemoUser).where(DemoUser.handle == payload.handle).with_for_update())
        valid = verify_password(payload.password, user.password_hash if user else DUMMY_HASH)
        if not user or not user.active or (user.locked_until and user.locked_until > now) or not valid:
            if user:
                user.failed_logins += 1
                if user.failed_logins >= 5:
                    user.locked_until = now + timedelta(minutes=5)
                    user.failed_logins = 0
                db.commit()
            raise HTTPException(401, "Invalid credentials")
        user.failed_logins = 0
        user.locked_until = None
        previous = request.cookies.get(COOKIE)
        if previous:
            db.execute(delete(LoginSession).where(LoginSession.token_hash == digest_token(previous)))
        db.execute(delete(LoginSession).where(LoginSession.expires_at <= now))
        token = secrets.token_urlsafe(32)
        db.add(LoginSession(token_hash=digest_token(token), user_id=user.id,
                            expires_at=now + timedelta(seconds=SESSION_SECONDS)))
        db.commit()
        response.set_cookie(COOKIE, token, httponly=True, samesite="strict", path="/",
                            secure=os.environ.get("COOKIE_SECURE", "true").lower() != "false",
                            max_age=SESSION_SECONDS)
        response.headers["Cache-Control"] = "no-store"
        return {"handle": user.handle, "csrf_token": csrf_token(token)}


@router.get("/auth/me")
def me(request: Request, response: Response, user: DemoUser = Depends(current_user)):
    response.headers["Cache-Control"] = "no-store"
    return {"handle": user.handle, "csrf_token": csrf_token(request.cookies[COOKIE])}


@router.post("/auth/logout", status_code=204)
def logout(request: Request, response: Response, _: DemoUser = Depends(require_mutation)):
    with Session(request.app.state.engine) as db:
        db.execute(delete(LoginSession).where(LoginSession.token_hash == digest_token(request.cookies[COOKIE])))
        db.commit()
    response.delete_cookie(COOKIE, path="/", httponly=True, samesite="strict",
                           secure=os.environ.get("COOKIE_SECURE", "true").lower() != "false")


@router.get("/ops/health", dependencies=[Depends(require_ops)])
def ops_health():
    return {"status": "ok", "scope": "diagnostics-only"}
