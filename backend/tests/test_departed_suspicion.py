from __future__ import annotations

import random

import pytest

from backend.app.arcade.models import ArcadePlayer, ArcadeRoom
from backend.app.games.base import GameRuleError
from backend.app.games.departed_suspicion.cards import (
    EQUIPMENT_CARDS,
    EXPANDED_EQUIPMENT_IDS,
)
from backend.app.games.departed_suspicion.engine import DepartedSuspicionEngine


def make_room(
    player_count: int = 4,
    *,
    equipment_set: str = "expanded",
    seed: int = 7,
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


def test_catalog_keeps_all_33_cards_and_excludes_only_cover_card_from_deck() -> None:
    assert len(EQUIPMENT_CARDS) == 33
    assert len({card.id for card in EQUIPMENT_CARDS}) == 33
    assert len(EXPANDED_EQUIPMENT_IDS) == 32
    assert "new_assignment" not in EXPANDED_EQUIPMENT_IDS


@pytest.mark.parametrize("player_count", range(4, 9))
def test_setup_deals_three_cards_and_separates_leaders(player_count: int) -> None:
    _, room = make_room(player_count, seed=player_count)

    assert all(len(board.cards) == 3 for board in room.state.boards.values())
    agent_seat, _ = leader_owner(room, "agent")
    kingpin_seat, _ = leader_owner(room, "kingpin")
    assert agent_seat != kingpin_seat
    assert room.state.gun_total == (2 if player_count == 4 else 3 if player_count <= 6 else 4)
    assert all(not board.equipment for board in room.state.boards.values())


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
    assert all(card["kind"] is not None for card in self_board["cards"])


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
    assert bystander_view["players"][1]["cards"][0]["kind"] is None


def test_equip_reveals_a_card_and_draws_without_starting_equipment() -> None:
    engine, room = make_room(equipment_set="base")
    first_equipment = room.state.equipment_deck[0]

    engine.act(room, room.players[0], "equip", {"cardIndex": 0})

    assert room.state.boards[0].cards[0].revealed is True
    assert room.state.boards[0].equipment == [first_equipment]
    assert room.state.action_done is True


@pytest.mark.parametrize("action", ["equip", "arm"])
def test_fully_revealed_player_can_equip_or_arm(action: str) -> None:
    engine, room = make_room(equipment_set="base")
    board = room.state.boards[0]
    for card in board.cards:
        card.revealed = True

    payload = {"targetSeat": 1} if action == "arm" else {}
    engine.act(room, room.players[0], action, payload)

    assert room.state.action_done is True
    if action == "arm":
        assert board.gun is True
        assert board.aim_seat == 1
    else:
        assert len(board.equipment) == 1


@pytest.mark.parametrize("action", ["equip", "arm"])
def test_hidden_card_is_still_required_as_cost_when_available(action: str) -> None:
    engine, room = make_room(equipment_set="base")
    payload = {"targetSeat": 1} if action == "arm" else {}

    with pytest.raises(GameRuleError, match="底细牌"):
        engine.act(room, room.players[0], action, payload)


def test_crutches_revives_an_all_revealed_player_who_can_still_equip() -> None:
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
    assert view["legal"]["normalActionIds"] == ["equip"]
    assert view["legal"]["canTakeExtraInvestigation"] is False

    with pytest.raises(GameRuleError, match="只能执行获取装备"):
        engine.act(room, room.players[target], "investigate", {})
    with pytest.raises(GameRuleError, match="只能执行获取装备"):
        engine.act(room, room.players[target], "extra_investigate", {})

    state.equipment_deck = ["coffee"]
    engine.act(room, room.players[target], "equip", {})

    assert state.action_done is True
    assert revived.equipment == ["coffee"]


@pytest.mark.parametrize("player_count", range(4, 9))
def test_every_fully_revealed_player_can_finish_repeated_turns(
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
        assert "equip" in view["legal"]["normalActionIds"]

        engine.act(room, room.players[seat], "equip", {})
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

    assert view["legal"]["normalActionIds"] == ["equip"]
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
    assert state.choice and state.choice["kind"] == "grenade_pass"
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
    assert state.choice and state.choice["kind"] == "grenade_pass"

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

    engine.act(room, room.players[responder], "resign", {})

    assert state.pending_action is None
    assert state.action_done is True
    assert state.boards[target].cards[0].id in state.knowledge[actor]


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


def test_classified_orders_lets_the_selected_player_redirect_immediately() -> None:
    engine, room = make_room()
    state = room.state
    state.boards[0].gun = True
    state.boards[0].aim_seat = 1
    state.acquired_gun_turn[0] = 0
    state.boards[1].equipment = ["classified_orders"]

    engine.act(room, room.players[0], "shoot", {})
    engine.act(
        room,
        room.players[1],
        "play_equipment",
        {"cardId": "classified_orders", "deciderSeat": 2},
    )
    assert state.choice == {
        "kind": "classified_redirect",
        "seat": 2,
        "shooterSeat": 0,
        "resumePendingAfterSeat": 1,
    }
    engine.act(room, room.players[2], "choose_redirect", {"targetSeat": 3})

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
    assert state.choice and state.choice["seat"] == decider

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


def test_coffee_inserts_a_full_turn_then_continues_after_the_user() -> None:
    engine, room = make_room()
    state = room.state
    state.boards[2].equipment = ["coffee"]
    engine.act(
        room,
        room.players[2],
        "play_equipment",
        {"cardId": "coffee"},
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
    assert state.turn_seat == 3


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
    assert state.choice and state.choice["kind"] == "equipment_limit"
    assert state.choice["seat"] == 2
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
    assert state.choice and state.choice["seat"] == recipient

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
        assert state.choice and state.choice["seat"] == seat
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
        seat = int(state.choice["seat"])
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
                choice_seat = int(choice["seat"])
                kind = choice["kind"]
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
                    shooter = int(choice["shooterSeat"])
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
                    target
                    for target, board in state.boards.items()
                    if target != seat and board.alive
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
            else:
                hidden = [
                    index
                    for index, card in enumerate(state.boards[seat].cards)
                    if not card.revealed
                ]
                payload = {"cardIndex": hidden[0]} if hidden else {}
                engine.act(room, player, "equip", payload)

        assert room.phase == "finished", (
            f"{player_count}人局 seed={seed} 在等待状态中未能结束"
        )
