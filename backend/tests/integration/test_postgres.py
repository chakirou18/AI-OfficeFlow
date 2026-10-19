from uuid import UUID, uuid4

import pytest
from sqlalchemy import delete, select, text
from sqlalchemy.orm import Session

from app.database import build_engine, database_url
from app.models import FoundationCheck

pytestmark = pytest.mark.integration


@pytest.fixture
def engine():
    if not (database_url().database or "").endswith("_test"):
        pytest.fail("Integration tests require an isolated database ending in _test")
    engine = build_engine()
    with engine.begin() as connection:
        connection.execute(delete(FoundationCheck))
    yield engine
    with engine.begin() as connection:
        connection.execute(delete(FoundationCheck))
    engine.dispose()


def test_readiness_checks_real_postgres_and_migrated_table(engine, auth_context):
    client = auth_context[0]
    response = client.get("/api/v1/health/ready")
    assert response.status_code == 200
    assert response.json()["migration"] == "0003_requests"
    with engine.connect() as connection:
        assert connection.execute(text("SELECT current_database()")).scalar_one().endswith("_test")


def test_api_write_is_committed_and_readable_in_independent_session(engine, auth_context):
    client = auth_context[0]
    created = client.post("/api/v1/foundation/checks")
    assert created.status_code == 201
    payload = created.json()
    with Session(engine) as independent_session:
        record = independent_session.scalars(
            select(FoundationCheck).where(FoundationCheck.id == UUID(payload["id"]))
        ).one()
        assert record.marker == "synthetic-foundation-check"
    fetched = client.get(f"/api/v1/foundation/checks/{payload['id']}")
    assert fetched.status_code == 200
    assert fetched.json() == payload


def test_unknown_record_and_invalid_uuid_have_distinct_errors(engine, auth_context):
    client = auth_context[0]
    assert client.get(f"/api/v1/foundation/checks/{uuid4()}").status_code == 404
    assert client.get("/api/v1/foundation/checks/not-a-uuid").status_code == 422
