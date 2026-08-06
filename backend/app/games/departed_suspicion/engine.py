from __future__ import annotations

import copy
import random
from dataclasses import dataclass, field
from typing import Any

from backend.app.arcade.models import ArcadePlayer, ArcadeRoom
from backend.app.games.base import GameRuleError

from .cards import (
    BASE_EQUIPMENT_IDS,
    EQUIPMENT_BY_ID,
    EQUIPMENT_CARDS,
    EXPANDED_EQUIPMENT_IDS,
)


INTEGRITY_NAMES = {
    "honest": "正直",
    "crooked": "腐败",
    "agent": "探员",
    "kingpin": "头目",
}
TEAM_NAMES = {"honest": "正直阵营", "crooked": "腐败阵营"}
ACTION_NAMES = {
    "investigate": "调查",
    "equip": "获取装备",
    "arm": "武装",
    "shoot": "射击",
    "extra_investigate": "额外调查",
}
EQUIPMENT_SETS = {"base", "expanded"}
NORMAL_INTEGRITY_PER_TEAM = {
    4: 5,
    5: 7,
    6: 8,
    7: 10,
    8: 11,
}


@dataclass
class IntegrityCard:
    id: str
    kind: str
    revealed: bool = False
    wounded: bool = False


@dataclass
class PlayerBoard:
    cards: list[IntegrityCard] = field(default_factory=list)
    alive: bool = True
    gun: bool = False
    aim_seat: int | None = None
    equipment: list[str] = field(default_factory=list)
    effects: list[str] = field(default_factory=list)
    restricted_to_equip: bool = False
    grenade_stage: int = 0


@dataclass
class PendingAction:
    actor_seat: int
    action: str
    payload: dict[str, Any]
    response_order: list[int] = field(default_factory=list)
    response_index: int = 0


@dataclass
class PendingShot:
    shooter_seat: int | None
    target_seat: int
    source: str
    advance_after: bool = False
    scanner_seat: int | None = None


@dataclass
class DepartedSuspicionState:
    boards: dict[int, PlayerBoard] = field(default_factory=dict)
    turn_seat: int = 0
    direction: int = 1
    action_done: bool = False
    extra_investigation_done: bool = False
    equipment_deck: list[str] = field(default_factory=list)
    gun_total: int = 0
    turn_number: int = 1
    acquired_gun_turn: dict[int, int] = field(default_factory=dict)
    pending_action: PendingAction | None = None
    pending_shot: PendingShot | None = None
    choice: dict[str, Any] | None = None
    post_shot: dict[str, Any] | None = None
    coffee_after: list[int] = field(default_factory=list)
    knowledge: dict[int, set[str]] = field(default_factory=dict)
    last_investigation: dict[str, int] | None = None
    history: list[dict[str, Any]] = field(default_factory=list)


class DepartedSuspicionEngine:
    key = "departed_suspicion"
    name = "无间疑云"
    min_players = 4
    max_players = 8

    def __init__(self, rng: random.Random | None = None) -> None:
        self.rng = rng or random.Random()

    def room_options(self, options: dict[str, Any]) -> dict[str, Any]:
        equipment_set = str(options.get("equipmentSet", "expanded"))
        if equipment_set not in EQUIPMENT_SETS:
            raise GameRuleError("请选择基础16张或扩展32张装备牌库")
        return {
            "equipmentSet": equipment_set,
            "firstPlayer": (
                "host" if options.get("firstPlayer") == "host" else "random"
            ),
            "allowGuests": bool(options.get("allowGuests", True)),
        }

    def initial_state(self) -> DepartedSuspicionState:
        return DepartedSuspicionState()

    def start(self, room: ArcadeRoom) -> None:
        player_count = len(room.players)
        cards = self._deal_integrity(player_count)
        boards = {
            seat: PlayerBoard(cards=cards[seat]) for seat in range(player_count)
        }
        equipment_ids = list(
            BASE_EQUIPMENT_IDS
            if room.options.get("equipmentSet") == "base"
            else EXPANDED_EQUIPMENT_IDS
        )
        self.rng.shuffle(equipment_ids)
        room.state = DepartedSuspicionState(
            boards=boards,
            turn_seat=0,
            equipment_deck=equipment_ids,
            gun_total=self._gun_count(player_count),
            knowledge={seat: set() for seat in range(player_count)},
        )
        room.phase = "playing"
        self._log(room.state, "game_start", f"{player_count}人对局开始")

    def act(
        self,
        room: ArcadeRoom,
        player: ArcadePlayer,
        action: str,
        payload: dict[str, Any],
    ) -> None:
        state: DepartedSuspicionState = room.state
        seat = player.seat

        if action == "resign":
            self._resign(room, state, seat)
            return
        if state.pending_shot is not None:
            self._handle_pending_shot(room, state, seat, action, payload)
            return
        if state.post_shot is not None:
            self._handle_post_shot(room, state, seat, action, payload)
            return
        if state.choice is not None:
            self._handle_choice(room, state, seat, action, payload)
            return
        if state.pending_action is not None:
            if action == "pass_response":
                self._pass_response(room, state, seat)
                return
            if action == "play_equipment":
                self._play_equipment(room, state, seat, payload)
                return
            raise GameRuleError("请先处理当前行动的装备响应")

        board = self._board(state, seat)
        if action == "play_equipment":
            self._play_equipment(room, state, seat, payload)
            return
        if seat != state.turn_seat:
            raise GameRuleError("现在不是你的回合")
        if not board.alive:
            raise GameRuleError("你已经出局")
        if action == "end_turn":
            self._end_turn(room, state, seat, payload)
            return
        if action in {"investigate", "equip", "arm", "shoot"}:
            if state.action_done:
                raise GameRuleError("本回合已经执行过正常行动")
            if board.restricted_to_equip and action != "equip":
                raise GameRuleError("拐杖限制你只能执行获取装备")
            self._declare_action(room, state, seat, action, payload)
            return
        if action == "extra_investigate":
            if board.restricted_to_equip:
                raise GameRuleError("拐杖限制你只能执行获取装备")
            if "key" not in board.effects:
                raise GameRuleError("你没有钥匙提供的额外调查")
            if state.extra_investigation_done:
                raise GameRuleError("本回合已经执行过额外调查")
            self._declare_action(room, state, seat, action, payload)
            return
        raise GameRuleError("不支持这个无间疑云操作")

    def view(self, room: ArcadeRoom, viewer: ArcadePlayer) -> dict[str, Any]:
        state: DepartedSuspicionState = room.state
        viewer_seat = viewer.seat
        if not state.boards:
            return self._lobby_view()
        finished = room.phase == "finished"
        pending = state.pending_action
        response_seat = self._response_seat(pending)
        choice = state.choice if state.choice and state.choice.get("seat") == viewer_seat else None
        post_shot_actor = (
            state.post_shot.get("seat") if state.post_shot is not None else None
        )
        pending_shot_actor = (
            state.pending_shot.scanner_seat
            if state.pending_shot is not None
            else None
        )
        equipment_hand = [
            EQUIPMENT_BY_ID[card_id].as_dict()
            for card_id in state.boards.get(viewer_seat, PlayerBoard()).equipment
        ]
        can_take_normal_action = (
            room.phase == "playing"
            and viewer_seat == state.turn_seat
            and state.boards[viewer_seat].alive
            and not state.action_done
            and pending is None
            and state.choice is None
            and state.pending_shot is None
            and state.post_shot is None
        )
        return {
            "turnPlayerId": self._player_id(room, state.turn_seat),
            "turnNumber": state.turn_number,
            "direction": "clockwise" if state.direction == 1 else "counterclockwise",
            "centralGuns": self._central_guns(state),
            "actionDone": state.action_done,
            "extraInvestigationDone": state.extra_investigation_done,
            "players": [
                self._player_view(room, state, board_seat, viewer_seat, finished)
                for board_seat in range(len(room.players))
            ],
            "selfTeam": (
                self._team(state.boards[viewer_seat])
                if viewer_seat in state.boards
                else None
            ),
            "equipmentHand": equipment_hand,
            "equipmentCatalog": [
                card.as_dict(available=not card.requires_cover)
                for card in EQUIPMENT_CARDS
            ],
            "pendingAction": (
                {
                    "actorPlayerId": self._player_id(room, pending.actor_seat),
                    "action": pending.action,
                    "actionLabel": ACTION_NAMES[pending.action],
                    "targetPlayerId": (
                        self._player_id(
                            room, state.boards[pending.actor_seat].aim_seat
                        )
                        if pending.action == "shoot"
                        else self._pending_target_id(room, pending)
                    ),
                    "responsePlayerId": self._player_id(room, response_seat),
                    "isMyResponse": response_seat == viewer_seat,
                }
                if pending is not None
                else None
            ),
            "pendingShot": (
                {
                    "targetPlayerId": self._player_id(
                        room, state.pending_shot.target_seat
                    ),
                    "source": state.pending_shot.source,
                    "scannerPlayerId": self._player_id(room, pending_shot_actor),
                    "isMyDecision": pending_shot_actor == viewer_seat,
                }
                if state.pending_shot is not None
                else None
            ),
            "choice": self._choice_view(room, state, choice),
            "postShot": (
                {
                    "kind": state.post_shot.get("kind"),
                    "isMyDecision": post_shot_actor == viewer_seat,
                }
                if state.post_shot is not None
                else None
            ),
            "waiting": self._waiting_view(room, state, response_seat),
            "legal": {
                "canTakeNormalAction": can_take_normal_action,
                "normalActionIds": (
                    self._normal_action_ids(state, viewer_seat)
                    if can_take_normal_action
                    else []
                ),
                "canTakeExtraInvestigation": (
                    room.phase == "playing"
                    and viewer_seat == state.turn_seat
                    and state.boards[viewer_seat].alive
                    and not state.boards[viewer_seat].restricted_to_equip
                    and "key" in state.boards[viewer_seat].effects
                    and self._has_investigation_target(state, viewer_seat)
                    and not state.extra_investigation_done
                    and pending is None
                    and state.choice is None
                    and state.pending_shot is None
                    and state.post_shot is None
                ),
                "canEndTurn": (
                    room.phase == "playing"
                    and viewer_seat == state.turn_seat
                    and state.action_done
                    and pending is None
                    and state.choice is None
                    and state.pending_shot is None
                    and state.post_shot is None
                ),
                "canRespond": response_seat == viewer_seat,
                "responseEquipmentIds": (
                    self._response_equipment_ids(state, viewer_seat, pending)
                    if pending is not None and response_seat == viewer_seat
                    else []
                ),
                "playableEquipmentIds": (
                    self._playable_equipment_ids(state, viewer_seat)
                    if room.phase == "playing"
                    else []
                ),
            },
            "history": state.history[-30:],
            "rulesNotice": "卧底牌能力尚未启用；新任务保留在33张资料库中但不会进入牌堆。",
        }

    def player_result(
        self, room: ArcadeRoom, player: ArcadePlayer
    ) -> tuple[str, str, bool]:
        state: DepartedSuspicionState = room.state
        board = state.boards[player.seat]
        leaders = [card.kind for card in board.cards if card.kind in {"agent", "kingpin"}]
        role = "+".join(INTEGRITY_NAMES[kind] for kind in leaders) or TEAM_NAMES[
            self._team(board)
        ]
        team = "solo" if len(leaders) == 2 else self._team(board)
        return role, team, player.id in room.winner_player_ids

    def manual_forfeit(self, room: ArcadeRoom, player: ArcadePlayer) -> bool:
        self._resign(room, room.state, player.seat)
        return True

    disconnect_timeout = manual_forfeit

    def _deal_integrity(self, player_count: int) -> dict[int, list[IntegrityCard]]:
        normal_count = NORMAL_INTEGRITY_PER_TEAM[player_count]
        normal_cards = [
            IntegrityCard(f"honest-{index}", "honest")
            for index in range(1, normal_count + 1)
        ] + [
            IntegrityCard(f"crooked-{index}", "crooked")
            for index in range(1, normal_count + 1)
        ]
        self.rng.shuffle(normal_cards)
        leader_round = [
            IntegrityCard("agent", "agent"),
            IntegrityCard("kingpin", "kingpin"),
            *normal_cards[: player_count - 2],
        ]
        self.rng.shuffle(leader_round)
        remainder = normal_cards[player_count - 2 :]
        self.rng.shuffle(remainder)
        # Odd-player games have one extra normal card after applying the
        # physical cards' player-count marks. It stays unseen and undealt.
        remainder = remainder[: player_count * 2]
        hands = {seat: [leader_round[seat]] for seat in range(player_count)}
        for seat in range(player_count):
            hands[seat].extend(remainder[seat * 2 : seat * 2 + 2])
            self.rng.shuffle(hands[seat])
        return hands

    @staticmethod
    def _gun_count(player_count: int) -> int:
        if player_count <= 4:
            return 2
        if player_count <= 6:
            return 3
        return 4

    def _declare_action(
        self,
        room: ArcadeRoom,
        state: DepartedSuspicionState,
        seat: int,
        action: str,
        payload: dict[str, Any],
    ) -> None:
        self._validate_action(room, state, seat, action, payload)
        state.last_investigation = None
        pending = PendingAction(seat, action, dict(payload))
        pending.response_order = self._response_order(state, pending)
        state.pending_action = pending
        self._log(
            state,
            "action_declared",
            f"{room.players[seat].name}宣布{ACTION_NAMES[action]}",
            playerId=room.players[seat].id,
        )
        if not pending.response_order:
            self._resolve_pending_action(room, state)

    def _validate_action(
        self,
        room: ArcadeRoom,
        state: DepartedSuspicionState,
        seat: int,
        action: str,
        payload: dict[str, Any],
    ) -> None:
        board = self._board(state, seat)
        if action in {"investigate", "extra_investigate"}:
            target = self._target_seat(room, state, payload, other_than=seat)
            target_board = state.boards[target]
            if "disguise" in target_board.effects:
                raise GameRuleError("伪装使这名玩家不能被调查")
            self._hidden_card(target_board, payload.get("cardIndex"))
            return
        if action == "equip":
            if any(not card.revealed for card in board.cards):
                self._hidden_card(board, payload.get("cardIndex"))
            return
        if action == "arm":
            if board.gun:
                raise GameRuleError("你已经持有一把枪")
            if self._central_guns(state) <= 0:
                raise GameRuleError("中央已经没有可拿的枪")
            if any(not card.revealed for card in board.cards):
                self._hidden_card(board, payload.get("cardIndex"))
            self._target_seat(room, state, payload, other_than=seat)
            return
        if action == "shoot":
            if not board.gun or board.aim_seat is None:
                raise GameRuleError("你必须持枪并已经瞄准目标")
            if state.acquired_gun_turn.get(seat) == state.turn_number:
                raise GameRuleError("本回合刚取得的枪不能立刻射击")
            if not state.boards[board.aim_seat].alive:
                raise GameRuleError("当前瞄准目标已经出局")

    def _resolve_pending_action(
        self, room: ArcadeRoom, state: DepartedSuspicionState
    ) -> None:
        pending = state.pending_action
        if pending is None:
            return
        state.pending_action = None
        try:
            self._validate_action(
                room,
                state,
                pending.actor_seat,
                pending.action,
                pending.payload,
            )
        except GameRuleError:
            self._log(state, "action_cancelled", "原行动已不再合法，可重新选择行动")
            return
        actor = state.boards[pending.actor_seat]
        action = pending.action
        if action in {"investigate", "extra_investigate"}:
            target = int(pending.payload["targetSeat"])
            card_index = int(pending.payload["cardIndex"])
            card = state.boards[target].cards[card_index]
            state.knowledge[pending.actor_seat].add(card.id)
            state.last_investigation = (
                {
                    "actorSeat": pending.actor_seat,
                    "targetSeat": target,
                    "cardIndex": card_index,
                    "cardId": card.id,
                    "turnNumber": state.turn_number,
                }
                if action == "investigate"
                else None
            )
            if action == "extra_investigate":
                state.extra_investigation_done = True
            else:
                state.action_done = True
            self._log(
                state,
                "investigate",
                f"{room.players[pending.actor_seat].name}调查了{room.players[target].name}的一张底细",
            )
            return
        if action == "equip":
            if any(not card.revealed for card in actor.cards):
                self._hidden_card(actor, pending.payload.get("cardIndex")).revealed = True
            state.action_done = True
            self._draw_equipment(state, pending.actor_seat)
            self._log(state, "equip", f"{room.players[pending.actor_seat].name}获取了装备")
            return
        if action == "arm":
            if any(not card.revealed for card in actor.cards):
                self._hidden_card(actor, pending.payload.get("cardIndex")).revealed = True
            actor.gun = True
            actor.aim_seat = int(pending.payload["targetSeat"])
            state.acquired_gun_turn[pending.actor_seat] = state.turn_number
            state.action_done = True
            self._log(
                state,
                "arm",
                f"{room.players[pending.actor_seat].name}武装并瞄准{room.players[actor.aim_seat].name}",
            )
            return
        if action == "shoot":
            state.action_done = True
            self._begin_shot(
                room,
                state,
                pending.actor_seat,
                actor.aim_seat,
                source="gun",
            )

    def _pass_response(
        self, room: ArcadeRoom, state: DepartedSuspicionState, seat: int
    ) -> None:
        pending = state.pending_action
        if pending is None or self._response_seat(pending) != seat:
            raise GameRuleError("现在不轮到你响应")
        pending.response_index += 1
        if pending.response_index >= len(pending.response_order):
            self._resolve_pending_action(room, state)

    def _resume_pending_action(
        self,
        room: ArcadeRoom,
        state: DepartedSuspicionState,
        *,
        after: int,
    ) -> None:
        pending = state.pending_action
        if pending is None or state.choice is not None:
            return
        if not state.boards[pending.actor_seat].alive:
            state.pending_action = None
            self._log(state, "action_cancelled", "行动玩家已经出局，原行动取消")
            return
        if pending.action == "shoot" and not state.boards[pending.actor_seat].gun:
            state.pending_action = None
            self._log(state, "shot_cancelled", "射手失去枪，射击取消并可重新选择行动")
            return
        pending.response_order = self._response_order(state, pending, after=after)
        pending.response_index = 0
        if not pending.response_order:
            self._resolve_pending_action(room, state)

    def _skip_departed_responder(
        self,
        room: ArcadeRoom,
        state: DepartedSuspicionState,
    ) -> None:
        pending = state.pending_action
        if pending is None or state.choice is not None:
            return
        remaining = pending.response_order[pending.response_index :]
        pending.response_order = [
            seat
            for seat in remaining
            if state.boards[seat].alive
            and self._response_equipment_ids(state, seat, pending)
        ]
        pending.response_index = 0
        if not pending.response_order:
            self._resolve_pending_action(room, state)

    def _response_order(
        self, state: DepartedSuspicionState, pending: PendingAction, *, after: int | None = None
    ) -> list[int]:
        start = pending.actor_seat if after is None else after
        seats: list[int] = []
        cursor = start
        for _ in range(len(state.boards)):
            cursor = self._next_alive(state, cursor)
            if cursor in seats:
                break
            seats.append(cursor)
        return [
            seat
            for seat in seats
            if self._response_equipment_ids(state, seat, pending)
        ]

    @staticmethod
    def _response_seat(pending: PendingAction | None) -> int | None:
        if pending is None or pending.response_index >= len(pending.response_order):
            return None
        return pending.response_order[pending.response_index]

    def _response_equipment_ids(
        self,
        state: DepartedSuspicionState,
        seat: int,
        pending: PendingAction | None,
    ) -> list[str]:
        if pending is None:
            return []
        result: list[str] = []
        for card_id in state.boards[seat].equipment:
            timing = EQUIPMENT_BY_ID[card_id].timing
            if timing == "anytime":
                result.append(card_id)
            elif timing == "other_turn" and seat != state.turn_seat:
                result.append(card_id)
            elif timing == "shoot_response" and pending.action == "shoot":
                result.append(card_id)
            elif timing == "own_shoot" and pending.action == "shoot" and seat == pending.actor_seat:
                result.append(card_id)
            elif (
                timing == "self_shot"
                and pending.action == "shoot"
                and state.boards[pending.actor_seat].aim_seat == seat
            ):
                result.append(card_id)
        return result

    def _playable_equipment_ids(
        self, state: DepartedSuspicionState, seat: int
    ) -> list[str]:
        board = state.boards.get(seat)
        if board is None or not board.alive:
            return []
        if (
            state.pending_shot is not None
            or state.post_shot is not None
            or state.choice is not None
        ):
            return []
        if state.pending_action is not None:
            if self._response_seat(state.pending_action) != seat:
                return []
            return self._response_equipment_ids(state, seat, state.pending_action)
        result: list[str] = []
        for card_id in board.equipment:
            timing = EQUIPMENT_BY_ID[card_id].timing
            if timing == "anytime":
                result.append(card_id)
            elif timing == "active" and seat == state.turn_seat:
                result.append(card_id)
            elif timing == "other_turn" and seat != state.turn_seat:
                result.append(card_id)
            elif timing == "after_investigate" and state.last_investigation is not None:
                result.append(card_id)
        return result

    def _play_equipment(
        self,
        room: ArcadeRoom,
        state: DepartedSuspicionState,
        seat: int,
        payload: dict[str, Any],
    ) -> None:
        card_id = str(payload.get("cardId", ""))
        board = self._board(state, seat)
        if card_id not in board.equipment:
            raise GameRuleError("你没有这张装备")
        if card_id not in self._playable_equipment_ids(state, seat):
            raise GameRuleError("当前不是这张装备的使用时机")
        if card_id == "new_assignment":
            raise GameRuleError("卧底牌能力尚未启用，新任务暂时不能使用")

        original_state = copy.deepcopy(state)
        board.equipment.remove(card_id)
        keep_card = card_id == "fingerprint_kit" and bool(payload.get("returnToHand"))
        try:
            if card_id != "surveillance_camera" and state.last_investigation is not None:
                state.last_investigation = None
            self._resolve_equipment(room, state, seat, card_id, payload)
        except Exception:
            room.state = original_state
            raise
        if room.phase == "finished":
            return
        definition = EQUIPMENT_BY_ID[card_id]
        if keep_card:
            board.equipment.append(card_id)
        elif not definition.persistent:
            state.equipment_deck.append(card_id)
        self._log(
            state,
            "equipment",
            f"{room.players[seat].name}使用了{definition.name}",
            cardId=card_id,
        )

        pending = state.pending_action
        if pending is not None and state.choice is None:
            self._resume_pending_action(room, state, after=seat)
        elif pending is not None and state.choice is not None:
            state.choice["resumePendingAfterSeat"] = seat

    def _resolve_equipment(
        self,
        room: ArcadeRoom,
        state: DepartedSuspicionState,
        seat: int,
        card_id: str,
        payload: dict[str, Any],
    ) -> None:
        board = state.boards[seat]
        if card_id == "blackmail":
            first, second = self._two_targets(room, state, payload, excluded={seat})
            first_index = self._card_index(payload.get("firstCardIndex"))
            second_index = self._card_index(payload.get("secondCardIndex"))
            state.boards[first].cards[first_index], state.boards[second].cards[second_index] = (
                state.boards[second].cards[second_index],
                state.boards[first].cards[first_index],
            )
            self._check_victory(room, state)
            return
        if card_id == "coffee":
            if seat == state.turn_seat:
                raise GameRuleError("咖啡只能在另一名玩家回合中使用")
            if seat not in state.coffee_after:
                state.coffee_after.append(seat)
            return
        if card_id == "defibrillator":
            target = self._eliminated_target(room, state, payload, other_than=seat)
            self._revive(state, target, restricted=False)
            return
        if card_id == "evidence_bag":
            owner = self._target_seat(room, state, payload, key="ownerSeat")
            recipient = self._target_seat(room, state, payload, key="recipientSeat")
            if recipient == seat:
                raise GameRuleError("证物袋的接收者不能是你")
            if recipient == owner:
                raise GameRuleError("证物袋必须把装备交给另一名玩家")
            if not state.boards[owner].equipment:
                raise GameRuleError("装备持有者手中没有装备")
            moved = state.boards[owner].equipment.pop(0)
            state.boards[recipient].equipment.append(moved)
            if len(state.boards[recipient].equipment) > 1:
                state.choice = {"kind": "equipment_limit", "seat": recipient}
            return
        if card_id == "flashbang":
            target = self._target_seat(room, state, payload)
            hidden_ids = {
                card.id for card in state.boards[target].cards if not card.revealed
            }
            self.rng.shuffle(state.boards[target].cards)
            for known in state.knowledge.values():
                known.difference_update(hidden_ids)
            return
        if card_id == "k9_unit":
            target = self._armed_target(room, state, payload)
            self._drop_gun(state, target)
            return
        if card_id == "metal_detector":
            choices = payload.get("choices", {})
            for target, target_board in state.boards.items():
                if target == seat or not target_board.alive or not target_board.gun:
                    continue
                if "disguise" in target_board.effects:
                    continue
                index = self._choice_index(choices, target, target_board)
                if index is not None:
                    state.knowledge[seat].add(target_board.cards[index].id)
            return
        if card_id == "planted_evidence":
            target = self._target_seat(room, state, payload)
            self._add_effect(state.boards[target], card_id)
            return
        if card_id == "polygraph":
            target = self._target_seat(room, state, payload, other_than=seat)
            if "disguise" not in state.boards[target].effects:
                self._learn_all_hidden(state, seat, target)
            if "disguise" not in board.effects:
                self._learn_all_hidden(state, target, seat)
            return
        if card_id == "report_audit":
            seats = [
                target
                for target, target_board in state.boards.items()
                if target_board.alive and any(not card.revealed for card in target_board.cards)
            ]
            if not seats:
                raise GameRuleError("没有玩家可以公开暗置底细")
            state.choice = {"kind": "report_audit", "seat": seats[0], "queue": seats}
            return
        if card_id == "restraining_order":
            pending = self._pending_shoot(state)
            target = self._target_seat(room, state, payload, other_than=pending.actor_seat)
            old_target = state.boards[pending.actor_seat].aim_seat
            if target == old_target:
                raise GameRuleError("限制令必须改瞄另一名目标")
            state.boards[pending.actor_seat].aim_seat = target
            return
        if card_id == "smoke_grenade":
            state.direction *= -1
            return
        if card_id == "surveillance_camera":
            investigation = state.last_investigation
            if investigation is None:
                raise GameRuleError("当前没有刚刚完成的正常调查行动")
            target = investigation["targetSeat"]
            card = next(
                (item for item in state.boards[target].cards if item.id == investigation["cardId"]),
                None,
            )
            if card is None:
                raise GameRuleError("刚才被调查的底细已经移动")
            card.revealed = True
            state.last_investigation = None
            return
        if card_id == "taser":
            if board.gun:
                raise GameRuleError("你已有枪时不能使用电击枪")
            target = self._armed_target(room, state, payload)
            aim = self._target_seat(room, state, payload, key="aimSeat", other_than=seat)
            self._drop_gun(state, target)
            board.gun = True
            board.aim_seat = aim
            state.acquired_gun_turn[seat] = state.turn_number
            return
        if card_id == "truth_serum":
            target = self._target_seat(room, state, payload)
            if not any(not card.revealed for card in state.boards[target].cards):
                raise GameRuleError("目标没有暗置底细")
            state.choice = {"kind": "truth_serum", "seat": target}
            return
        if card_id == "wiretap":
            first, second = self._two_targets(room, state, payload)
            for target, key in ((first, "firstCardIndex"), (second, "secondCardIndex")):
                target_board = state.boards[target]
                if "disguise" in target_board.effects:
                    continue
                card = self._hidden_card(target_board, payload.get(key))
                state.knowledge[seat].add(card.id)
            return
        if card_id == "classified_orders":
            pending = self._pending_shoot(state)
            decider = self._target_seat(room, state, payload, key="deciderSeat", other_than=seat)
            state.choice = {
                "kind": "classified_redirect",
                "seat": decider,
                "shooterSeat": pending.actor_seat,
            }
            return
        if card_id == "fake_id":
            first, second = self._two_targets(room, state, payload)
            first_card = state.boards[first].cards[self._card_index(payload.get("firstCardIndex"))]
            second_card = state.boards[second].cards[self._card_index(payload.get("secondCardIndex"))]
            if any(
                not card.revealed or card.kind not in {"honest", "crooked"}
                for card in (first_card, second_card)
            ):
                raise GameRuleError("假证件只能交换公开的普通正直/腐败底细")
            first_index = state.boards[first].cards.index(first_card)
            second_index = state.boards[second].cards.index(second_card)
            state.boards[first].cards[first_index], state.boards[second].cards[second_index] = second_card, first_card
            return
        if card_id == "fingerprint_kit":
            target = self._target_seat(room, state, payload, other_than=seat)
            if "disguise" in state.boards[target].effects:
                raise GameRuleError("伪装使这名玩家不能被调查")
            card = self._hidden_card(state.boards[target], payload.get("cardIndex"))
            state.knowledge[seat].add(card.id)
            if payload.get("returnToHand"):
                own = self._hidden_card(board, payload.get("ownCardIndex"))
                own.revealed = True
            return
        if card_id == "grenade":
            target = self._target_seat(room, state, payload, other_than=seat)
            if state.boards[target].grenade_stage:
                raise GameRuleError("目标已经持有手榴弹")
            state.boards[target].grenade_stage = 1
            self._add_effect(state.boards[target], card_id)
            return
        if card_id == "holster":
            pending = self._pending_shoot(state)
            if pending.actor_seat != seat:
                raise GameRuleError("枪套只能用于自己的射击")
            target = self._target_seat(room, state, payload, other_than=seat)
            state.boards[seat].aim_seat = target
            return
        if card_id == "concussion_grenade":
            if not any(item.gun for item in state.boards.values()):
                raise GameRuleError("当前没有持枪玩家")
            for target in state.boards:
                self._drop_gun(state, target)
            return
        if card_id == "crutches":
            target = self._eliminated_target(room, state, payload, other_than=seat)
            self._revive(state, target, restricted=True)
            self._add_effect(state.boards[target], card_id)
            return
        if card_id == "disguise":
            target = self._target_seat(room, state, payload)
            self._add_effect(state.boards[target], card_id)
            return
        if card_id == "helmet":
            pending = self._pending_shoot(state)
            shooter = pending.actor_seat
            if state.boards[shooter].aim_seat != seat:
                raise GameRuleError("头盔只能取消自己即将受到的中枪")
            self._drop_gun(state, shooter)
            state.pending_action = None
            state.action_done = True
            return
        if card_id == "inspection_gloves":
            target = self._target_seat(room, state, payload)
            target_board = state.boards[target]
            if not target_board.equipment and not any(not card.revealed for card in target_board.cards):
                raise GameRuleError("目标没有可执行的搜查选项")
            state.choice = {"kind": "inspection_gloves", "seat": target}
            return
        if card_id == "key":
            target = self._target_seat(room, state, payload, other_than=seat)
            self._add_effect(state.boards[target], card_id)
            return
        if card_id == "med_kit":
            target = self._target_seat(room, state, payload)
            leader = self._leader_card(state.boards[target])
            if leader is None or not leader.wounded:
                raise GameRuleError("目标没有受伤的领袖牌")
            leader.wounded = False
            return
        if card_id == "security_wand":
            target = self._target_seat(room, state, payload, other_than=seat)
            target_board = state.boards[target]
            if "disguise" in target_board.effects:
                raise GameRuleError("伪装使这名玩家不能被调查")
            card = self._hidden_card(target_board, payload.get("cardIndex"))
            state.knowledge[seat].add(card.id)
            if payload.get("ownCardIndex") is not None:
                own = board.cards[self._card_index(payload.get("ownCardIndex"))]
                if not own.revealed:
                    raise GameRuleError("安检棒只能重新暗置自己的公开底细")
                own.revealed = False
                for known in state.knowledge.values():
                    known.add(own.id)
            return
        if card_id == "sunglasses":
            first, second = self._two_card_locations(room, state, payload)
            if first == second:
                raise GameRuleError("太阳镜必须选择两张不同底细")
            for target, index in (first, second):
                card = state.boards[target].cards[index]
                if not card.revealed:
                    raise GameRuleError("太阳镜只能重新暗置公开底细")
                card.revealed = False
                for known in state.knowledge.values():
                    known.add(card.id)
            return
        raise GameRuleError("这张装备尚未接入规则引擎")

    def _end_turn(
        self,
        room: ArcadeRoom,
        state: DepartedSuspicionState,
        seat: int,
        payload: dict[str, Any],
    ) -> None:
        if not state.action_done:
            raise GameRuleError("必须先完成本回合的正常行动")
        board = state.boards[seat]
        if board.gun:
            aim_value = payload.get("aimSeat")
            if aim_value is not None:
                aim = self._target_seat(room, state, payload, key="aimSeat", other_than=seat)
                board.aim_seat = aim
        state.last_investigation = None
        if board.grenade_stage == 1:
            state.choice = {"kind": "grenade_pass", "seat": seat}
            return
        if board.grenade_stage == 2:
            board.grenade_stage = 0
            if "grenade" in board.effects:
                board.effects.remove("grenade")
            state.equipment_deck.append("grenade")
            self._begin_shot(
                room,
                state,
                None,
                seat,
                source="grenade",
                advance_after=True,
            )
            return
        self._advance_turn(room, state)

    def _advance_turn(self, room: ArcadeRoom, state: DepartedSuspicionState) -> None:
        if room.phase == "finished":
            return
        if state.coffee_after:
            next_seat = state.coffee_after.pop(0)
            if not state.boards[next_seat].alive:
                next_seat = self._next_alive(state, state.turn_seat)
        else:
            next_seat = self._next_alive(state, state.turn_seat)
        state.turn_seat = next_seat
        state.turn_number += 1
        state.action_done = False
        state.extra_investigation_done = False
        state.last_investigation = None
        self._log(state, "turn", f"轮到{room.players[next_seat].name}")

    def _begin_shot(
        self,
        room: ArcadeRoom,
        state: DepartedSuspicionState,
        shooter_seat: int | None,
        target_seat: int | None,
        *,
        source: str,
        advance_after: bool = False,
    ) -> None:
        if target_seat is None or not state.boards[target_seat].alive:
            raise GameRuleError("射击目标已经出局")
        if shooter_seat is not None and source == "gun":
            self._drop_gun(state, shooter_seat)
        target = state.boards[target_seat]
        for card in target.cards:
            card.revealed = True
        scanner_seat = next(
            (
                seat
                for seat in self._seat_order(state, shooter_seat if shooter_seat is not None else target_seat)
                if state.boards[seat].alive
                and "thumbprint_scanner" in state.boards[seat].equipment
            ),
            None,
        )
        state.pending_shot = PendingShot(
            shooter_seat=shooter_seat,
            target_seat=target_seat,
            source=source,
            advance_after=advance_after,
            scanner_seat=scanner_seat,
        )
        self._log(
            state,
            "shot_reveal",
            f"{room.players[target_seat].name}中枪并公开全部底细",
        )
        if scanner_seat is None:
            self._apply_shot(room, state)

    def _handle_pending_shot(
        self,
        room: ArcadeRoom,
        state: DepartedSuspicionState,
        seat: int,
        action: str,
        payload: dict[str, Any],
    ) -> None:
        shot = state.pending_shot
        if shot is None or shot.scanner_seat != seat:
            raise GameRuleError("正在等待其他玩家处理指纹扫描器")
        if action == "pass_scanner":
            shot.scanner_seat = None
            self._apply_shot(room, state)
            return
        if action != "use_scanner":
            raise GameRuleError("请使用或放弃指纹扫描器")
        board = state.boards[seat]
        if "thumbprint_scanner" not in board.equipment:
            raise GameRuleError("你没有指纹扫描器")
        target = state.boards[shot.target_seat]
        own_index: int | None = None
        target_index: int | None = None
        if payload.get("ownCardIndex") is not None or payload.get("targetCardIndex") is not None:
            own_index = self._card_index(payload.get("ownCardIndex"))
            target_index = self._card_index(payload.get("targetCardIndex"))
            target_card = target.cards[target_index]
            if target_card.kind not in {"honest", "crooked"}:
                raise GameRuleError("不能拿走目标的领袖牌")
        board.equipment.remove("thumbprint_scanner")
        state.equipment_deck.append("thumbprint_scanner")
        self._learn_all_hidden(state, seat, shot.target_seat, include_revealed=True)
        if own_index is not None and target_index is not None:
            target_card = target.cards[target_index]
            board.cards[own_index], target.cards[target_index] = target_card, board.cards[own_index]
            self._check_victory(room, state)
            if room.phase == "finished":
                state.pending_shot = None
                return
        shot.scanner_seat = None
        self._apply_shot(room, state)

    def _apply_shot(self, room: ArcadeRoom, state: DepartedSuspicionState) -> None:
        shot = state.pending_shot
        if shot is None:
            return
        target_seat = shot.target_seat
        target = state.boards[target_seat]
        had_mobile = "mobile_detonator" in target.equipment
        leader = self._leader_card(target)
        advance_after = shot.advance_after
        state.pending_shot = None
        draw_after = False
        eliminated = False
        if leader is not None and not leader.wounded:
            leader.wounded = True
            draw_after = True
            self._log(state, "wounded", f"{room.players[target_seat].name}的领袖受伤")
        else:
            eliminated = True
            self._eliminate(state, target_seat, keep_equipment=had_mobile)
            self._log(state, "eliminated", f"{room.players[target_seat].name}出局")
            self._check_victory(room, state)
            if room.phase == "finished":
                return
        if had_mobile:
            state.post_shot = {
                "kind": "mobile_detonator",
                "seat": target_seat,
                "drawAfter": draw_after,
                "eliminated": eliminated,
                "advanceAfter": advance_after,
            }
            return
        if draw_after:
            self._draw_equipment(state, target_seat, advance_after=advance_after)
            if state.choice is not None:
                return
        if advance_after:
            self._advance_turn(room, state)

    def _handle_post_shot(
        self,
        room: ArcadeRoom,
        state: DepartedSuspicionState,
        seat: int,
        action: str,
        payload: dict[str, Any],
    ) -> None:
        post = state.post_shot
        if post is None or post.get("seat") != seat:
            raise GameRuleError("正在等待中枪玩家处理移动引爆器")
        if action not in {"use_mobile_detonator", "pass_mobile_detonator"}:
            raise GameRuleError("请使用或放弃移动引爆器")
        board = state.boards[seat]
        use = action == "use_mobile_detonator"
        if use:
            target = self._target_seat(room, state, payload, other_than=seat)
            if "mobile_detonator" not in board.equipment:
                raise GameRuleError("你没有移动引爆器")
            board.equipment.remove("mobile_detonator")
            state.equipment_deck.append("mobile_detonator")
        draw_after = bool(post.get("drawAfter"))
        eliminated = bool(post.get("eliminated"))
        advance_after = bool(post.get("advanceAfter"))
        state.post_shot = None
        if not use and "mobile_detonator" in board.equipment and eliminated:
            self._discard_all_equipment(state, board)
        elif eliminated:
            self._discard_all_equipment(state, board)
        if draw_after:
            self._draw_equipment(state, seat, advance_after=advance_after and not use)
        if use:
            self._begin_shot(
                room,
                state,
                seat,
                target,
                source="detonator",
                advance_after=advance_after,
            )
        elif advance_after and state.choice is None:
            self._advance_turn(room, state)

    def _handle_choice(
        self,
        room: ArcadeRoom,
        state: DepartedSuspicionState,
        seat: int,
        action: str,
        payload: dict[str, Any],
    ) -> None:
        choice = state.choice
        if choice is None or choice.get("seat") != seat:
            raise GameRuleError("正在等待其他玩家作出选择")
        kind = choice["kind"]
        board = state.boards[seat]
        if kind == "equipment_limit":
            if action != "choose_equipment":
                raise GameRuleError("请选择要保留的装备")
            keep = str(payload.get("cardId", ""))
            if keep not in board.equipment:
                raise GameRuleError("请选择手中的一张装备")
            for card_id in list(board.equipment):
                if card_id != keep:
                    board.equipment.remove(card_id)
                    state.equipment_deck.append(card_id)
            advance_after = bool(choice.get("advanceAfter"))
            resume_after = choice.get("resumePendingAfterSeat")
            state.choice = None
            if isinstance(resume_after, int):
                self._resume_pending_action(room, state, after=resume_after)
            elif advance_after:
                self._advance_turn(room, state)
            return
        if kind == "report_audit":
            if action != "choose_reveal":
                raise GameRuleError("请选择一张暗置底细公开")
            self._hidden_card(board, payload.get("cardIndex")).revealed = True
            queue = [item for item in choice["queue"] if item != seat]
            if queue:
                choice["queue"] = queue
                choice["seat"] = queue[0]
            else:
                state.choice = None
            return
        if kind == "truth_serum":
            if action != "choose_reveal":
                raise GameRuleError("请选择一张暗置底细公开")
            self._hidden_card(board, payload.get("cardIndex")).revealed = True
            state.choice = None
            return
        if kind == "inspection_gloves":
            if action != "inspection_choice":
                raise GameRuleError("请选择搜查手套的处理方式")
            decision = str(payload.get("choice", ""))
            if decision == "discard_equipment" and board.equipment:
                card_id = board.equipment.pop(0)
                state.equipment_deck.append(card_id)
            elif decision == "show_integrity" and any(not card.revealed for card in board.cards):
                for viewer in state.knowledge.values():
                    viewer.update(card.id for card in board.cards if not card.revealed)
            else:
                raise GameRuleError("这个搜查选项当前不能执行")
            state.choice = None
            return
        if kind == "classified_redirect":
            if action != "choose_redirect":
                raise GameRuleError("请选择新的射击目标")
            shooter = int(choice["shooterSeat"])
            target = self._target_seat(room, state, payload, other_than=shooter)
            state.boards[shooter].aim_seat = target
            state.choice = None
            state.pending_action = None
            state.action_done = True
            self._begin_shot(room, state, shooter, target, source="gun")
            return
        if kind == "grenade_pass":
            if action != "pass_grenade":
                raise GameRuleError("请把手榴弹传给另一名玩家")
            target = self._target_seat(room, state, payload, other_than=seat)
            if state.boards[target].grenade_stage:
                raise GameRuleError("目标已经持有手榴弹")
            board.grenade_stage = 0
            if "grenade" in board.effects:
                board.effects.remove("grenade")
            state.boards[target].grenade_stage = 2
            self._add_effect(state.boards[target], "grenade")
            state.choice = None
            self._advance_turn(room, state)
            return
        raise GameRuleError("未知的待处理选择")

    def _draw_equipment(
        self,
        state: DepartedSuspicionState,
        seat: int,
        *,
        advance_after: bool = False,
    ) -> None:
        if not state.equipment_deck:
            return
        board = state.boards[seat]
        board.equipment.append(state.equipment_deck.pop(0))
        if len(board.equipment) > 1:
            state.choice = {
                "kind": "equipment_limit",
                "seat": seat,
                "advanceAfter": advance_after,
            }

    def _resolve_hand_limit(
        self, state: DepartedSuspicionState, seat: int, keep_card_id: Any
    ) -> None:
        board = state.boards[seat]
        if len(board.equipment) <= 1:
            return
        keep = str(keep_card_id or "")
        if keep not in board.equipment:
            raise GameRuleError("接收者超出装备上限，请指定其保留的装备")
        for card_id in list(board.equipment):
            if card_id != keep:
                board.equipment.remove(card_id)
                state.equipment_deck.append(card_id)

    def _resign(
        self, room: ArcadeRoom, state: DepartedSuspicionState, seat: int
    ) -> None:
        board = self._board(state, seat)
        if not board.alive:
            turn_number = state.turn_number
            self._repair_waits_after_departure(room, state, seat)
            if (
                room.phase != "finished"
                and seat == state.turn_seat
                and state.turn_number == turn_number
            ):
                self._advance_turn(room, state)
            return
        was_turn = seat == state.turn_seat
        for card in board.cards:
            card.revealed = True
        self._eliminate(state, seat)
        self._log(state, "resign", f"{room.players[seat].name}认输并出局")
        self._check_victory(room, state)
        if room.phase == "finished":
            return
        turn_number = state.turn_number
        self._repair_waits_after_departure(room, state, seat)
        if (
            room.phase != "finished"
            and was_turn
            and state.turn_number == turn_number
        ):
            self._advance_turn(room, state)

    def _repair_waits_after_departure(
        self,
        room: ArcadeRoom,
        state: DepartedSuspicionState,
        seat: int,
    ) -> None:
        shot = state.pending_shot
        if shot is not None:
            if shot.target_seat == seat:
                state.pending_shot = None
                if shot.advance_after:
                    self._advance_turn(room, state)
                return
            if shot.scanner_seat == seat:
                shot.scanner_seat = None
                self._apply_shot(room, state)
                return

        post_shot = state.post_shot
        if post_shot is not None and post_shot.get("seat") == seat:
            self._handle_post_shot(
                room,
                state,
                seat,
                "pass_mobile_detonator",
                {},
            )
            return

        pending = state.pending_action
        if pending is not None and pending.actor_seat == seat:
            state.pending_action = None
            self._log(state, "action_cancelled", "行动玩家已经出局，原行动取消")
            if state.choice is not None:
                state.choice.pop("resumePendingAfterSeat", None)
                if state.choice.get("kind") == "classified_redirect":
                    state.choice = None
            return

        choice = state.choice
        if choice is not None and choice.get("kind") == "report_audit":
            queue = [
                queued_seat
                for queued_seat in choice.get("queue", [])
                if queued_seat != seat
                and state.boards[queued_seat].alive
                and any(not card.revealed for card in state.boards[queued_seat].cards)
            ]
            if not queue:
                state.choice = None
            else:
                choice["queue"] = queue
                if choice.get("seat") not in queue:
                    choice["seat"] = queue[0]
        elif choice is not None and choice.get("seat") == seat:
            resume_after = choice.get("resumePendingAfterSeat")
            advance_after = bool(choice.get("advanceAfter"))
            state.choice = None
            if isinstance(resume_after, int):
                self._resume_pending_action(room, state, after=resume_after)
            elif advance_after:
                self._advance_turn(room, state)

        self._skip_departed_responder(room, state)

    def _check_victory(
        self, room: ArcadeRoom, state: DepartedSuspicionState
    ) -> None:
        for seat, board in state.boards.items():
            kinds = {card.kind for card in board.cards}
            if {"agent", "kingpin"} <= kinds:
                room.finish(
                    "solo",
                    [room.players[seat].id],
                    f"{room.players[seat].name}同时获得探员与头目，单独获胜",
                )
                return
        agent_board = self._leader_owner(state, "agent")
        kingpin_board = self._leader_owner(state, "kingpin")
        if kingpin_board is not None and not state.boards[kingpin_board].alive:
            winners = [
                room.players[seat].id
                for seat, board in state.boards.items()
                if self._team(board) == "honest"
            ]
            room.finish("honest", winners, "头目出局，正直阵营获胜")
        elif agent_board is not None and not state.boards[agent_board].alive:
            winners = [
                room.players[seat].id
                for seat, board in state.boards.items()
                if self._team(board) == "crooked"
            ]
            room.finish("crooked", winners, "探员出局，腐败阵营获胜")

    def _eliminate(
        self,
        state: DepartedSuspicionState,
        seat: int,
        *,
        keep_equipment: bool = False,
    ) -> None:
        board = state.boards[seat]
        board.alive = False
        self._drop_gun(state, seat)
        if board.grenade_stage:
            board.grenade_stage = 0
            if "grenade" in board.effects:
                board.effects.remove("grenade")
            state.equipment_deck.append("grenade")
        if not keep_equipment:
            self._discard_all_equipment(state, board)

    @staticmethod
    def _revive(state: DepartedSuspicionState, seat: int, *, restricted: bool) -> None:
        board = state.boards[seat]
        board.alive = True
        board.restricted_to_equip = restricted

    @staticmethod
    def _add_effect(board: PlayerBoard, effect: str) -> None:
        if effect not in board.effects:
            board.effects.append(effect)

    @staticmethod
    def _drop_gun(state: DepartedSuspicionState, seat: int) -> None:
        board = state.boards[seat]
        board.gun = False
        board.aim_seat = None

    @staticmethod
    def _discard_all_equipment(
        state: DepartedSuspicionState, board: PlayerBoard
    ) -> None:
        while board.equipment:
            state.equipment_deck.append(board.equipment.pop(0))

    @staticmethod
    def _leader_card(board: PlayerBoard) -> IntegrityCard | None:
        return next(
            (card for card in board.cards if card.kind in {"agent", "kingpin"}),
            None,
        )

    @staticmethod
    def _leader_owner(state: DepartedSuspicionState, kind: str) -> int | None:
        return next(
            (
                seat
                for seat, board in state.boards.items()
                if any(card.kind == kind for card in board.cards)
            ),
            None,
        )

    @staticmethod
    def _team(board: PlayerBoard) -> str:
        kinds = {card.kind for card in board.cards}
        if "agent" in kinds:
            return "honest"
        if "kingpin" in kinds:
            return "crooked"
        honest = sum(card.kind == "honest" for card in board.cards)
        crooked = sum(card.kind == "crooked" for card in board.cards)
        if "planted_evidence" in board.effects:
            honest, crooked = crooked, honest
        return "honest" if honest > crooked else "crooked"

    def _player_view(
        self,
        room: ArcadeRoom,
        state: DepartedSuspicionState,
        seat: int,
        viewer_seat: int,
        finished: bool,
    ) -> dict[str, Any]:
        board = state.boards[seat]
        viewer_knowledge = state.knowledge.get(viewer_seat, set())
        cards = []
        for index, card in enumerate(board.cards):
            is_own = seat == viewer_seat
            visible = finished or is_own or card.revealed
            remembered = card.id in viewer_knowledge
            cards.append(
                {
                    "index": index,
                    "kind": card.kind if visible or remembered else None,
                    "label": INTEGRITY_NAMES[card.kind] if visible or remembered else "未知",
                    "revealed": card.revealed,
                    "knowledge": (
                        "own" if is_own else "public" if card.revealed or finished else "investigated" if remembered else "hidden"
                    ),
                    "wounded": card.wounded if visible else False,
                }
            )
        return {
            "playerId": room.players[seat].id,
            "seat": seat,
            "alive": board.alive,
            "gun": board.gun,
            "aimPlayerId": self._player_id(room, board.aim_seat),
            "equipmentCount": len(board.equipment),
            "effects": [
                {
                    "id": effect,
                    "name": EQUIPMENT_BY_ID[effect].name,
                    "grenadeStage": board.grenade_stage if effect == "grenade" else None,
                }
                for effect in board.effects
                if effect in EQUIPMENT_BY_ID
            ],
            "restrictedToEquip": board.restricted_to_equip,
            "cards": cards,
            "team": self._team(board) if finished or seat == viewer_seat else None,
        }

    def _choice_view(
        self,
        room: ArcadeRoom,
        state: DepartedSuspicionState,
        choice: dict[str, Any] | None,
    ) -> dict[str, Any] | None:
        if choice is None:
            return None
        kind = str(choice["kind"])
        result: dict[str, Any] = {"kind": kind, "isMyDecision": True}
        if kind == "equipment_limit":
            result["cards"] = [
                EQUIPMENT_BY_ID[card_id].as_dict()
                for card_id in state.boards[int(choice["seat"])].equipment
            ]
        if kind == "classified_redirect":
            result["shooterPlayerId"] = self._player_id(room, int(choice["shooterSeat"]))
        return result

    @staticmethod
    def _pending_target_id(room: ArcadeRoom, pending: PendingAction) -> str | None:
        if pending.action == "shoot":
            return None
        value = pending.payload.get("targetSeat")
        if isinstance(value, int) and 0 <= value < len(room.players):
            return room.players[value].id
        return None

    @staticmethod
    def _player_id(room: ArcadeRoom, seat: int | None) -> str | None:
        if seat is None or not 0 <= seat < len(room.players):
            return None
        return room.players[seat].id

    @staticmethod
    def _board(state: DepartedSuspicionState, seat: int) -> PlayerBoard:
        try:
            return state.boards[seat]
        except KeyError as exc:
            raise GameRuleError("找不到这个玩家") from exc

    def _target_seat(
        self,
        room: ArcadeRoom,
        state: DepartedSuspicionState,
        payload: dict[str, Any],
        *,
        key: str = "targetSeat",
        other_than: int | None = None,
    ) -> int:
        value = payload.get(key)
        if not isinstance(value, int) or not 0 <= value < len(room.players):
            raise GameRuleError("请选择合法目标")
        if other_than is not None and value == other_than:
            raise GameRuleError("不能选择自己作为目标")
        if not state.boards[value].alive:
            raise GameRuleError("目标已经出局")
        return value

    def _eliminated_target(
        self,
        room: ArcadeRoom,
        state: DepartedSuspicionState,
        payload: dict[str, Any],
        *,
        other_than: int,
    ) -> int:
        value = payload.get("targetSeat")
        if not isinstance(value, int) or not 0 <= value < len(room.players) or value == other_than:
            raise GameRuleError("请选择另一名已出局玩家")
        board = state.boards[value]
        if board.alive:
            raise GameRuleError("目标尚未出局")
        if self._leader_card(board) is not None:
            raise GameRuleError("不能复活探员或头目")
        return value

    def _armed_target(
        self,
        room: ArcadeRoom,
        state: DepartedSuspicionState,
        payload: dict[str, Any],
    ) -> int:
        target = self._target_seat(room, state, payload)
        if not state.boards[target].gun:
            raise GameRuleError("目标没有持枪")
        return target

    def _two_targets(
        self,
        room: ArcadeRoom,
        state: DepartedSuspicionState,
        payload: dict[str, Any],
        *,
        excluded: set[int] | None = None,
    ) -> tuple[int, int]:
        first = self._target_seat(room, state, payload, key="firstSeat")
        second = self._target_seat(room, state, payload, key="secondSeat")
        if first == second:
            raise GameRuleError("请选择两名不同玩家")
        if excluded and (first in excluded or second in excluded):
            raise GameRuleError("这张装备不能选择使用者自己")
        return first, second

    def _two_card_locations(
        self,
        room: ArcadeRoom,
        state: DepartedSuspicionState,
        payload: dict[str, Any],
    ) -> tuple[tuple[int, int], tuple[int, int]]:
        first, second = self._two_targets_allow_same_player(room, state, payload)
        return (
            (first, self._card_index(payload.get("firstCardIndex"))),
            (second, self._card_index(payload.get("secondCardIndex"))),
        )

    def _two_targets_allow_same_player(
        self,
        room: ArcadeRoom,
        state: DepartedSuspicionState,
        payload: dict[str, Any],
    ) -> tuple[int, int]:
        first = self._target_seat(room, state, payload, key="firstSeat")
        second = self._target_seat(room, state, payload, key="secondSeat")
        return first, second

    @staticmethod
    def _card_index(value: Any) -> int:
        if not isinstance(value, int) or not 0 <= value < 3:
            raise GameRuleError("请选择一张底细牌")
        return value

    def _hidden_card(self, board: PlayerBoard, value: Any) -> IntegrityCard:
        card = board.cards[self._card_index(value)]
        if card.revealed:
            raise GameRuleError("请选择一张暗置底细")
        return card

    def _choice_index(
        self, choices: Any, seat: int, board: PlayerBoard
    ) -> int | None:
        hidden = [index for index, card in enumerate(board.cards) if not card.revealed]
        if not hidden:
            return None
        if isinstance(choices, dict):
            value = choices.get(str(seat), choices.get(seat))
            if isinstance(value, int) and value in hidden:
                return value
        return hidden[0]

    def _pending_shoot(self, state: DepartedSuspicionState) -> PendingAction:
        pending = state.pending_action
        if pending is None or pending.action != "shoot":
            raise GameRuleError("当前没有等待结算的射击")
        return pending

    def _next_alive(self, state: DepartedSuspicionState, seat: int) -> int:
        count = len(state.boards)
        for offset in range(1, count + 1):
            candidate = (seat + state.direction * offset) % count
            if state.boards[candidate].alive:
                return candidate
        return seat

    def _seat_order(self, state: DepartedSuspicionState, after: int) -> list[int]:
        result: list[int] = []
        cursor = after
        for _ in range(len(state.boards)):
            cursor = self._next_alive(state, cursor)
            if cursor in result:
                break
            result.append(cursor)
        return result

    def _normal_action_ids(
        self,
        state: DepartedSuspicionState,
        seat: int,
    ) -> list[str]:
        board = state.boards[seat]
        if board.restricted_to_equip:
            return ["equip"]
        actions: list[str] = []
        if self._has_investigation_target(state, seat):
            actions.append("investigate")
        actions.append("equip")
        if (
            not board.gun
            and self._central_guns(state) > 0
            and any(
                target != seat and target_board.alive
                for target, target_board in state.boards.items()
            )
        ):
            actions.append("arm")
        if (
            board.gun
            and board.aim_seat is not None
            and state.boards[board.aim_seat].alive
            and state.acquired_gun_turn.get(seat) != state.turn_number
        ):
            actions.append("shoot")
        return actions

    @staticmethod
    def _has_investigation_target(
        state: DepartedSuspicionState,
        seat: int,
    ) -> bool:
        return any(
            target != seat
            and target_board.alive
            and "disguise" not in target_board.effects
            and any(not card.revealed for card in target_board.cards)
            for target, target_board in state.boards.items()
        )

    @staticmethod
    def _central_guns(state: DepartedSuspicionState) -> int:
        return state.gun_total - sum(board.gun for board in state.boards.values())

    @staticmethod
    def _learn_all_hidden(
        state: DepartedSuspicionState,
        viewer_seat: int,
        target_seat: int,
        *,
        include_revealed: bool = False,
    ) -> None:
        state.knowledge[viewer_seat].update(
            card.id
            for card in state.boards[target_seat].cards
            if include_revealed or not card.revealed
        )

    @staticmethod
    def _log(
        state: DepartedSuspicionState,
        event: str,
        text: str,
        **extra: Any,
    ) -> None:
        state.history.append({"event": event, "text": text, **extra})
        state.history = state.history[-80:]

    @staticmethod
    def _lobby_view() -> dict[str, Any]:
        return {
            "turnPlayerId": None,
            "turnNumber": 0,
            "direction": "clockwise",
            "centralGuns": 0,
            "actionDone": False,
            "extraInvestigationDone": False,
            "players": [],
            "selfTeam": None,
            "equipmentHand": [],
            "equipmentCatalog": [
                card.as_dict(available=not card.requires_cover)
                for card in EQUIPMENT_CARDS
            ],
            "pendingAction": None,
            "pendingShot": None,
            "choice": None,
            "postShot": None,
            "waiting": None,
            "legal": {
                "canTakeNormalAction": False,
                "normalActionIds": [],
                "canTakeExtraInvestigation": False,
                "canEndTurn": False,
                "canRespond": False,
                "responseEquipmentIds": [],
                "playableEquipmentIds": [],
            },
            "history": [],
            "rulesNotice": "卧底牌能力尚未启用；新任务保留在33张资料库中但不会进入牌堆。",
        }

    @staticmethod
    def _waiting_view(
        room: ArcadeRoom,
        state: DepartedSuspicionState,
        response_seat: int | None,
    ) -> dict[str, str] | None:
        if state.choice is not None:
            seat = int(state.choice["seat"])
            return {
                "kind": str(state.choice["kind"]),
                "playerId": room.players[seat].id,
            }
        if state.pending_shot is not None and state.pending_shot.scanner_seat is not None:
            seat = state.pending_shot.scanner_seat
            return {"kind": "thumbprint_scanner", "playerId": room.players[seat].id}
        if state.post_shot is not None:
            seat = int(state.post_shot["seat"])
            return {"kind": "mobile_detonator", "playerId": room.players[seat].id}
        if response_seat is not None:
            return {"kind": "equipment_response", "playerId": room.players[response_seat].id}
        return None
