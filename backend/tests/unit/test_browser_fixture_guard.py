from types import SimpleNamespace

import pytest

from app import browser_fixture


@pytest.mark.parametrize("enabled,database", [("", "officeflow_browser_test"), ("enabled", "officeflow")])
def test_browser_seed_refuses_missing_permission_or_non_test_database(monkeypatch, enabled, database):
    monkeypatch.setenv("BROWSER_FIXTURES", enabled)
    monkeypatch.setattr(browser_fixture, "database_url", lambda: SimpleNamespace(database=database))
    with pytest.raises(SystemExit, match="isolated _test database"):
        browser_fixture.main()
