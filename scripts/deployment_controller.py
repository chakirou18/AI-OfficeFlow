"""Outbound-only fixed deployment controller. Start only after explicit host approval."""
import argparse
import json
import time

from deployment import Deployment, ENVIRONMENTS, REPOSITORY, STATE, run, validate_release
from private_registry import check_private_packages


def api(path, body=None):
    command = ["gh", "api", "repos/" + REPOSITORY + "/" + path]
    if body is not None:
        command += ["--method", "POST", "--input", "-"]
    return json.loads(run(command, data=json.dumps(body).encode() if body is not None else None))


def verify_request(request, fetch=api):
    if (request["environment"] not in ENVIRONMENTS or request["creator"]["login"] != "github-actions[bot]"
            or request["ref"] != request["sha"]):
        raise ValueError("Untrusted deployment identity")
    payload = request["payload"]
    if set(payload) != {"release", "request_run"}:
        raise ValueError("Invalid deployment payload")
    release = validate_release(payload["release"])
    if request["sha"] != release["commit"] or type(payload["request_run"]) is not int:
        raise ValueError("Commit/run mismatch")
    ci = fetch(f"actions/runs/{release['ci_run']}")
    publish = fetch(f"actions/runs/{release['release_run']}")
    for workflow in (ci, publish):
        if (workflow["head_branch"] != "main" or workflow["conclusion"] != "success"
                or workflow["head_repository"]["full_name"] != REPOSITORY):
            raise ValueError("Trusted successful main workflow required")
    if ci["event"] != "push" or ci["head_sha"] != release["commit"] or ci["path"] != ".github/workflows/ci.yml":
        raise ValueError("Release did not pass trusted main CI")
    if publish["event"] != "workflow_run" or publish["path"] != ".github/workflows/release.yml":
        raise ValueError("Untrusted image publisher")
    if request["environment"] == "development":
        if payload["request_run"] != release["release_run"]:
            raise ValueError("Development request must originate in release workflow")
        latest = fetch("git/ref/heads/main")["object"]["sha"]
        if latest != release["commit"]:
            raise ValueError("Stale development release")
    else:
        promotion = fetch(f"actions/runs/{payload['request_run']}")
        if (promotion["event"] != "workflow_dispatch" or promotion["head_branch"] != "main"
                or promotion["path"] != ".github/workflows/promote.yml" or promotion["conclusion"] != "success"
                or promotion["head_repository"]["full_name"] != REPOSITORY):
            raise ValueError("Manual trusted production promotion required")
        current = Deployment("development").read_state()
        if current != release:
            raise ValueError("Production must promote the currently verified development digests")
    return release


def status(identifier, state, *, url=None):
    api(f"deployments/{identifier}/statuses", {"state": state, "description": "Fixed local deployment controller: " + state,
        "auto_inactive": False, **({"environment_url": url} if url else {})})


def poll_once():
    processed = STATE / "processed-requests.json"
    seen = json.loads(processed.read_text()) if processed.exists() else []
    for environment in ENVIRONMENTS:
        requests = api("deployments?environment=" + environment + "&per_page=10")
        # Oldest first; stale main checks prevent rolling development backwards.
        for request in reversed(requests):
            identifier = request["id"]
            if identifier in seen:
                continue
            states = api(f"deployments/{identifier}/statuses")
            if states and states[0]["state"] in {"success", "failure", "error", "inactive", "in_progress"}:
                continue
            # A request is created at the end of a hosted job; wait for its success.
            payload = request.get("payload", {})
            if not isinstance(payload, dict) or type(payload.get("request_run")) is not int:
                continue
            if api(f"actions/runs/{payload['request_run']}")["status"] != "completed":
                continue
            try:
                release = verify_request(request)
                check_private_packages()
                # Record in_progress before action; an interrupted process never
                # blindly retries an already-started deployment.
                status(identifier, "in_progress")
                Deployment(environment).apply(release)
                status(identifier, "success", url=f"http://127.0.0.1:{ENVIRONMENTS[environment]}")
                result = "success"
            except Exception:
                status(identifier, "failure")
                result = "failure"
            seen = (seen + [identifier])[-500:]
            STATE.mkdir(parents=True, exist_ok=True)
            processed.write_text(json.dumps(seen), encoding="utf-8")
            print(json.dumps({"deployment_id": identifier, "environment": environment, "result": result}), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--approved-host", action="store_true", help="Explicit approval to activate this fixed local controller")
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    if not args.approved_host:
        parser.error("Host activation requires explicit human approval")
    while True:
        poll_once()
        if args.once:
            return
        time.sleep(15)


if __name__ == "__main__":
    main()
