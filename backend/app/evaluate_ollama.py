"""Explicit real evaluation on isolated synthetic data; never part of CI."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import secrets
import subprocess
import sys
import time
from uuid import UUID, uuid4

from fastapi.testclient import TestClient
import httpx
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api import create_app
from app.auth import hash_password
from app.database import build_engine, database_url
from app.model_adapter import OllamaAdapter, Proposal
from app.models import AnalysisRun, DemoUser, Task


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--real", action="store_true", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--cases", nargs="+", default=["simple", "ambiguous", "injection"])
    args = parser.parse_args()
    if not (database_url().database or "").endswith("_test"):
        parser.error("Real evaluation requires an isolated _test database")
    # Only repository-owned fixtures can enter this explicit evaluation report.
    fixtures = json.loads((Path(__file__).parents[1] / "tests/fixtures/ollama_evaluations.json").read_text())
    selected = [item for item in fixtures if item["id"] in args.cases and item["case"] == "valid"]
    if len(selected) != len(args.cases) or len(selected) > 5:
        parser.error("Choose 1-5 unique valid synthetic fixture IDs")
    subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], check=True)
    adapter = OllamaAdapter("http://host.docker.internal:11434", max_calls=20)
    with httpx.Client(trust_env=False, timeout=5) as provider:
        version = provider.get(adapter.base_url + "/api/version").json()["version"]
        tags = provider.get(adapter.base_url + "/api/tags").json()["models"]
    installed = next(item for item in tags if item["name"] == adapter.provider_model)
    engine = build_engine()
    handle, password = "eval_" + secrets.token_hex(6), secrets.token_urlsafe(24)
    with Session(engine) as db:
        user = DemoUser(handle=handle, password_hash=hash_password(password))
        db.add(user)
        db.commit()
        tasks_before = db.scalar(select(func.count()).select_from(Task))
    report = {"evaluated_at": datetime.now(timezone.utc).isoformat(), "real_inference": True,
              "provider": "Ollama", "server_version": version, "model": adapter.provider_model,
              "model_digest": installed["digest"], "fixture_source": "backend/tests/fixtures/ollama_evaluations.json",
              "limits": {"deadline_seconds": 30, "num_ctx": 4096, "num_predict": 512, "num_gpu": 0,
                         "max_response_bytes": 32768, "max_calls": 20, "concurrency": 1,
                         "automatic_retry": False, "fallback": False}, "results": []}
    application = create_app(engine)
    application.state.model_adapter = adapter
    with TestClient(application) as client:
        origin = "http://testserver"
        response = client.post("/api/v1/auth/login", json={"handle": handle, "password": password}, headers={"Origin": origin})
        response.raise_for_status()
        client.headers.update({"Origin": origin, "X-CSRF-Token": response.json()["csrf_token"]})
        for item in selected:
            response = client.post("/api/v1/requests", json={"title": item["title"], "description": item["description"]})
            response.raise_for_status()
            request_id = response.json()["id"]
            started = time.monotonic()
            response = client.post(f"/api/v1/requests/{request_id}/analyses", headers={"Idempotency-Key": str(uuid4())})
            elapsed = round(time.monotonic() - started, 3)
            run = response.json()
            valid = False
            if run.get("proposal"):
                Proposal.model_validate(run["proposal"])
                valid = True
            with Session(engine) as db:
                stored = db.get(AnalysisRun, UUID(run["id"]))
                assert stored.state == run["state"] and stored.proposal == run["proposal"]
                assert db.scalar(select(func.count()).select_from(Task)) == tasks_before
            report["results"].append({"fixture_id": item["id"], "http_status": response.status_code,
                "elapsed_seconds": elapsed, "schema_valid": valid, "persisted": True,
                "tasks_created": 0, "analysis": run})
            # Preserve the first genuine failure, with no automatic retry.
            if run["state"] != "pending":
                break
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    engine.dispose()
    print(json.dumps({"real_inference": True, "model": adapter.provider_model,
                      "results": [{"fixture_id": r["fixture_id"], "state": r["analysis"]["state"],
                      "elapsed_seconds": r["elapsed_seconds"]} for r in report["results"]]}))
    return 0 if len(report["results"]) == len(selected) and all(r["schema_valid"] for r in report["results"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
