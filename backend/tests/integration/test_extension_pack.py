"""T17 real protocol demo, confined to the existing isolated test PostgreSQL."""
import asyncio
from importlib.metadata import version
import json
import os
import sys

from mcp import Client, StdioServerParameters
import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Task

pytestmark = pytest.mark.integration


def test_module5_existing_mcp_real_protocol_and_denied_capabilities(auth_context):
    client, engine, _, _, _ = auth_context
    record = client.post("/api/v1/requests", json={"title": "Synthetic Module 5 review",
                         "description": "Synthetic read-only protocol fixture."}).json()
    evidence = {"server": "app.mcp_server", "mcp_version": version("mcp"),
                "synthetic_only": True, "transport": "real subprocess stdio"}

    async def verify():
        params = StdioServerParameters(command=sys.executable, args=["-m", "app.mcp_server"],
                                       env=dict(os.environ, MODEL_MODE="simulated", TELEMETRY_ENABLED="false"))
        async with Client(params, read_timeout_seconds=10) as mcp:
            tools = (await mcp.list_tools()).tools
            assert [tool.name for tool in tools] == ["get_request_summary"]
            assert tools[0].annotations.model_dump(by_alias=True)["readOnlyHint"]
            result = await mcp.call_tool("get_request_summary", {"params": {"request_id": record["id"]}})
            assert not result.is_error
            summary = result.structured_content
            assert summary["title"] == record["title"] and summary["untrusted_content"]
            assert summary["classification"] == "synthetic_only"
            assert len(summary["description_excerpt"]) <= 600 and len(json.dumps(summary)) < 1500
            evidence["bounded_summary_read"] = True
            for label, arguments in (
                    ("invalid_uuid_denied", {"params": {"request_id": "invalid"}}),
                    ("write_input_denied", {"params": {"request_id": record["id"], "decision": "approve"}})):
                assert (await mcp.call_tool("get_request_summary", arguments)).is_error
                evidence[label] = True
            for label, name in (("write_tool_denied", "create_task"), ("approval_tool_denied", "approve_analysis"),
                                ("unknown_tool_denied", "unknown_tool")):
                assert (await mcp.call_tool(name, {"request_id": record["id"]})).is_error
                evidence[label] = True

    asyncio.run(verify())
    with Session(engine) as db:
        assert db.scalar(select(func.count()).select_from(Task)) == 0
    evidence["active_tasks_created"] = 0
    print("T17_MCP_EVIDENCE=" + json.dumps(evidence, sort_keys=True))
