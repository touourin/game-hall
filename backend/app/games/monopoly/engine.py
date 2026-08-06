from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any

from backend.app.arcade.models import ArcadePlayer, ArcadeRoom
from backend.app.games.base import GameRuleError


STARTING_CASH_OPTIONS = {6_000, 8_000, 10_000}
MAX_ROUND_OPTIONS = {12, 20, 30}
DEFAULT_STARTING_CASH = 8_000
DEFAULT_MAX_ROUNDS = 20
PASS_START_BONUS = 1_200
MAX_HOUSES = 3
PLAYER_COLORS = ("#ef6f6c", "#57a4e5", "#5fc596", "#dca95f")
RENT_MULTIPLIERS = (1, 2, 4, 7)


BOARD: tuple[dict[str, Any], ...] = (
    {"name": "梦想启程", "type": "start", "icon": "🚩"},
    {
        "name": "星河街", "type": "property", "group": "sky",
        "groupLabel": "星空蓝", "color": "#58a7d8", "price": 800,
        "baseRent": 160, "upgradeCost": 400,
    },
    {"name": "机会", "type": "chance", "icon": "?"},
    {
        "name": "云港路", "type": "property", "group": "sky",
        "groupLabel": "星空蓝", "color": "#58a7d8", "price": 1_000,
        "baseRent": 200, "upgradeCost": 500,
    },
    {"name": "城市维护", "type": "tax", "amount": 500, "icon": "◇"},
    {
        "name": "晨曦站", "type": "property", "group": "coral",
        "groupLabel": "珊瑚橙", "color": "#e98567", "price": 1_200,
        "baseRent": 230, "upgradeCost": 600,
    },
    {"name": "探访看守所", "type": "jail", "icon": "⌁"},
    {
        "name": "翡翠湾", "type": "property", "group": "coral",
        "groupLabel": "珊瑚橙", "color": "#e98567", "price": 1_400,
        "baseRent": 270, "upgradeCost": 700,
    },
    {"name": "机会", "type": "chance", "icon": "?"},
    {
        "name": "桂影坊", "type": "property", "group": "violet",
        "groupLabel": "暮光紫", "color": "#9a7bd0", "price": 1_500,
        "baseRent": 300, "upgradeCost": 750,
    },
    {
        "name": "创想园", "type": "property", "group": "violet",
        "groupLabel": "暮光紫", "color": "#9a7bd0", "price": 1_700,
        "baseRent": 340, "upgradeCost": 850,
    },
    {"name": "城市分红", "type": "bonus", "amount": 450, "icon": "+"},
    {"name": "中央公园", "type": "rest", "icon": "♧"},
    {
        "name": "金桂路", "type": "property", "group": "amber",
        "groupLabel": "鎏金黄", "color": "#d7aa4e", "price": 1_800,
        "baseRent": 380, "upgradeCost": 900,
    },
    {"name": "机会", "type": "chance", "icon": "?"},
    {
        "name": "艺术街", "type": "property", "group": "amber",
        "groupLabel": "鎏金黄", "color": "#d7aa4e", "price": 2_000,
        "baseRent": 420, "upgradeCost": 1_000,
    },
    {"name": "公益基金", "type": "tax", "amount": 800, "icon": "♡"},
    {
        "name": "科技港", "type": "property", "group": "jade",
        "groupLabel": "未来绿", "color": "#55ad88", "price": 2_200,
        "baseRent": 480, "upgradeCost": 1_100,
    },
    {"name": "前往看守所", "type": "go_to_jail", "icon": "↠"},
    {
        "name": "天际广场", "type": "property", "group": "jade",
        "groupLabel": "未来绿", "color": "#55ad88", "price": 2_400,
        "baseRent": 520, "upgradeCost": 1_200,
    },
    {"name": "机会", "type": "chance", "icon": "?"},
    {
        "name": "月华里", "type": "property", "group": "rose",
        "groupLabel": "霓虹红", "color": "#d85f78", "price": 2_600,
        "baseRent": 580, "upgradeCost": 1_300,
    },
    {
        "name": "皇冠大道", "type": "property", "group": "rose",
        "groupLabel": "霓虹红", "color": "#d85f78", "price": 3_000,
        "baseRent": 680, "upgradeCost": 1_500,
    },
    {"name": "幸运礼金", "type": "bonus", "amount": 650, "icon": "✦"},
)


@dataclass
class PropertyOwnership:
    owner_id: str
    houses: int = 0


@dataclass
class MonopolyState:
    positions: dict[str, int] = field(default_factory=dict)
    cash: dict[str, int] = field(default_factory=dict)
    ownership: dict[int, PropertyOwnership] = field(default_factory=dict)
    bankrupt_ids: list[str] = field(default_factory=list)
    jailed_turns: dict[str, int] = field(default_factory=dict)
    current_player_id: str | None = None
    turn_stage: str = "await_roll"
    last_roll: list[int] | None = None
    current_round: int = 1
    max_rounds: int = DEFAULT_MAX_ROUNDS
    starting_cash: int = DEFAULT_STARTING_CASH
    turn_number: int = 1
    last_event: str = ""
    history: list[str] = field(default_factory=list)


class MonopolyEngine:
    key = "monopoly"
    name = "大富翁"
    min_players = 2
    max_players = 4

    def __init__(
        self,
        rng: random.Random | random.SystemRandom | None = None,
    ) -> None:
        self.rng = rng or random.SystemRandom()

    def initial_state(self) -> MonopolyState:
        return MonopolyState()

    def room_options(self, options: dict[str, Any]) -> dict[str, Any]:
        starting_cash = options.get("startingCash", DEFAULT_STARTING_CASH)
        max_rounds = options.get("maxRounds", DEFAULT_MAX_ROUNDS)
        if (
            not isinstance(starting_cash, int)
            or isinstance(starting_cash, bool)
            or starting_cash not in STARTING_CASH_OPTIONS
        ):
            raise GameRuleError("请选择 6000、8000 或 10000 起始资金")
        if (
            not isinstance(max_rounds, int)
            or isinstance(max_rounds, bool)
            or max_rounds not in MAX_ROUND_OPTIONS
        ):
            raise GameRuleError("请选择 12、20 或 30 回合赛制")
        return {"startingCash": starting_cash, "maxRounds": max_rounds}

    def start(self, room: ArcadeRoom) -> None:
        if not self.min_players <= len(room.players) <= self.max_players:
            raise GameRuleError("大富翁需要 2–4 名玩家")
        starting_cash = int(
            room.options.get("startingCash", DEFAULT_STARTING_CASH)
        )
        state = MonopolyState(
            positions={player.id: 0 for player in room.players},
            cash={player.id: starting_cash for player in room.players},
            jailed_turns={player.id: 0 for player in room.players},
            current_player_id=room.players[0].id,
            starting_cash=starting_cash,
            max_rounds=int(room.options.get("maxRounds", DEFAULT_MAX_ROUNDS)),
        )
        state.last_event = f"{room.players[0].name} 先行，所有玩家从梦想启程出发"
        state.history.append(state.last_event)
        room.state = state
        room.phase = "playing"

    def act(
        self,
        room: ArcadeRoom,
        player: ArcadePlayer,
        action: str,
        payload: dict[str, Any],
    ) -> None:
        del payload
        state: MonopolyState = room.state
        if action == "resign":
            self._resign(room, state, player, "主动退出")
            return
        if player.id in state.bankrupt_ids:
            raise GameRuleError("你已经离开本局，不能继续操作")
        if player.id != state.current_player_id:
            raise GameRuleError("还没有轮到你行动")

        if action == "roll":
            self._roll(room, state, player)
        elif action == "buy_property":
            self._buy_property(room, state, player)
        elif action == "decline_property":
            self._decline_property(room, state, player)
        elif action == "upgrade_property":
            self._upgrade_property(room, state, player)
        elif action == "decline_upgrade":
            self._decline_upgrade(room, state, player)
        else:
            raise GameRuleError("不支持这个大富翁操作")

    def manual_forfeit(
        self,
        room: ArcadeRoom,
        player: ArcadePlayer,
    ) -> bool:
        self._resign(room, room.state, player, "主动退出")
        return True

    def disconnect_timeout(
        self,
        room: ArcadeRoom,
        player: ArcadePlayer,
    ) -> bool:
        self._resign(room, room.state, player, "掉线超时")
        return True

    def view(self, room: ArcadeRoom, viewer: ArcadePlayer) -> dict[str, Any]:
        state: MonopolyState = room.state
        player_lookup = {player.id: player for player in room.players}
        current_cell = (
            BOARD[state.positions[state.current_player_id]]
            if state.current_player_id in state.positions
            else None
        )
        standings = sorted(
            room.players,
            key=lambda player: (
                player.id not in state.bankrupt_ids,
                self._net_worth(state, player.id),
                -player.seat,
            ),
            reverse=True,
        )
        is_viewer_turn = (
            room.phase == "playing"
            and viewer.id == state.current_player_id
            and viewer.id not in state.bankrupt_ids
        )
        return {
            "board": [
                self._cell_view(state, index, cell, player_lookup)
                for index, cell in enumerate(BOARD)
            ],
            "players": [
                {
                    "id": player.id,
                    "name": player.name,
                    "seat": player.seat,
                    "color": PLAYER_COLORS[player.seat % len(PLAYER_COLORS)],
                    "position": state.positions.get(player.id, 0),
                    "cash": state.cash.get(player.id, 0),
                    "netWorth": self._net_worth(state, player.id),
                    "propertyCount": sum(
                        ownership.owner_id == player.id
                        for ownership in state.ownership.values()
                    ),
                    "bankrupt": player.id in state.bankrupt_ids,
                    "jailedTurns": state.jailed_turns.get(player.id, 0),
                    "isCurrent": player.id == state.current_player_id,
                }
                for player in room.players
            ],
            "currentPlayerId": state.current_player_id,
            "turnStage": state.turn_stage,
            "lastRoll": state.last_roll,
            "currentRound": state.current_round,
            "maxRounds": state.max_rounds,
            "turnNumber": state.turn_number,
            "passStartBonus": PASS_START_BONUS,
            "lastEvent": state.last_event,
            "history": list(reversed(state.history[-12:])),
            "currentCell": (
                self._cell_view(
                    state,
                    state.positions[state.current_player_id],
                    current_cell,
                    player_lookup,
                )
                if current_cell is not None and state.current_player_id is not None
                else None
            ),
            "standings": [
                {
                    "playerId": player.id,
                    "name": player.name,
                    "netWorth": self._net_worth(state, player.id),
                    "bankrupt": player.id in state.bankrupt_ids,
                }
                for player in standings
            ],
            "legalActions": {
                "canRoll": is_viewer_turn and state.turn_stage == "await_roll",
                "canBuy": is_viewer_turn and state.turn_stage == "await_purchase",
                "canDecline": is_viewer_turn
                and state.turn_stage == "await_purchase",
                "canUpgrade": is_viewer_turn
                and state.turn_stage == "await_upgrade",
                "canDeclineUpgrade": is_viewer_turn
                and state.turn_stage == "await_upgrade",
            },
        }

    def player_result(
        self,
        room: ArcadeRoom,
        player: ArcadePlayer,
    ) -> tuple[str, str, bool]:
        state: MonopolyState = room.state
        return (
            f"资产 {self._net_worth(state, player.id)}",
            "investor",
            player.id in room.winner_player_ids,
        )

    def _roll(
        self,
        room: ArcadeRoom,
        state: MonopolyState,
        player: ArcadePlayer,
    ) -> None:
        if state.turn_stage != "await_roll":
            raise GameRuleError("请先完成当前地块的选择")
        if state.jailed_turns.get(player.id, 0) > 0:
            state.jailed_turns[player.id] -= 1
            state.last_roll = None
            self._log(state, f"{player.name} 在看守所停留一回合")
            self._advance_turn(room, state, player.id)
            return
        dice = [self.rng.randint(1, 6), self.rng.randint(1, 6)]
        state.last_roll = dice
        steps = sum(dice)
        old_position = state.positions[player.id]
        self._move_player(state, player, steps)
        self._log(
            state,
            f"{player.name} 掷出 {dice[0]} + {dice[1]}，从 {BOARD[old_position]['name']} 前进 {steps} 格",
        )
        self._resolve_landing(room, state, player)

    def _buy_property(
        self,
        room: ArcadeRoom,
        state: MonopolyState,
        player: ArcadePlayer,
    ) -> None:
        if state.turn_stage != "await_purchase":
            raise GameRuleError("当前没有可以购买的地产")
        position = state.positions[player.id]
        cell = BOARD[position]
        if cell["type"] != "property" or position in state.ownership:
            raise GameRuleError("这块地产已经不能购买")
        price = int(cell["price"])
        if state.cash[player.id] < price:
            raise GameRuleError("现金不足，无法购买这块地产")
        state.cash[player.id] -= price
        state.ownership[position] = PropertyOwnership(player.id)
        message = f"{player.name} 花费 {price} 买下 {cell['name']}"
        if self._owns_group(state, player.id, str(cell["group"])):
            message += f"，集齐{cell['groupLabel']}地块"
        self._log(state, message)
        self._advance_turn(room, state, player.id)

    def _decline_property(
        self,
        room: ArcadeRoom,
        state: MonopolyState,
        player: ArcadePlayer,
    ) -> None:
        if state.turn_stage != "await_purchase":
            raise GameRuleError("当前不需要放弃购买")
        cell = BOARD[state.positions[player.id]]
        self._log(state, f"{player.name} 放弃购买 {cell['name']}")
        self._advance_turn(room, state, player.id)

    def _upgrade_property(
        self,
        room: ArcadeRoom,
        state: MonopolyState,
        player: ArcadePlayer,
    ) -> None:
        if state.turn_stage != "await_upgrade":
            raise GameRuleError("当前没有可以升级的地产")
        position = state.positions[player.id]
        cell = BOARD[position]
        ownership = state.ownership.get(position)
        if ownership is None or ownership.owner_id != player.id:
            raise GameRuleError("你不是这块地产的业主")
        if ownership.houses >= MAX_HOUSES:
            raise GameRuleError("这块地产已经升到最高等级")
        if not self._owns_group(state, player.id, str(cell["group"])):
            raise GameRuleError("集齐同色地块后才能升级")
        cost = int(cell["upgradeCost"])
        if state.cash[player.id] < cost:
            raise GameRuleError("现金不足，无法升级这块地产")
        state.cash[player.id] -= cost
        ownership.houses += 1
        self._log(
            state,
            f"{player.name} 花费 {cost} 将 {cell['name']} 升到 {ownership.houses} 级",
        )
        self._advance_turn(room, state, player.id)

    def _decline_upgrade(
        self,
        room: ArcadeRoom,
        state: MonopolyState,
        player: ArcadePlayer,
    ) -> None:
        if state.turn_stage != "await_upgrade":
            raise GameRuleError("当前不需要跳过升级")
        cell = BOARD[state.positions[player.id]]
        self._log(state, f"{player.name} 暂不升级 {cell['name']}")
        self._advance_turn(room, state, player.id)

    def _resolve_landing(
        self,
        room: ArcadeRoom,
        state: MonopolyState,
        player: ArcadePlayer,
        *,
        allow_chance: bool = True,
    ) -> None:
        position = state.positions[player.id]
        cell = BOARD[position]
        cell_type = cell["type"]
        if cell_type == "property":
            ownership = state.ownership.get(position)
            if ownership is None:
                if state.cash[player.id] >= int(cell["price"]):
                    state.turn_stage = "await_purchase"
                    state.last_event = (
                        f"{player.name} 抵达 {cell['name']}，可以花费 {cell['price']} 购买"
                    )
                else:
                    self._log(
                        state,
                        f"{player.name} 抵达 {cell['name']}，但现金不足以购买",
                    )
                    self._advance_turn(room, state, player.id)
                return
            if ownership.owner_id == player.id:
                can_upgrade = (
                    ownership.houses < MAX_HOUSES
                    and self._owns_group(state, player.id, str(cell["group"]))
                    and state.cash[player.id] >= int(cell["upgradeCost"])
                )
                if can_upgrade:
                    state.turn_stage = "await_upgrade"
                    state.last_event = (
                        f"回到自己的 {cell['name']}，可以花费 {cell['upgradeCost']} 升级"
                    )
                else:
                    self._log(state, f"{player.name} 回到自己的 {cell['name']}")
                    self._advance_turn(room, state, player.id)
                return
            owner = room.player(ownership.owner_id)
            rent = self._rent(state, position)
            paid = self._charge(
                room,
                state,
                player,
                rent,
                f"向 {owner.name} 支付 {cell['name']} 租金",
                creditor_id=owner.id,
            )
            if room.phase == "playing":
                self._log(
                    state,
                    f"{player.name} 向 {owner.name} 支付 {paid} 租金",
                )
                self._advance_turn(room, state, player.id)
            return
        if cell_type == "chance" and allow_chance:
            self._apply_chance(room, state, player)
            return
        if cell_type == "tax":
            amount = int(cell["amount"])
            paid = self._charge(
                room, state, player, amount, str(cell["name"])
            )
            if room.phase == "playing":
                self._log(state, f"{player.name} 支付 {paid} 城市费用")
                self._advance_turn(room, state, player.id)
            return
        if cell_type == "bonus":
            amount = int(cell["amount"])
            state.cash[player.id] += amount
            self._log(state, f"{player.name} 获得 {amount} {cell['name']}")
        elif cell_type == "go_to_jail":
            state.positions[player.id] = 6
            state.jailed_turns[player.id] = 1
            self._log(state, f"{player.name} 被送往看守所，下回合停留一次")
        elif cell_type == "rest":
            self._log(state, f"{player.name} 在中央公园休息片刻")
        elif cell_type == "start":
            self._log(state, f"{player.name} 回到梦想启程")
        elif cell_type == "jail":
            self._log(state, f"{player.name} 只是探访看守所，不受影响")
        else:
            self._log(state, f"{player.name} 抵达 {cell['name']}")
        self._advance_turn(room, state, player.id)

    def _apply_chance(
        self,
        room: ArcadeRoom,
        state: MonopolyState,
        player: ArcadePlayer,
    ) -> None:
        event = self.rng.randrange(7)
        if event == 0:
            state.cash[player.id] += 600
            self._log(state, f"机会：{player.name} 的项目获奖，获得 600")
        elif event == 1:
            paid = self._charge(room, state, player, 500, "房屋维修")
            if room.phase != "playing":
                return
            self._log(state, f"机会：{player.name} 支付房屋维修费 {paid}")
        elif event == 2:
            self._log(state, f"机会：{player.name} 搭上快车，向前移动 3 格")
            self._move_player(state, player, 3)
            self._resolve_landing(room, state, player, allow_chance=False)
            return
        elif event == 3:
            state.positions[player.id] = 0
            state.cash[player.id] += PASS_START_BONUS
            self._log(
                state,
                f"机会：{player.name} 直达梦想启程，领取 {PASS_START_BONUS}",
            )
        elif event == 4:
            state.positions[player.id] = 6
            state.jailed_turns[player.id] = 1
            self._log(state, f"机会：{player.name} 被送往看守所")
        elif event == 5:
            state.cash[player.id] += 300
            self._log(state, f"机会：{player.name} 获得城市创意补贴 300")
        else:
            paid = self._charge(room, state, player, 300, "旅行支出")
            if room.phase != "playing":
                return
            self._log(state, f"机会：{player.name} 支付旅行支出 {paid}")
        self._advance_turn(room, state, player.id)

    def _move_player(
        self,
        state: MonopolyState,
        player: ArcadePlayer,
        steps: int,
    ) -> None:
        old_position = state.positions[player.id]
        destination = old_position + steps
        if destination >= len(BOARD):
            state.cash[player.id] += PASS_START_BONUS
            self._log(
                state,
                f"{player.name} 经过梦想启程，领取 {PASS_START_BONUS}",
            )
        state.positions[player.id] = destination % len(BOARD)

    def _advance_turn(
        self,
        room: ArcadeRoom,
        state: MonopolyState,
        previous_player_id: str,
    ) -> None:
        if room.phase != "playing":
            return
        active_players = [
            player
            for player in room.players
            if player.id not in state.bankrupt_ids
        ]
        if len(active_players) <= 1:
            self._finish_last_player(room, state)
            return
        previous = room.player(previous_player_id)
        ordered = sorted(active_players, key=lambda player: player.seat)
        next_player = next(
            (player for player in ordered if player.seat > previous.seat),
            ordered[0],
        )
        if next_player.seat <= previous.seat:
            if state.current_round >= state.max_rounds:
                self._finish_by_assets(room, state)
                return
            state.current_round += 1
        state.current_player_id = next_player.id
        state.turn_stage = "await_roll"
        state.turn_number += 1
        state.last_roll = None

    def _charge(
        self,
        room: ArcadeRoom,
        state: MonopolyState,
        player: ArcadePlayer,
        amount: int,
        reason: str,
        *,
        creditor_id: str | None = None,
    ) -> int:
        paid = min(state.cash[player.id], amount)
        state.cash[player.id] -= paid
        if creditor_id is not None:
            state.cash[creditor_id] += paid
        if paid < amount:
            self._bankrupt(
                room,
                state,
                player,
                f"{reason}，尚欠 {amount - paid}",
                creditor_id=creditor_id,
            )
        return paid

    def _bankrupt(
        self,
        room: ArcadeRoom,
        state: MonopolyState,
        player: ArcadePlayer,
        reason: str,
        *,
        creditor_id: str | None = None,
    ) -> None:
        if player.id in state.bankrupt_ids:
            return
        state.bankrupt_ids.append(player.id)
        state.cash[player.id] = 0
        for position, ownership in list(state.ownership.items()):
            if ownership.owner_id != player.id:
                continue
            if creditor_id is None:
                del state.ownership[position]
            else:
                ownership.owner_id = creditor_id
                ownership.houses = 0
        self._log(state, f"{player.name} 因{reason}破产离场")
        if len(room.players) - len(state.bankrupt_ids) <= 1:
            self._finish_last_player(room, state)

    def _resign(
        self,
        room: ArcadeRoom,
        state: MonopolyState,
        player: ArcadePlayer,
        reason: str,
    ) -> None:
        if player.id in state.bankrupt_ids:
            return
        was_current = player.id == state.current_player_id
        self._bankrupt(room, state, player, reason)
        if room.phase == "playing" and was_current:
            self._advance_turn(room, state, player.id)

    def _finish_last_player(
        self,
        room: ArcadeRoom,
        state: MonopolyState,
    ) -> None:
        survivors = [
            player
            for player in room.players
            if player.id not in state.bankrupt_ids
        ]
        if not survivors:
            room.finish("draw", [], "所有玩家均已破产，本局无胜者")
            return
        winner = survivors[0]
        room.finish(
            "fortune",
            [winner.id],
            f"{winner.name} 成为最后的城市大亨，净资产 {self._net_worth(state, winner.id)}",
        )

    def _finish_by_assets(
        self,
        room: ArcadeRoom,
        state: MonopolyState,
    ) -> None:
        active = [
            player
            for player in room.players
            if player.id not in state.bankrupt_ids
        ]
        highest = max(self._net_worth(state, player.id) for player in active)
        winners = [
            player for player in active
            if self._net_worth(state, player.id) == highest
        ]
        if len(winners) == 1:
            reason = (
                f"{state.max_rounds} 回合结束，{winners[0].name} 以净资产 {highest} 获胜"
            )
            winner = "assets"
        else:
            names = "、".join(player.name for player in winners)
            reason = f"{state.max_rounds} 回合结束，{names} 以净资产 {highest} 并列第一"
            winner = "draw"
        room.finish(winner, [player.id for player in winners], reason)

    def _cell_view(
        self,
        state: MonopolyState,
        index: int,
        cell: dict[str, Any],
        player_lookup: dict[str, ArcadePlayer],
    ) -> dict[str, Any]:
        ownership = state.ownership.get(index)
        owner = (
            player_lookup.get(ownership.owner_id)
            if ownership is not None
            else None
        )
        result = {"index": index, **cell}
        result.update(
            {
                "ownerId": ownership.owner_id if ownership else None,
                "ownerName": owner.name if owner else None,
                "ownerColor": (
                    PLAYER_COLORS[owner.seat % len(PLAYER_COLORS)]
                    if owner is not None
                    else None
                ),
                "houses": ownership.houses if ownership else 0,
                "rent": self._rent(state, index) if ownership else cell.get("baseRent"),
                "groupComplete": bool(
                    ownership
                    and cell.get("group")
                    and self._owns_group(
                        state, ownership.owner_id, str(cell["group"])
                    )
                ),
            }
        )
        return result

    def _rent(self, state: MonopolyState, position: int) -> int:
        cell = BOARD[position]
        ownership = state.ownership[position]
        rent = int(cell["baseRent"]) * RENT_MULTIPLIERS[ownership.houses]
        if ownership.houses == 0 and self._owns_group(
            state, ownership.owner_id, str(cell["group"])
        ):
            rent *= 2
        return rent

    @staticmethod
    def _owns_group(
        state: MonopolyState,
        player_id: str,
        group: str,
    ) -> bool:
        positions = [
            index for index, cell in enumerate(BOARD)
            if cell.get("group") == group
        ]
        return bool(positions) and all(
            state.ownership.get(position) is not None
            and state.ownership[position].owner_id == player_id
            for position in positions
        )

    @staticmethod
    def _net_worth(state: MonopolyState, player_id: str) -> int:
        total = state.cash.get(player_id, 0)
        for position, ownership in state.ownership.items():
            if ownership.owner_id != player_id:
                continue
            cell = BOARD[position]
            total += int(cell["price"])
            total += int(cell["upgradeCost"]) * ownership.houses
        return total

    @staticmethod
    def _log(state: MonopolyState, message: str) -> None:
        state.last_event = message
        state.history.append(message)
        state.history = state.history[-30:]
