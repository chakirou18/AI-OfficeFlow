"""Explicit synthetic browser-test fixture, never an app task-creation mechanism."""
import json
import os
import sys
from uuid import uuid4

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.auth import hash_password
from app.database import build_engine, database_url
from app.models import CustomerRequest, DemoUser, LoginSession, Task

HANDLE = "t08_browser_fixture"


def main():
    if os.environ.get("BROWSER_FIXTURES") != "enabled" or not (database_url().database or "").endswith("_test"):
        raise SystemExit("Browser fixtures require explicit enablement and an isolated _test database")
    password = json.load(sys.stdin)["password"]
    if not isinstance(password, str) or not 16 <= len(password) <= 128:
        raise SystemExit("A privately generated 16-128 character fixture password is required")
    engine = build_engine()
    try:
        with Session(engine) as db:
            user = db.scalar(select(DemoUser).where(DemoUser.handle == HANDLE))
            if user is None:
                user = DemoUser(handle=HANDLE, password_hash=hash_password(password))
                db.add(user)
                db.flush()
            else:
                # Reset only this named test fixture's records; never other users/data.
                db.execute(delete(CustomerRequest).where(CustomerRequest.creator_id == user.id))
                db.execute(delete(LoginSession).where(LoginSession.user_id == user.id))
                user.password_hash = hash_password(password)
                user.active = True
                user.failed_logins = 0
                user.locked_until = None
            requests = [CustomerRequest(title=f"Synthetic workspace request {index + 1:02d}",
                                        description="Synthetic browser pagination fixture only.",
                                        creator_id=user.id, creator_handle=HANDLE) for index in range(11)]
            work = CustomerRequest(title="Synthetic equipment review", description="Review demonstration equipment only.",
                                   creator_id=user.id, creator_handle=HANDLE)
            db.add_all(requests + [work])
            db.flush()
            source = uuid4()
            # Test-only persisted approved-task fixtures; NOT evidence of T11 approval.
            for index, (title, priority, state) in enumerate([
                ("Inspect synthetic equipment", "high", "open"),
                ("Prepare synthetic checklist", "medium", "open"),
                ("Archive synthetic notes", "low", "done"),
            ]):
                db.add(Task(request_id=work.id, analysis_id=source, suggestion_index=index,
                            title=title, rationale="Explicit synthetic browser fixture; approval workflow is not implemented.",
                            priority=priority, state=state))
            db.commit()
        print("Synthetic browser fixture ready (isolated test database only).")
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
