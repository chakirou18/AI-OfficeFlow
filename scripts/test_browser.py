"""Run real browser tests on a separate Compose project and synthetic test database."""
import json
import os
from pathlib import Path
import secrets
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def main():
    artifacts = ROOT / "artifacts"
    artifacts.mkdir(exist_ok=True)
    config = artifacts / "browser.env"
    if not config.exists():
        config.write_text("POSTGRES_PASSWORD=" + secrets.token_urlsafe(32) + "\n", encoding="utf-8")
    environment = os.environ.copy()
    environment.update(POSTGRES_DB="officeflow_browser_test", FRONTEND_PORT="8081", API_PORT="8001",
                       MODEL_MODE="simulated",
                       TELEMETRY_ENABLED="false",
                       COOKIE_SECURE="false", APP_ORIGINS="http://127.0.0.1:8081")
    command = ["docker", "compose", "-p", "officeflow-browser", "--env-file", str(config)]
    password = secrets.token_urlsafe(32)
    try:
        subprocess.run(command + ["up", "--build", "-d", "--wait", "db", "migrate", "api", "frontend"], cwd=ROOT, env=environment, check=True)
        subprocess.run(command + ["exec", "-T", "-e", "BROWSER_FIXTURES=enabled", "api", "python", "-m", "app.browser_fixture"],
                       cwd=ROOT, env=environment, input=json.dumps({"password": password}), text=True, check=True)
        environment.update(DEMO_HANDLE="t08_browser_fixture", DEMO_PASSWORD=password,
                           FRONTEND_URL="http://127.0.0.1:8081", API_URL="http://127.0.0.1:8001")
        npm = shutil.which("npm.cmd" if os.name == "nt" else "npm")
        if not npm:
            raise SystemExit("Install Node 24/npm and run npm --prefix frontend ci before browser tests")
        subprocess.run([npm, "--prefix", "frontend", "run", "test:e2e"], cwd=ROOT, env=environment, check=True)
    finally:
        # No volume deletion. This does not touch the regular officeflow project.
        subprocess.run(command + ["down"], cwd=ROOT, env=environment, check=True)


if __name__ == "__main__":
    main()
