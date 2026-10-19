"""Offline-only adapter contract. No providers, API keys, tools or live calls."""
from typing import Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field


class Suggestion(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    title: str = Field(min_length=1, max_length=200)
    priority: Literal["low", "medium", "high"]
    rationale: str = Field(min_length=1, max_length=1000)


class Proposal(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    summary: str = Field(min_length=1, max_length=1000)
    tasks: list[Suggestion] = Field(min_length=1, max_length=5)


class ModelAdapter(Protocol):
    async def analyze(self, title: str, description: str) -> dict: ...


class OfflineAdapter:
    async def analyze(self, title: str, description: str) -> dict:
        # Request content is untrusted data, never commands. No keyword-triggered faults.
        return {
            "summary": "Simulated review of this synthetic request. Confirm scope and any missing timing or resources with a human.",
            "tasks": [{"title": f"Review request: {title}"[:200], "priority": "medium",
                       "rationale": "Simulated suggestion based on the request title. Timing and available resources are unverified."}],
        }
