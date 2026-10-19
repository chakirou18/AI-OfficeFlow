import asyncio
import subprocess
import sys
from types import SimpleNamespace

import pytest

from app.model_adapter import OllamaAdapter
import run_tests


@pytest.mark.parametrize("result", [0, 1])
def test_aggregate_runner_forces_simulation_and_preserves_test_exit_status(monkeypatch, result):
    monkeypatch.setenv("MODEL_MODE", "ollama")
    monkeypatch.setattr(run_tests, "database_url", lambda: SimpleNamespace(database="isolated_test"))
    commands = []

    def migrate(command, **kwargs):
        commands.append(command)
        assert kwargs["check"] is True and kwargs["env"]["MODEL_MODE"] == "simulated"

    def test(command, **kwargs):
        commands.append(command)
        assert kwargs["env"]["MODEL_MODE"] == "simulated"
        return result

    monkeypatch.setattr(run_tests.subprocess, "run", migrate)
    monkeypatch.setattr(run_tests.subprocess, "call", test)
    assert run_tests.main() == result
    assert commands == [[sys.executable, "-m", "alembic", "upgrade", "head"],
                        [sys.executable, "-m", "pytest", "-v"]]


def test_runner_refuses_non_test_database_before_starting_any_process(monkeypatch):
    monkeypatch.setattr(run_tests, "database_url", lambda: SimpleNamespace(database="officeflow"))
    monkeypatch.setattr(run_tests.subprocess, "run", lambda *a, **k: pytest.fail("Migration must not run"))
    monkeypatch.setattr(run_tests.subprocess, "call", lambda *a, **k: pytest.fail("Tests must not run"))
    with pytest.raises(SystemExit, match="database name must end in _test"):
        run_tests.main()


def test_failed_migration_prevents_pytest_execution(monkeypatch):
    monkeypatch.setattr(run_tests, "database_url", lambda: SimpleNamespace(database="isolated_test"))

    def fail(command, **kwargs):
        raise subprocess.CalledProcessError(1, command)

    monkeypatch.setattr(run_tests.subprocess, "run", fail)
    monkeypatch.setattr(run_tests.subprocess, "call", lambda *a, **k: pytest.fail("Tests must not run"))
    with pytest.raises(subprocess.CalledProcessError):
        run_tests.main()


def test_automatic_tests_deny_real_model_transport_before_network_access():
    adapter = OllamaAdapter("http://localhost:11434")
    with pytest.raises(pytest.fail.Exception, match="Live async HTTP is disabled"):
        asyncio.run(adapter.analyze("Synthetic guard", "Synthetic only; no network call is authorized."))
