from __future__ import annotations

from collections.abc import Iterable

import pytest

from backend.app.arcade.models import ArcadePlayer, ArcadeRoom
from backend.app.games.base import GameRuleError
from backend.app.games.monopoly.engine import (
    MonopolyEngine,
    PropertyOwnership,
)
from backend.app.games.registry import build_engine_registry


class FixedRng:
    def __init__(
        self,
        dice: Iterable[int] = (),
        events: Iterable[int] = (),
    ) -> None:
        self.dice = iter(dice)
        self.events = iter(events)

    def randint(self, _minimum: int, _maximum: int) -> int:
        return next(self.dice)

    def randrange(self, _stop: int) -> int:
        return next(self.events)


def make_room(
    engine: MonopolyEngine,
    count: int = 2,
    options: dict | None = None,
) -> ArcadeRoom:
    players = [
        ArcadePlayer(
            id=f"p{seat}",
            account_id=f"a{seat}",
            name=f"玩家{seat + 1}",
            token_hash=f"token-{seat}",
            seat=seat,
        )
        for seat in range(count)
    ]
    room = ArcadeRoom(
        code="RICH",
        game_key="monopoly",
        host_id=players[0].id,
        players=players,
        state=engine.initial_state(),
        options=options or {"startingCash": 8_000, "maxRounds": 20},
    )
    engine.start(room)
    return room


def test_monopoly_is_registered_as_a_two_to_four_player_game() -> None:
    engine = build_engine_registry()["monopoly"]

    assert engine.name == "大富翁"
    assert engine.min_players == 2
    assert engine.max_players == 4


def test_monopoly_validates_room_options() -> None:
    engine = MonopolyEngine()

    assert engine.room_options({}) == {
        "startingCash": 8_000,
        "maxRounds": 20,
    }
    with pytest.raises(GameRuleError, match="起始资金"):
        engine.room_options({"startingCash": 7_000})
    with pytest.raises(GameRuleError, match="回合"):
        engine.room_options({"maxRounds": 99})


def test_player_can_buy_property_and_collect_rent() -> None:
    engine = MonopolyEngine(FixedRng(dice=[1, 1, 1, 1]))
    room = make_room(engine)
    first, second = room.players
    room.state.positions[first.id] = 23

    engine.act(room, first, "roll", {})

    assert room.state.positions[first.id] == 1
    assert room.state.turn_stage == "await_purchase"
    assert room.state.cash[first.id] == 9_200

    engine.act(room, first, "buy_property", {})

    assert room.state.ownership[1].owner_id == first.id
    assert room.state.cash[first.id] == 8_400
    assert room.state.current_player_id == second.id

    room.state.positions[second.id] = 23
    engine.act(room, second, "roll", {})

    assert room.state.cash[second.id] == 9_040
    assert room.state.cash[first.id] == 8_560
    assert room.state.current_player_id == first.id


def test_complete_color_group_doubles_rent_and_allows_upgrades() -> None:
    engine = MonopolyEngine(FixedRng(dice=[1, 1]))
    room = make_room(engine)
    first = room.players[0]
    room.state.ownership[1] = PropertyOwnership(first.id)
    room.state.ownership[3] = PropertyOwnership(first.id)
    room.state.positions[first.id] = 23

    engine.act(room, first, "roll", {})

    assert room.state.turn_stage == "await_upgrade"
    view = engine.view(room, first)
    assert view["currentCell"]["rent"] == 320
    assert view["currentCell"]["groupComplete"] is True

    engine.act(room, first, "upgrade_property", {})

    assert room.state.ownership[1].houses == 1
    assert room.state.cash[first.id] == 8_800
    assert engine.view(room, first)["board"][1]["rent"] == 320


def test_go_to_jail_skips_the_players_next_turn() -> None:
    engine = MonopolyEngine(FixedRng(dice=[1, 1]))
    room = make_room(engine)
    first, second = room.players
    room.state.positions[first.id] = 16

    engine.act(room, first, "roll", {})

    assert room.state.positions[first.id] == 6
    assert room.state.jailed_turns[first.id] == 1
    assert room.state.current_player_id == second.id

    room.state.current_player_id = first.id
    engine.act(room, first, "roll", {})

    assert room.state.jailed_turns[first.id] == 0
    assert room.state.last_roll is None
    assert room.state.current_player_id == second.id


def test_unpaid_rent_causes_bankruptcy_and_transfers_properties() -> None:
    engine = MonopolyEngine(FixedRng(dice=[1, 1]))
    room = make_room(engine, 3)
    debtor, owner, third = room.players
    room.state.positions[debtor.id] = 19
    room.state.cash[debtor.id] = 100
    room.state.ownership[21] = PropertyOwnership(owner.id, houses=3)
    room.state.ownership[1] = PropertyOwnership(debtor.id, houses=1)

    engine.act(room, debtor, "roll", {})

    assert debtor.id in room.state.bankrupt_ids
    assert room.state.ownership[1].owner_id == owner.id
    assert room.state.ownership[1].houses == 0
    assert room.state.cash[owner.id] == 8_100
    assert room.state.current_player_id == owner.id
    assert room.phase == "playing"
    assert third.id not in room.state.bankrupt_ids


def test_round_limit_uses_net_worth_to_finish_the_game() -> None:
    engine = MonopolyEngine(FixedRng(dice=[1, 1]))
    room = make_room(engine, options={"startingCash": 8_000, "maxRounds": 12})
    first, second = room.players
    room.state.current_player_id = second.id
    room.state.current_round = 12
    room.state.positions[second.id] = 10
    room.state.cash[first.id] = 9_000

    engine.act(room, second, "roll", {})

    assert room.phase == "finished"
    assert room.winner == "assets"
    assert room.winner_player_ids == [first.id]
    assert "12 回合结束" in (room.win_reason or "")
