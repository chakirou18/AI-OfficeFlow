import pytest
from pydantic import ValidationError

from app.requests import RequestInput, TaskUpdate


def test_request_trims_text_and_accepts_exact_limits():
    value = RequestInput(title="  Synthetic request  ", description="\n Review demo stock \t")
    assert value.title == "Synthetic request"
    assert value.description == "Review demo stock"
    assert len(RequestInput(title="x" * 200, description="x" * 5000).description) == 5000


@pytest.mark.parametrize("title,description", [(" ", "valid"), ("valid", "\t"),
                                                ("x" * 201, "valid"), ("valid", "x" * 5001)])
def test_request_rejects_blank_or_oversized_text(title, description):
    with pytest.raises(ValidationError):
        RequestInput(title=title, description=description)


def test_task_update_has_no_creation_or_priority_override():
    with pytest.raises(ValidationError):
        TaskUpdate(state="done", priority="high")
    with pytest.raises(ValidationError):
        TaskUpdate(state="approved")
