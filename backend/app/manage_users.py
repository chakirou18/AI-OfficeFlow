"""Private terminal-only account creation/revocation; no public signup."""
import argparse
from getpass import getpass
import re

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.auth import hash_password
from app.database import build_engine
from app.models import DemoUser, LoginSession


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["create", "revoke", "disable"])
    parser.add_argument("handle")
    args = parser.parse_args()
    if not re.fullmatch(r"[a-z0-9_-]{1,40}", args.handle):
        parser.error("Handle must contain 1-40 lowercase letters, digits, underscores or hyphens")
    encoded = None
    if args.action == "create":
        password = getpass("New demo password (16-128 characters): ")
        if not 16 <= len(password) <= 128 or password != getpass("Confirm password: "):
            parser.error("Password length or confirmation invalid")
        encoded = hash_password(password)
    engine = build_engine()
    try:
        with Session(engine) as db:
            user = db.scalar(select(DemoUser).where(DemoUser.handle == args.handle).with_for_update())
            if args.action == "create":
                if user:
                    parser.error("Account already exists; existing credentials are preserved")
                db.add(DemoUser(handle=args.handle, password_hash=encoded))
            else:
                if not user:
                    parser.error("Account not found")
                db.execute(delete(LoginSession).where(LoginSession.user_id == user.id))
                if args.action == "disable":
                    user.active = False
            db.commit()
        print("Account operation completed; no credentials printed.")
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
