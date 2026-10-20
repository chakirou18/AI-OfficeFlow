"""Executable guardrail for one synthetic reviewer tool, not a shell sandbox."""
import argparse
import hashlib
import json
from pathlib import Path
import tempfile

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "agent-capabilities/review-api-change/fixtures/approval-change.diff"
POLICY = Path(__file__).with_name("review-policy.json")


class Denied(Exception):
    pass


def load_policy():
    raw = POLICY.read_bytes()
    if len(raw) > 4096:
        raise ValueError("Oversized policy")
    return json.loads(raw)


def fixture_digest():
    # Preserve the policy across Git's LF/CRLF checkout conversion.
    return hashlib.sha256(FIXTURE.read_text(encoding="utf-8").encode()).hexdigest()


def guarded(action, operation, *, policy_loader=load_policy):
    """Invoke a trusted handler only after the fixed read policy passes."""
    try:
        policy = policy_loader()
        if (not isinstance(policy, dict) or set(policy) != {"role", "actions", "fixture_sha256"}
                or policy["role"] != "api_reviewer" or policy["actions"] != ["read_fixture"]
                or not isinstance(policy["fixture_sha256"], str)
                or fixture_digest() != policy["fixture_sha256"]):
            raise ValueError("Invalid policy")
    except Exception:
        raise Denied("policy_check_failed") from None
    if action != "read_fixture":
        raise Denied("action_not_allowed")
    return operation()


def read_fixture():
    return guarded("read_fixture", lambda: {
        "classification": "synthetic_only", "untrusted_content": True,
        "fixture": "approval-change", "content": FIXTURE.read_text(encoding="utf-8")})


def demonstrate():
    allowed = read_fixture()
    outcomes = {"allowed_read": allowed["untrusted_content"] and bool(allowed["content"])}
    with tempfile.TemporaryDirectory(prefix="officeflow-review-") as directory:
        sentinel = Path(directory) / "synthetic-sentinel.txt"
        sentinel.write_bytes(b"unchanged")
        def forbidden_write():
            sentinel.write_bytes(b"changed")
        for name, action, loader in (
                ("unauthorized_write", "write_fixture", load_policy),
                ("failed_policy", "read_fixture", lambda: {"actions": ["write_fixture"]})):
            try:
                guarded(action, forbidden_write, policy_loader=loader)
            except Denied as error:
                outcomes[name] = {"blocked": True, "reason": str(error),
                                  "sentinel_unchanged": sentinel.read_bytes() == b"unchanged"}
            else:
                raise RuntimeError("Guardrail failed to block a side effect")
    assert outcomes["allowed_read"] and all(outcomes[key]["sentinel_unchanged"]
                                           for key in ("unauthorized_write", "failed_policy"))
    return outcomes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--read-fixture", action="store_true")
    mode.add_argument("--demo", action="store_true")
    args = parser.parse_args()
    print(json.dumps(demonstrate() if args.demo else read_fixture()))


if __name__ == "__main__":
    main()
