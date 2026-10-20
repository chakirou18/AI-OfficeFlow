"""Fixed local Compose deployment operations; immutable images, no remote code checkout."""
import argparse
from http.cookiejar import CookieJar
import json
import os
from pathlib import Path
import re
import secrets
import subprocess
import time
from urllib.error import HTTPError
from urllib.request import HTTPCookieProcessor, Request, build_opener
from uuid import uuid4

from private_registry import IMAGE_REPOSITORIES

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "artifacts/deployment"
SCHEMA = "0006_human_decisions"
REPOSITORY = "chakirou18/AI-OfficeFlow"
ENVIRONMENTS = {"development": 18080, "production": 28080}


def run(command, *, data=None, env=None):
    result = subprocess.run(command, input=data, capture_output=True, cwd=ROOT, env=env)
    if result.returncode:
        raise RuntimeError("Deployment command failed; raw output withheld to protect credentials")
    return result.stdout


def validate_release(release, *, local=False):
    if set(release) != {"commit", "api", "frontend", "compatible_revisions", "ci_run", "release_run"}:
        raise ValueError("Unexpected release fields")
    if not re.fullmatch(r"[a-f0-9]{40}", release["commit"]):
        raise ValueError("Invalid commit")
    if release["compatible_revisions"] != [SCHEMA] or any(
            not (local and release[key] is None) and (type(release[key]) is not int or release[key] < 1)
            for key in ("ci_run", "release_run")):
        raise ValueError("Unverified schema compatibility or provenance")
    for service in ("api", "frontend"):
        pattern = re.escape(IMAGE_REPOSITORIES[service]) + r"@sha256:[a-f0-9]{64}"
        if not (re.fullmatch(pattern, release[service]) or local and re.fullmatch(r"sha256:[a-f0-9]{64}", release[service])):
            raise ValueError("Only repository-owned immutable digests are accepted")
    return release


class Deployment:
    def __init__(self, environment, *, isolated_ci=False):
        if environment not in ENVIRONMENTS:
            raise ValueError("Unknown deployment environment")
        if isolated_ci and os.getenv("CI") != "true":
            raise ValueError("Isolated CI mode is restricted to CI")
        self.environment, self.isolated_ci = environment, isolated_ci
        self.directory = STATE / environment
        self.directory.mkdir(parents=True, exist_ok=True)
        self.config_path = self.directory / "private.json"
        if not self.config_path.exists():
            self.config_path.write_text(json.dumps({"password": secrets.token_urlsafe(32)}), encoding="utf-8")
            self.config_path.chmod(0o600)
        self.password = json.loads(self.config_path.read_text())["password"]
        self.project = "officeflow-" + environment
        self.port = ENVIRONMENTS[environment]

    def compose(self, release, *args, data=None):
        env = dict(os.environ, DEPLOY_ENVIRONMENT=self.environment, DEPLOY_DATABASE="officeflow_" + self.environment,
                   DEPLOY_PASSWORD=self.password, DEPLOY_PORT=str(self.port), API_IMAGE=release["api"],
                   FRONTEND_IMAGE=release["frontend"], DEPLOY_TELEMETRY="false" if self.isolated_ci else "true")
        return run(["docker", "compose", "-p", self.project, "-f", str(ROOT / "infra/deployment/compose.yaml"), *args], data=data, env=env)

    def read_state(self, name="current"):
        path = self.directory / (name + ".json")
        return json.loads(path.read_text()) if path.exists() else None

    def write_state(self, name, value):
        path = self.directory / (name + ".json")
        temporary = path.with_suffix(".tmp")
        temporary.write_text(json.dumps(value, indent=2), encoding="utf-8")
        temporary.replace(path)

    def database_revision(self, release):
        return self.compose(release, "exec", "-T", "db", "psql", "-U", "officeflow", "-d", "officeflow_" + self.environment,
                            "-Atc", "SELECT version_num FROM alembic_version").decode().strip()

    def connect_collector(self):
        if self.isolated_ci:
            return
        collector = run(["docker", "compose", "ps", "-q", "otel-collector"]).decode().strip()
        if not collector:
            raise RuntimeError("Existing private telemetry Collector must be running")
        networks = json.loads(run(["docker", "inspect", "--format", "{{json .NetworkSettings.Networks}}", collector]))
        network = self.project + "_default"
        if network not in networks:
            # Only Collector joins release networks; APIs never share core aliases.
            run(["docker", "network", "connect", "--alias", "otel-collector", network, collector])

    def apply(self, release, *, local=False):
        validate_release(release, local=local)
        previous = self.read_state()
        if previous:
            revision = self.database_revision(previous)
            if revision not in release["compatible_revisions"]:
                raise RuntimeError("Database revision is outside the tested compatibility contract")
            self.backup(previous)
        if not local:
            for service in ("api", "frontend"):
                run(["docker", "pull", release[service]])
        self.compose(release, "up", "-d", "--wait", "db")
        self.connect_collector()
        try:
            self.compose(release, "run", "--rm", "migrate")
            self.compose(release, "up", "-d", "--wait", "--wait-timeout", "90", "api", "frontend")
            proof = self.smoke(release)
        except Exception:
            if previous and self.database_revision(previous) in previous["compatible_revisions"]:
                self.compose(previous, "up", "-d", "--no-deps", "--wait", "api", "frontend")
                self.smoke(previous)
                self.write_state("last-failure", {"rolled_back": True, "previous": previous, "at": time.time()})
            raise
        if previous and previous != release:
            self.write_state("previous", previous)
        self.write_state("current", release)
        self.write_state("proof", proof | {"release": release, "at": time.time()})
        return proof

    def rollback(self):
        previous, current = self.read_state("previous"), self.read_state()
        if not previous or self.database_revision(current) not in previous["compatible_revisions"]:
            raise RuntimeError("No tested compatible previous release")
        self.compose(previous, "up", "-d", "--no-deps", "--wait", "api", "frontend")
        proof = self.smoke(previous)
        self.write_state("current", previous)
        self.write_state("previous", current)
        self.write_state("rollback-proof", proof | {"release": previous, "at": time.time()})
        return proof

    def smoke(self, release):
        handle, password = "deploy_" + secrets.token_hex(6), secrets.token_urlsafe(32)
        code = """import json,sys
from app.auth import hash_password
from app.database import build_engine
from app.models import DemoUser
from sqlalchemy.orm import Session
p=json.load(sys.stdin)
with Session(build_engine()) as db:
 db.add(DemoUser(handle=p['handle'],password_hash=hash_password(p['password'])))
 db.commit()
"""
        self.compose(release, "exec", "-T", "api", "python", "-c", code,
                     data=json.dumps({"handle": handle, "password": password}).encode())
        login_path = self.directory / "demo-login.json"
        login_path.write_text(json.dumps({"handle": handle, "password": password}), encoding="utf-8")
        login_path.chmod(0o600)
        browser, csrf = build_opener(HTTPCookieProcessor(CookieJar())), ""
        url = f"http://127.0.0.1:{self.port}"
        def call(path, body=None, *, status=200, method=None, extra=None):
            headers = {"Origin": url, "X-CSRF-Token": csrf} | (extra or {})
            data = json.dumps(body).encode() if body is not None else None
            if data is not None:
                headers["Content-Type"] = "application/json"
            try:
                response = browser.open(Request(url + path, data=data, headers=headers, method=method), timeout=35)
            except HTTPError as error:
                response = error
            if response.status != status:
                raise RuntimeError("Authenticated deployment smoke failed; response withheld")
            return json.load(response) if status != 404 else None
        assert call("/api/v1/health/ready")["migration"] in release["compatible_revisions"]
        call("/api/v1/dashboard", status=401)
        csrf = call("/api/v1/auth/login", {"handle": handle, "password": password})["csrf_token"]
        call("/api/v1/ops/exercise/diagnostics", status=404)
        before = call("/api/v1/dashboard")["total_tasks"]
        call("/api/v1/requests", {"title": "Synthetic deployment smoke", "description": "Synthetic release check"}, status=403, extra={"X-CSRF-Token": "invalid"})
        record = call("/api/v1/requests", {"title": "Synthetic deployment smoke", "description": "Synthetic release check"}, status=201)
        analysis = call(f"/api/v1/requests/{record['id']}/analyses", method="POST", status=201, extra={"Idempotency-Key": str(uuid4())})
        assert analysis["state"] == "pending" and analysis["provider_mode"] == "simulated" and 1 <= len(analysis["proposal"]["tasks"]) <= 5
        assert call(f"/api/v1/requests/{record['id']}")["tasks"] == []
        assert call("/api/v1/dashboard")["total_tasks"] == before
        return {"healthy": True, "authenticated_smoke": True, "csrf_enforced": True, "pending_persisted": True,
                "active_tasks_created": 0, "url": url}

    def backup(self, release=None):
        release = release or self.read_state()
        snapshot = self.compose(release, "exec", "-T", "db", "pg_dump", "-U", "officeflow", "-d",
                                "officeflow_" + self.environment, "-Fc", "--no-owner", "--no-acl")
        path = self.directory / ("backup-" + str(time.time_ns()) + ".dump")
        path.write_bytes(snapshot)
        path.chmod(0o600)
        return path

    def restore_smoke(self):
        release = self.read_state()
        dump = self.backup(release)
        name = "officeflow-restore-" + uuid4().hex
        env = dict(os.environ, POSTGRES_PASSWORD=secrets.token_urlsafe(32))
        # A fresh no-network tmpfs instance; no live database or volume is restored.
        run(["docker", "run", "-d", "--name", name, "--network", "none", "--tmpfs", "/var/lib/postgresql/data",
             "-e", "POSTGRES_PASSWORD", "-e", "POSTGRES_USER=officeflow", "-e", "POSTGRES_DB=officeflow_restore_test",
             "postgres@sha256:b0f9560a2de083e2cc7382e75f808c7381a32852a7ec49117deedb300e552b24"], env=env)
        try:
            for attempt in range(30):
                try:
                    run(["docker", "exec", name, "pg_isready", "-h", "127.0.0.1", "-U", "officeflow", "-d", "officeflow_restore_test"])
                    break
                except RuntimeError:
                    if attempt == 29:
                        raise
                    time.sleep(1)
            run(["docker", "exec", "-i", name, "pg_restore", "-U", "officeflow", "-d", "officeflow_restore_test",
                 "--no-owner", "--no-acl", "--exit-on-error"], data=dump.read_bytes())
            query = "SELECT (SELECT count(*) FROM requests),(SELECT count(*) FROM tasks),(SELECT count(*) FROM analysis_runs),(SELECT version_num FROM alembic_version)"
            restored = run(["docker", "exec", name, "psql", "-U", "officeflow", "-d", "officeflow_restore_test", "-Atc", query]).decode().strip()
            original = self.compose(release, "exec", "-T", "db", "psql", "-U", "officeflow", "-d", "officeflow_" + self.environment, "-Atc", query).decode().strip()
            if restored != original:
                raise RuntimeError("Restore schema/count verification failed")
            proof = {"restored_counts_and_revision": restored, "isolated_no_network": True, "live_database_unchanged": True}
            self.write_state("restore-proof", proof)
            return proof
        finally:
            # Stop only the exact fresh scratch container; never remove any volume.
            run(["docker", "stop", name])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["apply", "smoke", "backup", "restore-smoke", "rollback"])
    parser.add_argument("environment", choices=ENVIRONMENTS)
    parser.add_argument("--release", type=Path)
    parser.add_argument("--local-rehearsal", action="store_true")
    parser.add_argument("--isolated-ci", action="store_true")
    args = parser.parse_args()
    deployment = Deployment(args.environment, isolated_ci=args.isolated_ci)
    if args.action == "apply":
        result = deployment.apply(json.loads(args.release.read_text()), local=args.local_rehearsal)
    elif args.action == "smoke":
        result = deployment.smoke(deployment.read_state())
    else:
        result = getattr(deployment, args.action.replace("-", "_"))()
    print(json.dumps(result if not isinstance(result, Path) else {"backup_created": True}))


if __name__ == "__main__":
    main()
