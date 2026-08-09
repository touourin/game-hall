import pytest

from backend.app.games.avalon.engine import GameEngine
from backend.app.games.avalon.models import (
    Alignment,
    AvalonMode,
    ChatMessage,
    MissionRecord,
    Phase,
    Role,
)
from backend.app.games.avalon.views import build_player_view

from .test_engine import make_room, start_room


def test_player_view_never_exposes_other_roles_during_game():
    engine, room = start_room(7)
    viewer = room.players[0]

    view = build_player_view(room, viewer, engine)

    assert view["self"]["role"]["code"] == viewer.role.value
    assert all("role" not in player for player in view["players"])


def test_final_assassination_keeps_oberon_alignment_and_all_roles_private():
    engine, room = start_room(7)
    room.phase = Phase.ASSASSINATION

    view = build_player_view(room, room.players[0], engine)
    assassin = next(
        player for player in room.players if player.role == Role.ASSASSIN
    )

    oberon = next(
        player for player in room.players if player.role == Role.OBERON
    )
    public_alignment_ids = {
        player["id"]
        for player in view["players"]
        if "alignment" in player
    }
    expected_public_ids = {
        player.id
        for player in room.players
        if player.alignment == Alignment.EVIL
        and player.role != Role.OBERON
    }
    assert public_alignment_ids == expected_public_ids
    assert all(
        player["alignment"] == "evil"
        for player in view["players"]
        if "alignment" in player
    )
    assert all("role" not in player for player in view["players"])
    oberon_view = next(
        player for player in view["players"] if player["id"] == oberon.id
    )
    assert "alignment" not in oberon_view
    assassin_view = build_player_view(room, assassin, engine)
    assert set(assassin_view["result"]["eligibleTargetIds"]) == {
        player.id
        for player in room.players
        if player.alignment == Alignment.GOOD or player.role == Role.OBERON
    }
    non_assassin = next(
        player for player in room.players if player.id != assassin.id
    )
    assert build_player_view(room, non_assassin, engine)["result"][
        "eligibleTargetIds"
    ] == []


def test_game_over_reveals_oberon_alignment_and_role():
    engine, room = start_room(7)
    room.phase = Phase.GAME_OVER
    oberon = next(
        player for player in room.players if player.role == Role.OBERON
    )

    view = build_player_view(room, room.players[0], engine)
    oberon_view = next(
        player for player in view["players"] if player["id"] == oberon.id
    )

    assert oberon_view["alignment"] == "evil"
    assert oberon_view["role"] == "oberon"
    assert oberon_view["roleLabel"] == "奥伯伦"


def test_merlin_sees_evil_except_mordred():
    engine, room = start_room(9)
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


def test_mission_view_marks_failure_caused_by_five_rejections():
    engine, room = start_room(5)
    room.mission_history = [
        MissionRecord(
            1,
            [],
            False,
            0,
            failed_by_rejections=True,
        )
    ]
    room.phase = Phase.ROUND_RESULT

    view = build_player_view(room, room.players[0], engine)

    assert view["game"]["missionHistory"] == [
        {
            "number": 1,
            "teamIds": [],
            "success": False,
            "failCount": 0,
            "failedByRejections": True,
        }
    ]


def test_chat_history_is_visible_to_every_room_member():
    engine, room = start_room(5)
    sender = room.players[0]
    viewer = room.players[1]

    room.chat_messages.append(
        ChatMessage(
            id="message-1",
            sender_id=sender.id,
            sender_name=sender.name,
            content="这支队伍我赞成",
            created_at="2026-08-01T00:00:00+00:00",
        )
    )
    view = build_player_view(room, viewer, engine)

    assert view["chat"]["maxLength"] == 300
    assert view["chat"]["messages"][-1]["senderName"] == sender.name
    assert view["chat"]["messages"][-1]["content"] == "这支队伍我赞成"


def test_avalon_views_include_account_avatars():
    room = make_room(1)
    host = room.players[0]
    host.avatar_url = "/avatars/jade-owl.webp"

    view = build_player_view(room, host, GameEngine())

    assert view["self"]["avatarUrl"] == "/avatars/jade-owl.webp"
    assert view["players"][0]["avatarUrl"] == "/avatars/jade-owl.webp"


def test_ai_player_marker_is_in_player_view():
    room = make_room(2)
    host, ai_player = room.players
    ai_player.is_bot = True

    view = build_player_view(room, host, GameEngine())
    ai_view = next(
        player for player in view["players"] if player["id"] == ai_player.id
    )

    assert ai_view["isBot"] is True
    assert ai_view["seat"] == 1


def test_only_lobby_host_can_dissolve_avalon_room():
    room = make_room(2)
    host, guest = room.players

    host_view = build_player_view(room, host, GameEngine())
    guest_view = build_player_view(room, guest, GameEngine())

    assert host_view["actions"]["canDissolve"] is True
    assert guest_view["actions"]["canDissolve"] is False

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
    assert set(assassin_view["result"]["eligibleTargetIds"]) == {
        player.id
        for player in room.players
        if player.alignment == Alignment.GOOD
    }
    assert other_view["result"]["eligibleTargetIds"] == []


def test_only_assassin_can_choose_the_council_assassination_target():
    engine, room = start_room(
        6,
        mode=AvalonMode.COURT_UNDERCURRENT,
        shadow_merlin_enabled=True,
    )
    room.phase = Phase.EXILE_COUNCIL_ASSASSINATION_TARGET
    assassin = next(
        player for player in room.players if player.role == Role.ASSASSIN
    )
    shadow = next(
        player for player in room.players if player.role == Role.SHADOW_MERLIN
    )

    assassin_view = build_player_view(room, assassin, engine)
    shadow_view = build_player_view(room, shadow, engine)

    assert assassin_view["actions"][
        "canSubmitExileCouncilAssassinationTarget"
    ] is True
    assert shadow_view["actions"][
        "canSubmitExileCouncilAssassinationTarget"
    ] is False
    assert set(
        assassin_view["shadowMerlin"]["eligibleAssassinationTargetIds"]
    ) == set(engine.eligible_assassination_targets(room))
    assert shadow_view["shadowMerlin"][
        "eligibleAssassinationTargetIds"
    ] == []


def test_court_undercurrent_initial_knowledge_is_private():
    engine, room = start_room(9, mode=AvalonMode.COURT_UNDERCURRENT)
    merlin = next(player for player in room.players if player.role == Role.MERLIN)
    assassin = next(
        player for player in room.players if player.role == Role.ASSASSIN
    )
    dissenting = next(
        player
        for player in room.players
        if player.role == Role.DISSENTING_COURTIER
    )

    merlin_knowledge = build_player_view(room, merlin, engine)["self"]["role"][
        "knowledge"
    ]
    dissenting_knowledge = build_player_view(room, dissenting, engine)["self"][
        "role"
    ]["knowledge"]
    assassin_knowledge = build_player_view(room, assassin, engine)["self"][
        "role"
    ]["knowledge"]

    assert all(
        item["playerId"] != dissenting.id
        for item in merlin_knowledge
    )
    merlin_description = build_player_view(room, merlin, engine)["self"][
        "role"
    ]["description"]
    assert "心怀异念之臣" not in merlin_description
    assert dissenting_knowledge == [
        {
            "playerId": assassin.id,
            "playerName": assassin.name,
            "kind": "assassin",
            "label": "你认出的刺客",
        }
    ]
    assert all(
        item["playerId"] != dissenting.id
        for item in assassin_knowledge
    )


def test_five_player_merlin_cannot_identify_dissenting_or_percival():
    engine, room = start_room(5, mode=AvalonMode.COURT_UNDERCURRENT)
    merlin = next(player for player in room.players if player.role == Role.MERLIN)
    percival = next(
        player for player in room.players if player.role == Role.PERCIVAL
    )
    dissenting = next(
        player
        for player in room.players
        if player.role == Role.DISSENTING_COURTIER
    )

    knowledge_ids = {
        item["playerId"]
        for item in build_player_view(room, merlin, engine)["self"]["role"][
            "knowledge"
        ]
    }

    assert percival.id not in knowledge_ids
    assert dissenting.id not in knowledge_ids
    assert knowledge_ids == {
        player.id
        for player in room.players
        if player.alignment == Alignment.EVIL
    }


def test_only_assassin_sees_dagger_candidates():
    engine, room = start_room(5, mode=AvalonMode.COURT_UNDERCURRENT)
    room.phase = Phase.DAGGER_GRANT
    dissenting = next(
        player
        for player in room.players
        if player.role == Role.DISSENTING_COURTIER
    )
    decoy = next(
        player
        for player in room.players
        if player.alignment == Alignment.GOOD and player.id != dissenting.id
    )
    room.dagger_candidate_ids = [dissenting.id, decoy.id]
    assassin = next(
        player for player in room.players if player.role == Role.ASSASSIN
    )
    other = next(player for player in room.players if player.id != assassin.id)

    assassin_view = build_player_view(room, assassin, engine)
    other_view = build_player_view(room, other, engine)

    assert assassin_view["actions"]["canGrantDagger"] is True
    assert assassin_view["courtUndercurrent"]["daggerCandidateIds"] == [
        dissenting.id,
        decoy.id,
    ]
    assert other_view["actions"]["canGrantDagger"] is False
    assert other_view["courtUndercurrent"]["daggerCandidateIds"] == []


def test_successful_dagger_grant_reunites_evil_except_oberon():
    engine, room = start_room(7, mode=AvalonMode.COURT_UNDERCURRENT)
    assassin = next(
        player for player in room.players if player.role == Role.ASSASSIN
    )
    morgana = next(
        player for player in room.players if player.role == Role.MORGANA
    )
    oberon = next(
        player for player in room.players if player.role == Role.OBERON
    )
    dissenting = next(
        player
        for player in room.players
        if player.role == Role.DISSENTING_COURTIER
    )
    room.phase = Phase.DAGGER_GRANT
    room.dagger_candidate_ids = [dissenting.id, room.players[0].id]
    engine.grant_dagger(room, assassin.id, dissenting.id)

    assassin_view = build_player_view(room, assassin, engine)
    morgana_view = build_player_view(room, morgana, engine)
    dissenting_view = build_player_view(room, dissenting, engine)
    oberon_view = build_player_view(room, oberon, engine)
    good_view = build_player_view(
        room,
        next(player for player in room.players if player.alignment == Alignment.GOOD),
        engine,
    )

    for view in (
        assassin_view,
        morgana_view,
        dissenting_view,
        oberon_view,
        good_view,
    ):
        assert view["courtUndercurrent"]["daggerHit"] is True
        assert (
            view["courtUndercurrent"]["daggerTargetId"]
            == dissenting.id
        )
        assert (
            view["courtUndercurrent"]["transformedPlayerId"]
            == dissenting.id
        )

    assert any(
        item["playerId"] == dissenting.id
        for item in assassin_view["self"]["role"]["knowledge"]
    )
    assert any(
        item["playerId"] == dissenting.id
        for item in morgana_view["self"]["role"]["knowledge"]
    )
    assert {
        item["playerId"]
        for item in dissenting_view["self"]["role"]["knowledge"]
    } == {assassin.id, morgana.id}
    assert oberon_view["self"]["role"]["knowledge"] == []
    assert all(
        item["playerId"] != oberon.id
        for item in dissenting_view["self"]["role"]["knowledge"]
    )
    assert all("alignment" not in player for player in assassin_view["players"])


def test_court_ending_reveals_both_candidate_lists_to_everyone():
    engine, room = start_room(7, mode=AvalonMode.COURT_UNDERCURRENT)
    assassin = next(
        player for player in room.players if player.role == Role.ASSASSIN
    )
    dissenting = next(
        player
        for player in room.players
        if player.role == Role.DISSENTING_COURTIER
    )
    decoy = next(
        player
        for player in room.players
        if player.alignment == Alignment.GOOD and player.id != dissenting.id
    )
    room.phase = Phase.DAGGER_GRANT
    room.dagger_candidate_ids = [dissenting.id, decoy.id]
    engine.grant_dagger(room, assassin.id, dissenting.id)
    merlin = next(player for player in room.players if player.role == Role.MERLIN)
    final_candidates = engine.eligible_dissenting_targets(room)
    engine.dissenting_assassinate(room, dissenting.id, merlin.id)

    viewer = next(
        player for player in room.players if player.alignment == Alignment.GOOD
    )
    view = build_player_view(room, viewer, engine)

    assert view["courtUndercurrent"]["daggerCandidateIds"] == [
        dissenting.id,
        decoy.id,
    ]
    assert view["courtUndercurrent"]["eligibleTargetIds"] == final_candidates
    assert view["courtUndercurrent"]["transformedPlayerId"] == dissenting.id


@pytest.mark.parametrize(
    ("player_count", "expected_labels"),
    [
        (6, {"梅林", "刺客", "莫甘娜"}),
        (7, {"梅林", "刺客", "莫甘娜", "奥伯伦"}),
        (8, {"梅林", "刺客", "莫甘娜", "莫德雷德的爪牙"}),
        (9, {"梅林", "刺客", "莫甘娜"}),
        (10, {"梅林", "刺客", "莫甘娜", "奥伯伦"}),
    ],
)
def test_shadow_merlin_knowledge_is_exact_and_hidden_from_everyone_else(
    player_count: int,
    expected_labels: set[str],
):
    engine, room = start_room(
        player_count,
        mode=AvalonMode.COURT_UNDERCURRENT,
        shadow_merlin_enabled=True,
    )
    shadow = next(
        player for player in room.players if player.role == Role.SHADOW_MERLIN
    )
    merlin = next(player for player in room.players if player.role == Role.MERLIN)
    assassin = next(
        player for player in room.players if player.role == Role.ASSASSIN
    )
    shadow_role = build_player_view(room, shadow, engine)["self"]["role"]
    shadow_knowledge = shadow_role["knowledge"]

    assert {item["label"] for item in shadow_knowledge} == expected_labels
    assert all(item["kind"] == "special_identity" for item in shadow_knowledge)
    assert "除莫德雷德外所有邪恶角色" in shadow_role["description"]

    merlin_knowledge_ids = {
        item["playerId"]
        for item in build_player_view(room, merlin, engine)["self"]["role"][
            "knowledge"
        ]
    }
    assassin_knowledge_ids = {
        item["playerId"]
        for item in build_player_view(room, assassin, engine)["self"]["role"][
            "knowledge"
        ]
    }
    assert shadow.id not in merlin_knowledge_ids
    assert shadow.id not in assassin_knowledge_ids
    assert build_player_view(room, shadow, engine)["actions"][
        "canMissionFail"
    ] is False


def test_council_ballots_stay_anonymous_until_game_over():
    engine, room = start_room(
        6,
        mode=AvalonMode.COURT_UNDERCURRENT,
        shadow_merlin_enabled=True,
    )
    room.phase = Phase.EXILE_COUNCIL_BALLOT
    room.exile_council_triggered = True
    target = room.players[1]
    engine.submit_exile_council_ballot(
        room,
        room.players[0].id,
        open_council=True,
        target_id=target.id,
    )

    during = build_player_view(room, room.players[1], engine)["shadowMerlin"]
    assert during["ballotsSubmitted"] == 1
    assert during["openVotes"] == []
    assert during["targetVotes"] == []

    room.phase = Phase.GAME_OVER
    after = build_player_view(room, room.players[1], engine)["shadowMerlin"]
    assert after["openVotes"][0]["playerId"] == room.players[0].id
    assert after["targetVotes"][0]["targetId"] == target.id
