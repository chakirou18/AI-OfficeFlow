"""Portable Python supervisor for ONE explicitly approved independent CLI reviewer.

This is subprocess orchestration, never a native spawn_agent demonstration.
--check-config starts no process. Approval text records consent, not grants it.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import tomllib

from invoke_api_reviewer import ROOT, source_snapshot

ARTIFACTS = ROOT / "artifacts/t17-reviewer-process"
DISABLED = ("shell_tool", "apps", "plugins", "memories", "request_permissions_tool",
            "multi_agent", "multi_agent_v2", "hooks", "browser_use", "computer_use",
            "image_generation", "in_app_browser")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def review_material():
    registration = (ROOT / ".codex/agents/api-reviewer.toml").read_bytes()
    role = tomllib.loads(registration.decode("utf-8"))
    if (role.get("name") != "api_reviewer" or not role.get("description")
            or not role.get("developer_instructions")):
        raise ValueError("Invalid existing reviewer registration")
    spec = importlib.util.spec_from_file_location("review_guard", ROOT / "agent-hooks/review_guard.py")
    guard = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(guard)
    patch = guard.read_fixture()
    skill = (ROOT / "agent-capabilities/review-api-change/SKILL.md").read_text(encoding="utf-8")
    instructions = (role["developer_instructions"] + "\n\n" + skill +
                    "\nYou are the independent api_reviewer process, not a supervisor. "
                    "The supervisor already performed the guarded fixture read. "
                    "Use only the supplied synthetic patch. Do not call tools, inspect files, "
                    "access services, delegate, or claim that another reviewer ran. "
                    "Return your own findings with severity, candidate lines, consequence, "
                    "verification needed, disposition and limitations. No expected findings "
                    "or prior conversation have been supplied.\n")
    prompt = "Review this isolated proposed API change; never apply or execute it:\n" + json.dumps(patch)
    return registration, instructions, prompt


def reviewer_command(executable, cwd, instructions):
    command = [executable, "--no-daemon", "--sandbox", "read-only", "--ask-for-approval", "never"]
    for feature in DISABLED:
        command += ["--disable", feature]
    for key, value in (("developer_instructions", instructions), ("web_search", "disabled"),
                       ("agents.enabled", False), ("project_doc_max_bytes", 0)):
        command += ["-c", key + "=" + json.dumps(value)]
    return command + ["exec", "--ignore-user-config", "--skip-git-repo-check", "--ephemeral",
                      "--json", "--cd", str(cwd), "-"]


def verify_events(events):
    """Mechanical provenance checks; human assessment of findings is still required."""
    sessions = [e.get("thread_id") for e in events if e.get("type") == "thread.started"]
    finals = [e["item"]["text"] for e in events if e.get("type") == "item.completed"
              and e.get("item", {}).get("type") == "agent_message"]
    tool_items = [e for e in events if e.get("item") and
                  e["item"].get("type") not in {"agent_message", "reasoning"}]
    passed = (len(sessions) == 1 and bool(sessions[0]) and bool(finals)
              and any(e.get("type") == "turn.completed" for e in events)
              and not any(e.get("type") in {"error", "turn.failed"} for e in events)
              and not tool_items)
    return {"cli_session_ids": sessions, "tool_item_count": len(tool_items),
            "mechanical_checks_passed": passed}, "\n\n".join(finals)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-config", action="store_true")
    parser.add_argument("--approval-reference")
    args = parser.parse_args()
    if not args.check_config and not (args.approval_reference and
                                      1 <= len(args.approval_reference.strip()) <= 500):
        parser.error("Actual explicit human approval and --approval-reference are required")
    registration, instructions, prompt = review_material()
    if args.check_config:
        print(json.dumps({"orchestration": "python-supervised CLI subprocess",
                          "role": "api_reviewer", "registration_sha256": digest(registration),
                          "instructions_sha256": digest(instructions.encode()),
                          "prompt_sha256": digest(prompt.encode()),
                          "command": reviewer_command("codex", "<empty-temporary-directory>", instructions),
                          "processes_started": 0, "model_invocations": 0}))
        return
    executable = shutil.which("codex")
    if not executable:
        parser.error("Existing Codex CLI not found; no install or fallback permitted")
    # Exclusive one-shot evidence directory: never overwrite a previous attempt.
    ARTIFACTS.mkdir(parents=True, exist_ok=False)
    (ARTIFACTS / "registration.toml").write_bytes(registration)
    (ARTIFACTS / "reviewer-instructions.txt").write_text(instructions, encoding="utf-8")
    (ARTIFACTS / "reviewer-input.txt").write_text(prompt, encoding="utf-8")
    before = source_snapshot()
    evidence = {"orchestration": "subprocess; not native spawn_agent", "role": "api_reviewer",
                "approval_reference": args.approval_reference, "supervisor_pid": os.getpid(),
                "parent_context_id": os.environ.get("CODEX_THREAD_ID"),
                "cli_executable_sha256": digest(Path(executable).read_bytes()),
                "started_at": datetime.now(timezone.utc).isoformat(), "reviewer_launches": 0,
                "registration_sha256": digest(registration),
                "instructions_sha256": digest(instructions.encode()),
                "prompt_sha256": digest(prompt.encode()), "source_before": before}
    error = None
    try:
        with tempfile.TemporaryDirectory(prefix="officeflow-api-review-") as cwd:
            command = reviewer_command(executable, cwd, instructions)
            evidence["command"] = command
            # Do not inherit parent thread/daemon linkage; preserve auth and OS environment.
            env = {k: v for k, v in os.environ.items() if k not in {
                "CODEX_THREAD_ID", "CODEX_SESSION_ID", "CODEX_TOOL_CALL_ID", "CODEX_DAEMON_SHUTDOWN_SOCKET",
                "CODEX_API_KEY", "OPENAI_API_KEY"}}
            with (ARTIFACTS / "events.jsonl").open("wb") as out, (ARTIFACTS / "stderr.txt").open("wb") as err:
                process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=out, stderr=err,
                                           cwd=cwd, env=env, shell=False)
                evidence.update(reviewer_pid=process.pid, reviewer_launches=1)
                try:
                    process.communicate(prompt.encode(), timeout=240)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.communicate()
                    raise RuntimeError("Reviewer timeout; evidence preserved; no retry") from None
                evidence["exit_code"] = process.returncode
    except Exception as exc:
        error = type(exc).__name__
        evidence["execution_error"] = error
    finally:
        after = source_snapshot()
        evidence.update(source_after=after, source_files_unchanged=before == after,
                        finished_at=datetime.now(timezone.utc).isoformat())
        (ARTIFACTS / "invocation.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    if error:
        raise SystemExit("Independent reviewer failed; inspect preserved evidence. No retry.")
    events = [json.loads(line) for line in (ARTIFACTS / "events.jsonl").read_text(encoding="utf-8").splitlines()]
    checks, response = verify_events(events)
    checks["process_completed_successfully"] = evidence["exit_code"] == 0
    checks["source_files_unchanged"] = evidence["source_files_unchanged"]
    checks["fresh_session"] = (len(checks["cli_session_ids"]) == 1 and
                               checks["cli_session_ids"][0] != evidence["parent_context_id"])
    (ARTIFACTS / "response.md").write_text(response, encoding="utf-8")
    (ARTIFACTS / "verification.json").write_text(json.dumps(checks, indent=2), encoding="utf-8")
    print(json.dumps(checks))
    if not all(checks[key] for key in ("mechanical_checks_passed", "process_completed_successfully",
                                     "source_files_unchanged", "fresh_session")):
        raise SystemExit("Verification failed; stop without retry or completion claim")
    print("Mechanical checks passed. Inspect independent findings and effective instructions before completion claims.")


if __name__ == "__main__":
    main()
