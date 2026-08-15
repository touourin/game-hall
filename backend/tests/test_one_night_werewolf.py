from __future__ import annotations

import random

import pytest

from backend.app.arcade.models import ArcadePlayer, ArcadeRoom
from backend.app.games.base import GameRuleError
from backend.app.games.one_night_werewolf.engine import (
    OneNightWerewolfEngine,
    OneNightWerewolfState,
)


def make_room(
    player_count: int = 3,
    *,
    preset: str = "standard",
) -> tuple[OneNightWerewolfEngine, ArcadeRoom]:
    players = [
        ArcadePlayer(
            id=f"p{seat + 1}",
            account_id=f"a{seat + 1}",
            name=f"玩家{seat + 1}",
            token_hash=f"t{seat + 1}",
            seat=seat,
        )
        for seat in range(player_count)
    ]
    engine = OneNightWerewolfEngine(random.Random(7))
    room = ArcadeRoom(
        code="MOON",
        game_key=engine.key,
        host_id=players[0].id,
        players=players,
        state=engine.initial_state(),
        options=engine.room_options({
            "rolePreset": preset,
            "listed": True,
        }),
    )
    engine.start(room)
    return engine, room


def force_roles(
    room: ArcadeRoom,
    roles: list[str],
    *,
    phase: str = "role_reveal",
) -> OneNightWerewolfState:
    state = room.state
    assert isinstance(state, OneNightWerewolfState)
    assert len(roles) == len(room.players) + 3
    state.initial_roles = list(roles)
    state.current_roles = list(roles)
    state.role_deck = list(roles)
    state.confirmed_player_ids.clear()
    state.wake_index = 0
    state.current_actor_ids.clear()
    state.completed_actor_ids.clear()
    state.night_results = {player.id: [] for player in room.players}
    state.votes.clear()
    state.vote_counts.clear()
    state.eliminated_player_ids.clear()
    room.phase = phase
    room.winner = None
    room.winner_player_ids = []
    room.win_reason = None
    return state


def confirm_everyone(engine: OneNightWerewolfEngine, room: ArcadeRoom) -> None:
    for player in room.players:
        engine.act(room, player, "confirm_role", {})


def finish_simple_night(engine: OneNightWerewolfEngine, room: ArcadeRoom) -> None:
    state = room.state
    assert isinstance(state, OneNightWerewolfState)
    guard = 0
    while room.phase == "night":
        guard += 1
        assert guard < 20
        for player_id in list(state.current_actor_ids - state.completed_actor_ids):
            player = room.player(player_id)
            role = state.initial_roles[player.seat]
            payload: dict[str, object] = {}
            if role == "werewolf" and sum(
                state.initial_roles[item.seat] == "werewolf"
                for item in room.players
            ) == 1:
                payload = {"centerIndex": 0}
            elif role == "seer":
                payload = {"centerIndices": [0, 1]}
            elif role == "robber":
                payload = {"skip": True}
            elif role == "troublemaker":
                payload = {"skip": True}
            elif role == "drunk":
                payload = {"centerIndex": 0}
            engine.act(room, player, "night_action", payload)


def test_room_options_leave_spectating_to_the_shared_room_platform() -> None:
    engine = OneNightWerewolfEngine()
    options = engine.room_options({
        "rolePreset": "chaos",
        "discussionSeconds": 480,
        "listed": False,
        "allowSpectators": True,
    })
    assert options == {
        "rolePreset": "chaos",
        "listed": False,
    }


def test_player_view_keeps_other_roles_private_until_resolution() -> None:
    engine, room = make_room()
    state = force_roles(
        room,
        ["seer", "werewolf", "villager", "robber", "minion", "tanner"],
    )
    view = engine.view(room, room.players[0])
    assert view["self"]["initialRole"]["code"] == "seer"
    assert "players" not in view
    assert view["resolution"] is None

    state.current_roles[0], state.current_roles[3] = (
        state.current_roles[3],
        state.current_roles[0],
    )
    room.finish("village", [room.players[0].id], "测试结算")
    finished = engine.view(room, room.players[0])
    assert finished["self"]["finalRole"]["code"] == "robber"
    assert finished["resolution"]["centerRoles"][0]["code"] == "seer"


def test_night_actions_follow_wake_order_and_apply_swaps() -> None:
    engine, room = make_room(5)
    state = force_roles(
        room,
        [
            "werewolf", "seer", "robber", "troublemaker", "insomniac",
            "villager", "minion", "tanner",
        ],
    )
    confirm_everyone(engine, room)
    assert state.current_actor_ids == {"p1"}

    engine.act(room, room.players[0], "night_action", {"centerIndex": 0})
    assert state.current_actor_ids == {"p2"}
    engine.act(room, room.players[1], "night_action", {"targetPlayerId": "p1"})
    assert "狼人" in state.night_results["p2"][0].text

    engine.act(room, room.players[2], "night_action", {"targetPlayerId": "p1"})
    assert state.current_roles[:2] == ["robber", "seer"]
    engine.act(
        room,
        room.players[3],
        "night_action",
        {"targetPlayerIds": ["p1", "p2"]},
    )
    assert state.current_roles[:2] == ["seer", "robber"]
    engine.act(room, room.players[4], "night_action", {})
    assert room.phase == "discussion"
    assert "失眠者" in state.night_results["p5"][0].text


def test_seer_can_view_two_center_cards_without_changing_them() -> None:
    engine, room = make_room()
    state = force_roles(
        room,
        ["seer", "villager", "hunter", "werewolf", "minion", "tanner"],
    )
    confirm_everyone(engine, room)
    assert state.current_actor_ids == {"p1"}
    engine.act(room, room.players[0], "night_action", {"centerIndices": [0, 2]})
    assert state.current_roles == state.initial_roles
    assert "狼人" in state.night_results["p1"][0].text
    assert "皮匠" in state.night_results["p1"][0].text


def test_discussion_is_untimed_and_host_starts_secret_voting() -> None:
    engine, room = make_room()
    force_roles(
        room,
        ["villager", "villager", "hunter", "werewolf", "minion", "tanner"],
    )
    confirm_everyone(engine, room)
    assert room.phase == "discussion"
    with pytest.raises(GameRuleError, match="只有房主"):
        engine.act(room, room.players[1], "start_vote", {})
    assert room.phase == "discussion"
    engine.act(room, room.players[0], "start_vote", {})
    assert room.phase == "voting"


def test_vote_kills_tied_leaders_and_hunter_target_then_village_wins() -> None:
    engine, room = make_room(5)
    state = force_roles(
        room,
        [
            "hunter", "werewolf", "villager", "villager", "villager",
            "seer", "robber", "minion",
        ],
        phase="voting",
    )
    votes = {"p1": "p2", "p2": "p1", "p3": "p1", "p4": "p2", "p5": "p3"}
    for player in room.players:
        engine.act(room, player, "vote", {"targetPlayerId": votes[player.id]})
    assert room.phase == "finished"
    assert set(state.eliminated_player_ids) == {"p1", "p2"}
    assert room.winner == "village"
    assert set(room.winner_player_ids) == {"p1", "p3", "p4", "p5"}


def test_tanner_loses_when_executed_without_a_wolf_death() -> None:
    engine, room = make_room()
    force_roles(
        room,
        ["tanner", "werewolf", "villager", "seer", "robber", "minion"],
        phase="voting",
    )
    engine.act(room, room.players[0], "vote", {"targetPlayerId": "p2"})
    engine.act(room, room.players[1], "vote", {"targetPlayerId": "p1"})
    engine.act(room, room.players[2], "vote", {"targetPlayerId": "p1"})
    assert room.winner == "werewolf"
    assert set(room.winner_player_ids) == {"p2"}


def test_lone_minion_wins_but_tanner_does_not_when_tanner_dies() -> None:
    engine, room = make_room()
    force_roles(
        room,
        ["tanner", "minion", "villager", "werewolf", "seer", "robber"],
        phase="voting",
    )
    engine.act(room, room.players[0], "vote", {"targetPlayerId": "p2"})
    engine.act(room, room.players[1], "vote", {"targetPlayerId": "p1"})
    engine.act(room, room.players[2], "vote", {"targetPlayerId": "p1"})
    assert room.winner == "werewolf"
    assert set(room.winner_player_ids) == {"p2"}


def test_tanner_and_village_win_together_when_tanner_and_wolf_die() -> None:
    engine, room = make_room(4)
    force_roles(
        room,
        [
            "tanner", "werewolf", "villager", "villager",
            "seer", "robber", "minion",
        ],
        phase="voting",
    )
    votes = {"p1": "p2", "p2": "p1", "p3": "p1", "p4": "p2"}
    for player in room.players:
        engine.act(room, player, "vote", {"targetPlayerId": votes[player.id]})
    assert room.winner == "village"
    assert set(room.winner_player_ids) == {"p1", "p3", "p4"}


def test_only_killing_the_minion_in_a_no_wolf_game_has_no_winner() -> None:
    engine, room = make_room()
    force_roles(
        room,
        ["minion", "villager", "hunter", "werewolf", "seer", "robber"],
        phase="voting",
    )
    engine.act(room, room.players[0], "vote", {"targetPlayerId": "p2"})
    engine.act(room, room.players[1], "vote", {"targetPlayerId": "p1"})
    engine.act(room, room.players[2], "vote", {"targetPlayerId": "p1"})
    assert room.winner == "none"
    assert room.winner_player_ids == []


def test_no_wolf_village_wins_only_when_nobody_is_executed() -> None:
    engine, room = make_room()
    force_roles(
        room,
        ["villager", "seer", "hunter", "werewolf", "minion", "tanner"],
        phase="voting",
    )
    # All three players receive one vote, so nobody is eliminated.
    engine.act(room, room.players[0], "vote", {"targetPlayerId": "p2"})
    engine.act(room, room.players[1], "vote", {"targetPlayerId": "p3"})
    engine.act(room, room.players[2], "vote", {"targetPlayerId": "p1"})
    assert room.winner == "village"
    assert set(room.winner_player_ids) == {"p1", "p2", "p3"}


def test_players_cannot_vote_for_themselves_or_submit_twice() -> None:
    engine, room = make_room()
    force_roles(
        room,
        ["villager", "seer", "hunter", "werewolf", "minion", "tanner"],
        phase="voting",
    )
    with pytest.raises(GameRuleError, match="不能选择自己"):
        engine.act(room, room.players[0], "vote", {"targetPlayerId": "p1"})
    engine.act(room, room.players[0], "vote", {"targetPlayerId": "p2"})
    with pytest.raises(GameRuleError, match="已经投过票"):
        engine.act(room, room.players[0], "vote", {"targetPlayerId": "p3"})
