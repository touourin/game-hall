from __future__ import annotations

from typing import Any, TypeVar

from backend.app.arcade.models import ArcadeRoom
from backend.app.games.base import GameRuleError


HANDICAP_GIVERS = frozenset({"host", "opponent"})

SideT = TypeVar("SideT")


def normalize_handicap_giver(value: Any) -> str:
    if not isinstance(value, str) or value not in HANDICAP_GIVERS:
        raise GameRuleError("让子方只能选择房主或对手")
    return value


def handicap_seat_assignment(
    room: ArcadeRoom,
    *,
    giver: SideT,
    receiver: SideT,
) -> list[SideT]:
    if len(room.players) != 2:
        raise GameRuleError("让子规则只适用于双人对局")
    giver_role = normalize_handicap_giver(
        room.options.get("handicapGiver", "host")
    )
    giver_id = (
        room.host_id
        if giver_role == "host"
        else next(
            player.id
            for player in room.players
            if player.id != room.host_id
        )
    )
    giver_seat = room.player(giver_id).seat
    return [
        giver if seat == giver_seat else receiver
        for seat in range(len(room.players))
    ]
