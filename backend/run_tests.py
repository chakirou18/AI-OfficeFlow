"""Aggregate deterministic suites; refuse to migrate a non-test database."""

import os
import subprocess
import sys

from app.database import database_url


def main():
    if not (database_url().database or "").endswith("_test"):
        sys.exit("Refusing test migrations: database name must end in _test")
    environment = os.environ | {"MODEL_MODE": "simulated"}
    subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], check=True, env=environment)
    return subprocess.call([sys.executable, "-m", "pytest", "-v"], env=environment)


if __name__ == "__main__":
    sys.exit(main())
