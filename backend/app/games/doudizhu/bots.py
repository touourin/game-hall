from __future__ import annotations

import asyncio
import copy
import itertools
import os
import random
from collections import Counter
from dataclasses import dataclass
from functools import cache
from typing import TYPE_CHECKING, Any

from backend.app.ai import DouZeroClient
from backend.app.arcade.bots import BotAction
from backend.app.arcade.models import ArcadePlayer, ArcadeRoom
from backend.app.games.base import GameRuleError

from .engine import (
    Card,
    PlayPattern,
    _classify_ranks,
    beats,
    create_deck,
)

if TYPE_CHECKING:
    from .engine import DoudizhuEngine, DoudizhuState


RANKS = tuple(range(3, 18))
NORMAL_RANKS = tuple(range(3, 16))
SEQUENCE_RANKS = tuple(range(3, 15))
DECK_CAPACITY = {
    **{rank: 4 for rank in NORMAL_RANKS},
    16: 1,
    17: 1,
}
DEFAULT_BID_SAMPLES = 32
CALL_FAVORABLE_RATIO = 0.56
ROB_FAVORABLE_RATIO = 0.66
DouZeroInfoSet = dict[str, Any]


@dataclass(frozen=True)
class LegalPlay:
    cards: tuple[Card, ...]
    pattern: PlayPattern


@dataclass(frozen=True)
class RankPattern:
    counts: tuple[int, ...]
    pattern: PlayPattern


class DoudizhuBotStrategy:
    def __init__(
        self,
        engine: DoudizhuEngine,
        client: DouZeroClient | None = None,
        rng: random.Random | random.SystemRandom | None = None,
        bid_samples: int | None = None,
    ) -> None:
        self.engine = engine
        self.client = client or DouZeroClient()
        self.rng = rng or random.SystemRandom()
        self.bid_samples = (
            bid_samples
            if bid_samples is not None
            else int(os.getenv("DOUZERO_BID_SAMPLES", str(DEFAULT_BID_SAMPLES)))
        )
        if not 1 <= self.bid_samples <= 256:
            raise ValueError("DouZero 叫抢采样数必须在 1 到 256 之间")

    async def choose_action(self, room: ArcadeRoom) -> BotAction | None:
        bot = self._active_bot(room)
        if bot is None:
            return None
        if room.phase == "bidding":
            return await self._bid_action(room, bot)

        state: DoudizhuState = room.state
        if state.variant == "laizi" or not getattr(
            self.client, "configured", True
        ):
            return await asyncio.to_thread(self.fallback_action, room)

        plays = await asyncio.to_thread(self.legal_plays, state, bot.seat)
        can_pass = self._can_pass(state, bot.seat)
        if not plays and not can_pass:
            return None
        infoset = self._douzero_infoset(room, bot, plays, can_pass)
        selected_ranks = await self.client.best_action(infoset)
        if not selected_ranks:
            selected = BotAction(bot.id, "pass") if can_pass else None
        else:
            selected_key = tuple(sorted(selected_ranks))
            play = next(
                (
                    candidate
                    for candidate in plays
                    if self._douzero_cards(candidate.cards) == selected_key
                ),
                None,
            )
            selected = (
                BotAction(
                    bot.id,
                    "play",
                    {"cardIds": [card.id for card in play.cards]},
                )
                if play is not None
                else None
            )
        if selected is None or not await asyncio.to_thread(
            self._is_legal, room, selected
        ):
            return await asyncio.to_thread(self.fallback_action, room)
        return selected

    def fallback_action(self, room: ArcadeRoom) -> BotAction | None:
        bot = self._active_bot(room)
        if bot is None:
            return None
        if room.phase == "bidding":
            return BotAction(bot.id, "bid", {"decision": "pass"})

        state: DoudizhuState = room.state
        can_pass = self._can_pass(state, bot.seat)
        if can_pass:
            return BotAction(bot.id, "pass")
        plays = self.legal_plays(state, bot.seat)
        if not plays:
            return None
        selected_play = plays[0]
        return BotAction(
            bot.id,
            "play",
            {"cardIds": [card.id for card in selected_play.cards]},
        )

    async def close(self) -> None:
        await self.client.close()

    async def warm_up(self) -> None:
        warmer = getattr(self.client, "warm_up", None)
        if callable(warmer):
            await warmer()

    def legal_plays(
        self,
        state: DoudizhuState,
        seat: int,
    ) -> list[LegalPlay]:
        hand = state.hands.get(seat, [])
        previous = self.engine._last_pattern(state)
        return self._legal_plays_for_hand(hand, previous)

    @staticmethod
    def _legal_plays_for_hand(
        hand: list[Card],
        previous: PlayPattern | None = None,
    ) -> list[LegalPlay]:
        by_rank: dict[int, list[Card]] = {
            rank: sorted(
                (card for card in hand if card.rank == rank),
                key=lambda card: card.id,
            )
            for rank in RANKS
        }
        candidates: list[LegalPlay] = []

        for rank_pattern in _rank_pattern_universe():
            cards = _realize_rank_pattern(rank_pattern, by_rank)
            if cards is None:
                continue
            pattern = rank_pattern.pattern
            if previous is not None and not beats(pattern, previous):
                continue
            candidates.append(LegalPlay(cards, pattern))

        return sorted(
            candidates,
            key=lambda play: (
                play.pattern.bomb_level,
                play.pattern.main_rank,
                -len(play.cards),
                tuple(card.id for card in play.cards),
            ),
        )

    async def _bid_action(
        self,
        room: ArcadeRoom,
        bot: ArcadePlayer,
    ) -> BotAction:
        state: DoudizhuState = room.state
        expected = "call" if state.landlord_candidate_seat is None else "rob"
        infosets = await asyncio.to_thread(
            self._opening_infosets,
            state.hands.get(bot.seat, []),
        )
        values = await self.client.opening_values(infosets)
        favorable_ratio = sum(value > 0 for value in values) / len(values)
        threshold = (
            CALL_FAVORABLE_RATIO if expected == "call" else ROB_FAVORABLE_RATIO
        )
        positive = favorable_ratio >= threshold
        return BotAction(
            bot.id,
            "bid",
            {"decision": expected if positive else "pass"},
        )

    def _opening_infosets(self, hand: list[Card]) -> list[DouZeroInfoSet]:
        hand_ids = {card.id for card in hand}
        unknown_cards = [card for card in create_deck() if card.id not in hand_ids]
        sampled_bottoms = [
            self.rng.sample(unknown_cards, 3)
            for _ in range(self.bid_samples)
        ]

        infosets: list[DouZeroInfoSet] = []
        for bottom in sampled_bottoms:
            landlord_hand = [*hand, *bottom]
            plays = self._legal_plays_for_hand(landlord_hand)
            bottom_ids = {card.id for card in bottom}
            other_cards = [
                card for card in unknown_cards if card.id not in bottom_ids
            ]
            infosets.append(
                {
                    "position": "landlord",
                    "playerHandCards": list(self._douzero_cards(landlord_hand)),
                    "otherHandCards": list(self._douzero_cards(other_cards)),
                    "threeLandlordCards": list(self._douzero_cards(bottom)),
                    "legalActions": [
                        list(self._douzero_cards(play.cards)) for play in plays
                    ],
                    "cardPlayActionSeq": [],
                    "lastMove": [],
                    "lastTwoMoves": [[], []],
                    "lastMoveDict": {
                        "landlord": [],
                        "landlord_up": [],
                        "landlord_down": [],
                    },
                    "playedCards": {
                        "landlord": [],
                        "landlord_up": [],
                        "landlord_down": [],
                    },
                    "numCardsLeftDict": {
                        "landlord": 20,
                        "landlord_up": 17,
                        "landlord_down": 17,
                    },
                    "lastPid": "landlord",
                    "bombNum": 0,
                }
            )
        return infosets

    def _douzero_infoset(
        self,
        room: ArcadeRoom,
        bot: ArcadePlayer,
        plays: list[LegalPlay],
        can_pass: bool,
    ) -> DouZeroInfoSet:
        state: DoudizhuState = room.state
        if state.landlord_seat is None:
            raise RuntimeError("地主尚未确定")
        positions = {
            state.landlord_seat: "landlord",
            (state.landlord_seat + 1) % 3: "landlord_down",
            (state.landlord_seat - 1) % 3: "landlord_up",
        }
        position = positions[bot.seat]
        played_cards = {role: [] for role in positions.values()}
        last_move_dict = {role: [] for role in positions.values()}
        action_sequence: list[list[int]] = []
        last_pid = "landlord"
        bomb_num = 0
        for entry in state.history:
            if entry.get("type") not in {"play", "pass"}:
                continue
            seat = entry.get("seat")
            if not isinstance(seat, int) or seat not in positions:
                continue
            role = positions[seat]
            cards = entry.get("cards", []) if entry.get("type") == "play" else []
            action = sorted(
                self._douzero_rank(int(card["rank"]))
                for card in cards
                if isinstance(card, dict) and isinstance(card.get("rank"), int)
            )
            action_sequence.append(action)
            last_move_dict[role] = action
            if action:
                played_cards[role].extend(action)
                last_pid = role
                pattern = entry.get("pattern")
                if isinstance(pattern, dict) and pattern.get("kind") in {
                    "bomb",
                    "rocket",
                }:
                    bomb_num += 1

        hand = state.hands[bot.seat]
        known_counter = Counter(self._douzero_rank(card.rank) for card in create_deck())
        known_counter.subtract(self._douzero_cards(hand))
        for cards in played_cards.values():
            known_counter.subtract(cards)
        other_hand_cards = sorted(
            rank
            for rank, count in known_counter.items()
            for _ in range(max(0, count))
        )
        last_two_moves: list[list[int]] = [[], []]
        for action in action_sequence[-2:]:
            last_two_moves.insert(0, action)
            last_two_moves = last_two_moves[:2]
        bottom_counter = Counter(
            self._douzero_rank(card.rank) for card in state.bottom_cards
        )
        bottom_counter.subtract(played_cards["landlord"])
        legal_actions = [list(self._douzero_cards(play.cards)) for play in plays]
        if can_pass:
            legal_actions.append([])

        return {
            "position": position,
            "playerHandCards": list(self._douzero_cards(hand)),
            "otherHandCards": other_hand_cards,
            "threeLandlordCards": sorted(
                rank
                for rank, count in bottom_counter.items()
                for _ in range(max(0, count))
            ),
            "legalActions": legal_actions,
            "cardPlayActionSeq": action_sequence,
            "lastMove": (
                sorted(
                    self._douzero_rank(int(card["rank"]))
                    for card in state.last_play.get("cards", [])
                )
                if state.last_play is not None
                else []
            ),
            "lastTwoMoves": last_two_moves,
            "lastMoveDict": last_move_dict,
            "playedCards": played_cards,
            "numCardsLeftDict": {
                role: len(state.hands[seat]) for seat, role in positions.items()
            },
            "lastPid": last_pid,
            "bombNum": bomb_num,
        }

    def _is_legal(self, room: ArcadeRoom, action: BotAction) -> bool:
        clone = copy.deepcopy(room)
        try:
            self.engine.act(
                clone,
                clone.player(action.player_id),
                action.action,
                dict(action.payload),
            )
        except (GameRuleError, IndexError, KeyError, TypeError, ValueError):
            return False
        return True

    @staticmethod
    def _can_pass(state: DoudizhuState, seat: int) -> bool:
        return state.last_play is not None and state.last_play_seat != seat

    @staticmethod
    def _douzero_rank(rank: int) -> int:
        return {15: 17, 16: 20, 17: 30}.get(rank, rank)

    @classmethod
    def _douzero_cards(cls, cards: list[Card] | tuple[Card, ...]) -> tuple[int, ...]:
        return tuple(sorted(cls._douzero_rank(card.rank) for card in cards))

    @staticmethod
    def _active_bot(room: ArcadeRoom) -> ArcadePlayer | None:
        if len(room.players) != 3:
            return None
        state: DoudizhuState = room.state
        if room.phase == "bidding":
            player = room.players[state.current_bidder]
        elif room.phase == "playing" and state.current_seat is not None:
            player = room.players[state.current_seat]
        else:
            return None
        return player if player.is_bot else None


def _counts(ranks: tuple[int, ...] | list[int]) -> tuple[int, ...]:
    counter = Counter(ranks)
    return tuple(counter[rank] for rank in RANKS)


def _add_rank_pattern(
    patterns: dict[tuple[int, ...], RankPattern],
    ranks: tuple[int, ...] | list[int],
) -> None:
    if not ranks or len(ranks) > 20:
        return
    counts = _counts(ranks)
    if any(count > DECK_CAPACITY[rank] for rank, count in zip(RANKS, counts)):
        return
    try:
        pattern = _classify_ranks(list(ranks))
    except GameRuleError:
        return
    patterns[counts] = RankPattern(counts, pattern)


@cache
def _rank_pattern_universe() -> tuple[RankPattern, ...]:
    patterns: dict[tuple[int, ...], RankPattern] = {}
    for rank in RANKS:
        _add_rank_pattern(patterns, [rank])
    for rank in NORMAL_RANKS:
        _add_rank_pattern(patterns, [rank] * 2)
        _add_rank_pattern(patterns, [rank] * 3)
        _add_rank_pattern(patterns, [rank] * 4)
        for kicker in RANKS:
            if kicker != rank:
                _add_rank_pattern(patterns, [rank] * 3 + [kicker])
        for kicker in NORMAL_RANKS:
            if kicker != rank:
                _add_rank_pattern(patterns, [rank] * 3 + [kicker] * 2)
    _add_rank_pattern(patterns, [16, 17])

    for length in range(5, len(SEQUENCE_RANKS) + 1):
        for start in range(3, 16 - length):
            sequence = list(range(start, start + length))
            _add_rank_pattern(patterns, sequence)
    for length in range(3, 11):
        for start in range(3, 16 - length):
            sequence = list(range(start, start + length))
            _add_rank_pattern(patterns, sequence * 2)
    for length in range(2, 7):
        for start in range(3, 16 - length):
            sequence = tuple(range(start, start + length))
            core = [rank for rank in sequence for _ in range(3)]
            _add_rank_pattern(patterns, core)
            capacities = tuple(
                (rank, DECK_CAPACITY[rank])
                for rank in RANKS
                if rank not in sequence
            )
            if len(core) + length <= 20:
                for wings in _multiset_choices(capacities, length):
                    _add_rank_pattern(patterns, [*core, *wings])
            if len(core) + length * 2 <= 20:
                pair_ranks = [
                    rank
                    for rank in NORMAL_RANKS
                    if rank not in sequence
                ]
                for wings in itertools.combinations(pair_ranks, length):
                    _add_rank_pattern(
                        patterns,
                        [*core, *(rank for rank in wings for _ in range(2))],
                    )

    for bomb_rank in NORMAL_RANKS:
        capacities = tuple(
            (rank, DECK_CAPACITY[rank])
            for rank in RANKS
            if rank != bomb_rank
        )
        for wings in _multiset_choices(capacities, 2):
            _add_rank_pattern(patterns, [bomb_rank] * 4 + list(wings))
        for wings in itertools.combinations(
            (rank for rank in NORMAL_RANKS if rank != bomb_rank),
            2,
        ):
            _add_rank_pattern(
                patterns,
                [bomb_rank] * 4 + [rank for rank in wings for _ in range(2)],
            )
    return tuple(patterns.values())


def _multiset_choices(
    capacities: tuple[tuple[int, int], ...],
    total: int,
) -> list[tuple[int, ...]]:
    choices: list[tuple[int, ...]] = []

    def visit(index: int, remaining: int, selected: list[int]) -> None:
        if remaining == 0:
            choices.append(tuple(selected))
            return
        if index >= len(capacities):
            return
        rank, capacity = capacities[index]
        for count in range(min(capacity, remaining) + 1):
            selected.extend([rank] * count)
            visit(index + 1, remaining - count, selected)
            if count:
                del selected[-count:]

    visit(0, total, [])
    return choices


def _realize_rank_pattern(
    rank_pattern: RankPattern,
    by_rank: dict[int, list[Card]],
) -> tuple[Card, ...] | None:
    selected: list[Card] = []
    for rank, required in zip(RANKS, rank_pattern.counts):
        if not required:
            continue
        cards = by_rank[rank]
        if len(cards) < required:
            return None
        selected.extend(cards[:required])
    return tuple(selected)
