import copy
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import deployment
from deployment_controller import verify_request


def release():
    return {"commit": "a" * 40, "api": "ghcr.io/chakirou18/ai-officeflow-private-api@sha256:" + "b" * 64,
            "frontend": "ghcr.io/chakirou18/ai-officeflow-private-frontend@sha256:" + "c" * 64,
            "compatible_revisions": [deployment.SCHEMA], "ci_run": 10, "release_run": 20}


class ReleaseSafety(unittest.TestCase):
    def test_immutable_owner_images_and_exact_schema_required(self):
        deployment.validate_release(release())
        for key, value in [("api", "ghcr.io/chakirou18/ai-officeflow-api:latest"),
                           ("frontend", "ghcr.io/other/frontend@sha256:" + "b" * 64),
                           ("api", "ghcr.io/chakirou18/ai-officeflow-api@sha256:" + "b" * 64),
                           ("commit", "main"), ("ci_run", True), ("compatible_revisions", ["unverified"])]:
            with self.subTest(key=key):
                with self.assertRaises(ValueError):
                    deployment.validate_release(release() | {key: value})

    def test_local_ids_are_only_for_explicit_rehearsal(self):
        candidate = release() | {"api": "sha256:" + "a" * 64, "ci_run": None, "release_run": None}
        with self.assertRaises(ValueError):
            deployment.validate_release(candidate)
        deployment.validate_release(candidate, local=True)

    def test_environment_credentials_and_state_are_isolated_and_preserved(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(deployment, "STATE", Path(directory)):
            dev, prod = deployment.Deployment("development"), deployment.Deployment("production")
            self.assertNotEqual(dev.password, prod.password)
            self.assertNotEqual(dev.project, prod.project)
            self.assertNotEqual(dev.port, prod.port)
            self.assertEqual(dev.password, deployment.Deployment("development").password)
            dev.write_state("current", release())
            self.assertIsNone(prod.read_state())
            self.assertEqual(dev.read_state(), release())

    def test_unknown_environment_and_ci_bypass_denied(self):
        with self.assertRaises(ValueError):
            deployment.Deployment("arbitrary")
        with patch.dict(os.environ, {"CI": "false"}):
            with self.assertRaises(ValueError):
                deployment.Deployment("development", isolated_ci=True)

    def test_no_compatible_previous_image_means_no_rollback(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(deployment, "STATE", Path(directory)):
            dev = deployment.Deployment("development")
            with patch.object(dev, "compose") as compose:
                with self.assertRaises(RuntimeError):
                    dev.rollback()
                compose.assert_not_called()

    def test_compose_uses_fixed_files_projects_no_shell_or_secret_arguments(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(deployment, "STATE", Path(directory)):
            dev = deployment.Deployment("development")
            with patch.object(deployment, "run", return_value=b"") as command:
                dev.compose(release(), "up", "-d", "db")
            arguments, options = command.call_args
            self.assertNotIn(dev.password, json.dumps(arguments))
            self.assertEqual(options["env"]["DEPLOY_PASSWORD"], dev.password)
            self.assertEqual(options["env"]["DEPLOY_ENVIRONMENT"], "development")
            self.assertNotIn("--volumes", arguments[0])


class RequestProvenance(unittest.TestCase):
    def setUp(self):
        self.request = {"environment": "development", "creator": {"login": "github-actions[bot]"},
                        "ref": "a" * 40, "sha": "a" * 40, "payload": {"release": release(), "request_run": 20}}
        common = {"head_branch": "main", "head_sha": "a" * 40, "conclusion": "success", "head_repository": {"full_name": deployment.REPOSITORY}}
        self.responses = {"actions/runs/10": common | {"event": "push", "path": ".github/workflows/ci.yml"},
                          "actions/runs/20": common | {"event": "workflow_run", "path": ".github/workflows/release.yml"},
                          "actions/runs/30": common | {"event": "workflow_dispatch", "path": ".github/workflows/promote.yml"},
                          "git/ref/heads/main": {"object": {"sha": "a" * 40}}}

    def fetch(self, path):
        return copy.deepcopy(self.responses[path])

    def test_verified_main_development_request(self):
        self.assertEqual(verify_request(self.request, self.fetch), release())

    def test_pr_fork_failure_wrong_workflow_and_stale_commit_are_denied(self):
        cases = [("actions/runs/10", "event", "pull_request"), ("actions/runs/10", "conclusion", "failure"),
                 ("actions/runs/20", "path", ".github/workflows/untrusted.yml"),
                 ("actions/runs/20", "head_repository", {"full_name": "untrusted/fork"}),
                 ("git/ref/heads/main", "object", {"sha": "f" * 40})]
        for path, key, value in cases:
            with self.subTest(key=key):
                original = copy.deepcopy(self.responses)
                self.responses[path][key] = value
                with self.assertRaises(ValueError):
                    verify_request(self.request, self.fetch)
                self.responses = original

    def test_manual_production_must_match_verified_development(self):
        request = self.request | {"environment": "production", "payload": {"release": release(), "request_run": 30}}
        with patch("deployment_controller.Deployment") as deploy:
            deploy.return_value.read_state.return_value = release()
            self.assertEqual(verify_request(request, self.fetch), release())
            deploy.return_value.read_state.return_value = release() | {"commit": "f" * 40}
            with self.assertRaises(ValueError):
                verify_request(request, self.fetch)
        self.responses["actions/runs/30"]["event"] = "push"
        with self.assertRaises(ValueError):
            verify_request(request, self.fetch)

    def test_wrong_creator_ref_or_payload_cannot_request_deployment(self):
        for change in ({"creator": {"login": "ordinary-demo-user"}}, {"ref": "main"},
                       {"payload": {"release": release(), "request_run": 20, "shell": "untrusted"}}):
            with self.assertRaises(ValueError):
                verify_request(self.request | change, self.fetch)


if __name__ == "__main__":
    unittest.main()
