"""Hosted trusted workflow helper: create a deployment request, not a deployment."""
import argparse
import json
import os
from pathlib import Path

from deployment import REPOSITORY, validate_release
from deployment_controller import api
from private_registry import check_private_packages


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("environment", choices=["development", "production"])
    parser.add_argument("--release", type=Path)
    parser.add_argument("--development-id", type=int)
    args = parser.parse_args()
    if os.getenv("GITHUB_REPOSITORY") != REPOSITORY or os.getenv("GITHUB_REF") != "refs/heads/main":
        raise SystemExit("Deployment requests require this repository's trusted main")
    if args.environment == "development":
        if os.getenv("GITHUB_EVENT_NAME") != "workflow_run":
            raise SystemExit("Development requires a successful trusted CI trigger")
        release = validate_release(json.loads(args.release.read_text()))
        if api("git/ref/heads/main")["object"]["sha"] != release["commit"]:
            raise SystemExit("A newer main commit superseded this release")
    else:
        if os.getenv("GITHUB_EVENT_NAME") != "workflow_dispatch" or not args.development_id:
            raise SystemExit("Production promotion must be explicitly dispatched")
        development = api(f"deployments/{args.development_id}")
        states = api(f"deployments/{args.development_id}/statuses")
        if development["environment"] != "development" or not states or states[0]["state"] != "success":
            raise SystemExit("Successful development deployment required")
        release = validate_release(development["payload"]["release"])
    check_private_packages()
    request = api("deployments", {"ref": release["commit"], "environment": args.environment,
        "auto_merge": False, "required_contexts": [], "production_environment": args.environment == "production",
        "payload": {"release": release, "request_run": int(os.environ["GITHUB_RUN_ID"])},
        "description": "Awaiting actual health-checked deployment by approved private controller"})
    print(json.dumps({"deployment_request": request["id"], "environment": args.environment}))
    summary = os.getenv("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as stream:
            stream.write(f"Deployment request {request['id']} created. This is NOT proof of deployment; await controller success.\n")


if __name__ == "__main__":
    main()
