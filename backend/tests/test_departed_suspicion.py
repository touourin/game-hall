from __future__ import annotations

import json
import random
from collections import Counter
from typing import Any

import pytest

from backend.app.arcade.models import ArcadePlayer, ArcadeRoom
from backend.app.games.base import GameRuleError
from backend.app.games.departed_suspicion.cards import (
    BOMBERS_EQUIPMENT_IDS,
    EQUIPMENT_CARDS,
)
from backend.app.games.departed_suspicion.engine import (
    DepartedSuspicionEngine,
    PendingAction,
    PendingShot,
)


def make_room(
    player_count: int = 4,
    *,
    equipment_set: str = "bombers",
    seed: int = 7,
    deal_starting_equipment: bool = False,
    first_player: str = "host",
    host_seat: int = 0,
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
        host_id=players[host_seat].id,
        players=players,
        state=engine.initial_state(),
        options={
            "equipmentSet": equipment_set,
            "firstPlayer": first_player,
        },
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


def test_undercover_equipment_is_marked_unavailable_in_current_game_modes() -> None:
    engine, room = make_room()
    view = engine.view(room, room.players[0])
    catalog = {card["id"]: card for card in view["equipmentCatalog"]}

    undercover_ids = {
        card.id for card in EQUIPMENT_CARDS if card.expansion == "undercover"
    }
    assert len(undercover_ids) == 12
    for card_id in undercover_ids:
        assert catalog[card_id]["available"] is False
        assert card_id not in room.state.equipment_deck


def test_new_assignment_explicitly_rejects_play_without_undercover_cards() -> None:
    engine, room = make_room()
    room.state.boards[0].equipment = ["new_assignment"]

    with pytest.raises(GameRuleError, match="卧底牌能力尚未启用"):
        engine.act(
            room,
            room.players[0],
            "play_equipment",
            {"cardId": "new_assignment"},
        )

    assert room.state.boards[0].equipment == ["new_assignment"]


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


def test_start_honors_host_and_random_first_player_options() -> None:
    _, host_room = make_room(first_player="host", host_seat=2)
    assert host_room.state.turn_seat == host_room.players[2].seat

    random_starts = {
        make_room(seed=seed, first_player="random")[1].state.turn_seat
        for seed in range(20)
    }
    assert random_starts == set(range(4))


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


def test_security_wand_can_optionally_rehide_one_of_its_users_public_cards() -> None:
    engine, room = make_room()
    state = room.state
    actor = 0
    target = 1
    own_card_index = 0
    target_card_index = 1
    own_card = state.boards[actor].cards[own_card_index]
    target_card = state.boards[target].cards[target_card_index]
    own_card.revealed = True
    state.boards[actor].equipment = ["security_wand"]

    engine.act(
        room,
        room.players[actor],
        "play_equipment",
        {
            "cardId": "security_wand",
            "targetSeat": target,
            "cardIndex": target_card_index,
            "ownCardIndex": own_card_index,
        },
    )

    assert target_card.id in state.knowledge[actor]
    assert own_card.revealed is False
    assert all(own_card.id in known for known in state.knowledge.values())


def test_security_wand_omits_the_optional_field_when_user_has_no_public_card() -> None:
    engine, room = make_room()
    room.state.boards[0].equipment = ["security_wand"]

    option = next(
        item
        for item in engine.view(room, room.players[0])["legal"]["equipmentOptions"]
        if item["cardId"] == "security_wand"
    )

    assert [field["key"] for field in option["fields"]] == [
        "targetSeat",
        "cardIndex",
    ]


def test_sunglasses_can_rehide_two_public_cards_from_the_same_player() -> None:
    engine, room = make_room()
    state = room.state
    actor = 0
    target = 1
    first_card = state.boards[target].cards[0]
    second_card = state.boards[target].cards[1]
    first_card.revealed = True
    second_card.revealed = True
    state.boards[actor].equipment = ["sunglasses"]

    engine.act(
        room,
        room.players[actor],
        "play_equipment",
        {
            "cardId": "sunglasses",
            "firstSeat": target,
            "firstCardIndex": 0,
            "secondSeat": target,
            "secondCardIndex": 1,
        },
    )

    assert first_card.revealed is False
    assert second_card.revealed is False
    for known in state.knowledge.values():
        assert {first_card.id, second_card.id} <= known


def test_wiretap_skips_only_the_disguised_half_of_its_effect() -> None:
    engine, room = make_room()
    state = room.state
    actor, visible_target, disguised_target = 0, 1, 2
    state.boards[actor].equipment = ["wiretap"]
    for seat in (actor, 3):
        for card in state.boards[seat].cards:
            card.revealed = True
    state.boards[disguised_target].effects.append("disguise")

    assert "wiretap" in engine.view(room, room.players[actor])["legal"][
        "playableEquipmentIds"
    ]
    engine.act(
        room,
        room.players[actor],
        "play_equipment",
        {
            "cardId": "wiretap",
            "firstSeat": visible_target,
            "firstCardIndex": 0,
            "secondSeat": disguised_target,
            "secondCardIndex": 1,
        },
    )

    assert state.boards[visible_target].cards[0].id in state.knowledge[actor]
    assert state.boards[disguised_target].cards[1].id not in state.knowledge[actor]


def test_fingerprint_kit_can_target_its_user_and_return_to_their_hand() -> None:
    engine, room = make_room()
    state = room.state
    actor = state.turn_seat
    state.boards[actor].equipment = ["fingerprint_kit"]

    option = next(
        item
        for item in engine.view(room, room.players[actor])["legal"]["equipmentOptions"]
        if item["cardId"] == "fingerprint_kit"
    )
    target_field = next(field for field in option["fields"] if field["key"] == "targetSeat")
    assert actor in {item["value"] for item in target_field["options"]}

    engine.act(
        room,
        room.players[actor],
        "play_equipment",
        {
            "cardId": "fingerprint_kit",
            "targetSeat": actor,
            "cardIndex": 0,
            "returnToHand": True,
            "ownCardIndex": 1,
        },
    )

    assert state.boards[actor].cards[1].revealed is True
    assert state.boards[actor].equipment == ["fingerprint_kit"]


def test_fake_id_swaps_public_ordinary_cards_and_keeps_them_public() -> None:
    engine, room = make_room()
    state = room.state
    locations = [
        (seat, index)
        for seat, board in state.boards.items()
        for index, card in enumerate(board.cards)
        if card.kind in {"honest", "crooked"}
    ]
    first = locations[0]
    second = next(location for location in locations if location[0] != first[0])
    first_card = state.boards[first[0]].cards[first[1]]
    second_card = state.boards[second[0]].cards[second[1]]
    first_card.revealed = True
    second_card.revealed = True
    actor = state.turn_seat
    state.boards[actor].equipment = ["fake_id"]

    engine.act(
        room,
        room.players[actor],
        "play_equipment",
        {
            "cardId": "fake_id",
            "firstSeat": first[0],
            "firstCardIndex": first[1],
            "secondSeat": second[0],
            "secondCardIndex": second[1],
        },
    )

    assert state.boards[first[0]].cards[first[1]] is second_card
    assert state.boards[second[0]].cards[second[1]] is first_card
    assert first_card.revealed is True
    assert second_card.revealed is True


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


def test_polygraph_keeps_both_results_private_and_applies_disguise_per_target() -> None:
    engine, room = make_room()
    actor, target, bystander = 0, 1, 2
    state = room.state
    state.boards[actor].equipment = ["polygraph"]
    state.boards[target].effects.append("disguise")

    engine.act(
        room,
        room.players[actor],
        "play_equipment",
        {"cardId": "polygraph", "targetSeat": target},
    )

    actor_view = engine.view(room, room.players[actor])
    target_view = engine.view(room, room.players[target])
    bystander_view = engine.view(room, room.players[bystander])
    assert all(
        card["knowledge"] == "hidden"
        for card in actor_view["players"][target]["cards"]
    )
    assert all(
        card["knowledge"] == "known"
        for card in target_view["players"][actor]["cards"]
    )
    assert all(
        card["kind"] is None
        for seat in (actor, target)
        for card in bystander_view["players"][seat]["cards"]
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


def test_inspection_gloves_can_make_the_target_discard_their_equipment() -> None:
    engine, room = make_room()
    state = room.state
    state.boards[0].equipment = ["inspection_gloves"]
    state.boards[1].equipment = ["coffee"]

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
        {"choice": "discard_equipment"},
    )

    assert state.choice is None
    assert state.boards[1].equipment == []
    assert {"inspection_gloves", "coffee"} <= set(state.equipment_deck)


def test_inspection_gloves_self_target_only_offers_choices_left_after_playing_it() -> None:
    engine, room = make_room()
    state = room.state
    state.boards[0].equipment = ["inspection_gloves"]

    option = next(
        item
        for item in engine.view(room, room.players[0])["legal"]["equipmentOptions"]
        if item["cardId"] == "inspection_gloves"
    )
    target_field = next(field for field in option["fields"] if field["key"] == "targetSeat")
    assert 0 in {item["value"] for item in target_field["options"]}

    engine.act(
        room,
        room.players[0],
        "play_equipment",
        {"cardId": "inspection_gloves", "targetSeat": 0},
    )

    assert state.choice and state.choice.kind == "inspection_gloves"
    assert state.boards[0].equipment == []
    with pytest.raises(GameRuleError, match="当前不能执行"):
        engine.act(
            room,
            room.players[0],
            "inspection_choice",
            {"choice": "discard_equipment"},
        )

    engine.act(
        room,
        room.players[0],
        "inspection_choice",
        {"choice": "show_integrity"},
    )
    assert state.choice is None


@pytest.mark.parametrize("extra_first", [True, False])
def test_key_extra_investigation_works_before_or_after_the_normal_action(
    extra_first: bool,
) -> None:
    engine, room = make_room()
    state = room.state
    owner = 0
    recipient = 1
    investigation_target = 2
    state.boards[owner].equipment = ["key"]

    engine.act(
        room,
        room.players[owner],
        "play_equipment",
        {"cardId": "key", "targetSeat": recipient},
    )

    assert "key" in state.boards[recipient].effects
    assert "key" not in state.equipment_deck
    state.turn_seat = recipient
    state.equipment_deck = ["coffee"]
    own_card_index = next(
        index
        for index, card in enumerate(state.boards[recipient].cards)
        if not card.revealed
    )
    target_card_index = next(
        index
        for index, card in enumerate(state.boards[investigation_target].cards)
        if not card.revealed
    )

    def investigate() -> None:
        engine.act(
            room,
            room.players[recipient],
            "extra_investigate",
            {
                "targetSeat": investigation_target,
                "cardIndex": target_card_index,
            },
        )

    def equip() -> None:
        engine.act(
            room,
            room.players[recipient],
            "equip",
            {"cardIndex": own_card_index},
        )

    if extra_first:
        investigate()
        assert state.extra_investigation_done is True
        assert state.action_done is False
        equip()
    else:
        equip()
        assert state.action_done is True
        assert state.extra_investigation_done is False
        investigate()

    assert state.action_done is True
    assert state.extra_investigation_done is True


def test_key_extra_investigation_remains_blocked_by_disguise() -> None:
    engine, room = make_room()
    state = room.state
    state.boards[0].effects.append("key")
    for target in range(1, len(state.boards)):
        state.boards[target].effects.append("disguise")

    view = engine.view(room, room.players[0])
    assert view["legal"]["canTakeExtraInvestigation"] is False
    with pytest.raises(GameRuleError, match="伪装"):
        engine.act(
            room,
            room.players[0],
            "extra_investigate",
            {"targetSeat": 1, "cardIndex": 0},
        )


def test_med_kit_only_heals_a_wounded_leader() -> None:
    engine, room = make_room()
    state = room.state
    target, _ = leader_owner(room, "agent")
    actor = next(seat for seat in state.boards if seat != target)
    leader = engine._leader_card(state.boards[target])
    assert leader is not None
    leader.wounded = True
    state.boards[actor].equipment = ["med_kit"]

    engine.act(
        room,
        room.players[actor],
        "play_equipment",
        {"cardId": "med_kit", "targetSeat": target},
    )

    assert leader.wounded is False
    assert "med_kit" in state.equipment_deck
    state.boards[actor].equipment = ["med_kit"]
    assert "med_kit" not in engine.view(room, room.players[actor])["legal"][
        "playableEquipmentIds"
    ]


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
    actor_view = engine.view(room, room.players[0])
    bystander_view = engine.view(room, room.players[3])
    for target, card_index in ((1, 1), (2, 2)):
        actor_card = actor_view["players"][target]["cards"][card_index]
        bystander_card = bystander_view["players"][target]["cards"][card_index]
        assert actor_card["knowledge"] == "known"
        assert bystander_card["kind"] is None


def test_metal_detector_is_not_advertised_without_an_eligible_armed_player() -> None:
    engine, room = make_room()
    room.state.boards[0].equipment = ["metal_detector"]

    assert "metal_detector" not in engine.view(room, room.players[0])["legal"][
        "playableEquipmentIds"
    ]


def test_metal_detector_includes_its_user_when_the_user_is_armed() -> None:
    engine, room = make_room()
    state = room.state
    state.boards[0].equipment = ["metal_detector"]
    state.boards[0].gun = True

    option = next(
        item
        for item in engine.view(room, room.players[0])["legal"]["equipmentOptions"]
        if item["cardId"] == "metal_detector"
    )
    assert [field["key"] for field in option["fields"]] == ["choices.0"]

    engine.act(
        room,
        room.players[0],
        "play_equipment",
        {"cardId": "metal_detector", "choices": {"0": 1}},
    )

    assert state.boards[0].cards[1].id in state.knowledge[0]


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


def test_fully_revealed_player_can_equip_without_revealing_a_card() -> None:
    engine, room = make_room(equipment_set="base")
    board = room.state.boards[0]
    for card in board.cards:
        card.revealed = True
    first_equipment = room.state.equipment_deck[0]

    assert "equip" in engine.view(room, room.players[0])["legal"]["normalActionIds"]
    engine.act(room, room.players[0], "equip", {})

    assert room.state.action_done is True
    assert board.equipment == [first_equipment]
    assert all(card.revealed for card in board.cards)


def test_fully_revealed_player_can_arm_without_revealing_a_card() -> None:
    engine, room = make_room(equipment_set="base")
    board = room.state.boards[0]
    for card in board.cards:
        card.revealed = True

    assert "arm" in engine.view(room, room.players[0])["legal"]["normalActionIds"]
    engine.act(room, room.players[0], "arm", {"targetSeat": 1})

    assert room.state.action_done is True
    assert board.gun is True
    assert board.aim_seat == 1
    assert all(card.revealed for card in board.cards)


@pytest.mark.parametrize("action", ["equip", "arm"])
def test_hidden_card_must_be_chosen_for_equip_or_arm_when_available(
    action: str,
) -> None:
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

    first_equipment = state.equipment_deck[0]
    engine.act(room, room.players[target], "equip", {})

    assert state.action_done is True
    assert revived.equipment == [first_equipment]


def test_defibrillator_does_not_remove_an_existing_crutches_restriction() -> None:
    engine, room = make_room()
    state = room.state
    actor = state.turn_seat
    target = next(
        seat
        for seat, board in state.boards.items()
        if seat != actor and engine._leader_card(board) is None
    )
    engine._eliminate(state, target)
    state.boards[actor].equipment = ["crutches"]
    engine.act(
        room,
        room.players[actor],
        "play_equipment",
        {"cardId": "crutches", "targetSeat": target},
    )
    engine._eliminate(state, target)
    state.boards[actor].equipment = ["defibrillator"]

    engine.act(
        room,
        room.players[actor],
        "play_equipment",
        {"cardId": "defibrillator", "targetSeat": target},
    )

    revived = state.boards[target]
    assert revived.alive is True
    assert "crutches" in revived.effects
    assert revived.restricted_to_equip is True


@pytest.mark.parametrize("player_count", range(4, 9))
def test_every_fully_revealed_player_can_equip_on_repeated_turns(
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
        assert view["legal"]["normalActionIds"] == ["equip", "arm"]

        engine.act(room, room.players[seat], "equip", {})
        assert engine.view(room, room.players[seat])["legal"]["canEndTurn"] is True
        engine.act(room, room.players[seat], "end_turn", {})

    assert state.turn_number == player_count * 5 + 1


def test_fully_revealed_player_without_guns_can_still_equip() -> None:
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
    assert all(card.revealed for card in state.boards[target].cards)

    state.turn_seat = target
    state.action_done = False
    target_view = engine.view(room, room.players[target])
    assert target_view["legal"]["normalActionIds"] == [
        "investigate",
        "equip",
        "arm",
    ]

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


def test_k9_disarming_a_bystander_does_not_cancel_the_declared_shot() -> None:
    engine, room = make_room()
    state = room.state
    shooter, target, armed_bystander, responder = range(4)
    state.turn_seat = shooter
    state.boards[shooter].gun = True
    state.boards[shooter].aim_seat = target
    state.boards[armed_bystander].gun = True
    state.acquired_gun_turn[shooter] = 0
    state.boards[responder].equipment = ["k9_unit"]

    engine.act(room, room.players[shooter], "shoot", {})
    engine.act(
        room,
        room.players[responder],
        "play_equipment",
        {"cardId": "k9_unit", "targetSeat": armed_bystander},
    )

    assert state.boards[armed_bystander].gun is False
    assert state.pending_action is None
    assert state.action_done is True
    assert state.boards[shooter].gun is False
    assert (
        not state.boards[target].alive
        or engine._leader_card(state.boards[target]).wounded is True
    )


def test_k9_can_return_its_armed_users_gun() -> None:
    engine, room = make_room()
    state = room.state
    actor = state.turn_seat
    state.boards[actor].equipment = ["k9_unit"]
    state.boards[actor].gun = True

    engine.act(
        room,
        room.players[actor],
        "play_equipment",
        {"cardId": "k9_unit", "targetSeat": actor},
    )

    assert state.boards[actor].gun is False
    assert "k9_unit" in state.equipment_deck


def test_helmet_cancels_shot_but_consumes_the_shooters_action() -> None:
    engine, room = make_room()
    state = room.state
    state.boards[0].gun = True
    state.boards[0].aim_seat = 1
    state.acquired_gun_turn[0] = 0
    state.boards[1].equipment = ["helmet"]
    state.boards[2].equipment = ["thumbprint_scanner"]

    engine.act(room, room.players[0], "shoot", {})
    engine.act(
        room,
        room.players[1],
        "play_equipment",
        {"cardId": "helmet"},
    )

    assert state.pending_action is None
    assert state.pending_shot is None
    assert state.boards[0].gun is False
    assert state.action_done is True
    assert state.boards[1].alive is True
    assert state.boards[2].equipment == ["thumbprint_scanner"]


def test_concussion_grenade_drops_every_gun_and_cancels_the_declared_shot() -> None:
    engine, room = make_room()
    state = room.state
    shooter, target, second_armed = 0, 1, 2
    state.boards[shooter].gun = True
    state.boards[shooter].aim_seat = target
    state.boards[second_armed].gun = True
    state.boards[second_armed].aim_seat = shooter
    state.acquired_gun_turn[shooter] = 0
    state.boards[target].equipment = ["concussion_grenade"]

    engine.act(room, room.players[shooter], "shoot", {})
    engine.act(
        room,
        room.players[target],
        "play_equipment",
        {"cardId": "concussion_grenade"},
    )

    assert state.pending_action is None
    assert state.action_done is False
    assert all(not board.gun and board.aim_seat is None for board in state.boards.values())


def test_disguise_blocks_investigation_but_not_truth_serum_reveal() -> None:
    engine, room = make_room()
    state = room.state
    actor, target = 0, 1
    state.boards[actor].equipment = ["disguise"]
    engine.act(
        room,
        room.players[actor],
        "play_equipment",
        {"cardId": "disguise", "targetSeat": target},
    )

    with pytest.raises(GameRuleError, match="不能被调查"):
        engine.act(
            room,
            room.players[actor],
            "investigate",
            {"targetSeat": target, "cardIndex": 0},
        )

    state.boards[actor].equipment = ["truth_serum"]
    engine.act(
        room,
        room.players[actor],
        "play_equipment",
        {"cardId": "truth_serum", "targetSeat": target},
    )
    engine.act(
        room,
        room.players[target],
        "choose_reveal",
        {"cardIndex": 0},
    )

    assert state.boards[target].cards[0].revealed is True
    assert "disguise" in state.boards[target].effects


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


def test_taser_transfers_the_gun_and_blocks_shooting_for_the_current_turn() -> None:
    engine, room = make_room()
    state = room.state
    actor, armed_player, aim = 2, 0, 1
    state.turn_seat = actor
    state.boards[armed_player].gun = True
    state.boards[armed_player].aim_seat = actor
    state.boards[actor].equipment = ["taser"]
    central_guns = engine._central_guns(state)

    engine.act(
        room,
        room.players[actor],
        "play_equipment",
        {
            "cardId": "taser",
            "targetSeat": armed_player,
            "aimSeat": aim,
        },
    )

    assert state.boards[armed_player].gun is False
    assert state.boards[armed_player].aim_seat is None
    assert state.boards[actor].gun is True
    assert state.boards[actor].aim_seat == aim
    assert engine._central_guns(state) == central_guns
    assert "shoot" not in engine.view(room, room.players[actor])["legal"][
        "normalActionIds"
    ]
    with pytest.raises(GameRuleError, match="本回合刚取得"):
        engine.act(room, room.players[actor], "shoot", {})


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


def test_equipment_victory_clears_the_action_it_interrupted() -> None:
    engine, room = make_room()
    state = room.state
    agent_seat, _ = leader_owner(room, "agent")
    kingpin_seat, kingpin_index = leader_owner(room, "kingpin")
    actor = next(
        seat for seat in state.boards if seat not in {agent_seat, kingpin_seat}
    )
    state.turn_seat = actor
    state.boards[actor].equipment = ["blackmail"]

    engine.act(
        room,
        room.players[actor],
        "investigate",
        {"targetSeat": agent_seat, "cardIndex": 0},
    )
    assert state.pending_action is not None
    assert engine._response_seat(state.pending_action) == actor

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
    assert state.pending_action is None
    assert state.pending_shot is None
    assert state.choice is None
    assert state.post_shot is None


def test_blackmail_is_restricted_to_its_owners_turn() -> None:
    engine, room = make_room()
    state = room.state
    state.boards[1].equipment = ["blackmail"]
    state.turn_seat = 0

    assert "blackmail" not in engine.view(room, room.players[1])["legal"][
        "playableEquipmentIds"
    ]
    with pytest.raises(GameRuleError, match="使用时机"):
        engine.act(
            room,
            room.players[1],
            "play_equipment",
            {
                "cardId": "blackmail",
                "firstSeat": 0,
                "firstCardIndex": 0,
                "secondSeat": 2,
                "secondCardIndex": 0,
            },
        )

    state.turn_seat = 1
    assert "blackmail" in engine.view(room, room.players[1])["legal"][
        "playableEquipmentIds"
    ]


def test_blackmail_moves_each_cards_public_state_with_the_card() -> None:
    engine, room = make_room()
    state = room.state
    actor = state.turn_seat
    first, second = [seat for seat in state.boards if seat != actor][:2]
    first_index = normal_card_index(room, first)
    second_index = normal_card_index(room, second)
    first_card = state.boards[first].cards[first_index]
    second_card = state.boards[second].cards[second_index]
    first_card.revealed = True
    state.knowledge[actor].add(second_card.id)
    state.boards[actor].equipment = ["blackmail"]

    engine.act(
        room,
        room.players[actor],
        "play_equipment",
        {
            "cardId": "blackmail",
            "firstSeat": first,
            "firstCardIndex": first_index,
            "secondSeat": second,
            "secondCardIndex": second_index,
        },
    )

    assert state.boards[first].cards[first_index] is second_card
    assert second_card.revealed is False
    assert state.boards[second].cards[second_index] is first_card
    assert first_card.revealed is True
    moved_view = engine.view(room, room.players[actor])["players"][first]["cards"][
        first_index
    ]
    assert moved_view["kind"] == second_card.kind
    assert moved_view["knowledge"] == "known"


def test_defibrillator_revives_a_non_leader_with_normal_actions() -> None:
    engine, room = make_room()
    state = room.state
    actor = state.turn_seat
    target = next(
        seat
        for seat, board in state.boards.items()
        if seat != actor and engine._leader_card(board) is None
    )
    engine._eliminate(state, target)
    state.boards[target].restricted_to_equip = True
    state.boards[actor].equipment = ["defibrillator"]

    engine.act(
        room,
        room.players[actor],
        "play_equipment",
        {"cardId": "defibrillator", "targetSeat": target},
    )

    assert state.boards[target].alive is True
    assert state.boards[target].restricted_to_equip is False
    assert "defibrillator" in state.equipment_deck


def test_defibrillator_cannot_revive_a_leader() -> None:
    engine, room = make_room()
    state = room.state
    leader, _ = leader_owner(room, "agent")
    actor = next(seat for seat in state.boards if seat != leader)
    ordinary = next(
        seat
        for seat, board in state.boards.items()
        if seat not in {actor, leader} and engine._leader_card(board) is None
    )
    state.boards[leader].alive = False
    state.boards[ordinary].alive = False
    state.boards[actor].equipment = ["defibrillator"]

    with pytest.raises(GameRuleError, match="不能复活探员或头目"):
        engine.act(
            room,
            room.players[actor],
            "play_equipment",
            {"cardId": "defibrillator", "targetSeat": leader},
        )

    assert room.state.boards[actor].equipment == ["defibrillator"]
    assert room.state.boards[leader].alive is False


def test_flashbang_preserves_public_cards_and_clears_hidden_card_memory() -> None:
    engine, room = make_room()
    state = room.state
    actor = state.turn_seat
    target = next(seat for seat in state.boards if seat != actor)
    target_cards = state.boards[target].cards
    target_cards[0].revealed = True
    public_id = target_cards[0].id
    hidden_ids = {card.id for card in target_cards[1:]}
    for known in state.knowledge.values():
        known.update(card.id for card in target_cards)
    state.boards[actor].equipment = ["flashbang"]

    engine.act(
        room,
        room.players[actor],
        "play_equipment",
        {"cardId": "flashbang", "targetSeat": target},
    )
    assert state.choice is not None
    assert state.choice.kind == "flashbang"
    assert state.choice.seat == target
    target_choice = engine.view(room, room.players[target])["choice"]
    assert [card["kind"] for card in target_choice["integrityCards"]] == [
        card.kind for card in target_cards
    ]
    assert engine.view(room, room.players[actor])["choice"] is None
    with pytest.raises(GameRuleError, match="各选择一次"):
        engine.act(
            room,
            room.players[target],
            "reorder_integrity",
            {"cardOrder": [0, 0, 2]},
        )
    engine.act(
        room,
        room.players[target],
        "reorder_integrity",
        {"cardOrder": [2, 0, 1]},
    )

    shuffled = state.boards[target].cards
    assert [card.id for card in shuffled] == [
        target_cards[2].id,
        target_cards[0].id,
        target_cards[1].id,
    ]
    assert {card.id for card in shuffled} == {public_id, *hidden_ids}
    assert next(card for card in shuffled if card.id == public_id).revealed is True
    assert all(
        not next(card for card in shuffled if card.id == card_id).revealed
        for card_id in hidden_ids
    )
    assert all(hidden_ids.isdisjoint(known) for known in state.knowledge.values())
    assert all(public_id in known for known in state.knowledge.values())


@pytest.mark.parametrize("revealed_count", [2, 3])
def test_flashbang_remains_usable_with_fewer_than_two_hidden_cards(
    revealed_count: int,
) -> None:
    engine, room = make_room()
    state = room.state
    actor = state.turn_seat
    target = next(seat for seat in state.boards if seat != actor)
    for card in state.boards[target].cards[:revealed_count]:
        card.revealed = True
    state.boards[actor].equipment = ["flashbang"]

    view = engine.view(room, room.players[actor])
    option = next(
        item
        for item in view["legal"]["equipmentOptions"]
        if item["cardId"] == "flashbang"
    )
    assert target in {
        item["value"] for item in option["fields"][0]["options"]
    }
    engine.act(
        room,
        room.players[actor],
        "play_equipment",
        {"cardId": "flashbang", "targetSeat": target},
    )
    engine.act(
        room,
        room.players[target],
        "reorder_integrity",
        {"cardOrder": [2, 1, 0]},
    )

    assert "flashbang" in state.equipment_deck


def test_flashbang_preserves_memory_when_only_one_hidden_card_remains() -> None:
    engine, room = make_room()
    state = room.state
    actor = state.turn_seat
    target = next(seat for seat in state.boards if seat != actor)
    for card in state.boards[target].cards[:2]:
        card.revealed = True
    hidden_card = state.boards[target].cards[2]
    observer = next(seat for seat in state.boards if seat not in {actor, target})
    state.knowledge[observer].add(hidden_card.id)
    state.boards[actor].equipment = ["flashbang"]

    engine.act(
        room,
        room.players[actor],
        "play_equipment",
        {"cardId": "flashbang", "targetSeat": target},
    )
    engine.act(
        room,
        room.players[target],
        "reorder_integrity",
        {"cardOrder": [2, 0, 1]},
    )

    assert hidden_card.id in state.knowledge[observer]


def test_flashbang_choice_resumes_the_action_it_interrupted() -> None:
    engine, room = make_room()
    state = room.state
    actor, responder, target = 0, 1, 2
    original_cards = list(state.boards[target].cards)
    state.boards[responder].equipment = ["flashbang"]

    engine.act(
        room,
        room.players[actor],
        "investigate",
        {"targetSeat": target, "cardIndex": 0},
    )
    engine.act(
        room,
        room.players[responder],
        "play_equipment",
        {"cardId": "flashbang", "targetSeat": target},
    )

    assert state.pending_action is not None
    assert state.choice is not None and state.choice.seat == target
    engine.act(
        room,
        room.players[target],
        "reorder_integrity",
        {"cardOrder": [2, 1, 0]},
    )

    assert state.choice is None
    assert state.pending_action is None
    assert state.action_done is True
    assert original_cards[2].id in state.knowledge[actor]


def test_departing_action_player_clears_their_interrupted_flashbang_choice() -> None:
    engine, room = make_room()
    state = room.state
    ordinary = [
        seat for seat, board in state.boards.items() if engine._leader_card(board) is None
    ]
    actor = ordinary[0]
    responder = next(seat for seat in state.boards if seat != actor)
    target = next(seat for seat in state.boards if seat not in {actor, responder})
    state.turn_seat = actor
    state.boards[responder].equipment = ["flashbang"]

    engine.act(
        room,
        room.players[actor],
        "investigate",
        {"targetSeat": target, "cardIndex": 0},
    )
    engine.act(
        room,
        room.players[responder],
        "play_equipment",
        {"cardId": "flashbang", "targetSeat": actor},
    )
    assert state.choice is not None and state.choice.seat == actor

    engine.act(room, room.players[actor], "resign", {})

    assert state.pending_action is None
    assert state.choice is None
    assert state.turn_seat != actor


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


def test_planted_evidence_does_not_change_a_leaders_team() -> None:
    engine, room = make_room()
    state = room.state
    actor = state.turn_seat
    target, _ = leader_owner(room, "agent")
    state.equipment_deck.remove("planted_evidence")
    state.boards[actor].equipment = ["planted_evidence"]

    engine.act(
        room,
        room.players[actor],
        "play_equipment",
        {"cardId": "planted_evidence", "targetSeat": target},
    )

    assert engine._team(state.boards[target]) == "honest"
    assert "planted_evidence" in state.boards[target].effects
    assert "planted_evidence" not in state.equipment_deck


def test_planted_evidence_updates_only_the_targets_private_team_view() -> None:
    engine, room = make_room()
    state = room.state
    actor = state.turn_seat
    target = next(
        seat
        for seat, board in state.boards.items()
        if seat != actor and engine._leader_card(board) is None
    )
    bystander = next(seat for seat in state.boards if seat not in {actor, target})
    original_team = engine._team(state.boards[target])
    state.boards[actor].equipment = ["planted_evidence"]

    engine.act(
        room,
        room.players[actor],
        "play_equipment",
        {"cardId": "planted_evidence", "targetSeat": target},
    )

    target_view = engine.view(room, room.players[target])
    bystander_view = engine.view(room, room.players[bystander])
    assert target_view["selfTeam"] != original_team
    assert bystander_view["players"][target]["team"] is None


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

    state.action_done = True
    engine.act(room, room.players[0], "end_turn", {})
    assert state.turn_seat == 1
    state.action_done = True
    engine.act(room, room.players[1], "end_turn", {})
    assert state.choice and state.choice.kind == "grenade_pass"
    engine.act(room, room.players[1], "pass_grenade", {"targetSeat": 2})
    assert state.boards[2].grenade_stage == 2

    assert state.turn_seat == 2
    state.action_done = True
    engine.act(room, room.players[2], "end_turn", {})
    assert state.boards[2].alive is False or engine._leader_card(state.boards[2]) is not None


def test_grenade_played_during_the_targets_turn_waits_until_their_next_turn() -> None:
    engine, room = make_room()
    state = room.state
    actor, target = 0, 1
    state.turn_seat = target
    state.boards[actor].equipment = ["grenade"]

    engine.act(
        room,
        room.players[actor],
        "play_equipment",
        {"cardId": "grenade", "targetSeat": target},
    )
    state.action_done = True
    engine.act(room, room.players[target], "end_turn", {})

    assert state.choice is None
    assert state.turn_seat == 2
    assert state.boards[target].grenade_stage == 1

    for turn_seat in (2, 3, 0):
        assert state.turn_seat == turn_seat
        state.action_done = True
        engine.act(room, room.players[turn_seat], "end_turn", {})
    assert state.turn_seat == target
    state.action_done = True
    engine.act(room, room.players[target], "end_turn", {})
    assert state.choice is not None
    assert state.choice.kind == "grenade_pass"


def test_grenade_pass_advances_in_the_direction_changed_by_smoke_grenade() -> None:
    engine, room = make_room()
    state = room.state
    holder = 0
    state.turn_seat = holder
    state.turn_number = 2
    state.action_done = True
    state.boards[holder].grenade_stage = 1
    state.boards[holder].grenade_received_turn = 1
    state.boards[holder].effects.append("grenade")
    state.boards[1].equipment = ["smoke_grenade"]

    engine.act(
        room,
        room.players[1],
        "play_equipment",
        {"cardId": "smoke_grenade"},
    )
    engine.act(room, room.players[holder], "end_turn", {})
    assert state.choice is not None and state.choice.kind == "grenade_pass"
    engine.act(room, room.players[holder], "pass_grenade", {"targetSeat": 2})

    assert state.direction == -1
    assert state.turn_seat == 3
    assert state.boards[2].grenade_stage == 2


def test_coffee_extra_turn_starts_only_after_the_grenade_pass_finishes() -> None:
    engine, room = make_room()
    state = room.state
    holder, coffee_user, grenade_target = 0, 2, 3
    state.turn_seat = holder
    state.turn_number = 2
    state.action_done = True
    state.boards[holder].grenade_stage = 1
    state.boards[holder].grenade_received_turn = 1
    state.boards[holder].effects.append("grenade")
    state.boards[coffee_user].equipment = ["coffee"]

    engine.act(
        room,
        room.players[coffee_user],
        "play_equipment",
        {"cardId": "coffee"},
    )
    engine.act(room, room.players[holder], "end_turn", {})

    assert state.choice is not None and state.choice.seat == holder
    assert state.turn_seat == holder
    engine.act(
        room,
        room.players[holder],
        "pass_grenade",
        {"targetSeat": grenade_target},
    )

    assert state.choice is None
    assert state.turn_seat == coffee_user
    assert state.boards[grenade_target].grenade_stage == 2


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


def test_smoke_grenade_reverses_the_remaining_equipment_response_order() -> None:
    engine, room = make_room()
    state = room.state
    actor, target = 0, 3
    state.boards[1].equipment = ["smoke_grenade"]
    state.boards[2].equipment = ["coffee"]
    state.boards[3].equipment = ["report_audit"]

    engine.act(
        room,
        room.players[actor],
        "investigate",
        {"targetSeat": target, "cardIndex": 0},
    )
    assert state.pending_action is not None
    assert state.pending_action.response_order == [1, 2, 3]
    engine.act(
        room,
        room.players[1],
        "play_equipment",
        {"cardId": "smoke_grenade"},
    )

    assert state.direction == -1
    assert state.pending_action is not None
    assert state.pending_action.response_order == [3, 2]


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


def test_restraining_order_lets_the_new_target_use_shot_response_equipment() -> None:
    engine, room = make_room()
    state = room.state
    shooter, original_target, new_target = 0, 1, 2
    state.boards[shooter].gun = True
    state.boards[shooter].aim_seat = original_target
    state.acquired_gun_turn[shooter] = 0
    state.boards[original_target].equipment = ["restraining_order"]
    state.boards[new_target].equipment = ["helmet"]

    engine.act(room, room.players[shooter], "shoot", {})
    engine.act(
        room,
        room.players[original_target],
        "play_equipment",
        {"cardId": "restraining_order", "targetSeat": new_target},
    )

    assert state.pending_action is not None
    assert engine._response_seat(state.pending_action) == new_target
    engine.act(
        room,
        room.players[new_target],
        "play_equipment",
        {"cardId": "helmet"},
    )

    assert state.pending_action is None
    assert state.action_done is True
    assert state.boards[shooter].gun is False
    assert all(not card.revealed for card in state.boards[new_target].cards)


def test_restraining_order_shot_still_resolves_if_k9_takes_the_gun_afterward() -> None:
    engine, room = make_room()
    state = room.state
    shooter, original_target, new_target = 0, 1, 2
    state.boards[shooter].gun = True
    state.boards[shooter].aim_seat = original_target
    state.acquired_gun_turn[shooter] = 0
    state.boards[original_target].equipment = ["restraining_order"]
    state.boards[new_target].equipment = ["k9_unit"]

    engine.act(room, room.players[shooter], "shoot", {})
    engine.act(
        room,
        room.players[original_target],
        "play_equipment",
        {"cardId": "restraining_order", "targetSeat": new_target},
    )
    engine.act(
        room,
        room.players[new_target],
        "play_equipment",
        {"cardId": "k9_unit", "targetSeat": shooter},
    )

    assert state.pending_action is None
    assert state.action_done is True
    assert state.boards[shooter].gun is False
    assert all(card.revealed for card in state.boards[new_target].cards)


def test_mandatory_redirected_shot_cancels_if_its_new_target_leaves() -> None:
    engine, room = make_room()
    state = room.state
    new_target = next(
        seat for seat, board in state.boards.items() if engine._leader_card(board) is None
    )
    shooter = next(seat for seat in state.boards if seat != new_target)
    original_target = next(
        seat for seat in state.boards if seat not in {shooter, new_target}
    )
    state.turn_seat = shooter
    state.boards[shooter].gun = True
    state.boards[shooter].aim_seat = original_target
    state.acquired_gun_turn[shooter] = 0
    state.boards[original_target].equipment = ["restraining_order"]
    state.boards[new_target].equipment = ["smoke_grenade"]

    engine.act(room, room.players[shooter], "shoot", {})
    engine.act(
        room,
        room.players[original_target],
        "play_equipment",
        {"cardId": "restraining_order", "targetSeat": new_target},
    )
    assert state.pending_action is not None
    assert engine._response_seat(state.pending_action) == new_target

    engine.act(room, room.players[new_target], "resign", {})

    assert state.pending_action is None
    assert state.boards[new_target].alive is False
    assert state.action_done is False


def test_holster_rejects_the_shooters_existing_target_server_side() -> None:
    engine, room = make_room()
    state = room.state
    shooter, target = 0, 1
    state.boards[shooter].gun = True
    state.boards[shooter].aim_seat = target
    state.acquired_gun_turn[shooter] = 0
    state.boards[shooter].equipment = ["holster"]

    engine.act(room, room.players[shooter], "shoot", {})
    assert state.pending_action is not None
    assert engine._response_seat(state.pending_action) == shooter
    with pytest.raises(GameRuleError, match="新的射击目标"):
        engine.act(
            room,
            room.players[shooter],
            "play_equipment",
            {"cardId": "holster", "targetSeat": target},
        )

    assert room.state.pending_action is not None
    assert room.state.boards[shooter].equipment == ["holster"]


def test_holster_reopens_responses_for_the_new_shot_target() -> None:
    engine, room = make_room()
    state = room.state
    shooter, original_target, new_target = 0, 1, 2
    state.boards[shooter].gun = True
    state.boards[shooter].aim_seat = original_target
    state.acquired_gun_turn[shooter] = 0
    state.boards[shooter].equipment = ["holster"]
    state.boards[new_target].equipment = ["helmet"]

    engine.act(room, room.players[shooter], "shoot", {})
    engine.act(
        room,
        room.players[shooter],
        "play_equipment",
        {"cardId": "holster", "targetSeat": new_target},
    )

    assert state.pending_action is not None
    assert engine._response_seat(state.pending_action) == new_target
    engine.act(
        room,
        room.players[new_target],
        "play_equipment",
        {"cardId": "helmet"},
    )

    assert state.pending_action is None
    assert state.action_done is True
    assert all(not card.revealed for card in state.boards[new_target].cards)


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


def test_classified_orders_shot_still_resolves_if_k9_takes_the_gun_afterward() -> None:
    engine, room = make_room()
    state = room.state
    shooter, original_target, decider, new_target = range(4)
    state.boards[shooter].gun = True
    state.boards[shooter].aim_seat = original_target
    state.acquired_gun_turn[shooter] = 0
    state.boards[original_target].equipment = ["classified_orders"]
    state.boards[new_target].equipment = ["k9_unit"]

    engine.act(room, room.players[shooter], "shoot", {})
    engine.act(
        room,
        room.players[original_target],
        "play_equipment",
        {"cardId": "classified_orders", "deciderSeat": decider},
    )
    engine.act(
        room,
        room.players[decider],
        "choose_redirect",
        {"targetSeat": new_target},
    )
    engine.act(
        room,
        room.players[new_target],
        "play_equipment",
        {"cardId": "k9_unit", "targetSeat": shooter},
    )

    assert state.pending_action is None
    assert state.action_done is True
    assert state.boards[shooter].gun is False
    assert all(card.revealed for card in state.boards[new_target].cards)


def test_classified_orders_is_unavailable_without_a_new_legal_target() -> None:
    engine, room = make_room()
    state = room.state
    shooter, target = 0, 1
    for seat in (2, 3):
        state.boards[seat].alive = False
    state.boards[shooter].gun = True
    state.boards[shooter].aim_seat = target
    state.acquired_gun_turn[shooter] = 0
    state.boards[target].equipment = ["classified_orders", "k9_unit"]

    engine.act(room, room.players[shooter], "shoot", {})

    response_ids = engine.view(room, room.players[target])["legal"][
        "responseEquipmentIds"
    ]
    assert "classified_orders" not in response_ids
    assert "k9_unit" in response_ids


def test_classified_orders_resumes_the_shot_if_all_new_targets_leave() -> None:
    engine, room = make_room()
    state = room.state
    shooter, _ = leader_owner(room, "agent")
    original_target, _ = leader_owner(room, "kingpin")
    departing_targets = [
        seat for seat, board in state.boards.items() if engine._leader_card(board) is None
    ]
    state.turn_seat = shooter
    state.boards[shooter].gun = True
    state.boards[shooter].aim_seat = original_target
    state.acquired_gun_turn[shooter] = 0
    state.boards[original_target].equipment = ["classified_orders"]

    engine.act(room, room.players[shooter], "shoot", {})
    engine.act(
        room,
        room.players[original_target],
        "play_equipment",
        {"cardId": "classified_orders", "deciderSeat": shooter},
    )

    assert state.choice is not None and state.choice.kind == "classified_redirect"
    engine.act(room, room.players[departing_targets[0]], "resign", {})
    assert state.choice is not None and state.choice.kind == "classified_redirect"
    engine.act(room, room.players[departing_targets[1]], "resign", {})

    assert state.choice is None
    assert state.pending_action is None
    leader = engine._leader_card(state.boards[original_target])
    assert leader is not None and leader.wounded is True


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


def test_surveillance_camera_tracks_the_card_investigated_after_flashbang_reorder() -> None:
    engine, room = make_room()
    state = room.state
    actor, target, flashbang_user, camera_user = 0, 1, 2, 3
    original_cards = list(state.boards[target].cards)
    state.boards[flashbang_user].equipment = ["flashbang"]
    state.boards[camera_user].equipment = ["surveillance_camera"]

    engine.act(
        room,
        room.players[actor],
        "investigate",
        {"targetSeat": target, "cardIndex": 0},
    )
    engine.act(
        room,
        room.players[flashbang_user],
        "play_equipment",
        {"cardId": "flashbang", "targetSeat": target},
    )
    engine.act(
        room,
        room.players[target],
        "reorder_integrity",
        {"cardOrder": [1, 0, 2]},
    )

    investigated = original_cards[1]
    assert state.boards[target].cards[0] is investigated
    assert investigated.id in state.knowledge[actor]
    assert "surveillance_camera" in engine.view(
        room,
        room.players[camera_user],
    )["legal"]["playableEquipmentIds"]
    engine.act(
        room,
        room.players[camera_user],
        "play_equipment",
        {"cardId": "surveillance_camera"},
    )

    assert investigated.revealed is True
    assert original_cards[0].revealed is False


def test_other_equipment_closes_the_surveillance_camera_window() -> None:
    engine, room = make_room()
    state = room.state
    engine.act(
        room,
        room.players[0],
        "investigate",
        {"targetSeat": 2, "cardIndex": 0},
    )
    state.boards[1].equipment = ["flashbang"]
    state.boards[3].equipment = ["surveillance_camera"]

    engine.act(
        room,
        room.players[1],
        "play_equipment",
        {"cardId": "flashbang", "targetSeat": 2},
    )
    engine.act(
        room,
        room.players[2],
        "reorder_integrity",
        {"cardOrder": [2, 1, 0]},
    )

    assert state.last_investigation is None
    assert "surveillance_camera" not in engine.view(room, room.players[3])[
        "legal"
    ]["playableEquipmentIds"]


def test_equipment_investigation_does_not_open_the_surveillance_camera_window() -> None:
    engine, room = make_room()
    state = room.state
    state.boards[0].equipment = ["polygraph"]
    state.boards[1].equipment = ["surveillance_camera"]

    engine.act(
        room,
        room.players[0],
        "play_equipment",
        {"cardId": "polygraph", "targetSeat": 2},
    )

    assert state.last_investigation is None
    assert "surveillance_camera" not in engine.view(room, room.players[1])[
        "legal"
    ]["playableEquipmentIds"]


def test_truth_serum_can_invalidate_the_investigation_it_interrupted() -> None:
    engine, room = make_room()
    state = room.state
    actor, responder, target = 0, 1, 2
    investigated_card = state.boards[target].cards[0]
    state.boards[responder].equipment = ["truth_serum"]

    engine.act(
        room,
        room.players[actor],
        "investigate",
        {"targetSeat": target, "cardIndex": 0},
    )
    engine.act(
        room,
        room.players[responder],
        "play_equipment",
        {"cardId": "truth_serum", "targetSeat": target},
    )

    assert state.choice is not None and state.choice.seat == target
    engine.act(
        room,
        room.players[target],
        "choose_reveal",
        {"cardIndex": 0},
    )

    assert investigated_card.revealed is True
    assert investigated_card.id not in state.knowledge[actor]
    assert state.pending_action is None
    assert state.action_done is False


def test_coffee_inserts_a_full_turn_then_resumes_after_the_original_player() -> None:
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


def test_coffee_gives_the_natural_successor_an_extra_and_normal_turn() -> None:
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

    state.boards[1].equipment = ["smoke_grenade"]
    engine.act(
        room,
        room.players[1],
        "play_equipment",
        {"cardId": "smoke_grenade"},
    )
    assert state.direction == -1
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
    del state.boards[0].grenade_received_turn
    state.boards[0].effects.append("crutches")
    state.boards[0].restricted_to_equip = False
    state.coffee_after = [2]  # type: ignore[attr-defined]
    state.choice = {  # type: ignore[assignment]
        "kind": "classified_redirect",
        "seat": 1,
        "shooterSeat": 0,
        "resumePendingAfterSeat": 2,
    }
    state.pending_shot = PendingShot(
        shooter_seat=0,
        target_seat=1,
        source="gun",
        scanner_seat=2,
    )
    del state.pending_shot.scanner_activated

    engine.repair_restored_room(room)

    assert state.extra_turns.pending_seats == [2]
    assert state.extra_turns.resume_after_seat is None
    assert state.choice is not None
    assert state.choice.kind == "classified_redirect"
    assert state.choice.seat == 1
    assert state.choice.shooter_seat == 0
    assert state.choice.resume_pending_after_seat == 2
    assert state.choice.source_card_id is None
    assert state.boards[0].grenade_received_turn is None
    assert state.boards[0].restricted_to_equip is True
    assert state.pending_shot.scanner_activated is False


def test_restored_declared_shot_captures_its_existing_aim_and_completion_flag() -> None:
    engine, room = make_room()
    state = room.state
    shooter, target = 0, 1
    state.boards[shooter].aim_seat = target
    state.pending_action = PendingAction(shooter, "shoot", {})
    del state.pending_action.completion_required
    state.pending_action.must_complete = True  # type: ignore[attr-defined]

    engine.repair_restored_room(room)

    assert state.pending_action.payload["targetSeat"] == target
    assert state.pending_action.completion_required is True


def test_restored_post_shot_dict_is_migrated_to_typed_resolution() -> None:
    engine, room = make_room()
    state = room.state
    state.post_shot = {  # type: ignore[assignment]
        "kind": "mobile_detonator",
        "seat": 2,
        "drawAfter": True,
        "eliminated": False,
        "advanceAfter": True,
    }

    engine.repair_restored_room(room)

    assert state.post_shot is not None
    assert state.post_shot.kind == "mobile_detonator"
    assert state.post_shot.seat == 2
    assert state.post_shot.draw_after is True
    assert state.post_shot.eliminated is False
    assert state.post_shot.advance_after is True


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


def test_evidence_bag_can_transfer_a_response_card_into_the_current_window() -> None:
    engine, room = make_room()
    state = room.state
    shooter, bag_user, target, equipment_owner = 0, 1, 2, 3
    state.boards[shooter].gun = True
    state.boards[shooter].aim_seat = target
    state.acquired_gun_turn[shooter] = 0
    state.boards[bag_user].equipment = ["evidence_bag"]
    state.boards[equipment_owner].equipment = ["k9_unit"]

    engine.act(room, room.players[shooter], "shoot", {})
    assert state.pending_action is not None
    assert engine._response_seat(state.pending_action) == bag_user
    engine.act(
        room,
        room.players[bag_user],
        "play_equipment",
        {
            "cardId": "evidence_bag",
            "ownerSeat": equipment_owner,
            "recipientSeat": target,
        },
    )

    assert state.boards[target].equipment == ["k9_unit"]
    assert state.pending_action is not None
    assert engine._response_seat(state.pending_action) == target
    engine.act(
        room,
        room.players[target],
        "play_equipment",
        {"cardId": "k9_unit", "targetSeat": shooter},
    )

    assert state.pending_action is None
    assert state.action_done is False
    assert state.boards[shooter].gun is False
    assert all(not card.revealed for card in state.boards[target].cards)


def test_evidence_bag_hand_limit_finishes_before_the_shot_response_reopens() -> None:
    engine, room = make_room()
    state = room.state
    shooter, bag_user, target, equipment_owner = 0, 1, 2, 3
    state.boards[shooter].gun = True
    state.boards[shooter].aim_seat = target
    state.acquired_gun_turn[shooter] = 0
    state.boards[bag_user].equipment = ["evidence_bag"]
    state.boards[target].equipment = ["coffee"]
    state.boards[equipment_owner].equipment = ["k9_unit"]

    engine.act(room, room.players[shooter], "shoot", {})
    engine.act(
        room,
        room.players[bag_user],
        "play_equipment",
        {
            "cardId": "evidence_bag",
            "ownerSeat": equipment_owner,
            "recipientSeat": target,
        },
    )

    assert state.choice is not None and state.choice.kind == "equipment_limit"
    assert state.pending_action is not None
    engine.act(
        room,
        room.players[target],
        "choose_equipment",
        {"cardId": "k9_unit"},
    )

    assert state.choice is None
    assert state.pending_action is not None
    assert engine._response_seat(state.pending_action) == target
    engine.act(
        room,
        room.players[target],
        "play_equipment",
        {"cardId": "k9_unit", "targetSeat": shooter},
    )

    assert state.pending_action is None
    assert state.action_done is False
    assert all(not card.revealed for card in state.boards[target].cards)


def test_evidence_bag_is_unusable_without_a_distinct_legal_recipient() -> None:
    engine, room = make_room()
    state = room.state
    actor = state.turn_seat
    owner = next(seat for seat in state.boards if seat != actor)
    for seat in state.boards:
        state.boards[seat].alive = seat in {actor, owner}
    state.boards[actor].equipment = ["evidence_bag"]
    state.boards[owner].equipment = ["coffee"]

    view = engine.view(room, room.players[actor])

    assert "evidence_bag" not in view["legal"]["playableEquipmentIds"]


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


def test_departing_turn_player_waits_for_report_audit_to_finish_before_advancing() -> None:
    engine, room = make_room()
    state = room.state
    ordinary = [
        seat for seat, board in state.boards.items() if engine._leader_card(board) is None
    ]
    actor = ordinary[0]
    user = next(seat for seat in state.boards if seat != actor)
    state.turn_seat = actor
    state.boards[user].equipment = ["report_audit"]

    engine.act(
        room,
        room.players[actor],
        "investigate",
        {"targetSeat": user, "cardIndex": 0},
    )
    engine.act(
        room,
        room.players[user],
        "play_equipment",
        {"cardId": "report_audit"},
    )
    assert state.choice is not None and state.choice.kind == "report_audit"

    engine.act(room, room.players[actor], "resign", {})

    assert state.pending_action is None
    assert state.choice is not None and state.choice.kind == "report_audit"
    assert state.turn_seat == actor

    while state.choice is not None:
        choice_seat = state.choice.seat
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

    assert state.turn_seat != actor


def test_departing_turn_player_waits_for_shot_chain_to_finish_before_advancing() -> None:
    engine, room = make_room()
    state = room.state
    ordinary = [
        seat for seat, board in state.boards.items() if engine._leader_card(board) is None
    ]
    actor = ordinary[0]
    scanner = next(seat for seat in state.boards if seat != actor)
    target = next(seat for seat in state.boards if seat not in {actor, scanner})
    state.turn_seat = actor
    state.pending_shot = PendingShot(
        shooter_seat=scanner,
        target_seat=target,
        source="gun",
        scanner_seat=scanner,
    )
    state.boards[scanner].equipment = ["thumbprint_scanner"]

    engine.act(room, room.players[actor], "resign", {})

    assert state.pending_shot is not None
    assert state.pending_shot.advance_after is True
    assert state.turn_seat == actor

    engine.act(room, room.players[scanner], "pass_scanner", {})

    assert state.pending_shot is None
    assert state.turn_seat != actor


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


def test_report_audit_skips_players_with_no_hidden_cards() -> None:
    engine, room = make_room()
    state = room.state
    actor = state.turn_seat
    already_public = next(seat for seat in state.boards if seat != actor)
    for card in state.boards[already_public].cards:
        card.revealed = True
    state.boards[actor].equipment = ["report_audit"]

    engine.act(
        room,
        room.players[actor],
        "play_equipment",
        {"cardId": "report_audit"},
    )

    queued: list[int] = []
    while state.choice is not None:
        seat = state.choice.seat
        queued.append(seat)
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

    assert already_public not in queued
    assert set(queued) == set(state.boards) - {already_public}


def test_report_audit_resumes_the_action_it_interrupted() -> None:
    engine, room = make_room()
    state = room.state
    actor, responder, target = 0, 1, 2
    investigated_card = state.boards[target].cards[0]
    state.boards[responder].equipment = ["report_audit"]

    engine.act(
        room,
        room.players[actor],
        "investigate",
        {"targetSeat": target, "cardIndex": 0},
    )
    engine.act(
        room,
        room.players[responder],
        "play_equipment",
        {"cardId": "report_audit"},
    )

    while state.choice is not None:
        seat = state.choice.seat
        hidden_indexes = [
            index
            for index, card in enumerate(state.boards[seat].cards)
            if not card.revealed
        ]
        card_index = hidden_indexes[-1] if seat == target else hidden_indexes[0]
        engine.act(
            room,
            room.players[seat],
            "choose_reveal",
            {"cardIndex": card_index},
        )

    assert state.pending_action is None
    assert state.action_done is True
    assert investigated_card.id in state.knowledge[actor]


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
    assert all(not card.revealed for card in state.boards[target].cards)
    bystander = next(
        seat for seat in state.boards if seat not in {agent_seat, target, shooter}
    )
    assert all(
        card["kind"] is None
        for card in engine.view(room, room.players[bystander])["players"][target]["cards"]
    )
    engine.act(
        room,
        room.players[agent_seat],
        "use_scanner",
        {},
    )

    assert state.pending_shot and state.pending_shot.scanner_activated is True
    scanner_view = engine.view(room, room.players[agent_seat])
    bystander_view = engine.view(room, room.players[bystander])
    assert all(
        card["knowledge"] == "known"
        for card in scanner_view["players"][target]["cards"]
    )
    assert all(
        card["kind"] is None
        for card in bystander_view["players"][target]["cards"]
    )
    assert engine.record_state(room)["equipmentPlayHistory"] == [
        {
            "sequence": 1,
            "turnNumber": 1,
            "seat": agent_seat,
            "cardId": "thumbprint_scanner",
            "targetSeats": [target],
        }
    ]

    engine.act(
        room,
        room.players[agent_seat],
        "resolve_scanner",
        {"ownCardIndex": agent_index, "targetCardIndex": target_index},
    )

    moved_agent = state.boards[target].cards[target_index]
    assert moved_agent.kind == "agent"
    assert moved_agent.wounded is True
    assert state.boards[target].alive is True
    assert all(card.revealed for card in state.boards[target].cards)


def test_thumbprint_scanner_can_be_used_without_exchanging_cards() -> None:
    engine, room = make_room()
    state = room.state
    target, _ = leader_owner(room, "agent")
    scanner = next(seat for seat in state.boards if seat != target)
    shooter = next(seat for seat in state.boards if seat not in {scanner, target})
    state.turn_seat = shooter
    state.boards[shooter].gun = True
    state.boards[shooter].aim_seat = target
    state.acquired_gun_turn[shooter] = 0
    state.boards[scanner].equipment = ["thumbprint_scanner"]

    engine.act(room, room.players[shooter], "shoot", {})
    engine.act(room, room.players[scanner], "use_scanner", {})
    engine.act(room, room.players[scanner], "resolve_scanner", {})

    assert state.pending_shot is None
    assert all(card.revealed for card in state.boards[target].cards)
    leader = engine._leader_card(state.boards[target])
    assert leader is not None and leader.wounded is True
    assert "thumbprint_scanner" in state.equipment_deck


def test_passing_thumbprint_scanner_reveals_and_applies_the_shot_without_using_it() -> None:
    engine, room = make_room()
    state = room.state
    target, _ = leader_owner(room, "agent")
    scanner = next(seat for seat in state.boards if seat != target)
    shooter = next(seat for seat in state.boards if seat not in {scanner, target})
    state.turn_seat = shooter
    state.boards[shooter].gun = True
    state.boards[shooter].aim_seat = target
    state.acquired_gun_turn[shooter] = 0
    state.boards[scanner].equipment = ["thumbprint_scanner"]
    target_ids = {card.id for card in state.boards[target].cards}

    engine.act(room, room.players[shooter], "shoot", {})
    assert all(not card.revealed for card in state.boards[target].cards)
    engine.act(room, room.players[scanner], "pass_scanner", {})

    assert state.pending_shot is None
    assert state.boards[scanner].equipment == ["thumbprint_scanner"]
    assert target_ids.isdisjoint(state.knowledge[scanner])
    assert all(card.revealed for card in state.boards[target].cards)
    assert state.equipment_play_history == []


def test_thumbprint_scanner_cannot_take_the_targets_leader_card() -> None:
    engine, room = make_room()
    state = room.state
    target, target_leader_index = leader_owner(room, "agent")
    scanner = next(seat for seat in state.boards if seat != target)
    shooter = next(seat for seat in state.boards if seat not in {scanner, target})
    state.turn_seat = shooter
    state.boards[shooter].gun = True
    state.boards[shooter].aim_seat = target
    state.acquired_gun_turn[shooter] = 0
    state.boards[scanner].equipment = ["thumbprint_scanner"]

    engine.act(room, room.players[shooter], "shoot", {})
    engine.act(room, room.players[scanner], "use_scanner", {})
    with pytest.raises(GameRuleError, match="不能拿走目标的领袖牌"):
        engine.act(
            room,
            room.players[scanner],
            "resolve_scanner",
            {"ownCardIndex": 0, "targetCardIndex": target_leader_index},
        )

    assert state.pending_shot and state.pending_shot.scanner_activated is True
    assert all(not card.revealed for card in state.boards[target].cards)
    engine.act(room, room.players[scanner], "resolve_scanner", {})
    assert state.pending_shot is None


def test_thumbprint_scanner_can_create_immediate_solo_leader_victory() -> None:
    engine, room = make_room()
    state = room.state
    scanner, agent_index = leader_owner(room, "agent")
    target, _ = leader_owner(room, "kingpin")
    shooter = next(seat for seat in state.boards if seat not in {scanner, target})
    target_index = normal_card_index(room, target)
    state.turn_seat = shooter
    state.boards[shooter].gun = True
    state.boards[shooter].aim_seat = target
    state.acquired_gun_turn[shooter] = 0
    state.boards[scanner].equipment = ["thumbprint_scanner"]

    engine.act(room, room.players[shooter], "shoot", {})
    engine.act(room, room.players[scanner], "use_scanner", {})
    engine.act(
        room,
        room.players[scanner],
        "resolve_scanner",
        {"ownCardIndex": agent_index, "targetCardIndex": target_index},
    )

    assert room.phase == "finished"
    assert room.winner == "solo"
    assert room.winner_player_ids == [room.players[target].id]
    assert state.pending_shot is None


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
    assert state.post_shot and state.post_shot.seat == target
    engine.act(
        room,
        room.players[target],
        "use_mobile_detonator",
        {"targetSeat": chained_target},
    )

    assert state.boards[target].alive is False
    assert state.boards[chained_target].alive is False
    assert engine.record_state(room)["equipmentPlayHistory"] == [
        {
            "sequence": 1,
            "turnNumber": 1,
            "seat": target,
            "cardId": "mobile_detonator",
            "targetSeats": [chained_target],
        }
    ]


def test_wounded_leader_can_keep_an_unused_mobile_detonator() -> None:
    engine, room = make_room()
    state = room.state
    target, _ = leader_owner(room, "agent")
    shooter = next(seat for seat in state.boards if seat != target)
    state.turn_seat = shooter
    state.boards[shooter].gun = True
    state.boards[shooter].aim_seat = target
    state.acquired_gun_turn[shooter] = 0
    state.boards[target].equipment = ["mobile_detonator"]
    state.equipment_deck = ["coffee"]

    engine.act(room, room.players[shooter], "shoot", {})
    assert state.post_shot and state.post_shot.seat == target

    engine.act(room, room.players[target], "pass_mobile_detonator", {})

    assert state.post_shot is None
    assert state.choice and state.choice.kind == "equipment_limit"
    assert state.boards[target].equipment == ["mobile_detonator", "coffee"]
    engine.act(
        room,
        room.players[target],
        "choose_equipment",
        {"cardId": "mobile_detonator"},
    )
    assert state.boards[target].equipment == ["mobile_detonator"]
    assert state.equipment_play_history == []


def test_grenade_shot_waits_for_scanner_then_mobile_detonator_before_advancing() -> None:
    engine, room = make_room()
    state = room.state
    target, _ = leader_owner(room, "agent")
    scanner = next(seat for seat in state.boards if seat != target)
    expected_next = engine._next_alive(state, target)
    state.turn_seat = target
    state.turn_number = 2
    state.action_done = True
    state.boards[target].grenade_stage = 2
    state.boards[target].grenade_received_turn = 1
    state.boards[target].effects.append("grenade")
    state.boards[target].equipment = ["mobile_detonator"]
    state.boards[scanner].equipment = ["thumbprint_scanner"]
    state.equipment_deck = []

    engine.act(room, room.players[target], "end_turn", {})

    assert state.pending_shot and state.pending_shot.scanner_seat == scanner
    assert all(not card.revealed for card in state.boards[target].cards)
    engine.act(room, room.players[scanner], "pass_scanner", {})

    assert state.pending_shot is None
    assert state.post_shot and state.post_shot.seat == target
    assert all(card.revealed for card in state.boards[target].cards)
    engine.act(room, room.players[target], "pass_mobile_detonator", {})

    assert state.post_shot is None
    assert state.choice and state.choice.kind == "equipment_limit"
    assert state.boards[target].equipment == ["mobile_detonator", "grenade"]
    engine.act(
        room,
        room.players[target],
        "choose_equipment",
        {"cardId": "mobile_detonator"},
    )

    assert state.choice is None
    assert state.turn_seat == expected_next
    assert state.turn_number == 3


def test_newly_drawn_mobile_detonator_cannot_respond_to_the_same_shot() -> None:
    engine, room = make_room()
    state = room.state
    target, _ = leader_owner(room, "agent")
    shooter = next(seat for seat in state.boards if seat != target)
    state.turn_seat = shooter
    state.boards[shooter].gun = True
    state.boards[shooter].aim_seat = target
    state.acquired_gun_turn[shooter] = 0
    state.equipment_deck = ["mobile_detonator"]

    engine.act(room, room.players[shooter], "shoot", {})

    assert state.post_shot is None
    assert state.boards[target].equipment == ["mobile_detonator"]
    assert state.equipment_draw_history[-1].source == "leader_wound"


def test_winning_shot_discards_mobile_detonator_without_offering_a_response() -> None:
    engine, room = make_room()
    state = room.state
    target, _ = leader_owner(room, "agent")
    shooter = next(seat for seat in state.boards if seat != target)
    leader = engine._leader_card(state.boards[target])
    assert leader is not None
    leader.wounded = True
    state.turn_seat = shooter
    state.boards[shooter].gun = True
    state.boards[shooter].aim_seat = target
    state.acquired_gun_turn[shooter] = 0
    state.boards[target].equipment = ["mobile_detonator"]

    engine.act(room, room.players[shooter], "shoot", {})

    assert room.phase == "finished"
    assert state.post_shot is None
    assert state.boards[target].equipment == []
    assert "mobile_detonator" in state.equipment_deck


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
    assert state.post_shot and state.post_shot.seat == target

    engine.disconnect_timeout(room, room.players[target])

    assert state.post_shot is None
    assert state.boards[target].equipment == []
    assert "mobile_detonator" in state.equipment_deck


def first_equipment_payload(option: dict[str, Any]) -> dict[str, Any]:
    values: dict[str, Any] = {}
    payload: dict[str, Any] = {"cardId": option["cardId"]}

    for field in option["fields"]:
        visible_when = field.get("visibleWhen")
        if visible_when and values.get(visible_when["field"]) != visible_when["equals"]:
            continue

        key = field["key"]
        if field["kind"] == "boolean":
            value = field.get("default", False)
        else:
            depends_on = field.get("dependsOn")
            options = (
                field.get("optionsByValue", {}).get(str(values.get(depends_on)), [])
                if depends_on
                else field.get("options", [])
            )
            distinct_from = field.get("distinctFrom")
            if distinct_from:
                options = [
                    item
                    for item in options
                    if item["value"] != values.get(distinct_from)
                ]
            relation = field.get("distinctLocationFrom")
            if relation and values.get(relation["ownSeatField"]) == values.get(
                relation["seatField"]
            ):
                options = [
                    item
                    for item in options
                    if item["value"] != values.get(relation["cardField"])
                ]
            if not options:
                if field.get("required"):
                    raise AssertionError(f"required equipment field has no option: {key}")
                continue
            value = options[0]["value"]

        values[key] = value
        root, separator, child = key.partition(".")
        if not separator:
            payload[root] = value
        else:
            nested = payload.setdefault(root, {})
            assert isinstance(nested, dict)
            nested[child] = value

    return payload


def resolve_automated_choice(
    engine: DepartedSuspicionEngine,
    room: ArcadeRoom,
) -> None:
    state = room.state
    choice = state.choice
    assert choice is not None
    seat = choice.seat
    board = state.boards[seat]
    if choice.kind == "equipment_limit":
        engine.act(
            room,
            room.players[seat],
            "choose_equipment",
            {"cardId": board.equipment[0]},
        )
    elif choice.kind in {"report_audit", "truth_serum"}:
        card_index = next(
            index for index, card in enumerate(board.cards) if not card.revealed
        )
        engine.act(
            room,
            room.players[seat],
            "choose_reveal",
            {"cardIndex": card_index},
        )
    elif choice.kind == "flashbang":
        engine.act(
            room,
            room.players[seat],
            "reorder_integrity",
            {"cardOrder": [2, 0, 1]},
        )
    elif choice.kind == "classified_redirect":
        assert choice.shooter_seat is not None
        target = engine._redirect_target_seats(state, choice.shooter_seat)[0]
        engine.act(
            room,
            room.players[seat],
            "choose_redirect",
            {"targetSeat": target},
        )
    else:
        target = next(
            target
            for target, target_board in state.boards.items()
            if target != seat and target_board.alive and not target_board.grenade_stage
        )
        engine.act(
            room,
            room.players[seat],
            "pass_grenade",
            {"targetSeat": target},
        )


def assert_equipment_interaction_invariants(
    engine: DepartedSuspicionEngine,
    room: ArcadeRoom,
) -> None:
    state = room.state
    wait_count = sum(
        wait is not None
        for wait in (state.pending_shot, state.post_shot, state.choice)
    )
    assert wait_count <= 1
    if state.pending_shot is not None or state.post_shot is not None:
        assert state.pending_action is None
    if room.phase == "finished":
        assert state.pending_action is None
        assert wait_count == 0
    elif state.pending_action is not None and state.choice is None:
        assert engine._response_seat(state.pending_action) is not None

    equipment_locations = list(state.equipment_deck)
    for seat, board in state.boards.items():
        equipment_locations.extend(board.equipment)
        if len(board.equipment) > 1:
            assert state.choice is not None
            assert state.choice.kind == "equipment_limit"
            assert state.choice.seat == seat
        if "planted_evidence" in board.effects:
            equipment_locations.append("planted_evidence")
        if board.grenade_stage:
            assert "grenade" in board.effects
            equipment_locations.append("grenade")
        else:
            assert "grenade" not in board.effects

    assert Counter(equipment_locations) == Counter(BOMBERS_EQUIPMENT_IDS)
    assert 0 <= engine._central_guns(state) <= state.gun_total


def test_automated_games_can_use_equipment_without_interaction_deadlocks() -> None:
    played_card_ids: set[str] = set()
    for player_count in range(4, 9):
        for seed in range(5):
            engine, room = make_room(
                player_count,
                seed=seed,
                deal_starting_equipment=True,
            )

            for _ in range(1_000):
                assert_equipment_interaction_invariants(engine, room)
                if room.phase == "finished":
                    break
                state = room.state
                if state.choice is not None:
                    resolve_automated_choice(engine, room)
                    continue
                if state.pending_shot is not None:
                    scanner = state.pending_shot.scanner_seat
                    assert scanner is not None
                    engine.act(room, room.players[scanner], "pass_scanner", {})
                    continue
                if state.post_shot is not None:
                    decision_seat = state.post_shot.seat
                    engine.act(
                        room,
                        room.players[decision_seat],
                        "pass_mobile_detonator",
                        {},
                    )
                    continue
                if state.pending_action is not None:
                    responder = engine._response_seat(state.pending_action)
                    assert responder is not None
                    options = engine.view(room, room.players[responder])["legal"][
                        "equipmentOptions"
                    ]
                    if options:
                        engine.act(
                            room,
                            room.players[responder],
                            "play_equipment",
                            first_equipment_payload(options[0]),
                        )
                    else:
                        engine.act(room, room.players[responder], "pass_response", {})
                    continue

                equipment_played = False
                for seat, board in state.boards.items():
                    if not board.alive:
                        continue
                    options = engine.view(room, room.players[seat])["legal"][
                        "equipmentOptions"
                    ]
                    if not options:
                        continue
                    engine.act(
                        room,
                        room.players[seat],
                        "play_equipment",
                        first_equipment_payload(options[0]),
                    )
                    equipment_played = True
                    break
                if equipment_played:
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
                        for target, target_board in state.boards.items()
                        if target != seat and target_board.alive
                    )
                    hidden = [
                        index
                        for index, card in enumerate(state.boards[seat].cards)
                        if not card.revealed
                    ]
                    payload = {"targetSeat": target}
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
                else:
                    target = engine._investigation_target_seats(state, seat)[0]
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

            assert room.phase == "finished", (
                f"{player_count}人局 seed={seed} 在装备交互状态中未能结束"
            )
            assert_equipment_interaction_invariants(engine, room)
            played_card_ids.update(
                play.card_id for play in room.state.equipment_play_history
            )

    # 监控摄像头需要紧接正常调查，已有专门的调查链测试；其余当前牌堆
    # 中的装备都必须在真实自动对局里至少完成一次结算。
    assert set(BOMBERS_EQUIPMENT_IDS) - played_card_ids == {"surveillance_camera"}


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
                decision_seat = state.post_shot.seat
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
                raise AssertionError(
                    f"存活玩家{seat}在第{state.turn_number}回合没有合法正常行动"
                )

        assert room.phase == "finished", (
            f"{player_count}人局 seed={seed} 在等待状态中未能结束"
        )
