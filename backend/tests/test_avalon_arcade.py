import random

import pytest

from backend.app.arcade.rooms import ArcadeRoomError, ArcadeRoomManager
from backend.app.games.base import GameRuleError
from backend.app.games.avalon.arcade import AvalonEngine
from backend.app.games.avalon.engine import GameEngine as AvalonRulesEngine
from backend.app.games.avalon.models import Alignment, Phase

from .test_engine import confirm_all_roles, make_room


def unified_avalon(player_count: int = 5):
    engine = AvalonEngine(AvalonRulesEngine(random.Random(42)))
    manager = ArcadeRoomManager({"avalon": engine}, random.Random(7))
    room, host, _ = manager.create_room(
        "avalon", "玩家0", "account-0"
    )
    for index in range(1, player_count):
        manager.join_room(
            room.code,
            "avalon",
            f"玩家{index}",
            f"account-{index}",
        )
    return manager, engine, room, host


def test_arcade_adapter_preserves_standard_avalon_rule_transitions() -> None:
    direct_room = make_room(5)
    direct_rules = AvalonRulesEngine(random.Random(42))
    manager, adapter, room, host = unified_avalon(5)

    direct_rules.start_game(direct_room, direct_room.host_id)
    manager.start(room, host.id)
    domain = room.state

    assert domain.phase == direct_room.phase == Phase.ROLE_REVEAL
    assert domain.leader_index == direct_room.leader_index
    assert [player.role for player in domain.players] == [
        player.role for player in direct_room.players
    ]
    assert domain.lady_holder_id == domain.players[
        (domain.leader_index - 1) % 5
    ].id

    confirm_all_roles(direct_rules, direct_room)
    for player in room.players:
        manager.act(room, player.id, "confirm_role", {})
    assert domain.phase == direct_room.phase == Phase.TEAM_BUILDING

    direct_team = [player.id for player in direct_room.players[:2]]
    unified_team = [player.id for player in room.players[:2]]
    direct_rules.propose_team(direct_room, direct_room.leader.id, direct_team)
    manager.act(
        room,
        domain.leader.id,
        "propose_team",
        {"team_ids": unified_team},
    )
    for index in range(5):
        approve = index < 3
        direct_rules.vote_team(direct_room, direct_room.players[index].id, approve)
        manager.act(room, room.players[index].id, "vote_team", {"approve": approve})

    assert domain.phase == direct_room.phase == Phase.MISSION_VOTING
    assert domain.proposal_history[-1].accepted is True
    for direct_id, unified_id in zip(direct_team, unified_team, strict=True):
        direct_rules.vote_mission(direct_room, direct_id, True)
        manager.act(room, unified_id, "vote_mission", {"success": True})

    assert domain.phase == direct_room.phase == Phase.ROUND_RESULT
    assert domain.mission_history[-1].success is True
    assert domain.mission_history[-1].fail_count == 0
    assert adapter.view(room, host)["game"]["successCount"] == 1


def test_court_undercurrent_keeps_its_original_fixed_rule_constraints() -> None:
    manager, _, room, host = unified_avalon(5)

    manager.update_options(
        room,
        host.id,
        {
            "mode": "court_undercurrent",
            "ladyEnabled": True,
            "listed": False,
            "earlyAssassinationEnabled": True,
        },
    )

    assert room.options == {
        "allowGuests": True,
        "mode": "court_undercurrent",
        "shadowMerlinEnabled": False,
        "ladyEnabled": False,
        "listed": False,
        "earlyAssassinationEnabled": False,
    }
    assert room.listed is False
    manager.start(room, host.id)
    domain = room.state
    assert domain.settings.lady_enabled is False
    assert domain.settings.early_assassination_enabled is False

    with pytest.raises(ArcadeRoomError, match="等待房间"):
        manager.update_options(room, host.id, {"mode": "standard"})


def test_shadow_merlin_is_a_six_player_court_only_extension() -> None:
    manager, adapter, room, host = unified_avalon(5)
    manager.update_options(
        room,
        host.id,
        {
            "mode": "court_undercurrent",
            "shadowMerlinEnabled": True,
        },
    )

    assert room.options["shadowMerlinEnabled"] is True
    assert adapter.view(room, host)["actions"]["canStart"] is False
    with pytest.raises(GameRuleError, match="至少需要 6"):
        manager.start(room, host.id)

    manager.update_options(
        room,
        host.id,
        {"mode": "standard", "shadowMerlinEnabled": True},
    )
    assert room.options["shadowMerlinEnabled"] is False


def test_avalon_ai_and_finished_room_lifecycle_remain_unchanged() -> None:
    engine = AvalonEngine(AvalonRulesEngine(random.Random(42)))
    manager = ArcadeRoomManager({"avalon": engine})
    room, host, _ = manager.create_room(
        "avalon", "房主", "account-host"
    )
    for _ in range(4):
        manager.act(room, host.id, "add_ai", {})
    assert len(room.players) == 5
    assert sum(player.is_bot for player in room.players) == 4

    manager.start(room, host.id)
    domain = room.state
    assert domain.phase == Phase.ROLE_REVEAL
    assert len(domain.role_confirmed_ids) == 4

    domain.winner = Alignment.GOOD
    domain.win_reason = "测试终局"
    domain.phase = Phase.GAME_OVER
    engine._sync_outer(room, domain)
    manager.leave(room, host.id)
    assert room.code not in manager.rooms
