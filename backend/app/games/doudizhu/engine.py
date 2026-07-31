from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any

from backend.app.arcade.models import ArcadePlayer, ArcadeRoom
from backend.app.games.base import GameRuleError


SUITS = ("spade", "heart", "club", "diamond")
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

    def as_dict(self) -> dict[str, str | int]:
        return {
            "kind": self.kind,
            "mainRank": self.main_rank,
            "size": self.size,
            "sequenceLength": self.sequence_length,
        }


@dataclass
class DoudizhuState:
    hands: dict[int, list[Card]] = field(default_factory=dict)
    bottom_cards: list[Card] = field(default_factory=list)
    bids: list[dict[str, int]] = field(default_factory=list)
    current_bidder: int = 0
    highest_bid: int = 0
    highest_bidder: int | None = None
    landlord_seat: int | None = None
    current_seat: int | None = None
    last_play: dict[str, Any] | None = None
    last_play_seat: int | None = None
    pass_count: int = 0


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


def classify_cards(cards: list[Card]) -> PlayPattern:
    if not cards:
        raise GameRuleError("请选择要出的牌")
    counts: dict[int, int] = {}
    for card in cards:
        counts[card.rank] = counts.get(card.rank, 0) + 1
    ranks = sorted(counts)
    size = len(cards)

    if size == 2 and ranks == [16, 17]:
        return PlayPattern("rocket", 17, 2)
    if size == 4 and len(ranks) == 1:
        return PlayPattern("bomb", ranks[0], 4)
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
    if (
        size >= 5
        and all(count == 1 for count in counts.values())
        and _is_sequence(ranks)
    ):
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
        sequence = _find_triple_sequence(counts, sequence_length)
        if sequence is not None and all(counts[rank] == 3 for rank in sequence):
            if len(counts) == sequence_length:
                return PlayPattern(
                    "airplane", sequence[-1], size, sequence_length
                )
    if size % 4 == 0:
        sequence_length = size // 4
        sequence = _find_triple_sequence(counts, sequence_length)
        if sequence is not None:
            remaining = _remaining_counts(counts, sequence)
            if sum(remaining.values()) == sequence_length:
                return PlayPattern(
                    "airplane_single", sequence[-1], size, sequence_length
                )
    if size % 5 == 0:
        sequence_length = size // 5
        sequence = _find_triple_sequence(counts, sequence_length)
        if sequence is not None:
            remaining = _remaining_counts(counts, sequence)
            if (
                len(remaining) == sequence_length
                and all(count == 2 for count in remaining.values())
            ):
                return PlayPattern(
                    "airplane_pair", sequence[-1], size, sequence_length
                )
    if size == 6 and 4 in counts.values():
        main = next(rank for rank, count in counts.items() if count == 4)
        return PlayPattern("four_two_single", main, 6)
    if size == 8 and 4 in counts.values():
        main = next(rank for rank, count in counts.items() if count == 4)
        remaining = {rank: count for rank, count in counts.items() if rank != main}
        if len(remaining) == 2 and all(count == 2 for count in remaining.values()):
            return PlayPattern("four_two_pair", main, 8)
    raise GameRuleError("这些牌不能组成有效牌型")


def beats(candidate: PlayPattern, previous: PlayPattern) -> bool:
    if candidate.kind == "rocket":
        return True
    if previous.kind == "rocket":
        return False
    if candidate.kind == "bomb" and previous.kind != "bomb":
        return True
    if candidate.kind != previous.kind:
        return False
    return (
        candidate.size == previous.size
        and candidate.sequence_length == previous.sequence_length
        and candidate.main_rank > previous.main_rank
    )


def _is_sequence(ranks: list[int]) -> bool:
    return bool(ranks) and ranks[-1] <= 14 and all(
        right == left + 1 for left, right in zip(ranks, ranks[1:])
    )


def _find_triple_sequence(
    counts: dict[int, int], length: int
) -> list[int] | None:
    if length < 2:
        return None
    triple_ranks = sorted(
        rank for rank, count in counts.items() if count >= 3 and rank <= 14
    )
    for start in range(len(triple_ranks) - length + 1):
        sequence = triple_ranks[start : start + length]
        if _is_sequence(sequence):
            return sequence
    return None


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

    def initial_state(self) -> DoudizhuState:
        return DoudizhuState()

    def start(self, room: ArcadeRoom) -> None:
        deck = create_deck()
        random.SystemRandom().shuffle(deck)
        state = DoudizhuState(
            hands={
                seat: self._sort_hand(deck[seat * 17 : (seat + 1) * 17])
                for seat in range(3)
            },
            bottom_cards=self._sort_hand(deck[51:]),
        )
        room.state = state
        room.phase = "bidding"

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
            "currentPlayerId": (
                room.players[
                    state.current_bidder
                    if room.phase == "bidding"
                    else state.current_seat or 0
                ].id
                if room.phase in {"bidding", "playing"}
                else None
            ),
            "bids": state.bids,
            "highestBid": state.highest_bid,
            "landlordPlayerId": (
                room.players[state.landlord_seat].id
                if state.landlord_seat is not None
                else None
            ),
            "bottomCards": [
                card.as_dict() for card in state.bottom_cards
            ]
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
        score = payload.get("score")
        if not isinstance(score, int) or isinstance(score, bool) or not 0 <= score <= 3:
            raise GameRuleError("叫分只能选择不叫、1 分、2 分或 3 分")
        if score and score <= state.highest_bid:
            raise GameRuleError("叫分必须高于当前最高分")
        state.bids.append({"seat": player.seat, "score": score})
        if score:
            state.highest_bid = score
            state.highest_bidder = player.seat
        if score == 3:
            self._assign_landlord(room, player.seat)
            return
        if len(state.bids) == 3:
            if state.highest_bidder is None:
                self.start(room)
                return
            self._assign_landlord(room, state.highest_bidder)
            return
        state.current_bidder = (state.current_bidder + 1) % 3

    def _assign_landlord(self, room: ArcadeRoom, seat: int) -> None:
        state: DoudizhuState = room.state
        state.landlord_seat = seat
        state.hands[seat] = self._sort_hand(
            [*state.hands[seat], *state.bottom_cards]
        )
        state.current_seat = seat
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
        pattern = classify_cards(cards)
        if state.last_play is not None:
            previous = PlayPattern(
                kind=state.last_play["pattern"]["kind"],
                main_rank=state.last_play["pattern"]["mainRank"],
                size=state.last_play["pattern"]["size"],
                sequence_length=state.last_play["pattern"]["sequenceLength"],
            )
            if not beats(pattern, previous):
                raise GameRuleError("这手牌压不过上一手")
        selected = set(card_ids)
        state.hands[player.seat] = [
            card for card in state.hands[player.seat] if card.id not in selected
        ]
        state.last_play = {
            "cards": [card.as_dict() for card in self._sort_hand(cards)],
            "pattern": pattern.as_dict(),
        }
        state.last_play_seat = player.seat
        state.pass_count = 0
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
            raise GameRuleError("叫地主阶段不能认输")
        if player.seat == state.landlord_seat:
            winners = [
                candidate.id
                for candidate in room.players
                if candidate.seat != state.landlord_seat
            ]
            room.finish("farmers", winners, f"地主 {player.name} 认输")
        else:
            landlord = room.players[state.landlord_seat]
            room.finish("landlord", [landlord.id], f"农民 {player.name} 认输")

    def _finish(self, room: ArcadeRoom, player: ArcadePlayer) -> None:
        state: DoudizhuState = room.state
        if player.seat == state.landlord_seat:
            room.finish("landlord", [player.id], f"地主 {player.name} 率先出完手牌")
        else:
            winners = [
                candidate.id
                for candidate in room.players
                if candidate.seat != state.landlord_seat
            ]
            room.finish("farmers", winners, f"农民 {player.name} 率先出完手牌")

    @staticmethod
    def _sort_hand(cards: list[Card]) -> list[Card]:
        suit_order = {suit: index for index, suit in enumerate(SUITS)}
        return sorted(
            cards,
            key=lambda card: (card.rank, suit_order.get(card.suit, 9)),
        )
