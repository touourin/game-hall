from backend.app.games.avalon.engine import GameEngine
from backend.app.games.avalon.models import Alignment, MissionRecord, Phase, Role
from backend.app.games.avalon.rooms import RoomManager
from backend.app.games.avalon.views import build_lobby_view, build_player_view

from .test_engine import start_room


def test_player_view_never_exposes_other_roles_during_game():
    engine, room = start_room(7)
    viewer = room.players[0]

    view = build_player_view(room, viewer, engine)

    assert view["self"]["role"]["code"] == viewer.role.value
    assert all("role" not in player for player in view["players"])


def test_final_assassination_reveals_alignments_but_not_roles():
    engine, room = start_room(7)
    room.phase = Phase.ASSASSINATION

    view = build_player_view(room, room.players[0], engine)

    assert all(player["alignment"] in ("good", "evil") for player in view["players"])
    assert all("role" not in player for player in view["players"])
    oberon = next(player for player in room.players if player.role == Role.OBERON)
    oberon_view = next(player for player in view["players"] if player["id"] == oberon.id)
    assert oberon_view["alignment"] == "evil"


def test_merlin_sees_evil_except_mordred():
    engine, room = start_room(8)
    merlin = next(player for player in room.players if player.role == Role.MERLIN)
    mordred = next(player for player in room.players if player.role == Role.MORDRED)
    visible_evil_ids = {
        item["playerId"]
        for item in build_player_view(room, merlin, engine)["self"]["role"][
            "knowledge"
        ]
    }

    assert mordred.id not in visible_evil_ids
    assert visible_evil_ids
    assert all(
        room.player(player_id).alignment == Alignment.EVIL
        for player_id in visible_evil_ids
    )


def test_lady_result_is_only_visible_to_inspector():
    engine, room = start_room(7)
    room.mission_history = [
        MissionRecord(1, ["p0", "p1"], True, 0),
        MissionRecord(2, ["p0", "p1", "p2"], False, 1),
    ]
    room.phase = Phase.LADY_SELECT
    inspector = room.player(room.lady_holder_id)
    target_id = engine.eligible_lady_targets(room)[0]
    engine.inspect_with_lady(room, inspector.id, target_id)

    inspector_view = build_player_view(room, inspector, engine)
    other = next(player for player in room.players if player.id != inspector.id)
    other_view = build_player_view(room, other, engine)

    assert inspector_view["lady"]["currentResult"] is not None
    assert other_view["lady"]["currentResult"] is None
    assert "alignment" not in other_view["lady"]["history"][-1]


def test_chat_history_is_visible_to_every_room_member():
    engine, room = start_room(5)
    sender = room.players[0]
    viewer = room.players[1]

    RoomManager().send_chat(room, sender.id, "这支队伍我赞成")
    view = build_player_view(room, viewer, engine)

    assert view["chat"]["maxLength"] == 300
    assert view["chat"]["messages"][-1]["senderName"] == sender.name
    assert view["chat"]["messages"][-1]["content"] == "这支队伍我赞成"


def test_ai_player_marker_and_add_action_are_in_player_view():
    manager = RoomManager()
    room, host, _ = manager.create_room("亚瑟")
    ai_player = manager.add_ai_player(room, host.id)

    view = build_player_view(room, host, GameEngine())
    ai_view = next(
        player for player in view["players"] if player["id"] == ai_player.id
    )

    assert ai_view["isBot"] is True
    assert ai_view["seat"] == 1
    assert view["actions"]["canAddAiPlayer"] is True


def test_lobby_view_only_lists_public_joinable_rooms():
    manager = RoomManager()
    visible, _, _ = manager.create_room("亚瑟")
    hidden, hidden_host, _ = manager.create_room("梅林")
    started, _, _ = manager.create_room("桂妮维亚")
    manager.set_listed(hidden, hidden_host.id, False)
    started.phase = Phase.ROLE_REVEAL

    lobby_view = build_lobby_view(manager.rooms.values())

    assert lobby_view == [
        {
            "roomCode": visible.code,
            "hostName": "亚瑟",
            "playerCount": 1,
            "maxPlayers": 10,
            "ladyEnabled": True,
        }
    ]


def test_lobby_view_hides_room_when_every_human_is_offline():
    manager = RoomManager()
    room, host, _ = manager.create_room("亚瑟")
    manager.add_ai_player(room, host.id)
    host.connected = False

    assert build_lobby_view(manager.rooms.values()) == []


def test_player_view_contains_public_team_vote_replay():
    engine, room = start_room(5)
    for player in room.players:
        engine.confirm_role(room, player.id)
    leader_id = room.leader.id
    team_ids = [player.id for player in room.players[:2]]
    engine.propose_team(room, leader_id, team_ids)
    for index, player in enumerate(room.players):
        engine.vote_team(room, player.id, approve=index < 3)

    view = build_player_view(room, room.players[0], engine)
    replay = view["game"]["proposalHistory"][-1]

    assert replay["leaderId"] == leader_id
    assert replay["teamIds"] == team_ids
    assert replay["accepted"] is True
    assert replay["votes"] == [
        {"playerId": player.id, "approve": index < 3}
        for index, player in enumerate(room.players)
    ]


def test_only_assassin_can_see_early_assassination_action():
    engine, room = start_room(5)
    room.settings.early_assassination_enabled = True
    for player in room.players:
        engine.confirm_role(room, player.id)
    assassin = next(
        player for player in room.players if player.role == Role.ASSASSIN
    )
    other = next(player for player in room.players if player.id != assassin.id)

    assassin_view = build_player_view(room, assassin, engine)
    other_view = build_player_view(room, other, engine)

    assert assassin_view["actions"]["canEarlyAssassinate"] is True
    assert other_view["actions"]["canEarlyAssassinate"] is False
    assert assassin_view["settings"]["earlyAssassinationEnabled"] is True
