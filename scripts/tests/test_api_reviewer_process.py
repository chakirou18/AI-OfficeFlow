"""Offline supervisor checks: no CLI/model process is launched by these tests."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
spec = importlib.util.spec_from_file_location(
    "reviewer_process", Path(__file__).resolve().parents[1] / "invoke_api_reviewer_process.py")
reviewer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reviewer)


class ReviewerProcessTests(unittest.TestCase):
    def test_check_config_never_launches_a_process(self):
        with patch.object(sys, "argv", ["reviewer", "--check-config"]), io.StringIO() as output:
            with contextlib.redirect_stdout(output), patch.object(
                    reviewer.subprocess, "Popen", side_effect=AssertionError("Model process forbidden")):
                reviewer.main()
            result = json.loads(output.getvalue())
        self.assertEqual(result["processes_started"], 0)
        self.assertEqual(result["model_invocations"], 0)

    def test_missing_approval_stops_before_launch(self):
        with patch.object(sys, "argv", ["reviewer"]), contextlib.redirect_stderr(io.StringIO()):
            with patch.object(reviewer.subprocess, "Popen", side_effect=AssertionError("Forbidden")):
                with self.assertRaises(SystemExit) as result:
                    reviewer.main()
        self.assertEqual(result.exception.code, 2)

    def test_command_preserves_boundaries_and_exact_instructions(self):
        _, instructions, prompt = reviewer.review_material()
        command = reviewer.reviewer_command("codex", "isolated-fixture", instructions)
        self.assertIn('developer_instructions=' + json.dumps(instructions), command)
        self.assertEqual(command[command.index("--sandbox") + 1], "read-only")
        self.assertEqual(command[command.index("--ask-for-approval") + 1], "never")
        for feature in reviewer.DISABLED:
            self.assertIn(["--disable", feature], [command[i:i+2] for i in range(len(command)-1)])
        self.assertIn("--ignore-user-config", command)
        self.assertNotIn("resume", command)
        self.assertNotIn("fork", command)
        self.assertIn("synthetic_only", prompt)
        self.assertIn("api_reviewer", instructions)

    def test_zero_exit_or_claimed_role_alone_is_not_proof(self):
        for events in ([], [{"type": "turn.completed"}],
                       [{"type": "item.completed", "item": {"type": "agent_message",
                                                               "text": "A reviewer ran"}}]):
            self.assertFalse(reviewer.verify_events(events)[0]["mechanical_checks_passed"])

    def test_tools_or_multiple_sessions_fail_closed(self):
        events = [{"type": "thread.started", "thread_id": "isolated-test-session"},
                  {"type": "item.completed", "item": {"type": "agent_message", "text": "Fixture response"}},
                  {"type": "turn.completed"}]
        self.assertTrue(reviewer.verify_events(events)[0]["mechanical_checks_passed"])
        for extra in ({"type": "item.started", "item": {"type": "collab_tool_call", "tool": "spawn_agent"}},
                      {"type": "thread.started", "thread_id": "second"}, {"type": "turn.failed"}):
            self.assertFalse(reviewer.verify_events(events + [extra])[0]["mechanical_checks_passed"])


if __name__ == "__main__":
    unittest.main()
