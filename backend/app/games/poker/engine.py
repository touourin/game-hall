from __future__ import annotations

import itertools
import random
from collections import Counter
from dataclasses import asdict, dataclass, field
from typing import Any

from backend.app.arcade.models import ArcadePlayer, ArcadeRoom
from backend.app.games.base import GameRuleError


SUITS = ("spade", "heart", "diamond", "club")
SUIT_SYMBOLS = {
    "spade": "♠",
    "heart": "♥",
    "diamond": "♦",
    "club": "♣",
}
RANK_LABELS = {
    14: "A",
    13: "K",
    12: "Q",
    11: "J",
    10: "10",
    9: "9",
    8: "8",
    7: "7",
    6: "6",
    5: "5",
    4: "4",
    3: "3",
    2: "2",
}
HAND_NAMES = {
    8: "同花顺",
    7: "四条",
    6: "葫芦",
    5: "同花",
    4: "顺子",
    3: "三条",
    2: "两对",
    1: "一对",
    0: "高牌",
}
STREETS = ("preflop", "flop", "turn", "river")
STREET_LABELS = {
    "preflop": "翻牌前",
    "flop": "翻牌",
    "turn": "转牌",
    "river": "河牌",
    "showdown": "摊牌",
}
STARTING_CHIP_OPTIONS = {500, 1000, 2000}
SMALL_BLIND_OPTIONS = {5, 10, 20}


@dataclass(frozen=True)
class PokerCard:
    id: str
    rank: int
    suit: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "rank": self.rank,
            "rankLabel": RANK_LABELS[self.rank],
            "suit": self.suit,
            "suitSymbol": SUIT_SYMBOLS[self.suit],
            "red": self.suit in {"heart", "diamond"},
        }


HandScore = tuple[int, ...]


def create_deck() -> list[PokerCard]:
    return [
        PokerCard(id=f"{suit}-{rank}", rank=rank, suit=suit)
        for suit in SUITS
        for rank in range(2, 15)
    ]


def evaluate_five(cards: list[PokerCard]) -> HandScore:
    if len(cards) != 5:
        raise ValueError("A poker hand must contain exactly five cards")
    ranks = sorted((card.rank for card in cards), reverse=True)
    counts = Counter(ranks)
    groups = sorted(
        ((count, rank) for rank, count in counts.items()),
        reverse=True,
    )
    flush = len({card.suit for card in cards}) == 1
    unique = sorted(set(ranks), reverse=True)
    straight_high = 0
    if len(unique) == 5 and unique[0] - unique[-1] == 4:
        straight_high = unique[0]
    elif unique == [14, 5, 4, 3, 2]:
        straight_high = 5

    if flush and straight_high:
        return (8, straight_high)
    if groups[0][0] == 4:
        four_rank = groups[0][1]
        kicker = next(rank for rank in ranks if rank != four_rank)
        return (7, four_rank, kicker)
    if groups[0][0] == 3 and groups[1][0] == 2:
        return (6, groups[0][1], groups[1][1])
    if flush:
        return (5, *ranks)
    if straight_high:
        return (4, straight_high)
    if groups[0][0] == 3:
        trip_rank = groups[0][1]
        kickers = sorted(
            (rank for rank in ranks if rank != trip_rank), reverse=True
        )
        return (3, trip_rank, *kickers)
    pairs = sorted(
        (rank for rank, count in counts.items() if count == 2), reverse=True
    )
    if len(pairs) == 2:
        kicker = next(rank for rank in ranks if rank not in pairs)
        return (2, pairs[0], pairs[1], kicker)
    if len(pairs) == 1:
        pair_rank = pairs[0]
        kickers = sorted(
            (rank for rank in ranks if rank != pair_rank), reverse=True
        )
        return (1, pair_rank, *kickers)
    return (0, *ranks)


def evaluate_best(cards: list[PokerCard]) -> HandScore:
    if not 5 <= len(cards) <= 7:
        raise ValueError("Texas Hold'em evaluates five to seven cards")
    return max(evaluate_five(list(combo)) for combo in itertools.combinations(cards, 5))


def hand_name(score: HandScore) -> str:
    if score[0] == 8 and score[1] == 14:
        return "皇家同花顺"
    return HAND_NAMES[score[0]]


def build_side_pots(
    contributions: dict[str, int],
    folded_ids: set[str],
    scores: dict[str, HandScore],
    seat_order: list[str],
) -> tuple[dict[str, int], list[dict[str, Any]]]:
    payouts = {player_id: 0 for player_id in contributions}
    pots: list[dict[str, Any]] = []
    levels = sorted({amount for amount in contributions.values() if amount > 0})
    previous = 0
    for level in levels:
        contributors = [
            player_id
            for player_id, amount in contributions.items()
            if amount >= level
        ]
        amount = (level - previous) * len(contributors)
        previous = level
        eligible = [
            player_id
            for player_id in contributors
            if player_id not in folded_ids and player_id in scores
        ]
        if not eligible or amount <= 0:
            continue
        best = max(scores[player_id] for player_id in eligible)
        winners = [
            player_id for player_id in seat_order
            if player_id in eligible and scores[player_id] == best
        ]
        share, remainder = divmod(amount, len(winners))
        for index, winner_id in enumerate(winners):
            payouts[winner_id] += share + (1 if index < remainder else 0)
        pots.append(
            {
                "amount": amount,
                "winnerIds": winners,
                "handName": hand_name(best),
            }
        )
    return payouts, pots


@dataclass
class PokerState:
    deck: list[PokerCard] = field(default_factory=list)
    burned: list[PokerCard] = field(default_factory=list)
    hands: dict[str, list[PokerCard]] = field(default_factory=dict)
    community: list[PokerCard] = field(default_factory=list)
    chips: dict[str, int] = field(default_factory=dict)
    street_bets: dict[str, int] = field(default_factory=dict)
    total_bets: dict[str, int] = field(default_factory=dict)
    folded_ids: list[str] = field(default_factory=list)
    all_in_ids: list[str] = field(default_factory=list)
    pending_player_ids: list[str] = field(default_factory=list)
    acted_at_bet: dict[str, int] = field(default_factory=dict)
    dealer_player_id: str | None = None
    small_blind_player_id: str | None = None
    big_blind_player_id: str | None = None
    action_player_id: str | None = None
    street: str = "preflop"
    current_bet: int = 0
    minimum_raise: int = 20
    pot: int = 0
    starting_chips: int = 1000
    small_blind: int = 10
    big_blind: int = 20
    showdown: bool = False
    hand_names: dict[str, str] = field(default_factory=dict)
    payouts: dict[str, int] = field(default_factory=dict)
    side_pots: list[dict[str, Any]] = field(default_factory=list)
    winner_ids: list[str] = field(default_factory=list)
    history: list[dict[str, Any]] = field(default_factory=list)


class PokerEngine:
    key = "poker"
    name = "德州扑克"
    min_players = 2
    max_players = 8

    def __init__(self, rng: random.Random | None = None) -> None:
        self.rng = rng or random.SystemRandom()

    def initial_state(self) -> PokerState:
        return PokerState()

    def room_options(self, options: dict[str, Any]) -> dict[str, Any]:
        starting_chips = options.get("startingChips", 1000)
        small_blind = options.get("smallBlind", 10)
        if (
            not isinstance(starting_chips, int)
            or isinstance(starting_chips, bool)
            or starting_chips not in STARTING_CHIP_OPTIONS
        ):
            raise GameRuleError("请选择 500、1000 或 2000 起始筹码")
        if (
            not isinstance(small_blind, int)
            or isinstance(small_blind, bool)
            or small_blind not in SMALL_BLIND_OPTIONS
        ):
            raise GameRuleError("请选择 5/10、10/20 或 20/40 盲注")
        return {
            "startingChips": starting_chips,
            "smallBlind": small_blind,
        }

    def start(self, room: ArcadeRoom) -> None:
        if not self.min_players <= len(room.players) <= self.max_players:
            raise GameRuleError("德州扑克需要 2–8 名玩家")
        state = PokerState(
            starting_chips=int(room.options.get("startingChips", 1000)),
            small_blind=int(room.options.get("smallBlind", 10)),
        )
        state.big_blind = state.small_blind * 2
        state.minimum_raise = state.big_blind
        state.deck = create_deck()
        self.rng.shuffle(state.deck)
        players = self._players(room)
        state.chips = {player.id: state.starting_chips for player in players}
        state.street_bets = {player.id: 0 for player in players}
        state.total_bets = {player.id: 0 for player in players}
        state.hands = {player.id: [] for player in players}

        dealer = players[0]
        if len(players) == 2:
            small_blind_player = dealer
            big_blind_player = players[1]
        else:
            small_blind_player = players[1]
            big_blind_player = players[2]
        state.dealer_player_id = dealer.id
        state.small_blind_player_id = small_blind_player.id
        state.big_blind_player_id = big_blind_player.id

        # Heads-up is the exception: the button/small blind receives the last
        # card, so dealing starts with the big blind.
        first_deal_seat = (
            big_blind_player.seat
            if len(players) == 2
            else small_blind_player.seat
        )
        for _ in range(2):
            for offset in range(len(players)):
                seat = (first_deal_seat + offset) % len(players)
                player = next(item for item in players if item.seat == seat)
                state.hands[player.id].append(state.deck.pop())

        self._contribute(state, small_blind_player.id, state.small_blind)
        self._contribute(state, big_blind_player.id, state.big_blind)
        state.current_bet = state.big_blind
        state.pending_player_ids = [
            player.id
            for player in players
            if player.id not in state.all_in_ids
        ]
        state.action_player_id = self._next_player_id(
            room,
            big_blind_player.seat,
            set(state.pending_player_ids),
        )
        state.history.extend(
            [
                {
                    "street": "preflop",
                    "playerId": small_blind_player.id,
                    "action": "small_blind",
                    "amount": state.street_bets[small_blind_player.id],
                },
                {
                    "street": "preflop",
                    "playerId": big_blind_player.id,
                    "action": "big_blind",
                    "amount": state.street_bets[big_blind_player.id],
                },
            ]
        )
        room.state = state
        room.phase = "playing"

    def act(
        self,
        room: ArcadeRoom,
        player: ArcadePlayer,
        action: str,
        payload: dict[str, Any],
    ) -> None:
        state: PokerState = room.state
        if action == "resign":
            self._resign(room, state, player)
            return
        if player.id != state.action_player_id:
            raise GameRuleError("还没有轮到你行动")
        if player.id in state.folded_ids or player.id in state.all_in_ids:
            raise GameRuleError("你已经不能继续下注")

        to_call = max(
            0,
            state.current_bet - state.street_bets[player.id],
        )
        amount = 0
        if action == "fold":
            state.folded_ids.append(player.id)
            self._remove_pending(state, player.id)
        elif action == "check":
            if to_call:
                raise GameRuleError("当前需要跟注或弃牌，不能过牌")
            self._remove_pending(state, player.id)
            state.acted_at_bet[player.id] = state.current_bet
        elif action == "call":
            if to_call <= 0:
                raise GameRuleError("当前无需跟注，可以选择过牌")
            amount = self._contribute(state, player.id, to_call)
            self._remove_pending(state, player.id)
            state.acted_at_bet[player.id] = state.current_bet
        elif action == "raise":
            if not self._betting_reopened(state, player.id):
                raise GameRuleError("短额全押未达到最小加注，本轮不能再次加注")
            raise_to = payload.get("raiseTo")
            if not isinstance(raise_to, int) or isinstance(raise_to, bool):
                raise GameRuleError("请输入正确的加注筹码")
            maximum = state.street_bets[player.id] + state.chips[player.id]
            minimum = state.current_bet + state.minimum_raise
            if raise_to < minimum:
                raise GameRuleError(f"本次至少需要加注到 {minimum}")
            if raise_to > maximum:
                raise GameRuleError("筹码不足，无法完成这次加注")
            previous_bet = state.current_bet
            amount = self._contribute(
                state,
                player.id,
                raise_to - state.street_bets[player.id],
            )
            state.current_bet = raise_to
            state.minimum_raise = raise_to - previous_bet
            state.acted_at_bet = {player.id: state.current_bet}
            self._reset_pending_after_raise(room, state, player.id)
        elif action == "all_in":
            if state.chips[player.id] <= 0:
                raise GameRuleError("你已经全押")
            previous_bet = state.current_bet
            raise_to = state.street_bets[player.id] + state.chips[player.id]
            if (
                raise_to > previous_bet
                and not self._betting_reopened(state, player.id)
            ):
                raise GameRuleError("短额全押未达到最小加注，本轮不能再次加注")
            amount = self._contribute(
                state,
                player.id,
                state.chips[player.id],
            )
            if raise_to > previous_bet:
                state.current_bet = raise_to
                raise_size = raise_to - previous_bet
                if raise_size >= state.minimum_raise:
                    state.minimum_raise = raise_size
                    state.acted_at_bet = {player.id: state.current_bet}
                else:
                    state.acted_at_bet[player.id] = state.current_bet
                self._reset_pending_after_raise(room, state, player.id)
            else:
                self._remove_pending(state, player.id)
                state.acted_at_bet[player.id] = state.current_bet
        else:
            raise GameRuleError("不支持这个德州扑克操作")

        state.history.append(
            {
                "street": state.street,
                "playerId": player.id,
                "action": action,
                "amount": amount,
                "streetBet": state.street_bets[player.id],
            }
        )
        self._progress_after_action(room, state, player.seat)

    def view(self, room: ArcadeRoom, viewer: ArcadePlayer) -> dict[str, Any]:
        state: PokerState = room.state
        players = self._players(room)
        player_states = []
        for player in players:
            reveal = player.id == viewer.id or (
                state.showdown and player.id not in state.folded_ids
            )
            player_states.append(
                {
                    "id": player.id,
                    "name": player.name,
                    "seat": player.seat,
                    "chips": state.chips.get(player.id, 0),
                    "streetBet": state.street_bets.get(player.id, 0),
                    "totalBet": state.total_bets.get(player.id, 0),
                    "folded": player.id in state.folded_ids,
                    "allIn": player.id in state.all_in_ids,
                    "isDealer": player.id == state.dealer_player_id,
                    "isSmallBlind": player.id == state.small_blind_player_id,
                    "isBigBlind": player.id == state.big_blind_player_id,
                    "isActing": player.id == state.action_player_id,
                    "cards": (
                        [card.as_dict() for card in state.hands.get(player.id, [])]
                        if reveal
                        else []
                    ),
                    "cardCount": len(state.hands.get(player.id, [])),
                    "handName": state.hand_names.get(player.id),
                    "payout": state.payouts.get(player.id, 0),
                }
            )
        legal = self._legal_actions(state, viewer.id)
        return {
            "street": state.street,
            "streetLabel": STREET_LABELS.get(state.street, state.street),
            "communityCards": [card.as_dict() for card in state.community],
            "pot": state.pot,
            "currentBet": state.current_bet,
            "smallBlind": state.small_blind,
            "bigBlind": state.big_blind,
            "startingChips": state.starting_chips,
            "actionPlayerId": state.action_player_id,
            "dealerPlayerId": state.dealer_player_id,
            "players": player_states,
            "legalActions": legal,
            "showdown": state.showdown,
            "sidePots": state.side_pots,
            "history": list(state.history),
        }

    def player_result(
        self, room: ArcadeRoom, player: ArcadePlayer
    ) -> tuple[str, str, bool]:
        state: PokerState = room.state
        role = "庄家" if player.id == state.dealer_player_id else "玩家"
        return role, "poker", player.id in room.winner_player_ids

    def record_state(self, room: ArcadeRoom) -> dict[str, Any]:
        """Return a match record without exposing mucked or undealt cards."""
        state: PokerState = room.state
        recorded = asdict(state)
        recorded.pop("deck", None)
        recorded.pop("burned", None)
        revealed_ids = (
            set(self._active_player_ids(room, state))
            if state.showdown
            else set()
        )
        recorded["hands"] = {
            player_id: hand if player_id in revealed_ids else []
            for player_id, hand in recorded["hands"].items()
        }
        return recorded

    def _legal_actions(self, state: PokerState, player_id: str) -> dict[str, Any]:
        if player_id != state.action_player_id:
            return {
                "canAct": False,
                "canFold": False,
                "canCheck": False,
                "canCall": False,
                "canRaise": False,
                "canAllIn": False,
                "callAmount": 0,
                "minimumRaiseTo": 0,
                "maximumRaiseTo": 0,
            }
        to_call = max(0, state.current_bet - state.street_bets[player_id])
        maximum = state.street_bets[player_id] + state.chips[player_id]
        minimum = state.current_bet + state.minimum_raise
        betting_reopened = self._betting_reopened(state, player_id)
        return {
            "canAct": True,
            "canFold": True,
            "canCheck": to_call == 0,
            "canCall": to_call > 0 and state.chips[player_id] > 0,
            "canRaise": betting_reopened and maximum >= minimum,
            "canAllIn": (
                state.chips[player_id] > 0
                and (maximum <= state.current_bet or betting_reopened)
            ),
            "callAmount": min(to_call, state.chips[player_id]),
            "minimumRaiseTo": minimum,
            "maximumRaiseTo": maximum,
        }

    def _resign(
        self,
        room: ArcadeRoom,
        state: PokerState,
        player: ArcadePlayer,
    ) -> None:
        if player.id in state.folded_ids:
            raise GameRuleError("你已经弃牌")
        if player.id in state.all_in_ids:
            raise GameRuleError("你已经全押，不能再弃牌或认输")
        state.folded_ids.append(player.id)
        self._remove_pending(state, player.id)
        state.history.append(
            {
                "street": state.street,
                "playerId": player.id,
                "action": "resign",
                "amount": 0,
            }
        )
        active = self._active_player_ids(room, state)
        if len(active) == 1:
            self._finish_uncontested(room, state, active[0])
        elif state.action_player_id == player.id:
            self._progress_after_action(room, state, player.seat)

    def _progress_after_action(
        self,
        room: ArcadeRoom,
        state: PokerState,
        actor_seat: int,
    ) -> None:
        active = self._active_player_ids(room, state)
        if len(active) == 1:
            self._finish_uncontested(room, state, active[0])
            return
        eligible = {
            player_id
            for player_id in active
            if player_id not in state.all_in_ids
        }
        state.pending_player_ids = [
            player_id
            for player_id in state.pending_player_ids
            if player_id in eligible
        ]
        if state.pending_player_ids:
            state.action_player_id = self._next_player_id(
                room,
                actor_seat,
                set(state.pending_player_ids),
            )
            return
        self._advance_street(room, state)

    def _advance_street(self, room: ArcadeRoom, state: PokerState) -> None:
        current_index = STREETS.index(state.street)
        if current_index == len(STREETS) - 1:
            self._showdown(room, state)
            return
        next_street = STREETS[current_index + 1]
        self._deal_street(state, next_street)
        state.street = next_street
        state.street_bets = {player.id: 0 for player in room.players}
        state.acted_at_bet = {}
        state.current_bet = 0
        state.minimum_raise = state.big_blind
        active = self._active_player_ids(room, state)
        eligible = [
            player_id
            for player_id in active
            if player_id not in state.all_in_ids
        ]
        if len(eligible) <= 1:
            self._runout_and_showdown(room, state)
            return
        state.pending_player_ids = list(eligible)
        dealer = room.player(state.dealer_player_id or "")
        state.action_player_id = self._next_player_id(
            room,
            dealer.seat,
            set(eligible),
        )

    def _runout_and_showdown(self, room: ArcadeRoom, state: PokerState) -> None:
        while state.street != "river":
            next_street = STREETS[STREETS.index(state.street) + 1]
            self._deal_street(state, next_street)
            state.street = next_street
        self._showdown(room, state)

    def _showdown(self, room: ArcadeRoom, state: PokerState) -> None:
        active = self._active_player_ids(room, state)
        scores = {
            player_id: evaluate_best(
                state.hands[player_id] + state.community
            )
            for player_id in active
        }
        state.showdown = True
        state.street = "showdown"
        state.action_player_id = None
        state.pending_player_ids = []
        state.hand_names = {
            player_id: hand_name(score) for player_id, score in scores.items()
        }
        seat_order = self._payout_order(room, state)
        payouts, pots = build_side_pots(
            state.total_bets,
            set(state.folded_ids),
            scores,
            seat_order,
        )
        state.payouts = payouts
        state.side_pots = pots
        for player_id, amount in payouts.items():
            state.chips[player_id] += amount
        net_scores = {
            player.id: state.chips[player.id] - state.starting_chips
            for player in room.players
        }
        positive_winners = [
            player.id for player in self._players(room)
            if net_scores[player.id] > 0
        ]
        if positive_winners:
            state.winner_ids = positive_winners
            winner_names = "、".join(
                room.player(player_id).name for player_id in positive_winners
            )
            best_label = "、".join(
                sorted(
                    {
                        state.hand_names[player_id]
                        for player_id in positive_winners
                    }
                )
            )
            room.finish(
                "poker",
                positive_winners,
                f"{winner_names} 赢得本局（摊牌：{best_label}）",
            )
        else:
            state.winner_ids = active
            room.finish("draw", active, "所有玩家平分底池，本局不分胜负")

    def _finish_uncontested(
        self,
        room: ArcadeRoom,
        state: PokerState,
        winner_id: str,
    ) -> None:
        state.action_player_id = None
        state.pending_player_ids = []
        state.payouts = {player.id: 0 for player in room.players}
        state.payouts[winner_id] = state.pot
        state.chips[winner_id] += state.pot
        state.side_pots = [
            {
                "amount": state.pot,
                "winnerIds": [winner_id],
                "handName": "其他玩家弃牌",
            }
        ]
        state.winner_ids = [winner_id]
        winner = room.player(winner_id)
        room.finish(
            "poker",
            [winner_id],
            f"{winner.name} 坚持到最后，赢得 {state.pot} 筹码",
        )

    def _deal_street(self, state: PokerState, street: str) -> None:
        state.burned.append(state.deck.pop())
        count = 3 if street == "flop" else 1
        for _ in range(count):
            state.community.append(state.deck.pop())

    def _contribute(
        self,
        state: PokerState,
        player_id: str,
        requested: int,
    ) -> int:
        amount = min(max(requested, 0), state.chips[player_id])
        state.chips[player_id] -= amount
        state.street_bets[player_id] += amount
        state.total_bets[player_id] += amount
        state.pot += amount
        if state.chips[player_id] == 0 and player_id not in state.all_in_ids:
            state.all_in_ids.append(player_id)
        return amount

    def _reset_pending_after_raise(
        self,
        room: ArcadeRoom,
        state: PokerState,
        raiser_id: str,
    ) -> None:
        state.pending_player_ids = [
            player.id
            for player in self._players(room)
            if player.id != raiser_id
            and player.id not in state.folded_ids
            and player.id not in state.all_in_ids
            and state.street_bets[player.id] < state.current_bet
        ]

    @staticmethod
    def _betting_reopened(state: PokerState, player_id: str) -> bool:
        previous_action_bet = state.acted_at_bet.get(player_id)
        return (
            previous_action_bet is None
            or state.current_bet - previous_action_bet >= state.minimum_raise
        )

    @staticmethod
    def _remove_pending(state: PokerState, player_id: str) -> None:
        state.pending_player_ids = [
            pending_id
            for pending_id in state.pending_player_ids
            if pending_id != player_id
        ]

    @staticmethod
    def _players(room: ArcadeRoom) -> list[ArcadePlayer]:
        return sorted(room.players, key=lambda player: player.seat)

    @staticmethod
    def _active_player_ids(
        room: ArcadeRoom,
        state: PokerState,
    ) -> list[str]:
        return [
            player.id
            for player in sorted(room.players, key=lambda item: item.seat)
            if player.id not in state.folded_ids
        ]

    def _next_player_id(
        self,
        room: ArcadeRoom,
        after_seat: int,
        candidates: set[str],
    ) -> str | None:
        players = self._players(room)
        for offset in range(1, len(players) + 1):
            seat = (after_seat + offset) % len(players)
            player = next(item for item in players if item.seat == seat)
            if player.id in candidates:
                return player.id
        return None

    def _payout_order(
        self,
        room: ArcadeRoom,
        state: PokerState,
    ) -> list[str]:
        dealer = room.player(state.dealer_player_id or "")
        players = self._players(room)
        order: list[str] = []
        for offset in range(1, len(players) + 1):
            seat = (dealer.seat + offset) % len(players)
            order.append(next(item.id for item in players if item.seat == seat))
        return order
