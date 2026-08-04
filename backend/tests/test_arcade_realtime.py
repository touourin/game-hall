import pytest
from pydantic import ValidationError

from backend.app.arcade.realtime import ActionPayload


def test_action_payload_accepts_legacy_council_action_from_open_browser() -> None:
    payload = ActionPayload.model_validate(
        {
            "action": "exile_council_assassination_decision",
            "payload": {"assassinate": False},
        }
    )

    assert payload.action == "exile_council_assassination_decision"


def test_action_payload_still_rejects_unbounded_action_names() -> None:
    with pytest.raises(ValidationError):
        ActionPayload.model_validate({"action": "a" * 65})
