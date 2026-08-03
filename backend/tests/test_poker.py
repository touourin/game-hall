from __future__ import annotations

import random

import pytest

from backend.app.arcade.models import ArcadePlayer, ArcadeRoom
from backend.app.games.base import GameRuleError
from backend.app.games.poker.engine import (
    PokerCard,
    PokerEngine,
    build_side_pots,
    evaluate_best,
    evaluate_five,
    hand_name,
)


def cards(spec: str) -> list[PokerCard]:
    suit_names = {"s": "spade", "h": "heart", "d": "diamond", "c": "club"}
    rank_names = {
        "A": 14,
        "K": 13,
        "Q": 12,
        "J": 11,
        "T": 10,
        "9": 9,
        "8": 8,
        "7": 7,
        "6": 6,
        "5": 5,
        "4": 4,
        "3": 3,
        "2": 2,
    }
    result = []
    for token in spec.split():
        rank = rank_names[token[0]]
        suit = suit_names[token[1]]
        result.append(PokerCard(id=token, rank=rank, suit=suit))
    return result


def make_room(player_count: int = 3) -> tuple[PokerEngine, ArcadeRoom]:
    engine = PokerEngine(random.Random(7))
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
        code="TEST",
        game_key="poker",
        host_id="p0",
        players=players,
        state=engine.initial_state(),
        options={"startingChips": 1000, "smallBlind": 10},
        game_id="poker-test",
        started_at="2026-08-01T00:00:00+00:00",
    )
    engine.start(room)
    return engine, room


def test_poker_hand_evaluator_covers_major_categories_and_wheel() -> None:
    royal = evaluate_five(cards("As Ks Qs Js Ts"))
    quads = evaluate_five(cards("Ah Ad Ac As 2d"))
    full_house = evaluate_five(cards("Kh Kd Ks 2c 2d"))
    wheel = evaluate_five(cards("As 2d 3h 4c 5s"))

    assert royal > quads > full_house > wheel
    assert royal == (8, 14)
    assert wheel == (4, 5)
    assert hand_name(royal) == "皇家同花顺"
    assert evaluate_best(cards("As Ad Kc Qh 9s 4d 2c"))[0] == 1


def test_poker_hand_evaluator_orders_every_category() -> None:
    hands = [
        evaluate_five(cards(spec))
        for spec in [
            "As Ks Qs Js Ts",
            "Ah Ad Ac As 2d",
            "Kh Kd Ks 2c 2d",
            "Ah Jh 8h 4h 2h",
            "9s 8d 7h 6c 5s",
            "Qh Qd Qs 8c 2d",
            "Jh Jd 4s 4c 9d",
            "Th Td As 7c 2d",
            "As Jd 8h 4c 2s",
        ]
    ]

    assert hands == sorted(hands, reverse=True)


def test_poker_posts_blinds_deals_private_cards_and_starts_left_of_big_blind() -> None:
    engine, room = make_room(3)
    state = room.state

    assert room.phase == "playing"
    assert state.dealer_player_id == "p0"
    assert state.small_blind_player_id == "p1"
    assert state.big_blind_player_id == "p2"
    assert state.action_player_id == "p0"
    assert state.pot == 30
    assert state.street_bets == {"p0": 0, "p1": 10, "p2": 20}
    assert all(len(hand) == 2 for hand in state.hands.values())
    assert len(state.deck) == 46
    assert engine.view(room, room.players[0])["legalActions"]["callAmount"] == 20


def test_heads_up_deals_the_button_last_card() -> None:
    class OrderedDeck:
        @staticmethod
        def shuffle(deck: list[PokerCard]) -> None:
            return None

    engine = PokerEngine(OrderedDeck())  # type: ignore[arg-type]
    players = [
        ArcadePlayer(
            id=f"p{seat}",
            account_id=f"a{seat}",
            name=f"玩家{seat + 1}",
            token_hash=f"token-{seat}",
            seat=seat,
        )
        for seat in range(2)
    ]
    room = ArcadeRoom(
        code="HEAD",
        game_key="poker",
        host_id="p0",
        players=players,
        state=engine.initial_state(),
        options={"startingChips": 1000, "smallBlind": 10},
    )

    engine.start(room)

    assert [card.id for card in room.state.hands["p1"]] == [
        "club-14",
        "club-12",
    ]
    assert [card.id for card in room.state.hands["p0"]] == [
        "club-13",
        "club-11",
    ]


def test_poker_requires_turn_and_minimum_raise() -> None:
    engine, room = make_room(3)

    with pytest.raises(GameRuleError, match="轮到"):
        engine.act(room, room.players[1], "call", {})
    with pytest.raises(GameRuleError, match="至少需要加注到 40"):
        engine.act(room, room.players[0], "raise", {"raiseTo": 30})

    engine.act(room, room.players[0], "raise", {"raiseTo": 60})
    assert room.state.current_bet == 60
    assert room.state.pot == 90
    assert room.state.action_player_id == "p1"
    assert room.state.history[-1]["amount"] == 60
    assert room.state.history[-1]["streetBet"] == 60

    engine.act(room, room.players[1], "raise", {"raiseTo": 100})
    assert room.state.history[-1]["amount"] == 90
    assert room.state.history[-1]["streetBet"] == 100


def test_short_all_in_requires_calls_without_reopening_the_raise() -> None:
    engine, room = make_room(3)
    state = room.state

    engine.act(room, room.players[0], "call", {})
    state.chips["p1"] = 25
    engine.act(room, room.players[1], "all_in", {})

    assert state.current_bet == 35
    assert state.minimum_raise == 20
    assert state.action_player_id == "p2"
    engine.act(room, room.players[2], "call", {})

    legal = engine.view(room, room.players[0])["legalActions"]
    assert state.action_player_id == "p0"
    assert legal["callAmount"] == 15
    assert legal["canCall"] is True
    assert legal["canRaise"] is False
    assert legal["canAllIn"] is False
    with pytest.raises(GameRuleError, match="不能再次加注"):
        engine.act(room, room.players[0], "raise", {"raiseTo": 60})


def test_poker_finishes_the_hand_when_everyone_else_folds() -> None:
    engine, room = make_room(3)

    engine.act(room, room.players[0], "fold", {})
    engine.act(room, room.players[1], "fold", {})

    assert room.phase == "between_hands"
    assert room.winner_player_ids == []
    assert room.state.payouts["p2"] == 30
    assert room.state.chips["p2"] == 1010
    assert room.state.showdown is False


def test_poker_all_in_player_cannot_resign_or_muck_the_hand() -> None:
    engine, room = make_room(3)

    engine.act(room, room.players[0], "all_in", {})

    with pytest.raises(GameRuleError, match="已经全押"):
        engine.act(room, room.players[0], "resign", {})
    assert "p0" not in room.state.folded_ids


def test_poker_match_record_removes_deck_and_hides_unrevealed_hands() -> None:
    engine, room = make_room(3)
    engine.act(room, room.players[0], "fold", {})
    engine.act(room, room.players[1], "fold", {})

    recorded = engine.record_state(room)

    assert "deck" not in recorded
    assert "burned" not in recorded
    assert all(hand == [] for hand in recorded["hands"].values())


def test_poker_checkdown_deals_all_community_cards_and_reveals_showdown() -> None:
    engine, room = make_room(2)
    state = room.state

    assert state.action_player_id == "p0"
    engine.act(room, room.players[0], "call", {})
    engine.act(room, room.players[1], "check", {})
    assert state.street == "flop"
    assert len(state.community) == 3

    for _ in range(3):
        first_id = state.action_player_id
        first = room.player(first_id)
        engine.act(room, first, "check", {})
        second = room.player(state.action_player_id)
        engine.act(room, second, "check", {})

    assert room.phase == "between_hands"
    assert state.showdown is True
    assert state.street == "showdown"
    assert len(state.community) == 5
    assert sum(state.payouts.values()) == state.pot == 40
    assert sum(state.chips.values()) == 2000


def test_poker_next_hand_preserves_chips_and_rotates_the_dealer() -> None:
    engine, room = make_room(2)
    state = room.state

    engine.act(room, room.players[0], "fold", {})
    assert room.phase == "between_hands"
    assert state.chips == {"p0": 990, "p1": 1010}
    assert state.dealer_player_id == "p0"

    engine.act(room, room.players[0], "ready_next_hand", {})
    assert room.phase == "between_hands"
    engine.act(room, room.players[1], "ready_next_hand", {})

    assert room.phase == "playing"
    assert state.hand_number == 2
    assert state.dealer_player_id == "p1"
    assert state.chips == {"p0": 970, "p1": 1000}
    assert state.pot == 30
    assert sum(state.chips.values()) + state.pot == 2000


def test_poker_resignation_eliminates_player_and_finishes_heads_up_table() -> None:
    engine, room = make_room(2)

    engine.act(room, room.players[0], "resign", {})

    assert room.phase == "finished"
    assert room.winner_player_ids == ["p1"]
    assert room.state.eliminated_ids == ["p0"]
    assert room.state.chips["p0"] == 0
    assert "赢得本桌" in (room.win_reason or "")


def test_poker_all_in_bust_finishes_the_table_with_conserved_chips() -> None:
    engine, room = make_room(2)

    engine.act(room, room.player(room.state.action_player_id), "all_in", {})
    engine.act(room, room.player(room.state.action_player_id), "call", {})

    assert room.phase == "finished"
    assert len(room.winner_player_ids) == 1
    assert len(room.state.eliminated_ids) == 1
    assert sum(room.state.chips.values()) == 2000
    assert len(room.state.hand_summaries) == 1


def test_poker_players_can_leave_between_hands_without_resetting_the_table() -> None:
    engine, room = make_room(3)
    state = room.state
    engine.act(room, room.players[0], "fold", {})
    engine.act(room, room.players[1], "fold", {})

    assert room.phase == "between_hands"
    assert engine.manual_forfeit(room, room.players[0]) is True
    assert room.phase == "between_hands"
    assert state.chips["p0"] == 0
    assert state.eliminated_ids == ["p0"]

    assert engine.manual_forfeit(room, room.players[1]) is True
    assert room.phase == "finished"
    assert room.winner_player_ids == ["p2"]
    assert len(state.hand_summaries) == 1


def test_poker_side_pots_pay_each_layer_to_its_best_eligible_hand() -> None:
    scores = {
        "short": (6, 14, 13),
        "middle": (4, 12),
        "deep": (1, 10, 14, 9, 8),
    }
    payouts, pots = build_side_pots(
        {"short": 100, "middle": 300, "deep": 300},
        set(),
        scores,
        ["short", "middle", "deep"],
    )

    assert payouts == {"short": 300, "middle": 400, "deep": 0}
    assert [pot["amount"] for pot in pots] == [300, 400]
    assert pots[0]["handName"] == "葫芦"
    assert pots[1]["winnerIds"] == ["middle"]


def test_poker_hides_opponents_cards_until_showdown() -> None:
    engine, room = make_room(3)

    view = engine.view(room, room.players[0])
    own = next(player for player in view["players"] if player["id"] == "p0")
    opponent = next(player for player in view["players"] if player["id"] == "p1")

    assert len(own["cards"]) == 2
    assert opponent["cards"] == []
    assert opponent["cardCount"] == 2
