import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("review_guard", ROOT / "agent-hooks/review_guard.py")
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


class ReviewGuard(unittest.TestCase):
    def test_allowed_read_returns_only_pinned_synthetic_fixture(self):
        result = guard.read_fixture()
        self.assertTrue(result["untrusted_content"])
        self.assertEqual(result["classification"], "synthetic_only")
        self.assertEqual(result["content"], guard.FIXTURE.read_text(encoding="utf-8"))

    def test_forbidden_actions_are_intercepted_before_handler(self):
        for action in ("write_fixture", "approve_request", "shell", "unknown_tool", "../read_fixture"):
            operation = Mock()
            with self.subTest(action=action), self.assertRaises(guard.Denied):
                guard.guarded(action, operation)
            operation.assert_not_called()

    def test_policy_read_failure_corruption_expansion_and_changed_fixture_deny_before_handler(self):
        original = guard.load_policy()
        policies = [None, {}, original | {"role": "writer"}, original | {"actions": ["read_fixture", "write_fixture"]},
                    original | {"fixture_sha256": "0" * 64}, original | {"extra": True}]
        for policy in policies:
            operation = Mock()
            with self.subTest(policy=policy), self.assertRaises(guard.Denied):
                guard.guarded("read_fixture", operation, policy_loader=lambda: policy)
            operation.assert_not_called()
        operation = Mock()
        with self.assertRaises(guard.Denied):
            guard.guarded("read_fixture", operation, policy_loader=Mock(side_effect=OSError("unavailable")))
        operation.assert_not_called()
        with tempfile.TemporaryDirectory() as directory:
            fixture = Path(directory) / "changed.diff"
            fixture.write_text("untrusted changed input", encoding="utf-8")
            with patch.object(guard, "FIXTURE", fixture), self.assertRaises(guard.Denied):
                guard.read_fixture()

    def test_guardrail_demo_preserves_sentinel_and_line_endings_do_not_change_policy(self):
        result = guard.demonstrate()
        self.assertTrue(result["allowed_read"])
        self.assertTrue(result["unauthorized_write"]["sentinel_unchanged"])
        self.assertTrue(result["failed_policy"]["sentinel_unchanged"])
        with tempfile.TemporaryDirectory() as directory:
            fixture = Path(directory) / "crlf.diff"
            fixture.write_bytes(guard.FIXTURE.read_text(encoding="utf-8").replace("\n", "\r\n").encode())
            with patch.object(guard, "FIXTURE", fixture):
                self.assertTrue(guard.read_fixture()["untrusted_content"])
