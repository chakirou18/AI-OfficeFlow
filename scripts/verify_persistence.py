"""Verify a synthetic row survives restarting the API and PostgreSQL containers."""

import json
from pathlib import Path
import subprocess
import time
from urllib.error import URLError
from urllib.request import Request, urlopen
import os


ROOT = Path(__file__).resolve().parents[1]


def read_json(url: str, method: str = "GET") -> dict:
    with urlopen(Request(url, method=method), timeout=5) as response:
        return json.load(response)


def main() -> None:
    base = os.environ.get("FRONTEND_URL", "http://127.0.0.1:8080").rstrip("/")
    created = read_json(f"{base}/api/v1/foundation/checks", "POST")
    endpoint = f"{base}/api/v1/foundation/checks/{created['id']}"
    assert read_json(endpoint) == created, "Initial database read does not match"
    print(f"Created and independently read synthetic record {created['id']}", flush=True)

    subprocess.run(["docker", "compose", "restart", "db", "api"], cwd=ROOT, check=True)
    deadline = time.monotonic() + 90
    while True:
        try:
            read_json(f"{base}/api/v1/health/ready")
            after_restart = read_json(endpoint)
            break
        except (URLError, TimeoutError):
            if time.monotonic() >= deadline:
                raise RuntimeError("Foundation did not become ready after restart") from None
            time.sleep(1)
    assert after_restart == created, "Record changed or disappeared after restart"
    evidence = {
        "check_id": created["id"],
        "before_restart": created,
        "after_restart": after_restart,
        "restarted_services": ["db", "api"],
        "result": "passed",
    }
    artifacts = ROOT / "artifacts"
    artifacts.mkdir(exist_ok=True)
    (artifacts / "t04-persistence.json").write_text(
        json.dumps(evidence, indent=2) + "\n", encoding="utf-8"
    )
    print(f"PASS: identical record {created['id']} survived db/api container restart.")
    print("Evidence saved to ignored artifacts/t04-persistence.json (synthetic data only).")


if __name__ == "__main__":
    main()
