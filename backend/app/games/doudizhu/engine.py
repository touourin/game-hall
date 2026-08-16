from __future__ import annotations

import itertools
import random
from dataclasses import dataclass, field
from typing import Any

from backend.app.arcade.bots import BotAvailability
from backend.app.arcade.models import ArcadePlayer, ArcadeRoom
from backend.app.games.base import GameRuleError


SUITS = ("spade", "heart", "club", "diamond")
VARIANTS = {"classic", "laizi", "no_shuffle"}
RANK_LABELS = {
    **{rank: str(rank) for rank in range(3, 11)},
    11: "J",
    12: "Q",
    13: "K",
    14: "A",
    15: "2",
    16: "小王",
    17: "大王",
}
PATTERN_LABELS = {
    "single": "单牌",
    "pair": "对子",
    "triple": "三张",
    "triple_single": "三带一",
    "triple_pair": "三带二",
    "straight": "顺子",
    "pair_straight": "连对",
    "airplane": "飞机",
    "airplane_single": "飞机带单",
    "airplane_pair": "飞机带对",
    "four_two_single": "四带二",
    "four_two_pair": "四带两对",
    "bomb": "炸弹",
    "rocket": "王炸",
}


@dataclass(frozen=True)
class Card:
    id: str
    rank: int
    suit: str | None

    def as_dict(self) -> dict[str, str | int | None]:
        return {
            "id": self.id,
            "rank": self.rank,
            "label": RANK_LABELS[self.rank],
            "suit": self.suit,
        }


@dataclass(frozen=True)
class PlayPattern:
    kind: str
    main_rank: int
    size: int
    sequence_length: int = 1
    bomb_level: int = 0

    def as_dict(self) -> dict[str, str | int]:
        return {
            "kind": self.kind,
            "label": PATTERN_LABELS[self.kind],
            "mainRank": self.main_rank,
            "size": self.size,
            "sequenceLength": self.sequence_length,
            "bombLevel": self.bomb_level,
        }


@dataclass
class DoudizhuState:
    hands: dict[int, list[Card]] = field(default_factory=dict)
    bottom_cards: list[Card] = field(default_factory=list)
    bids: list[dict[str, Any]] = field(default_factory=list)
    current_bidder: int = 0
    bidding_turns: int = 0
    landlord_candidate_seat: int | None = None
    landlord_seat: int | None = None
    current_seat: int | None = None
    last_play: dict[str, Any] | None = None
    last_play_seat: int | None = None
    pass_count: int = 0
    multiplier: int = 1
    multiplier_events: list[dict[str, Any]] = field(default_factory=list)
    play_counts: dict[int, int] = field(
        default_factory=lambda: {0: 0, 1: 0, 2: 0}
    )
    history: list[dict[str, Any]] = field(default_factory=list)
    played_cards: list[Card] = field(default_factory=list)
    wild_rank: int | None = None
    scores: dict[int, int] = field(default_factory=dict)
    settlement: dict[str, Any] | None = None
    next_deck: list[Card] | None = field(default=None, repr=False)
    variant: str = "classic"


def create_deck() -> list[Card]:
    cards = [
        Card(id=f"{rank}-{suit}", rank=rank, suit=suit)
        for rank in range(3, 16)
        for suit in SUITS
    ]
    cards.extend(
        [
            Card(id="joker-small", rank=16, suit=None),
            Card(id="joker-big", rank=17, suit=None),
        ]
    )
    return cards


def classify_cards(
    cards: list[Card],
    wild_rank: int | None = None,
    previous: PlayPattern | None = None,
) -> PlayPattern:
    candidates = _classification_candidates(cards, wild_rank)
    if previous is not None:
        candidates = [candidate for candidate in candidates if beats(candidate, previous)]
        if not candidates:
            raise GameRuleError("这手牌压不过上一手")
    if not candidates:
        raise GameRuleError("这些牌不能组成有效牌型")
    return max(candidates, key=_pattern_preference)


def _classification_candidates(
    cards: list[Card], wild_rank: int | None
) -> list[PlayPattern]:
    if not cards:
        raise GameRuleError("请选择要出的牌")
    if wild_rank is None:
        return [_classify_ranks([card.rank for card in cards])]

    wild_cards = [card for card in cards if card.rank == wild_rank]
    if not wild_cards or len(cards) == 1:
        return [_classify_ranks([card.rank for card in cards])]
    if len(cards) == 4 and len(wild_cards) == 4:
        return [PlayPattern("bomb", wild_rank, 4, bomb_level=3)]

    fixed_ranks = [card.rank for card in cards if card.rank != wild_rank]
    candidates: dict[tuple[str, int, int, int, int], PlayPattern] = {}
    for replacements in itertools.product(range(3, 16), repeat=len(wild_cards)):
        try:
            pattern = _classify_ranks([*fixed_ranks, *replacements])
        except GameRuleError:
            continue
        if pattern.kind == "bomb":
            pattern = PlayPattern(
                "bomb",
                pattern.main_rank,
                pattern.size,
                pattern.sequence_length,
                bomb_level=1,
            )
        key = (
            pattern.kind,
            pattern.main_rank,
            pattern.size,
            pattern.sequence_length,
            pattern.bomb_level,
        )
        candidates[key] = pattern
    return list(candidates.values())


def _classify_ranks(ranks_input: list[int]) -> PlayPattern:
    counts: dict[int, int] = {}
    for rank in ranks_input:
        counts[rank] = counts.get(rank, 0) + 1
    ranks = sorted(counts)
    size = len(ranks_input)

    if size == 2 and ranks == [16, 17]:
        return PlayPattern("rocket", 17, 2, bomb_level=4)
    if size == 4 and len(ranks) == 1:
        return PlayPattern("bomb", ranks[0], 4, bomb_level=2)
    if size == 1:
        return PlayPattern("single", ranks[0], 1)
    if size == 2 and len(ranks) == 1:
        return PlayPattern("pair", ranks[0], 2)
    if size == 3 and len(ranks) == 1:
        return PlayPattern("triple", ranks[0], 3)
    if size == 4 and sorted(counts.values()) == [1, 3]:
        main = next(rank for rank, count in counts.items() if count == 3)
        return PlayPattern("triple_single", main, 4)
    if size == 5 and sorted(counts.values()) == [2, 3]:
        main = next(rank for rank, count in counts.items() if count == 3)
        return PlayPattern("triple_pair", main, 5)
    if size >= 5 and all(count == 1 for count in counts.values()) and _is_sequence(ranks):
        return PlayPattern("straight", ranks[-1], size, len(ranks))
    if (
        size >= 6
        and size % 2 == 0
        and all(count == 2 for count in counts.values())
        and len(ranks) >= 3
        and _is_sequence(ranks)
    ):
        return PlayPattern("pair_straight", ranks[-1], size, len(ranks))

    if size % 3 == 0:
        sequence_length = size // 3
        for sequence in reversed(_triple_sequences(counts, sequence_length)):
            if len(counts) == sequence_length and all(
                counts[rank] == 3 for rank in sequence
            ):
                return PlayPattern("airplane", sequence[-1], size, sequence_length)
    if size % 4 == 0:
        sequence_length = size // 4
        for sequence in reversed(_triple_sequences(counts, sequence_length)):
            remaining = _remaining_counts(counts, sequence)
            if (
                sum(remaining.values()) == sequence_length
                and all(rank not in sequence for rank in remaining)
            ):
                return PlayPattern(
                    "airplane_single", sequence[-1], size, sequence_length
                )
    if size % 5 == 0:
        sequence_length = size // 5
        for sequence in reversed(_triple_sequences(counts, sequence_length)):
            remaining = _remaining_counts(counts, sequence)
            if len(remaining) == sequence_length and all(
                count == 2 for count in remaining.values()
            ):
                return PlayPattern("airplane_pair", sequence[-1], size, sequence_length)
    if size == 6 and 4 in counts.values():
        main = next(rank for rank, count in counts.items() if count == 4)
        remaining = {rank: count for rank, count in counts.items() if rank != main}
        if sum(remaining.values()) == 2:
            return PlayPattern("four_two_single", main, 6)
    if size == 8 and 4 in counts.values():
        main = next(rank for rank, count in counts.items() if count == 4)
        remaining = {rank: count for rank, count in counts.items() if rank != main}
        if len(remaining) == 2 and all(count == 2 for count in remaining.values()):
            return PlayPattern("four_two_pair", main, 8)
    raise GameRuleError("这些牌不能组成有效牌型")


def beats(candidate: PlayPattern, previous: PlayPattern) -> bool:
    if candidate.kind == "rocket":
        return previous.kind != "rocket"
    if previous.kind == "rocket":
        return False
    if candidate.kind == "bomb":
        if previous.kind != "bomb":
            return True
        if candidate.bomb_level != previous.bomb_level:
            return candidate.bomb_level > previous.bomb_level
        return candidate.main_rank > previous.main_rank
    if previous.kind == "bomb" or candidate.kind != previous.kind:
        return False
    return (
        candidate.size == previous.size
        and candidate.sequence_length == previous.sequence_length
        and candidate.main_rank > previous.main_rank
    )


def _pattern_preference(pattern: PlayPattern) -> tuple[int, int, int, int]:
    kind_priority = {
        "single": 1,
        "pair": 2,
        "triple": 3,
        "triple_single": 4,
        "triple_pair": 5,
        "straight": 6,
        "pair_straight": 7,
        "airplane": 8,
        "airplane_single": 9,
        "airplane_pair": 10,
        "four_two_single": 11,
        "four_two_pair": 12,
        "bomb": 20,
        "rocket": 30,
    }
    return (
        pattern.bomb_level,
        kind_priority.get(pattern.kind, 0),
        pattern.main_rank,
        pattern.sequence_length,
    )


def _is_sequence(ranks: list[int]) -> bool:
    return bool(ranks) and ranks[-1] <= 14 and all(
        right == left + 1 for left, right in zip(ranks, ranks[1:])
    )


def _triple_sequences(counts: dict[int, int], length: int) -> list[list[int]]:
    if length < 2:
        return []
    triple_ranks = sorted(
        rank for rank, count in counts.items() if count >= 3 and rank <= 14
    )
    sequences: list[list[int]] = []
    for start in range(len(triple_ranks) - length + 1):
        sequence = triple_ranks[start : start + length]
        if _is_sequence(sequence):
            sequences.append(sequence)
    return sequences


def _remaining_counts(
    counts: dict[int, int], sequence: list[int]
) -> dict[int, int]:
    remaining = dict(counts)
    for rank in sequence:
        remaining[rank] -= 3
    return {rank: count for rank, count in remaining.items() if count > 0}


class DoudizhuEngine:
    key = "doudizhu"
    name = "斗地主"
    min_players = 3
    max_players = 3
    bot_difficulties = ("douzero",)
    default_bot_difficulty = "douzero"
    bot_timeout_seconds = 8.0

    def __init__(self, rng: random.Random | random.SystemRandom | None = None) -> None:
        self.rng = rng or random.SystemRandom()
        from .bots import DoudizhuBotStrategy

        self.bot_strategy = DoudizhuBotStrategy(self, rng=self.rng)

    async def choose_bot_action_async(self, room: ArcadeRoom):
        return await self.bot_strategy.choose_action(room)

    def fallback_bot_action(self, room: ArcadeRoom):
        return self.bot_strategy.fallback_action(room)

    async def close(self) -> None:
        await self.bot_strategy.close()

    async def warm_up(self) -> None:
        await self.bot_strategy.warm_up()

    def bot_availability(self, room: ArcadeRoom) -> BotAvailability:
        if room.options.get("variant", "classic") == "laizi":
            return BotAvailability(False, "癞子玩法暂不支持 DouZero AI 玩家")
        if not getattr(
            self.bot_strategy.client,
            "available",
            self.bot_strategy.client.configured,
        ):
            return BotAvailability(
                False,
                "请先启用并正确配置 DouZero AI 引擎",
            )
        return BotAvailability(True)

    def room_options(self, options: dict[str, Any]) -> dict[str, Any]:
        variant = options.get("variant", "classic")
        if variant not in VARIANTS:
            raise GameRuleError("请选择经典、癞子或不洗牌玩法")
        return {"variant": variant}

    def initial_state(self) -> DoudizhuState:
        return DoudizhuState()

    def start(self, room: ArcadeRoom) -> None:
        previous = room.state if isinstance(room.state, DoudizhuState) else None
        variant = room.options.get("variant", "classic")
        if variant == "no_shuffle":
            deck = (
                list(previous.next_deck)
                if previous is not None and previous.next_deck is not None
                else self._initial_no_shuffle_deck()
            )
            if deck:
                cut = self.rng.randrange(len(deck))
                deck = deck[cut:] + deck[:cut]
        else:
            deck = create_deck()
            self.rng.shuffle(deck)
        state = DoudizhuState(
            hands={
                seat: self._sort_hand(deck[seat * 17 : (seat + 1) * 17])
                for seat in range(3)
            },
            bottom_cards=self._sort_hand(deck[51:]),
            variant=variant,
        )
        room.state = state
        room.phase = "bidding"

    def _initial_no_shuffle_deck(self) -> list[Card]:
        """Build a first-deal deck shaped like three sorted hands were gathered."""
        deck = create_deck()
        self.rng.shuffle(deck)
        gathered = [
            card
            for seat in range(3)
            for card in self._sort_hand(deck[seat * 17 : (seat + 1) * 17])
        ]
        gathered.extend(self._sort_hand(deck[51:]))
        return gathered

    def act(
        self,
        room: ArcadeRoom,
        player: ArcadePlayer,
        action: str,
        payload: dict[str, Any],
    ) -> None:
        if action == "resign":
            self._resign(room, player)
            return
        if room.phase == "bidding":
            if action != "bid":
                raise GameRuleError("请先完成叫地主")
            self._bid(room, player, payload)
            return
        if room.phase != "playing":
            raise GameRuleError("当前不能出牌")
        if action == "pass":
            self._pass(room, player)
        elif action == "play":
            self._play(room, player, payload)
        else:
            raise GameRuleError("不支持这个斗地主操作")

    def view(self, room: ArcadeRoom, viewer: ArcadePlayer) -> dict[str, Any]:
        state: DoudizhuState = room.state
        return {
            "phase": room.phase,
            "variant": state.variant,
            "currentPlayerId": (
                room.players[
                    state.current_bidder
                    if room.phase == "bidding"
                    else state.current_seat or 0
                ].id
                if room.phase in {"bidding", "playing"}
                else None
            ),
            "bids": [
                {
                    **bid,
                    "playerId": room.players[bid["seat"]].id,
                    "playerName": room.players[bid["seat"]].name,
                }
                for bid in state.bids
            ],
            "biddingMode": (
                "call" if state.landlord_candidate_seat is None else "rob"
            ),
            "landlordCandidatePlayerId": (
                room.players[state.landlord_candidate_seat].id
                if state.landlord_candidate_seat is not None
                else None
            ),
            "landlordPlayerId": (
                room.players[state.landlord_seat].id
                if state.landlord_seat is not None
                else None
            ),
            "bottomCards": [card.as_dict() for card in state.bottom_cards]
            if state.landlord_seat is not None
            else [],
            "hand": [card.as_dict() for card in state.hands.get(viewer.seat, [])],
            "cardCounts": {
                room.players[seat].id: len(state.hands.get(seat, []))
                for seat in range(len(room.players))
            },
            "teams": {
                room.players[seat].id: (
                    "landlord" if seat == state.landlord_seat else "farmer"
                )
                for seat in range(len(room.players))
            }
            if state.landlord_seat is not None
            else {},
            "lastPlay": state.last_play,
            "lastPlayPlayerId": (
                room.players[state.last_play_seat].id
                if state.last_play_seat is not None
                else None
            ),
            "multiplier": state.multiplier,
            "multiplierEvents": state.multiplier_events,
            "wildRank": state.wild_rank,
            "wildLabel": RANK_LABELS.get(state.wild_rank) if state.wild_rank else None,
            "history": [self._history_view(room, entry) for entry in state.history],
            "scores": {
                room.players[seat].id: score for seat, score in state.scores.items()
            },
            "settlement": state.settlement,
        }

    def player_result(
        self, room: ArcadeRoom, player: ArcadePlayer
    ) -> tuple[str, str, bool]:
        state: DoudizhuState = room.state
        team = "landlord" if player.seat == state.landlord_seat else "farmer"
        return team, team, player.id in room.winner_player_ids

    def _bid(
        self,
        room: ArcadeRoom,
        player: ArcadePlayer,
        payload: dict[str, Any],
    ) -> None:
        state: DoudizhuState = room.state
        if player.seat != state.current_bidder:
            raise GameRuleError("还没有轮到你叫地主")
        expected_positive = (
            "call" if state.landlord_candidate_seat is None else "rob"
        )
        decision = payload.get("decision")
        if decision not in {expected_positive, "pass"}:
            label = "叫地主" if expected_positive == "call" else "抢地主"
            raise GameRuleError(f"请选择{label}或不{label[0]}")
        state.bids.append({"seat": player.seat, "decision": decision})
        state.history.append(
            {"type": "bid", "seat": player.seat, "decision": decision}
        )

        if state.landlord_candidate_seat is None:
            state.bidding_turns += 1
            if decision == "call":
                state.landlord_candidate_seat = player.seat
                state.bidding_turns = 0
            elif state.bidding_turns >= 3:
                if state.variant == "no_shuffle":
                    state.next_deck = self._gather_for_next_deal(state)
                self.start(room)
                return
            state.current_bidder = (state.current_bidder + 1) % 3
            return

        state.bidding_turns += 1
        if decision == "rob":
            self._double(state, "抢地主", player.seat)
            state.landlord_candidate_seat = player.seat
        if state.bidding_turns >= 2:
            self._assign_landlord(room, state.landlord_candidate_seat)
            return
        state.current_bidder = (state.current_bidder + 1) % 3

    def _assign_landlord(self, room: ArcadeRoom, seat: int) -> None:
        state: DoudizhuState = room.state
        state.landlord_seat = seat
        state.hands[seat] = self._sort_hand(
            [*state.hands[seat], *state.bottom_cards]
        )
        state.current_seat = seat
        if state.variant == "laizi":
            state.wild_rank = self.rng.choice(list(range(3, 16)))
        state.history.append({"type": "landlord", "seat": seat})
        room.phase = "playing"

    def _play(
        self,
        room: ArcadeRoom,
        player: ArcadePlayer,
        payload: dict[str, Any],
    ) -> None:
        state: DoudizhuState = room.state
        if player.seat != state.current_seat:
            raise GameRuleError("还没有轮到你出牌")
        card_ids = payload.get("cardIds")
        if (
            not isinstance(card_ids, list)
            or not card_ids
            or not all(isinstance(card_id, str) for card_id in card_ids)
            or len(set(card_ids)) != len(card_ids)
        ):
            raise GameRuleError("请选择有效的手牌")
        hand_by_id = {card.id: card for card in state.hands[player.seat]}
        if any(card_id not in hand_by_id for card_id in card_ids):
            raise GameRuleError("选择的牌不在你的手牌中")
        cards = [hand_by_id[card_id] for card_id in card_ids]
        previous = self._last_pattern(state)
        pattern = classify_cards(cards, state.wild_rank, previous)
        selected = set(card_ids)
        state.hands[player.seat] = [
            card for card in state.hands[player.seat] if card.id not in selected
        ]
        sorted_cards = self._sort_hand(cards)
        state.last_play = {
            "cards": [card.as_dict() for card in sorted_cards],
            "pattern": pattern.as_dict(),
        }
        state.last_play_seat = player.seat
        state.pass_count = 0
        state.play_counts[player.seat] += 1
        state.played_cards.extend(sorted_cards)
        state.history.append(
            {
                "type": "play",
                "seat": player.seat,
                "cards": [card.as_dict() for card in sorted_cards],
                "pattern": pattern.as_dict(),
            }
        )
        if pattern.kind in {"bomb", "rocket"}:
            self._double(state, pattern.as_dict()["label"], player.seat)
        if not state.hands[player.seat]:
            self._finish(room, player)
            return
        state.current_seat = (player.seat + 1) % 3

    def _pass(self, room: ArcadeRoom, player: ArcadePlayer) -> None:
        state: DoudizhuState = room.state
        if player.seat != state.current_seat:
            raise GameRuleError("还没有轮到你出牌")
        if state.last_play is None or state.last_play_seat == player.seat:
            raise GameRuleError("新一轮必须出牌，不能不出")
        state.pass_count += 1
        state.history.append({"type": "pass", "seat": player.seat})
        if state.pass_count >= 2:
            leader = state.last_play_seat
            state.last_play = None
            state.last_play_seat = None
            state.pass_count = 0
            state.current_seat = leader
        else:
            state.current_seat = (player.seat + 1) % 3

    def _resign(self, room: ArcadeRoom, player: ArcadePlayer) -> None:
        state: DoudizhuState = room.state
        if state.landlord_seat is None:
            state.next_deck = (
                self._gather_for_next_deal(state)
                if state.variant == "no_shuffle"
                else None
            )
            room.finish("draw", [], f"{player.name} 退出叫地主，本局取消")
            return
        if player.seat == state.landlord_seat:
            self._settle(room, "farmers", f"地主 {player.name} 认输", spring=False)
        else:
            self._settle(room, "landlord", f"农民 {player.name} 认输", spring=False)

    def _finish(self, room: ArcadeRoom, player: ArcadePlayer) -> None:
        state: DoudizhuState = room.state
        winner = "landlord" if player.seat == state.landlord_seat else "farmers"
        role = "地主" if winner == "landlord" else "农民"
        self._settle(room, winner, f"{role} {player.name} 率先出完手牌", spring=True)

    def _settle(
        self,
        room: ArcadeRoom,
        winner: str,
        reason: str,
        *,
        spring: bool,
    ) -> None:
        state: DoudizhuState = room.state
        spring_name: str | None = None
        if spring and winner == "landlord" and all(
            state.play_counts[seat] == 0
            for seat in range(3)
            if seat != state.landlord_seat
        ):
            spring_name = "春天"
        elif spring and winner == "farmers" and state.landlord_seat is not None:
            if state.play_counts[state.landlord_seat] == 1:
                spring_name = "反春天"
        if spring_name is not None:
            self._double(state, spring_name, None)

        unit = state.multiplier
        landlord = state.landlord_seat
        if landlord is None:
            raise GameRuleError("尚未产生地主，无法结算")
        landlord_score = 2 * unit * (1 if winner == "landlord" else -1)
        state.scores = {
            seat: landlord_score if seat == landlord else -landlord_score // 2
            for seat in range(3)
        }
        state.settlement = {
            "baseScore": 1,
            "multiplier": state.multiplier,
            "spring": spring_name,
            "winner": winner,
        }
        if state.variant == "no_shuffle":
            state.next_deck = self._gather_for_next_deal(state)
        winners = (
            [room.players[landlord].id]
            if winner == "landlord"
            else [
                candidate.id
                for candidate in room.players
                if candidate.seat != landlord
            ]
        )
        suffix = f" · {spring_name}" if spring_name else ""
        room.finish(
            winner,
            winners,
            f"{reason}{suffix} · 最终倍数 ×{state.multiplier}",
        )

    @staticmethod
    def _double(state: DoudizhuState, reason: str, seat: int | None) -> None:
        state.multiplier *= 2
        state.multiplier_events.append(
            {"reason": reason, "seat": seat, "multiplier": state.multiplier}
        )

    @staticmethod
    def _last_pattern(state: DoudizhuState) -> PlayPattern | None:
        if state.last_play is None:
            return None
        raw = state.last_play["pattern"]
        return PlayPattern(
            kind=raw["kind"],
            main_rank=raw["mainRank"],
            size=raw["size"],
            sequence_length=raw["sequenceLength"],
            bomb_level=raw.get("bombLevel", 0),
        )

    @staticmethod
    def _history_view(room: ArcadeRoom, entry: dict[str, Any]) -> dict[str, Any]:
        seat = entry.get("seat")
        if not isinstance(seat, int) or not 0 <= seat < len(room.players):
            return dict(entry)
        return {
            **entry,
            "playerId": room.players[seat].id,
            "playerName": room.players[seat].name,
        }

    @staticmethod
    def _gather_for_next_deal(state: DoudizhuState) -> list[Card]:
        gathered = [*state.played_cards]
        seen = {card.id for card in gathered}
        for seat in range(3):
            for card in state.hands.get(seat, []):
                if card.id not in seen:
                    gathered.append(card)
                    seen.add(card.id)
        for card in state.bottom_cards:
            if card.id not in seen:
                gathered.append(card)
                seen.add(card.id)
        if len(gathered) != 54:
            return create_deck()
        return gathered

    @staticmethod
    def _sort_hand(cards: list[Card]) -> list[Card]:
        suit_order = {suit: index for index, suit in enumerate(SUITS)}
        return sorted(
            cards,
            key=lambda card: (card.rank, suit_order.get(card.suit, 9)),
        )
