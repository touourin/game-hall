from __future__ import annotations

import json
import random

import pytest

from backend.app.arcade.models import ArcadePlayer, ArcadeRoom
from backend.app.games.base import GameRuleError
from backend.app.games.departed_suspicion.cards import (
    BOMBERS_EQUIPMENT_IDS,
    EQUIPMENT_CARDS,
)
from backend.app.games.departed_suspicion.engine import DepartedSuspicionEngine


def make_room(
    player_count: int = 4,
    *,
    equipment_set: str = "bombers",
    seed: int = 7,
    deal_starting_equipment: bool = False,
) -> tuple[DepartedSuspicionEngine, ArcadeRoom]:
    engine = DepartedSuspicionEngine(rng=random.Random(seed))
    players = [
        ArcadePlayer(
            id=f"p{seat}",
            account_id=f"a{seat}",
            name=f"玩家{seat + 1}",
            token_hash=f"token-{seat}",
            seat=seat,
        )
        for seat in range(player_count)
    ]
    room = ArcadeRoom(
        code="COPS",
        game_key=engine.key,
        host_id=players[0].id,
        players=players,
        state=engine.initial_state(),
        options={"equipmentSet": equipment_set},
        game_id="game-cops",
        started_at="2026-08-06T00:00:00+00:00",
    )
    engine.start(room)
    if not deal_starting_equipment:
        room.state.equipment_deck = list(room.state.initial_equipment_order)
        room.state.equipment_draw_history.clear()
        for board in room.state.boards.values():
            board.equipment.clear()
    return engine, room


def leader_owner(room: ArcadeRoom, kind: str) -> tuple[int, int]:
    for seat, board in room.state.boards.items():
        for index, card in enumerate(board.cards):
            if card.kind == kind:
                return seat, index
    raise AssertionError(f"missing {kind}")


def normal_card_index(room: ArcadeRoom, seat: int) -> int:
    return next(
        index
        for index, card in enumerate(room.state.boards[seat].cards)
        if card.kind in {"honest", "crooked"}
    )


def test_catalog_keeps_all_33_cards_and_only_complete_modes_enter_the_deck() -> None:
    assert len(EQUIPMENT_CARDS) == 33
    assert len({card.id for card in EQUIPMENT_CARDS}) == 33
    assert len(BOMBERS_EQUIPMENT_IDS) == 21
    assert all(
        card.expansion in {"base", "bombers"}
        for card in EQUIPMENT_CARDS
        if card.id in BOMBERS_EQUIPMENT_IDS
    )
    assert "new_assignment" not in BOMBERS_EQUIPMENT_IDS


def test_production_engine_uses_system_randomness() -> None:
    assert isinstance(DepartedSuspicionEngine().rng, random.SystemRandom)


def test_legacy_expanded_option_migrates_to_the_complete_bombers_deck() -> None:
    options = DepartedSuspicionEngine().room_options(
        {"equipmentSet": "expanded"}
    )

    assert options["equipmentSet"] == "bombers"


@pytest.mark.parametrize("player_count", range(4, 9))
def test_setup_deals_integrity_and_one_private_equipment_per_player(
    player_count: int,
) -> None:
    engine, room = make_room(
        player_count,
        seed=player_count,
        deal_starting_equipment=True,
    )

    assert all(len(board.cards) == 3 for board in room.state.boards.values())
    agent_seat, _ = leader_owner(room, "agent")
    kingpin_seat, _ = leader_owner(room, "kingpin")
    assert agent_seat != kingpin_seat
    assert room.state.gun_total == (2 if player_count == 4 else 3 if player_count <= 6 else 4)
    assert all(len(board.equipment) == 1 for board in room.state.boards.values())
    assert [room.state.boards[seat].equipment[0] for seat in range(player_count)] == list(
        room.state.initial_equipment_order[:player_count]
    )
    assert [
        (draw.sequence, draw.seat, draw.card_id, draw.source)
        for draw in room.state.equipment_draw_history
    ] == [
        (seat + 1, seat, room.state.initial_equipment_order[seat], "setup")
        for seat in range(player_count)
    ]
    assert len(room.state.equipment_deck) == 21 - player_count
    for viewer in room.players:
        view = engine.view(room, viewer)
        assert len(view["equipmentHand"]) == 1
        assert all(board["equipmentCount"] == 1 for board in view["players"])


@pytest.mark.parametrize(
    ("player_count", "expected_normal_counts"),
    [
        (4, [5, 5]),
        (5, [6, 7]),
        (6, [8, 8]),
        (7, [9, 10]),
        (8, [11, 11]),
    ],
)
def test_integrity_cards_stay_balanced_at_every_player_count(
    player_count: int,
    expected_normal_counts: list[int],
) -> None:
    for seed in range(250):
        engine = DepartedSuspicionEngine(rng=random.Random(seed))
        hands = engine._deal_integrity(player_count)
        cards = [card for hand in hands.values() for card in hand]

        honest = sum(card.kind == "honest" for card in cards)
        crooked = sum(card.kind == "crooked" for card in cards)
        assert sorted([honest, crooked]) == expected_normal_counts
        assert sum(card.kind == "agent" for card in cards) == 1
        assert sum(card.kind == "kingpin" for card in cards) == 1
        assert all(len(hand) == 3 for hand in hands.values())


def test_private_view_never_leaks_other_hidden_integrity() -> None:
    engine, room = make_room()
    own_view = engine.view(room, room.players[0])
    other_board = next(board for board in own_view["players"] if board["seat"] == 1)
    self_board = next(board for board in own_view["players"] if board["seat"] == 0)

    assert all(card["kind"] is None for card in other_board["cards"])
    assert all(card["knowledgeKey"] is None for card in other_board["cards"])
    assert all(card["kind"] is not None for card in self_board["cards"])
    assert all(card["knowledgeKey"] is None for card in self_board["cards"])


def test_investigation_is_private_and_does_not_reveal_card() -> None:
    engine, room = make_room()
    engine.act(
        room,
        room.players[0],
        "investigate",
        {"targetSeat": 1, "cardIndex": 0},
    )

    investigated = room.state.boards[1].cards[0]
    assert investigated.revealed is False
    investigator_view = engine.view(room, room.players[0])
    bystander_view = engine.view(room, room.players[2])
    assert investigator_view["players"][1]["cards"][0]["kind"] == investigated.kind
    assert investigator_view["players"][1]["cards"][0]["knowledgeKey"] == investigated.id
    assert investigator_view["players"][1]["cards"][0]["knowledge"] == "known"
    assert bystander_view["players"][1]["cards"][0]["kind"] is None
    assert bystander_view["players"][1]["cards"][0]["knowledgeKey"] is None


@pytest.mark.parametrize(
    ("card_id", "payload", "learned"),
    [
        (
            "wiretap",
            {
                "firstSeat": 1,
                "firstCardIndex": 0,
                "secondSeat": 2,
                "secondCardIndex": 1,
            },
            [(1, 0), (2, 1)],
        ),
        (
            "fingerprint_kit",
            {"targetSeat": 1, "cardIndex": 1},
            [(1, 1)],
        ),
        (
            "security_wand",
            {"targetSeat": 1, "cardIndex": 2},
            [(1, 2)],
        ),
    ],
)
def test_targeted_investigation_equipment_updates_only_the_users_private_view(
    card_id: str,
    payload: dict[str, int],
    learned: list[tuple[int, int]],
) -> None:
    engine, room = make_room()
    room.state.boards[0].equipment = [card_id]

    engine.act(
        room,
        room.players[0],
        "play_equipment",
        {"cardId": card_id, **payload},
    )

    user_view = engine.view(room, room.players[0])
    bystander_view = engine.view(room, room.players[3])
    for target, card_index in learned:
        card = room.state.boards[target].cards[card_index]
        private_card = user_view["players"][target]["cards"][card_index]
        assert private_card["knowledgeKey"] == card.id
        assert private_card["kind"] == card.kind
        assert private_card["knowledge"] == "known"
        assert bystander_view["players"][target]["cards"][card_index]["kind"] is None


def test_polygraph_gives_each_player_the_other_players_hidden_cards() -> None:
    engine, room = make_room()
    room.state.boards[0].equipment = ["polygraph"]

    engine.act(
        room,
        room.players[0],
        "play_equipment",
        {"cardId": "polygraph", "targetSeat": 1},
    )

    actor_view = engine.view(room, room.players[0])
    target_view = engine.view(room, room.players[1])
    assert all(
        card["knowledge"] == "known"
        for card in actor_view["players"][1]["cards"]
    )
    assert all(
        card["knowledge"] == "known"
        for card in target_view["players"][0]["cards"]
    )


def test_inspection_gloves_show_option_teaches_every_player_the_hidden_cards() -> None:
    engine, room = make_room()
    room.state.boards[0].equipment = ["inspection_gloves"]

    engine.act(
        room,
        room.players[0],
        "play_equipment",
        {"cardId": "inspection_gloves", "targetSeat": 1},
    )
    engine.act(
        room,
        room.players[1],
        "inspection_choice",
        {"choice": "show_integrity"},
    )

    assert all(not card.revealed for card in room.state.boards[1].cards)
    for viewer in room.players:
        view = engine.view(room, viewer)
        if viewer.seat == 1:
            assert all(card["knowledge"] == "own" for card in view["players"][1]["cards"])
        else:
            assert all(card["knowledge"] == "known" for card in view["players"][1]["cards"])


def test_metal_detector_requires_and_honors_a_choice_for_every_armed_player() -> None:
    engine, room = make_room()
    state = room.state
    state.boards[0].equipment = ["metal_detector"]
    state.boards[1].gun = True
    state.boards[2].gun = True

    assert "metal_detector" in engine.view(room, room.players[0])["legal"][
        "playableEquipmentIds"
    ]
    with pytest.raises(GameRuleError, match="每名持枪玩家"):
        engine.act(
            room,
            room.players[0],
            "play_equipment",
            {"cardId": "metal_detector"},
        )

    assert room.state.boards[0].equipment == ["metal_detector"]
    engine.act(
        room,
        room.players[0],
        "play_equipment",
        {"cardId": "metal_detector", "choices": {"1": 1, "2": 2}},
    )

    assert room.state.boards[1].cards[1].id in room.state.knowledge[0]
    assert room.state.boards[2].cards[2].id in room.state.knowledge[0]


def test_metal_detector_is_not_advertised_without_an_eligible_armed_player() -> None:
    engine, room = make_room()
    room.state.boards[0].equipment = ["metal_detector"]

    assert "metal_detector" not in engine.view(room, room.players[0])["legal"][
        "playableEquipmentIds"
    ]


def test_equip_reveals_a_card_and_draws_without_starting_equipment() -> None:
    engine, room = make_room(equipment_set="base")
    first_equipment = room.state.equipment_deck[0]
    initial_order = list(room.state.equipment_deck)

    engine.act(room, room.players[0], "equip", {"cardIndex": 0})

    assert room.state.boards[0].cards[0].revealed is True
    assert room.state.boards[0].equipment == [first_equipment]
    assert room.state.action_done is True
    assert room.state.initial_equipment_order == initial_order
    assert room.state.equipment_audit_complete is True
    assert [
        (
            draw.sequence,
            draw.turn_number,
            draw.seat,
            draw.card_id,
            draw.source,
        )
        for draw in room.state.equipment_draw_history
    ] == [(1, 1, 0, first_equipment, "normal_action")]

    recorded = engine.record_state(room)
    assert recorded["initialEquipmentOrder"] == initial_order
    assert recorded["equipmentDrawHistory"] == [
        {
            "sequence": 1,
            "turnNumber": 1,
            "seat": 0,
            "cardId": first_equipment,
            "source": "normal_action",
        }
    ]
    json.dumps(recorded)


@pytest.mark.parametrize("action", ["equip", "arm"])
def test_fully_revealed_player_cannot_pay_to_equip_or_arm(action: str) -> None:
    engine, room = make_room(equipment_set="base")
    board = room.state.boards[0]
    for card in board.cards:
        card.revealed = True

    payload = {"targetSeat": 1} if action == "arm" else {}
    with pytest.raises(GameRuleError, match="没有暗置底细"):
        engine.act(room, room.players[0], action, payload)

    assert room.state.action_done is False


@pytest.mark.parametrize("action", ["equip", "arm"])
def test_hidden_card_is_still_required_as_cost_when_available(action: str) -> None:
    engine, room = make_room(equipment_set="base")
    payload = {"targetSeat": 1} if action == "arm" else {}

    with pytest.raises(GameRuleError, match="底细牌"):
        engine.act(room, room.players[0], action, payload)


def test_crutches_revives_an_all_revealed_player_who_can_skip_turn() -> None:
    engine, room = make_room(equipment_set="base")
    state = room.state
    actor = state.turn_seat
    target = next(
        seat
        for seat, board in state.boards.items()
        if seat != actor and engine._leader_card(board) is None
    )
    revived = state.boards[target]
    for card in revived.cards:
        card.revealed = True
    engine._eliminate(state, target)
    state.boards[actor].equipment = ["crutches"]

    engine.act(
        room,
        room.players[actor],
        "play_equipment",
        {"cardId": "crutches", "targetSeat": target},
    )

    assert revived.alive is True
    assert revived.restricted_to_equip is True
    assert all(card.revealed for card in revived.cards)

    state.turn_seat = target
    state.action_done = False
    revived.effects.append("key")
    view = engine.view(room, room.players[target])
    assert view["legal"]["canTakeNormalAction"] is True
    assert view["legal"]["normalActionIds"] == []
    assert view["legal"]["canPassNormalAction"] is True
    assert view["legal"]["canTakeExtraInvestigation"] is False

    with pytest.raises(GameRuleError, match="只能执行获取装备"):
        engine.act(room, room.players[target], "investigate", {})
    with pytest.raises(GameRuleError, match="只能执行获取装备"):
        engine.act(room, room.players[target], "extra_investigate", {})

    with pytest.raises(GameRuleError, match="没有暗置底细"):
        engine.act(room, room.players[target], "equip", {})
    engine.act(room, room.players[target], "pass_turn", {})

    assert state.action_done is True
    assert revived.equipment == []


@pytest.mark.parametrize("player_count", range(4, 9))
def test_every_fully_revealed_player_can_skip_repeated_turns(
    player_count: int,
) -> None:
    engine, room = make_room(player_count, equipment_set="base")
    state = room.state
    for board in state.boards.values():
        for card in board.cards:
            card.revealed = True
    state.equipment_deck.clear()

    for _ in range(player_count * 5):
        seat = state.turn_seat
        view = engine.view(room, room.players[seat])
        assert view["legal"]["normalActionIds"] == []
        assert view["legal"]["canPassNormalAction"] is True

        engine.act(room, room.players[seat], "pass_turn", {})
        assert engine.view(room, room.players[seat])["legal"]["canEndTurn"] is True
        engine.act(room, room.players[seat], "end_turn", {})

    assert state.turn_number == player_count * 5 + 1


def test_only_actions_that_can_resolve_are_advertised() -> None:
    engine, room = make_room()
    state = room.state
    actor = state.turn_seat
    for board in state.boards.values():
        for card in board.cards:
            card.revealed = True
    state.gun_total = 0
    state.boards[actor].effects.append("key")

    view = engine.view(room, room.players[actor])

    assert view["legal"]["normalActionIds"] == []
    assert view["legal"]["canPassNormalAction"] is True
    assert view["legal"]["canTakeExtraInvestigation"] is False


def test_forced_shot_decision_hides_unrelated_equipment_and_key_actions() -> None:
    engine, room = make_room()
    state = room.state
    actor = state.turn_seat
    target = next(seat for seat in state.boards if seat != actor)
    state.boards[actor].effects.append("key")
    state.boards[actor].equipment = ["thumbprint_scanner", "k9_unit"]

    engine._begin_shot(room, state, actor, target, source="gun")
    view = engine.view(room, room.players[actor])

    assert state.pending_shot and state.pending_shot.scanner_seat == actor
    assert view["legal"]["canTakeExtraInvestigation"] is False
    assert view["legal"]["playableEquipmentIds"] == []


def test_leader_is_wounded_once_then_eliminated_and_opposing_team_wins() -> None:
    engine, room = make_room()
    shooter = 0
    target, _ = leader_owner(room, "kingpin")
    if target == shooter:
        shooter = next(seat for seat in room.state.boards if seat != target)
    state = room.state
    state.turn_seat = shooter
    state.boards[shooter].gun = True
    state.boards[shooter].aim_seat = target
    state.acquired_gun_turn[shooter] = 0
    state.equipment_deck = ["coffee", "flashbang"]

    engine.act(room, room.players[shooter], "shoot", {})

    leader = engine._leader_card(state.boards[target])
    assert leader is not None and leader.wounded is True
    assert state.boards[target].alive is True
    assert state.boards[target].equipment == ["coffee"]

    state.boards[target].equipment.clear()
    state.action_done = False
    state.turn_seat = shooter
    state.turn_number += 1
    state.boards[shooter].gun = True
    state.boards[shooter].aim_seat = target
    state.acquired_gun_turn[shooter] = 0
    engine.act(room, room.players[shooter], "shoot", {})

    assert room.phase == "finished"
    assert room.winner == "honest"
    assert state.boards[target].alive is False


def test_k9_cancels_declared_shot_and_shooter_may_choose_a_new_action() -> None:
    engine, room = make_room()
    state = room.state
    state.boards[0].gun = True
    state.boards[0].aim_seat = 1
    state.acquired_gun_turn[0] = 0
    state.boards[1].equipment = ["k9_unit"]

    engine.act(room, room.players[0], "shoot", {})
    assert state.pending_action is not None
    assert engine._response_seat(state.pending_action) == 1

    engine.act(
        room,
        room.players[1],
        "play_equipment",
        {"cardId": "k9_unit", "targetSeat": 0},
    )

    assert state.pending_action is None
    assert state.boards[0].gun is False
    assert state.action_done is False


def test_helmet_cancels_shot_but_consumes_the_shooters_action() -> None:
    engine, room = make_room()
    state = room.state
    state.boards[0].gun = True
    state.boards[0].aim_seat = 1
    state.acquired_gun_turn[0] = 0
    state.boards[1].equipment = ["helmet"]

    engine.act(room, room.players[0], "shoot", {})
    engine.act(
        room,
        room.players[1],
        "play_equipment",
        {"cardId": "helmet"},
    )

    assert state.pending_action is None
    assert state.boards[0].gun is False
    assert state.action_done is True
    assert state.boards[1].alive is True


def test_equipment_without_explicit_timing_is_usable_on_another_players_turn() -> None:
    engine, room = make_room()
    state = room.state
    state.turn_seat = 0
    state.boards[1].equipment = ["smoke_grenade"]

    legal = engine.view(room, room.players[1])["legal"]

    assert legal["playableEquipmentIds"] == ["smoke_grenade"]
    assert legal["equipmentOptions"] == [
        {"cardId": "smoke_grenade", "fields": []}
    ]
    engine.act(
        room,
        room.players[1],
        "play_equipment",
        {"cardId": "smoke_grenade"},
    )
    assert state.direction == -1


def test_anytime_equipment_can_respond_before_a_declared_action_resolves() -> None:
    engine, room = make_room()
    state = room.state
    state.boards[1].equipment = ["smoke_grenade"]

    engine.act(
        room,
        room.players[0],
        "investigate",
        {"targetSeat": 2, "cardIndex": 0},
    )

    assert state.pending_action is not None
    assert engine._response_seat(state.pending_action) == 1
    assert engine.view(room, room.players[1])["legal"]["responseEquipmentIds"] == [
        "smoke_grenade"
    ]
    engine.act(
        room,
        room.players[1],
        "play_equipment",
        {"cardId": "smoke_grenade"},
    )

    assert state.pending_action is None
    assert state.action_done is True
    assert state.direction == -1


def test_taser_remains_restricted_to_its_owners_turn() -> None:
    engine, room = make_room()
    state = room.state
    state.boards[0].gun = True
    state.boards[0].aim_seat = 1
    state.boards[2].equipment = ["taser"]
    state.turn_seat = 0

    assert "taser" not in engine.view(room, room.players[2])["legal"][
        "playableEquipmentIds"
    ]
    with pytest.raises(GameRuleError, match="使用时机"):
        engine.act(
            room,
            room.players[2],
            "play_equipment",
            {"cardId": "taser", "targetSeat": 0, "aimSeat": 1},
        )

    state.turn_seat = 2
    option = engine.view(room, room.players[2])["legal"]["equipmentOptions"][0]
    assert option["cardId"] == "taser"
    assert option["fields"][0]["options"] == [
        {"value": 0, "label": room.players[0].name}
    ]


def test_blackmail_can_create_the_immediate_solo_leader_victory() -> None:
    engine, room = make_room()
    agent_seat, _ = leader_owner(room, "agent")
    kingpin_seat, kingpin_index = leader_owner(room, "kingpin")
    actor = next(
        seat for seat in room.state.boards if seat not in {agent_seat, kingpin_seat}
    )
    room.state.turn_seat = actor
    room.state.boards[actor].equipment = ["blackmail"]

    engine.act(
        room,
        room.players[actor],
        "play_equipment",
        {
            "cardId": "blackmail",
            "firstSeat": agent_seat,
            "firstCardIndex": normal_card_index(room, agent_seat),
            "secondSeat": kingpin_seat,
            "secondCardIndex": kingpin_index,
        },
    )

    assert room.phase == "finished"
    assert room.winner == "solo"
    assert room.winner_player_ids == [room.players[agent_seat].id]
    assert "blackmail" in room.state.equipment_deck
    assert room.state.history[-1]["cardId"] == "blackmail"
    assert engine.record_state(room)["equipmentPlayHistory"] == [
        {
            "sequence": 1,
            "turnNumber": 1,
            "seat": actor,
            "cardId": "blackmail",
            "targetSeats": [agent_seat, kingpin_seat],
        }
    ]


def test_wound_token_moves_with_a_transferred_leader_card() -> None:
    engine, room = make_room()
    agent_seat, agent_index = leader_owner(room, "agent")
    receiver = next(seat for seat in room.state.boards if seat != agent_seat)
    agent_card = room.state.boards[agent_seat].cards[agent_index]
    agent_card.wounded = True
    receiver_index = normal_card_index(room, receiver)

    room.state.boards[agent_seat].cards[agent_index], room.state.boards[receiver].cards[receiver_index] = (
        room.state.boards[receiver].cards[receiver_index],
        room.state.boards[agent_seat].cards[agent_index],
    )

    moved = room.state.boards[receiver].cards[receiver_index]
    assert moved.kind == "agent"
    assert moved.wounded is True


def test_planted_evidence_inverts_only_an_ordinary_players_team() -> None:
    engine, room = make_room()
    state = room.state
    ordinary = next(
        seat for seat, board in state.boards.items() if engine._leader_card(board) is None
    )
    actor = state.turn_seat
    state.boards[actor].equipment = ["planted_evidence"]
    original_team = engine._team(state.boards[ordinary])

    engine.act(
        room,
        room.players[actor],
        "play_equipment",
        {"cardId": "planted_evidence", "targetSeat": ordinary},
    )

    assert engine._team(state.boards[ordinary]) != original_team


def test_planted_evidence_changes_team_membership_in_final_settlement() -> None:
    engine, room = make_room()
    state = room.state
    ordinary = next(
        seat
        for seat, board in state.boards.items()
        if engine._leader_card(board) is None
    )
    for card in state.boards[ordinary].cards:
        card.kind = "honest"
    actor = state.turn_seat
    state.boards[actor].equipment = ["planted_evidence"]

    engine.act(
        room,
        room.players[actor],
        "play_equipment",
        {"cardId": "planted_evidence", "targetSeat": ordinary},
    )
    agent_seat, _ = leader_owner(room, "agent")
    engine._eliminate(state, agent_seat)
    engine._check_victory(room, state)

    assert room.winner == "crooked"
    assert room.players[ordinary].id in room.winner_player_ids
    _, alignment, won = engine.player_result(room, room.players[ordinary])
    assert alignment == "crooked"
    assert won is True


def test_failed_equipment_validation_rolls_back_the_card_and_board() -> None:
    engine, room = make_room()
    state = room.state
    state.boards[0].equipment = ["blackmail"]

    with pytest.raises(GameRuleError, match="不能选择使用者自己"):
        engine.act(
            room,
            room.players[0],
            "play_equipment",
            {
                "cardId": "blackmail",
                "firstSeat": 0,
                "firstCardIndex": 0,
                "secondSeat": 1,
                "secondCardIndex": 0,
            },
        )

    assert room.state.boards[0].equipment == ["blackmail"]
    assert room.phase == "playing"


def test_grenade_passes_once_then_shoots_the_second_receiver() -> None:
    engine, room = make_room()
    state = room.state
    state.boards[0].equipment = ["grenade"]
    engine.act(
        room,
        room.players[0],
        "play_equipment",
        {"cardId": "grenade", "targetSeat": 1},
    )
    assert state.boards[1].grenade_stage == 1

    state.turn_seat = 1
    state.action_done = True
    engine.act(room, room.players[1], "end_turn", {})
    assert state.choice and state.choice.kind == "grenade_pass"
    engine.act(room, room.players[1], "pass_grenade", {"targetSeat": 2})
    assert state.boards[2].grenade_stage == 2

    state.turn_seat = 2
    state.action_done = True
    engine.act(room, room.players[2], "end_turn", {})
    assert state.boards[2].alive is False or engine._leader_card(state.boards[2]) is not None


def test_resigning_grenade_holder_clears_the_forced_pass_and_advances() -> None:
    engine, room = make_room()
    state = room.state
    holder = next(
        seat for seat, board in state.boards.items() if engine._leader_card(board) is None
    )
    state.turn_seat = holder
    state.boards[holder].grenade_stage = 1
    state.boards[holder].effects.append("grenade")
    state.action_done = True

    engine.act(room, room.players[holder], "end_turn", {})
    assert state.choice and state.choice.kind == "grenade_pass"

    engine.act(room, room.players[holder], "resign", {})

    assert state.choice is None
    assert state.turn_seat != holder
    assert state.boards[holder].grenade_stage == 0
    assert "grenade" in state.equipment_deck


def test_response_priority_follows_seat_order_from_the_action_player() -> None:
    engine, room = make_room()
    state = room.state
    state.boards[0].gun = True
    state.boards[0].aim_seat = 3
    state.acquired_gun_turn[0] = 0
    state.boards[1].equipment = ["k9_unit"]
    state.boards[2].equipment = ["concussion_grenade"]

    engine.act(room, room.players[0], "shoot", {})

    assert state.pending_action is not None
    assert state.pending_action.response_order == [1, 2]
    engine.act(room, room.players[1], "pass_response", {})
    assert engine._response_seat(state.pending_action) == 2


def test_resigning_response_player_is_skipped_without_stalling_action() -> None:
    engine, room = make_room()
    state = room.state
    ordinary = [
        seat for seat, board in state.boards.items() if engine._leader_card(board) is None
    ]
    responder = ordinary[0]
    actor = next(seat for seat in state.boards if seat != responder)
    target = next(seat for seat in state.boards if seat not in {actor, responder})
    state.turn_seat = actor
    state.boards[responder].equipment = ["coffee"]

    engine.act(
        room,
        room.players[actor],
        "investigate",
        {"targetSeat": target, "cardIndex": 0},
    )
    assert state.pending_action is not None
    assert engine._response_seat(state.pending_action) == responder
    response_view = engine.view(room, room.players[responder])
    assert response_view["pendingAction"]["targetCardIndex"] == 0
    assert response_view["currentPrompt"] == {
        "kind": "equipment_response",
        "title": (
            f"{room.players[actor].name}宣布调查"
            f"{room.players[target].name}的第1张底细"
        ),
        "detail": f"等待{room.players[responder].name}决定是否使用装备。",
        "decisionPlayerId": room.players[responder].id,
        "isMyDecision": True,
        "actorPlayerId": room.players[actor].id,
        "targetPlayerId": room.players[target].id,
        "targetCardIndex": 0,
        "sourceCardId": None,
    }

    engine.act(room, room.players[responder], "resign", {})

    assert state.pending_action is None
    assert state.action_done is True
    assert state.boards[target].cards[0].id in state.knowledge[actor]
    assert any(
        entry["text"]
        == f"{room.players[actor].name}调查了{room.players[target].name}的第1张底细"
        for entry in state.history
    )


def test_restraining_order_redirects_and_completes_the_original_shot() -> None:
    engine, room = make_room()
    state = room.state
    state.boards[0].gun = True
    state.boards[0].aim_seat = 1
    state.acquired_gun_turn[0] = 0
    state.boards[1].equipment = ["restraining_order"]

    engine.act(room, room.players[0], "shoot", {})
    engine.act(
        room,
        room.players[1],
        "play_equipment",
        {"cardId": "restraining_order", "targetSeat": 2},
    )

    assert state.boards[0].gun is False
    assert all(card.revealed for card in state.boards[2].cards)
    assert all(not card.revealed for card in state.boards[1].cards)


def test_classified_orders_redirects_then_reopens_the_response_window() -> None:
    engine, room = make_room()
    state = room.state
    state.boards[0].gun = True
    state.boards[0].aim_seat = 1
    state.acquired_gun_turn[0] = 0
    state.boards[1].equipment = ["classified_orders"]
    state.boards[3].equipment = ["helmet"]

    engine.act(room, room.players[0], "shoot", {})
    engine.act(
        room,
        room.players[1],
        "play_equipment",
        {"cardId": "classified_orders", "deciderSeat": 2},
    )
    assert state.choice is not None
    assert state.choice.kind == "classified_redirect"
    assert state.choice.seat == 2
    assert state.choice.shooter_seat == 0
    assert state.choice.resume_pending_after_seat == 1
    decider_prompt = engine.view(room, room.players[2])["currentPrompt"]
    assert decider_prompt["title"] == f"{room.players[1].name}使用了机密指令"
    assert decider_prompt["detail"] == (
        f"由{room.players[2].name}替{room.players[0].name}选择新的射击目标。"
    )
    assert decider_prompt["isMyDecision"] is True
    assert decider_prompt["sourceCardId"] == "classified_orders"
    assert engine.view(room, room.players[3])["currentPrompt"]["isMyDecision"] is False
    engine.act(room, room.players[2], "choose_redirect", {"targetSeat": 3})

    assert state.pending_action is not None
    assert engine._response_seat(state.pending_action) == 3
    assert all(not card.revealed for card in state.boards[3].cards)
    engine.act(room, room.players[3], "pass_response", {})

    assert state.pending_action is None
    assert all(card.revealed for card in state.boards[3].cards)


def test_resigning_classified_orders_decider_resumes_original_shot() -> None:
    engine, room = make_room()
    state = room.state
    ordinary = [
        seat for seat, board in state.boards.items() if engine._leader_card(board) is None
    ]
    decider = ordinary[0]
    shooter = next(seat for seat in state.boards if seat != decider)
    responder = next(seat for seat in state.boards if seat not in {shooter, decider})
    state.turn_seat = shooter
    state.boards[shooter].gun = True
    state.boards[shooter].aim_seat = responder
    state.acquired_gun_turn[shooter] = 0
    state.boards[responder].equipment = ["classified_orders"]

    engine.act(room, room.players[shooter], "shoot", {})
    engine.act(
        room,
        room.players[responder],
        "play_equipment",
        {"cardId": "classified_orders", "deciderSeat": decider},
    )
    assert state.choice and state.choice.seat == decider

    engine.act(room, room.players[decider], "resign", {})

    assert state.choice is None
    assert state.pending_action is None
    assert all(card.revealed for card in state.boards[responder].cards)


def test_surveillance_camera_triggers_only_after_a_normal_investigation() -> None:
    engine, room = make_room()
    state = room.state
    state.boards[1].equipment = ["surveillance_camera"]
    engine.act(
        room,
        room.players[0],
        "investigate",
        {"targetSeat": 2, "cardIndex": 0},
    )
    engine.act(
        room,
        room.players[1],
        "play_equipment",
        {"cardId": "surveillance_camera"},
    )
    assert state.boards[2].cards[0].revealed is True

    state.boards[0].effects.append("key")
    state.boards[1].equipment = ["surveillance_camera"]
    engine.act(
        room,
        room.players[0],
        "extra_investigate",
        {"targetSeat": 2, "cardIndex": 1},
    )
    with pytest.raises(GameRuleError, match="使用时机"):
        engine.act(
            room,
            room.players[1],
            "play_equipment",
            {"cardId": "surveillance_camera"},
        )


def test_coffee_inserts_a_full_turn_then_resumes_the_original_order() -> None:
    engine, room = make_room()
    state = room.state
    state.boards[2].equipment = ["coffee"]
    engine.act(
        room,
        room.players[2],
        "play_equipment",
        {"cardId": "coffee"},
    )
    assert state.history[-1]["text"] == (
        f"{room.players[2].name}使用了咖啡，将在"
        f"{room.players[0].name}回合结束后获得额外回合"
    )
    engine.act(
        room,
        room.players[0],
        "investigate",
        {"targetSeat": 1, "cardIndex": 0},
    )
    engine.act(room, room.players[0], "end_turn", {})
    assert state.turn_seat == 2

    engine.act(
        room,
        room.players[2],
        "investigate",
        {"targetSeat": 1, "cardIndex": 1},
    )
    engine.act(room, room.players[2], "end_turn", {})
    assert state.turn_seat == 1


def test_coffee_gives_the_natural_successor_an_extra_turn() -> None:
    engine, room = make_room()
    state = room.state
    state.boards[1].equipment = ["coffee"]

    engine.act(
        room,
        room.players[1],
        "play_equipment",
        {"cardId": "coffee"},
    )
    state.action_done = True
    engine.act(room, room.players[0], "end_turn", {})
    assert state.turn_seat == 1

    state.action_done = True
    engine.act(room, room.players[1], "end_turn", {})
    assert state.turn_seat == 1


def test_coffee_resumption_uses_current_direction_and_skips_eliminated_players() -> None:
    engine, room = make_room(5)
    state = room.state
    state.boards[2].equipment = ["coffee"]

    engine.act(
        room,
        room.players[2],
        "play_equipment",
        {"cardId": "coffee"},
    )
    state.action_done = True
    engine.act(room, room.players[0], "end_turn", {})
    assert state.turn_seat == 2

    state.direction = -1
    state.boards[4].alive = False
    state.action_done = True
    engine.act(room, room.players[2], "end_turn", {})
    assert state.turn_seat == 3


def test_coffee_turn_is_skipped_if_its_user_is_eliminated_before_it_starts() -> None:
    engine, room = make_room()
    state = room.state
    state.boards[2].equipment = ["coffee"]

    engine.act(
        room,
        room.players[2],
        "play_equipment",
        {"cardId": "coffee"},
    )
    state.boards[2].alive = False
    state.action_done = True
    engine.act(room, room.players[0], "end_turn", {})

    assert state.turn_seat == 1
    assert state.extra_turns.resume_after_seat is None


def test_restored_coffee_queue_is_migrated_to_the_extra_turn_schedule() -> None:
    engine, room = make_room()
    state = room.state
    del state.extra_turns
    state.coffee_after = [2]  # type: ignore[attr-defined]
    state.choice = {  # type: ignore[assignment]
        "kind": "classified_redirect",
        "seat": 1,
        "shooterSeat": 0,
        "resumePendingAfterSeat": 2,
    }

    engine.repair_restored_room(room)

    assert state.extra_turns.pending_seats == [2]
    assert state.extra_turns.resume_after_seat is None
    assert state.choice is not None
    assert state.choice.kind == "classified_redirect"
    assert state.choice.seat == 1
    assert state.choice.shooter_seat == 0
    assert state.choice.resume_pending_after_seat == 2
    assert state.choice.source_card_id is None


def test_evidence_bag_prompts_the_recipient_to_keep_one_card() -> None:
    engine, room = make_room()
    state = room.state
    state.boards[0].equipment = ["evidence_bag"]
    state.boards[1].equipment = ["k9_unit"]
    state.boards[2].equipment = ["coffee"]

    engine.act(
        room,
        room.players[0],
        "play_equipment",
        {"cardId": "evidence_bag", "ownerSeat": 1, "recipientSeat": 2},
    )
    assert state.choice and state.choice.kind == "equipment_limit"
    assert state.choice.seat == 2
    recipient_view = engine.view(room, room.players[2])
    assert recipient_view["choice"]["kind"] == "equipment_limit"
    assert len(recipient_view["choice"]["cards"]) == 2
    assert engine.view(room, room.players[1])["choice"] is None
    engine.act(room, room.players[2], "choose_equipment", {"cardId": "k9_unit"})

    assert state.boards[2].equipment == ["k9_unit"]
    assert "coffee" in state.equipment_deck


def test_resigning_equipment_limit_player_clears_the_forced_choice() -> None:
    engine, room = make_room()
    state = room.state
    actor = state.turn_seat
    recipient = next(
        seat
        for seat, board in state.boards.items()
        if seat != actor and engine._leader_card(board) is None
    )
    owner = next(seat for seat in state.boards if seat not in {actor, recipient})
    state.boards[actor].equipment = ["evidence_bag"]
    state.boards[owner].equipment = ["k9_unit"]
    state.boards[recipient].equipment = ["coffee"]

    engine.act(
        room,
        room.players[actor],
        "play_equipment",
        {
            "cardId": "evidence_bag",
            "ownerSeat": owner,
            "recipientSeat": recipient,
        },
    )
    assert state.choice and state.choice.seat == recipient

    engine.act(room, room.players[recipient], "resign", {})

    assert state.choice is None
    assert state.boards[recipient].equipment == []
    assert engine.view(room, room.players[actor])["legal"]["canTakeNormalAction"] is True


def test_report_audit_requires_each_player_to_choose_their_own_card() -> None:
    engine, room = make_room()
    state = room.state
    state.boards[0].equipment = ["report_audit"]
    engine.act(
        room,
        room.players[0],
        "play_equipment",
        {"cardId": "report_audit"},
    )

    for seat in range(4):
        assert state.choice and state.choice.seat == seat
        engine.act(room, room.players[seat], "choose_reveal", {"cardIndex": 0})

    assert state.choice is None
    assert all(board.cards[0].revealed for board in state.boards.values())


def test_report_audit_skips_a_queued_player_who_resigns() -> None:
    engine, room = make_room()
    state = room.state
    actor = state.turn_seat
    departing = next(
        seat
        for seat, board in state.boards.items()
        if seat != actor and engine._leader_card(board) is None
    )
    state.boards[actor].equipment = ["report_audit"]
    engine.act(
        room,
        room.players[actor],
        "play_equipment",
        {"cardId": "report_audit"},
    )

    engine.act(room, room.players[departing], "resign", {})

    selected: list[int] = []
    while state.choice is not None:
        seat = state.choice.seat
        selected.append(seat)
        card_index = next(
            index
            for index, card in enumerate(state.boards[seat].cards)
            if not card.revealed
        )
        engine.act(
            room,
            room.players[seat],
            "choose_reveal",
            {"cardIndex": card_index},
        )

    assert departing not in selected


def test_thumbprint_scanner_can_transfer_a_leader_before_damage() -> None:
    engine, room = make_room()
    state = room.state
    agent_seat, agent_index = leader_owner(room, "agent")
    target = next(
        seat for seat, board in state.boards.items() if engine._leader_card(board) is None
    )
    shooter = next(seat for seat in state.boards if seat not in {agent_seat, target})
    state.turn_seat = shooter
    state.boards[shooter].gun = True
    state.boards[shooter].aim_seat = target
    state.acquired_gun_turn[shooter] = 0
    state.boards[agent_seat].equipment = ["thumbprint_scanner"]
    target_index = normal_card_index(room, target)
    state.equipment_deck = ["coffee"]

    engine.act(room, room.players[shooter], "shoot", {})
    assert state.pending_shot and state.pending_shot.scanner_seat == agent_seat
    engine.act(
        room,
        room.players[agent_seat],
        "use_scanner",
        {"ownCardIndex": agent_index, "targetCardIndex": target_index},
    )

    moved_agent = state.boards[target].cards[target_index]
    assert moved_agent.kind == "agent"
    assert moved_agent.wounded is True
    assert state.boards[target].alive is True


def test_resigning_thumbprint_scanner_owner_does_not_stall_damage() -> None:
    engine, room = make_room()
    state = room.state
    scanner = next(
        seat for seat, board in state.boards.items() if engine._leader_card(board) is None
    )
    target, _ = leader_owner(room, "agent")
    shooter = next(seat for seat in state.boards if seat not in {scanner, target})
    state.turn_seat = shooter
    state.boards[shooter].gun = True
    state.boards[shooter].aim_seat = target
    state.acquired_gun_turn[shooter] = 0
    state.boards[scanner].equipment = ["thumbprint_scanner"]

    engine.act(room, room.players[shooter], "shoot", {})
    assert state.pending_shot and state.pending_shot.scanner_seat == scanner

    engine.act(room, room.players[scanner], "resign", {})

    assert state.pending_shot is None
    leader = engine._leader_card(state.boards[target])
    assert leader is not None and leader.wounded is True


def test_mobile_detonator_chains_after_a_nonwinning_shot() -> None:
    engine, room = make_room()
    state = room.state
    ordinary = [
        seat for seat, board in state.boards.items() if engine._leader_card(board) is None
    ]
    target, chained_target = ordinary
    shooter = next(seat for seat in state.boards if seat not in ordinary)
    state.turn_seat = shooter
    state.boards[shooter].gun = True
    state.boards[shooter].aim_seat = target
    state.acquired_gun_turn[shooter] = 0
    state.boards[target].equipment = ["mobile_detonator"]

    engine.act(room, room.players[shooter], "shoot", {})
    assert state.post_shot and state.post_shot["seat"] == target
    engine.act(
        room,
        room.players[target],
        "use_mobile_detonator",
        {"targetSeat": chained_target},
    )

    assert state.boards[target].alive is False
    assert state.boards[chained_target].alive is False


def test_disconnected_eliminated_detonator_owner_is_auto_passed() -> None:
    engine, room = make_room()
    state = room.state
    target = next(
        seat for seat, board in state.boards.items() if engine._leader_card(board) is None
    )
    shooter = next(seat for seat in state.boards if seat != target)
    state.turn_seat = shooter
    state.boards[shooter].gun = True
    state.boards[shooter].aim_seat = target
    state.acquired_gun_turn[shooter] = 0
    state.boards[target].equipment = ["mobile_detonator"]

    engine.act(room, room.players[shooter], "shoot", {})
    assert state.boards[target].alive is False
    assert state.post_shot and state.post_shot["seat"] == target

    engine.disconnect_timeout(room, room.players[target])

    assert state.post_shot is None
    assert state.boards[target].equipment == []
    assert "mobile_detonator" in state.equipment_deck


@pytest.mark.parametrize("player_count", range(4, 9))
def test_automated_games_finish_without_wait_state_deadlocks(
    player_count: int,
) -> None:
    for seed in range(30):
        engine, room = make_room(player_count, seed=seed)

        for _ in range(1_000):
            if room.phase == "finished":
                break
            state = room.state
            if state.pending_action is not None:
                responder = engine._response_seat(state.pending_action)
                assert responder is not None
                engine.act(room, room.players[responder], "pass_response", {})
                continue
            if state.pending_shot is not None:
                scanner = state.pending_shot.scanner_seat
                assert scanner is not None
                engine.act(room, room.players[scanner], "pass_scanner", {})
                continue
            if state.post_shot is not None:
                decision_seat = int(state.post_shot["seat"])
                engine.act(
                    room,
                    room.players[decision_seat],
                    "pass_mobile_detonator",
                    {},
                )
                continue
            if state.choice is not None:
                choice = state.choice
                choice_seat = choice.seat
                kind = choice.kind
                if kind == "equipment_limit":
                    engine.act(
                        room,
                        room.players[choice_seat],
                        "choose_equipment",
                        {"cardId": state.boards[choice_seat].equipment[0]},
                    )
                elif kind in {"report_audit", "truth_serum"}:
                    card_index = next(
                        index
                        for index, card in enumerate(state.boards[choice_seat].cards)
                        if not card.revealed
                    )
                    engine.act(
                        room,
                        room.players[choice_seat],
                        "choose_reveal",
                        {"cardIndex": card_index},
                    )
                elif kind == "inspection_gloves":
                    decision = (
                        "discard_equipment"
                        if state.boards[choice_seat].equipment
                        else "show_integrity"
                    )
                    engine.act(
                        room,
                        room.players[choice_seat],
                        "inspection_choice",
                        {"choice": decision},
                    )
                elif kind == "classified_redirect":
                    assert choice.shooter_seat is not None
                    shooter = choice.shooter_seat
                    target = next(
                        seat
                        for seat, board in state.boards.items()
                        if seat != shooter and board.alive
                    )
                    engine.act(
                        room,
                        room.players[choice_seat],
                        "choose_redirect",
                        {"targetSeat": target},
                    )
                else:
                    target = next(
                        seat
                        for seat, board in state.boards.items()
                        if seat != choice_seat
                        and board.alive
                        and not board.grenade_stage
                    )
                    engine.act(
                        room,
                        room.players[choice_seat],
                        "pass_grenade",
                        {"targetSeat": target},
                    )
                continue

            seat = state.turn_seat
            player = room.players[seat]
            if state.action_done:
                engine.act(room, player, "end_turn", {})
                continue
            action_ids = engine.view(room, player)["legal"]["normalActionIds"]
            if "shoot" in action_ids:
                engine.act(room, player, "shoot", {})
            elif "arm" in action_ids:
                target = next(
                    (
                        target
                        for target, board in state.boards.items()
                        if target != seat
                        and board.alive
                        and engine._leader_card(board) is not None
                    ),
                    next(
                        target
                        for target, board in state.boards.items()
                        if target != seat and board.alive
                    ),
                )
                payload: dict[str, int] = {"targetSeat": target}
                hidden = [
                    index
                    for index, card in enumerate(state.boards[seat].cards)
                    if not card.revealed
                ]
                if hidden:
                    payload["cardIndex"] = hidden[0]
                engine.act(room, player, "arm", payload)
            elif "equip" in action_ids:
                hidden = [
                    index
                    for index, card in enumerate(state.boards[seat].cards)
                    if not card.revealed
                ]
                payload = {"cardIndex": hidden[0]} if hidden else {}
                engine.act(room, player, "equip", payload)
            elif "investigate" in action_ids:
                target = next(
                    target
                    for target in engine._investigation_target_seats(state, seat)
                )
                card_index = next(
                    index
                    for index, card in enumerate(state.boards[target].cards)
                    if not card.revealed
                )
                engine.act(
                    room,
                    player,
                    "investigate",
                    {"targetSeat": target, "cardIndex": card_index},
                )
            else:
                engine.act(room, player, "pass_turn", {})

        assert room.phase == "finished", (
            f"{player_count}人局 seed={seed} 在等待状态中未能结束"
        )
