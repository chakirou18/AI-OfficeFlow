"""Aggregate foundation suites; refuse to migrate a non-test database."""

import subprocess
import sys

from app.database import database_url


if __name__ == "__main__":
    if not (database_url().database or "").endswith("_test"):
        sys.exit("Refusing test migrations: database name must end in _test")
    subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], check=True)
    sys.exit(subprocess.call([sys.executable, "-m", "pytest", "-v"]))
