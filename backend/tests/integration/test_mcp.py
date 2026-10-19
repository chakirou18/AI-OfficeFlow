import asyncio
import json
import os
import sys
from uuid import uuid4

from mcp import Client, StdioServerParameters
import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from app.mcp_server import readonly_session
from app.models import FoundationCheck, Task

pytestmark = pytest.mark.integration


def test_real_mcp_stdio_initialization_list_read_input_validation_and_write_denial(auth_context):
    client, engine, _, _, _ = auth_context
    request_id = client.post("/api/v1/requests", json={"title": "Synthetic MCP input; DROP TABLE tasks;",
        "description": "Synthetic untrusted text only. " * 100}).json()["id"]

    async def verify():
        # A real subprocess/stdio handshake, not an in-memory server shortcut.
        params = StdioServerParameters(command=sys.executable, args=["-m", "app.mcp_server"], env=dict(os.environ))
        async with Client(params, read_timeout_seconds=10) as mcp:
            tools = (await mcp.list_tools()).tools
            assert [tool.name for tool in tools] == ["get_request_summary"]
            assert tools[0].annotations.model_dump(by_alias=True)["readOnlyHint"] is True
            result = await mcp.call_tool("get_request_summary", {"params": {"request_id": request_id}})
            assert not result.is_error
            data = result.structured_content
            assert data["request_id"] == request_id
            assert len(data["title"]) <= 200 and len(data["description_excerpt"]) <= 600
            assert data["classification"] == "synthetic_only" and data["untrusted_content"]
            assert len(json.dumps(data)) < 1500
            assert "creator_handle" not in data and "password" not in data
            for arguments in ({"params": {"request_id": "not-a-uuid"}},
                              {"params": {"request_id": request_id, "sql": "DELETE FROM tasks"}},
                              {"params": {"request_id": str(uuid4())}}):
                denied = await mcp.call_tool("get_request_summary", arguments)
                assert denied.is_error
            denied = await mcp.call_tool("create_task", {"request_id": request_id, "title": "unapproved"})
            assert denied.is_error
    asyncio.run(verify())
    with Session(engine) as db:
        assert db.scalar(select(func.count()).select_from(Task)) == 0


def test_mcp_database_transaction_rejects_writes(auth_context):
    engine = auth_context[1]
    with pytest.raises(DBAPIError):
        with readonly_session(engine) as db:
            db.add(FoundationCheck(marker="synthetic-read-only-denial"))
            db.flush()
