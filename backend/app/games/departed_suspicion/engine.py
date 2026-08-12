from __future__ import annotations

import copy
import random
from dataclasses import dataclass, field
from typing import Any

from backend.app.arcade.models import ArcadePlayer, ArcadeRoom
from backend.app.games.base import GameRuleError

from .cards import (
    BASE_EQUIPMENT_IDS,
    BOMBERS_EQUIPMENT_IDS,
    EQUIPMENT_BY_ID,
    EQUIPMENT_CARDS,
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
NORMAL_ACTIONS = ("investigate", "equip", "arm", "shoot")
EQUIPMENT_SETS = {"base", "bombers"}
RULES_NOTICE = (
    "当前实战牌堆只启用基础版和爆破者扩展；"
    "卧底扩展及其掩护、卧底牌系统尚未启用。"
)
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
    grenade_received_turn: int | None = None


@dataclass
class PendingAction:
    actor_seat: int
    action: str
    payload: dict[str, Any]
    response_order: list[int] = field(default_factory=list)
    response_index: int = 0
    completion_required: bool = False


@dataclass
class PendingShot:
    shooter_seat: int | None
    target_seat: int
    source: str
    advance_after: bool = False
    scanner_seat: int | None = None
    scanner_activated: bool = False


@dataclass
class PostShotResolution:
    kind: str
    seat: int
    draw_after: bool = False
    eliminated: bool = False
    advance_after: bool = False


@dataclass
class PendingChoice:
    kind: str
    seat: int
    queue: list[int] = field(default_factory=list)
    shooter_seat: int | None = None
    advance_after: bool = False
    resume_pending_after_seat: int | None = None
    source_card_id: str | None = None
    source_seat: int | None = None


@dataclass(frozen=True)
class EquipmentDraw:
    sequence: int
    turn_number: int
    seat: int
    card_id: str
    source: str


@dataclass(frozen=True)
class EquipmentPlay:
    sequence: int
    turn_number: int
    seat: int
    card_id: str
    target_seats: tuple[int, ...]


@dataclass
class ExtraTurnSchedule:
    pending_seats: list[int] = field(default_factory=list)
    resume_after_seat: int | None = None


@dataclass
class DepartedSuspicionState:
    boards: dict[int, PlayerBoard] = field(default_factory=dict)
    turn_seat: int = 0
    direction: int = 1
    action_done: bool = False
    extra_investigation_done: bool = False
    equipment_deck: list[str] = field(default_factory=list)
    initial_equipment_order: list[str] = field(default_factory=list)
    equipment_draw_history: list[EquipmentDraw] = field(default_factory=list)
    equipment_play_history: list[EquipmentPlay] = field(default_factory=list)
    equipment_audit_complete: bool = True
    gun_total: int = 0
    turn_number: int = 1
    acquired_gun_turn: dict[int, int] = field(default_factory=dict)
    pending_action: PendingAction | None = None
    pending_shot: PendingShot | None = None
    choice: PendingChoice | None = None
    post_shot: PostShotResolution | None = None
    extra_turns: ExtraTurnSchedule = field(default_factory=ExtraTurnSchedule)
    knowledge: dict[int, set[str]] = field(default_factory=dict)
    last_investigation: dict[str, int] | None = None
    history: list[dict[str, Any]] = field(default_factory=list)


class DepartedSuspicionEngine:
    key = "departed_suspicion"
    name = "无间疑云"
    min_players = 4
    max_players = 8

    def __init__(self, rng: random.Random | None = None) -> None:
        self.rng = rng if rng is not None else random.SystemRandom()

    def room_options(self, options: dict[str, Any]) -> dict[str, Any]:
        equipment_set = str(options.get("equipmentSet", "bombers"))
        if equipment_set == "expanded":
            equipment_set = "bombers"
        if equipment_set not in EQUIPMENT_SETS:
            raise GameRuleError("请选择基础16张或炸弹客/叛徒21张装备牌库")
        return {
            "equipmentSet": equipment_set,
            "firstPlayer": (
                "host" if options.get("firstPlayer") == "host" else "random"
            ),
            "allowGuests": bool(options.get("allowGuests", True)),
        }

    def initial_state(self) -> DepartedSuspicionState:
        return DepartedSuspicionState()

    def repair_restored_room(self, room: ArcadeRoom) -> None:
        state = room.state
        if not isinstance(state, DepartedSuspicionState):
            return
        if room.options.get("equipmentSet") == "expanded":
            room.options["equipmentSet"] = "bombers"
        if not hasattr(state, "initial_equipment_order"):
            state.initial_equipment_order = list(state.equipment_deck)
            state.equipment_audit_complete = False
        if not hasattr(state, "equipment_draw_history"):
            state.equipment_draw_history = []
            state.equipment_audit_complete = False
        if not hasattr(state, "equipment_play_history"):
            state.equipment_play_history = []
            state.equipment_audit_complete = False
        if not hasattr(state, "equipment_audit_complete"):
            state.equipment_audit_complete = False
        if not hasattr(state, "extra_turns"):
            state.extra_turns = ExtraTurnSchedule(
                pending_seats=list(getattr(state, "coffee_after", [])),
            )
        for board in state.boards.values():
            if "grenade_received_turn" not in vars(board):
                board.grenade_received_turn = None
            if "crutches" in board.effects:
                board.restricted_to_equip = True
        if isinstance(state.choice, dict):
            restored_choice = state.choice
            state.choice = PendingChoice(
                kind=str(restored_choice.get("kind", "")),
                seat=int(restored_choice.get("seat", 0)),
                queue=list(restored_choice.get("queue", [])),
                shooter_seat=restored_choice.get("shooterSeat"),
                advance_after=bool(restored_choice.get("advanceAfter", False)),
                resume_pending_after_seat=restored_choice.get(
                    "resumePendingAfterSeat"
                ),
            )
        elif state.choice is not None:
            if not hasattr(state.choice, "source_card_id"):
                state.choice.source_card_id = None
            if not hasattr(state.choice, "source_seat"):
                state.choice.source_seat = None
        if isinstance(state.post_shot, dict):
            restored_post_shot = state.post_shot
            state.post_shot = PostShotResolution(
                kind=str(restored_post_shot.get("kind", "")),
                seat=int(restored_post_shot.get("seat", 0)),
                draw_after=bool(restored_post_shot.get("drawAfter", False)),
                eliminated=bool(restored_post_shot.get("eliminated", False)),
                advance_after=bool(restored_post_shot.get("advanceAfter", False)),
            )
        if (
            state.pending_action is not None
            and "completion_required" not in vars(state.pending_action)
        ):
            state.pending_action.completion_required = bool(
                getattr(state.pending_action, "must_complete", False)
            )
        if (
            state.pending_action is not None
            and state.pending_action.action == "shoot"
            and not isinstance(state.pending_action.payload.get("targetSeat"), int)
        ):
            state.pending_action.payload["targetSeat"] = state.boards[
                state.pending_action.actor_seat
            ].aim_seat
        if (
            state.pending_shot is not None
            and "scanner_activated" not in vars(state.pending_shot)
        ):
            state.pending_shot.scanner_activated = False

    def start(self, room: ArcadeRoom) -> None:
        player_count = len(room.players)
        cards = self._deal_integrity(player_count)
        boards = {
            seat: PlayerBoard(cards=cards[seat]) for seat in range(player_count)
        }
        equipment_ids = list(
            BASE_EQUIPMENT_IDS
            if room.options.get("equipmentSet") == "base"
            else BOMBERS_EQUIPMENT_IDS
        )
        self.rng.shuffle(equipment_ids)
        room.state = DepartedSuspicionState(
            boards=boards,
            turn_seat=self._starting_seat(room),
            equipment_deck=equipment_ids,
            initial_equipment_order=list(equipment_ids),
            gun_total=self._gun_count(player_count),
            knowledge={seat: set() for seat in range(player_count)},
        )
        for seat in range(player_count):
            self._draw_equipment(
                room.state,
                seat,
                source="setup",
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
        if action in NORMAL_ACTIONS:
            if state.action_done:
                raise GameRuleError("本回合已经执行过正常行动")
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
        choice = state.choice if state.choice and state.choice.seat == viewer_seat else None
        post_shot_actor = (
            state.post_shot.seat if state.post_shot is not None else None
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
        normal_action_ids = (
            self._normal_action_ids(state, viewer_seat)
            if can_take_normal_action
            else []
        )
        equipment_options = (
            self._equipment_options_view(room, state, viewer_seat)
            if room.phase == "playing"
            else []
        )
        playable_equipment_ids = [
            option["cardId"] for option in equipment_options
        ]
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
                card.as_dict(
                    available=(
                        card.id
                        in (
                            BASE_EQUIPMENT_IDS
                            if room.options.get("equipmentSet") == "base"
                            else BOMBERS_EQUIPMENT_IDS
                        )
                    )
                )
                for card in EQUIPMENT_CARDS
            ],
            "pendingAction": (
                {
                    "actorPlayerId": self._player_id(room, pending.actor_seat),
                    "action": pending.action,
                    "actionLabel": ACTION_NAMES[pending.action],
                    "targetPlayerId": (
                        self._player_id(
                            room, self._pending_target_seat(state, pending)
                        )
                        if pending.action == "shoot"
                        else self._pending_target_id(room, pending)
                    ),
                    "targetCardIndex": self._pending_card_index(pending),
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
                    "scannerActivated": state.pending_shot.scanner_activated,
                }
                if state.pending_shot is not None
                else None
            ),
            "choice": self._choice_view(room, state, choice),
            "postShot": (
                {
                    "kind": state.post_shot.kind,
                    "isMyDecision": post_shot_actor == viewer_seat,
                    "targetPlayerIds": [
                        room.players[target].id
                        for target, target_board in state.boards.items()
                        if target != post_shot_actor and target_board.alive
                    ],
                }
                if state.post_shot is not None
                else None
            ),
            "waiting": self._waiting_view(room, state, response_seat),
            "currentPrompt": self._current_prompt_view(
                room,
                state,
                viewer_seat,
                response_seat,
            ),
            "legal": {
                "canTakeNormalAction": can_take_normal_action,
                "normalActionIds": normal_action_ids,
                "investigationTargetPlayerIds": [
                    room.players[target].id
                    for target in self._investigation_target_seats(
                        state,
                        viewer_seat,
                    )
                ],
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
                    playable_equipment_ids
                    if pending is not None and response_seat == viewer_seat
                    else []
                ),
                "playableEquipmentIds": playable_equipment_ids,
                "equipmentOptions": equipment_options,
            },
            "history": state.history[-30:],
            "rulesNotice": RULES_NOTICE,
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

    def record_state(self, room: ArcadeRoom) -> dict[str, Any]:
        state: DepartedSuspicionState = room.state
        return {
            "roundNumber": room.round_number,
            "turnNumber": state.turn_number,
            "initialEquipmentOrder": list(state.initial_equipment_order),
            "equipmentDrawHistory": [
                {
                    "sequence": draw.sequence,
                    "turnNumber": draw.turn_number,
                    "seat": draw.seat,
                    "cardId": draw.card_id,
                    "source": draw.source,
                }
                for draw in state.equipment_draw_history
            ],
            "equipmentPlayHistory": [
                {
                    "sequence": play.sequence,
                    "turnNumber": play.turn_number,
                    "seat": play.seat,
                    "cardId": play.card_id,
                    "targetSeats": list(play.target_seats),
                }
                for play in state.equipment_play_history
            ],
            "equipmentAuditComplete": state.equipment_audit_complete,
            "remainingEquipmentDeck": list(state.equipment_deck),
            "equipmentBySeat": {
                str(seat): list(board.equipment)
                for seat, board in state.boards.items()
            },
            "effectsBySeat": {
                str(seat): list(board.effects)
                for seat, board in state.boards.items()
            },
            "history": list(state.history),
        }

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

    def _starting_seat(self, room: ArcadeRoom) -> int:
        if room.options.get("firstPlayer") == "host":
            return next(
                player.seat
                for player in room.players
                if player.id == room.host_id
            )
        return self.rng.randrange(len(room.players))

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
        pending_payload = dict(payload)
        if action == "shoot":
            pending_payload["targetSeat"] = state.boards[seat].aim_seat
        pending = PendingAction(seat, action, pending_payload)
        state.pending_action = pending
        pending.response_order = self._response_order(room, state, pending)
        self._log(
            state,
            "action_declared",
            self._action_declaration_text(room, state, pending),
            playerId=room.players[seat].id,
            targetPlayerId=self._player_id(
                room,
                self._pending_target_seat(state, pending),
            ),
            targetCardIndex=self._pending_card_index(pending),
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
        if action in NORMAL_ACTIONS:
            self._require_normal_action_available(state, seat, action)
        if action in {"investigate", "extra_investigate"}:
            target = self._target_seat(room, state, payload, other_than=seat)
            target_board = state.boards[target]
            if "disguise" in target_board.effects:
                raise GameRuleError("伪装使这名玩家不能被调查")
            self._hidden_card(target_board, payload.get("cardIndex"))
            return
        if action == "equip":
            self._action_reveal_card(board, payload.get("cardIndex"))
            return
        if action == "arm":
            self._action_reveal_card(board, payload.get("cardIndex"))
            self._target_seat(room, state, payload, other_than=seat)
            return

    def _resolve_pending_action(
        self, room: ArcadeRoom, state: DepartedSuspicionState
    ) -> None:
        pending = state.pending_action
        if pending is None:
            return
        state.pending_action = None
        try:
            self._validate_pending_action(room, state, pending)
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
                (
                    f"{room.players[pending.actor_seat].name}调查了"
                    f"{room.players[target].name}的第{card_index + 1}张底细"
                ),
                playerId=room.players[pending.actor_seat].id,
                targetPlayerId=room.players[target].id,
                targetCardIndex=card_index,
            )
            return
        if action == "equip":
            reveal = self._action_reveal_card(
                actor,
                pending.payload.get("cardIndex"),
            )
            state.action_done = True
            self._draw_equipment(
                state,
                pending.actor_seat,
                source="normal_action",
            )
            if reveal is not None:
                reveal.revealed = True
            self._log(state, "equip", f"{room.players[pending.actor_seat].name}获取了装备")
            return
        if action == "arm":
            reveal = self._action_reveal_card(
                actor,
                pending.payload.get("cardIndex"),
            )
            actor.gun = True
            actor.aim_seat = int(pending.payload["targetSeat"])
            state.acquired_gun_turn[pending.actor_seat] = state.turn_number
            state.action_done = True
            if reveal is not None:
                reveal.revealed = True
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
                self._pending_target_seat(state, pending),
                source="gun",
            )

    def _validate_pending_action(
        self,
        room: ArcadeRoom,
        state: DepartedSuspicionState,
        pending: PendingAction,
    ) -> None:
        if pending.action == "shoot" and pending.completion_required:
            target = self._pending_target_seat(state, pending)
            if target is None or not state.boards[target].alive:
                raise GameRuleError("射击目标已经出局")
            return
        self._validate_action(
            room,
            state,
            pending.actor_seat,
            pending.action,
            pending.payload,
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
        if (
            pending.action == "shoot"
            and not pending.completion_required
            and not state.boards[pending.actor_seat].gun
        ):
            state.pending_action = None
            self._log(state, "shot_cancelled", "射手失去枪，射击取消并可重新选择行动")
            return
        pending.response_order = self._response_order(
            room,
            state,
            pending,
            after=after,
        )
        pending.response_index = 0
        if not pending.response_order:
            self._resolve_pending_action(room, state)

    def _prune_pending_responders(
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
            and self._response_equipment_ids(room, state, seat, pending)
        ]
        pending.response_index = 0
        if not pending.response_order:
            self._resolve_pending_action(room, state)

    def _response_order(
        self,
        room: ArcadeRoom,
        state: DepartedSuspicionState,
        pending: PendingAction,
        *,
        after: int | None = None,
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
            if self._response_equipment_ids(room, state, seat, pending)
        ]

    @staticmethod
    def _response_seat(pending: PendingAction | None) -> int | None:
        if pending is None or pending.response_index >= len(pending.response_order):
            return None
        return pending.response_order[pending.response_index]

    def _response_equipment_ids(
        self,
        room: ArcadeRoom,
        state: DepartedSuspicionState,
        seat: int,
        pending: PendingAction | None,
    ) -> list[str]:
        if pending is None:
            return []
        return [
            card_id
            for card_id in state.boards[seat].equipment
            if self._equipment_timing_allows(state, seat, card_id, pending)
            and self._equipment_form(room, state, seat, card_id) is not None
        ]

    def _playable_equipment_ids(
        self,
        room: ArcadeRoom,
        state: DepartedSuspicionState,
        seat: int,
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
            return self._response_equipment_ids(
                room,
                state,
                seat,
                state.pending_action,
            )
        return [
            card_id
            for card_id in board.equipment
            if self._equipment_timing_allows(state, seat, card_id, None)
            and self._equipment_form(room, state, seat, card_id) is not None
        ]

    def _equipment_options_view(
        self,
        room: ArcadeRoom,
        state: DepartedSuspicionState,
        seat: int,
    ) -> list[dict[str, Any]]:
        return [
            {
                "cardId": card_id,
                "fields": self._equipment_form(room, state, seat, card_id) or [],
            }
            for card_id in self._playable_equipment_ids(room, state, seat)
        ]

    @staticmethod
    def _equipment_timing_allows(
        state: DepartedSuspicionState,
        seat: int,
        card_id: str,
        pending: PendingAction | None,
    ) -> bool:
        timing = EQUIPMENT_BY_ID[card_id].timing
        if timing == "anytime":
            return True
        if timing == "own_turn":
            return seat == state.turn_seat
        if timing == "other_turn":
            return seat != state.turn_seat
        if timing == "after_investigate":
            return pending is None and state.last_investigation is not None
        if pending is None or pending.action != "shoot":
            return False
        if timing == "shoot_response":
            return True
        if timing == "own_shoot":
            return seat == pending.actor_seat
        if timing == "self_shot":
            return pending.payload.get("targetSeat") == seat
        return False

    def _equipment_form(
        self,
        room: ArcadeRoom,
        state: DepartedSuspicionState,
        seat: int,
        card_id: str,
    ) -> list[dict[str, Any]] | None:
        """Return the complete legal input contract, or None when unusable."""

        board = state.boards[seat]
        alive = [target for target, item in state.boards.items() if item.alive]

        def player_field(
            key: str,
            label: str,
            seats: list[int],
            **extra: Any,
        ) -> dict[str, Any]:
            return {
                "key": key,
                "label": label,
                "kind": "player",
                "required": True,
                "options": [
                    {"value": target, "label": room.players[target].name}
                    for target in seats
                ],
                **extra,
            }

        def card_options(
            target: int,
            indices: list[int],
            *,
            show_identity: bool = False,
        ) -> list[dict[str, Any]]:
            result: list[dict[str, Any]] = []
            for index in indices:
                card = state.boards[target].cards[index]
                label = f"第{index + 1}张"
                if show_identity:
                    label += f" · {INTEGRITY_NAMES[card.kind]}"
                result.append({"value": index, "label": label})
            return result

        def dependent_card_field(
            key: str,
            label: str,
            depends_on: str,
            seats: list[int],
            indices_by_seat: dict[int, list[int]],
            *,
            show_identity: bool = False,
            **extra: Any,
        ) -> dict[str, Any]:
            return {
                "key": key,
                "label": label,
                "kind": "card",
                "required": True,
                "dependsOn": depends_on,
                "optionsByValue": {
                    str(target): card_options(
                        target,
                        indices_by_seat[target],
                        show_identity=show_identity,
                    )
                    for target in seats
                },
                **extra,
            }

        hidden_by_seat = {
            target: [
                index
                for index, card in enumerate(target_board.cards)
                if not card.revealed
            ]
            for target, target_board in state.boards.items()
        }
        all_indices = {target: list(range(3)) for target in state.boards}

        def equipment_after_play(target: int) -> list[str]:
            equipment = list(state.boards[target].equipment)
            if target == seat and card_id in equipment:
                equipment.remove(card_id)
            return equipment

        if card_id == "blackmail":
            targets = [target for target in alive if target != seat]
            if len(targets) < 2:
                return None
            return [
                player_field("firstSeat", "第一名玩家", targets),
                dependent_card_field(
                    "firstCardIndex",
                    "第一张底细",
                    "firstSeat",
                    targets,
                    all_indices,
                ),
                player_field(
                    "secondSeat",
                    "第二名玩家",
                    targets,
                    distinctFrom="firstSeat",
                ),
                dependent_card_field(
                    "secondCardIndex",
                    "第二张底细",
                    "secondSeat",
                    targets,
                    all_indices,
                ),
            ]
        if card_id == "coffee":
            return [] if seat != state.turn_seat else None
        if card_id in {"defibrillator", "crutches"}:
            targets = [
                target
                for target, target_board in state.boards.items()
                if target != seat
                and not target_board.alive
                and self._leader_card(target_board) is None
            ]
            return [player_field("targetSeat", "复活目标", targets)] if targets else None
        if card_id == "evidence_bag":
            owners = [
                target
                for target in alive
                if equipment_after_play(target)
            ]
            recipients = [target for target in alive if target != seat]
            if not any(
                owner != recipient
                for owner in owners
                for recipient in recipients
            ):
                return None
            return [
                player_field("ownerSeat", "装备持有者", owners),
                player_field(
                    "recipientSeat",
                    "装备接收者",
                    recipients,
                    distinctFrom="ownerSeat",
                ),
            ]
        if card_id == "flashbang":
            return [player_field("targetSeat", "目标玩家", alive)]
        if card_id == "k9_unit":
            targets = [target for target in alive if state.boards[target].gun]
            return [player_field("targetSeat", "持枪玩家", targets)] if targets else None
        if card_id == "metal_detector":
            targets = self._metal_detector_target_seats(state)
            if not targets:
                return None
            return [
                {
                    "key": f"choices.{target}",
                    "label": f"{room.players[target].name}的暗置底细",
                    "kind": "card",
                    "required": True,
                    "options": card_options(target, hidden_by_seat[target]),
                }
                for target in targets
            ]
        if card_id in {"planted_evidence", "disguise"}:
            targets = alive
            if card_id == "disguise":
                targets = [
                    target
                    for target in targets
                    if "disguise" not in state.boards[target].effects
                ]
            return [player_field("targetSeat", "目标玩家", targets)] if targets else None
        if card_id == "polygraph":
            targets = [target for target in alive if target != seat]
            return [player_field("targetSeat", "目标玩家", targets)] if targets else None
        if card_id == "report_audit":
            return [] if any(hidden_by_seat[target] for target in alive) else None
        if card_id == "restraining_order":
            pending = state.pending_action
            if pending is None or pending.action != "shoot":
                return None
            targets = self._redirect_target_seats(state, pending.actor_seat)
            return [player_field("targetSeat", "新的射击目标", targets)] if targets else None
        if card_id == "smoke_grenade":
            return []
        if card_id == "surveillance_camera":
            return [] if state.last_investigation is not None else None
        if card_id == "taser":
            armed = [target for target in alive if target != seat and state.boards[target].gun]
            aims = [target for target in alive if target != seat]
            if board.gun or not armed or not aims:
                return None
            return [
                player_field("targetSeat", "夺枪目标", armed),
                player_field("aimSeat", "新的瞄准目标", aims),
            ]
        if card_id == "truth_serum":
            targets = [target for target in alive if hidden_by_seat[target]]
            return [player_field("targetSeat", "目标玩家", targets)] if targets else None
        if card_id == "wiretap":
            targets = [
                target
                for target in alive
                if hidden_by_seat[target]
            ]
            if len(targets) < 2:
                return None
            return [
                player_field("firstSeat", "第一名玩家", targets),
                dependent_card_field(
                    "firstCardIndex",
                    "第一张暗置底细",
                    "firstSeat",
                    targets,
                    hidden_by_seat,
                ),
                player_field(
                    "secondSeat",
                    "第二名玩家",
                    targets,
                    distinctFrom="firstSeat",
                ),
                dependent_card_field(
                    "secondCardIndex",
                    "第二张暗置底细",
                    "secondSeat",
                    targets,
                    hidden_by_seat,
                ),
            ]
        if card_id == "classified_orders":
            pending = state.pending_action
            if pending is None or pending.action != "shoot":
                return None
            if not self._redirect_target_seats(state, pending.actor_seat):
                return None
            targets = [target for target in alive if target != seat]
            return [player_field("deciderSeat", "决定新目标的玩家", targets)] if targets else None
        if card_id == "fake_id":
            indices_by_seat = {
                target: [
                    index
                    for index, card in enumerate(state.boards[target].cards)
                    if card.revealed and card.kind in {"honest", "crooked"}
                ]
                for target in alive
            }
            targets = [target for target in alive if indices_by_seat[target]]
            if len(targets) < 2:
                return None
            return [
                player_field("firstSeat", "第一名玩家", targets),
                dependent_card_field(
                    "firstCardIndex",
                    "第一张公开底细",
                    "firstSeat",
                    targets,
                    indices_by_seat,
                    show_identity=True,
                ),
                player_field(
                    "secondSeat",
                    "第二名玩家",
                    targets,
                    distinctFrom="firstSeat",
                ),
                dependent_card_field(
                    "secondCardIndex",
                    "第二张公开底细",
                    "secondSeat",
                    targets,
                    indices_by_seat,
                    show_identity=True,
                ),
            ]
        if card_id in {"fingerprint_kit", "security_wand"}:
            targets = [
                target
                for target in alive
                if (card_id == "fingerprint_kit" or target != seat)
                and "disguise" not in state.boards[target].effects
                and hidden_by_seat[target]
            ]
            if not targets:
                return None
            fields = [
                player_field("targetSeat", "调查目标", targets),
                dependent_card_field(
                    "cardIndex",
                    "目标暗置底细",
                    "targetSeat",
                    targets,
                    hidden_by_seat,
                ),
            ]
            if card_id == "fingerprint_kit" and hidden_by_seat[seat]:
                fields.extend(
                    [
                        {
                            "key": "returnToHand",
                            "label": "公开自己一张暗牌，让指纹工具回到手中",
                            "kind": "boolean",
                            "required": False,
                            "default": False,
                        },
                        {
                            "key": "ownCardIndex",
                            "label": "公开自己的底细",
                            "kind": "card",
                            "required": True,
                            "options": card_options(
                                seat,
                                hidden_by_seat[seat],
                                show_identity=True,
                            ),
                            "visibleWhen": {
                                "field": "returnToHand",
                                "equals": True,
                            },
                        },
                    ]
                )
            elif card_id == "security_wand":
                public = [
                    index
                    for index, card in enumerate(board.cards)
                    if card.revealed
                ]
                if public:
                    fields.append(
                        {
                            "key": "ownCardIndex",
                            "label": "可选：重新暗置自己的公开底细",
                            "kind": "card",
                            "required": False,
                            "options": card_options(
                                seat,
                                public,
                                show_identity=True,
                            ),
                        }
                    )
            return fields
        if card_id == "grenade":
            targets = [
                target
                for target in alive
                if target != seat and not state.boards[target].grenade_stage
            ]
            return [player_field("targetSeat", "第一位接收者", targets)] if targets else None
        if card_id == "holster":
            pending = state.pending_action
            if pending is None or pending.action != "shoot" or pending.actor_seat != seat:
                return None
            targets = self._redirect_target_seats(state, seat)
            return [player_field("targetSeat", "新的射击目标", targets)] if targets else None
        if card_id == "concussion_grenade":
            return [] if any(item.gun for item in state.boards.values()) else None
        if card_id == "helmet":
            pending = state.pending_action
            if (
                pending is not None
                and pending.action == "shoot"
                and self._pending_target_seat(state, pending) == seat
            ):
                return []
            return None
        if card_id == "inspection_gloves":
            targets = [
                target
                for target in alive
                if equipment_after_play(target) or hidden_by_seat[target]
            ]
            return [player_field("targetSeat", "搜查目标", targets)] if targets else None
        if card_id == "key":
            targets = [
                target
                for target in alive
                if target != seat and "key" not in state.boards[target].effects
            ]
            return [player_field("targetSeat", "获得钥匙的玩家", targets)] if targets else None
        if card_id == "med_kit":
            targets = [
                target
                for target in alive
                if (leader := self._leader_card(state.boards[target])) is not None
                and leader.wounded
            ]
            return [player_field("targetSeat", "受伤领袖", targets)] if targets else None
        if card_id == "sunglasses":
            indices_by_seat = {
                target: [
                    index
                    for index, card in enumerate(state.boards[target].cards)
                    if card.revealed
                ]
                for target in alive
            }
            targets = [target for target in alive if indices_by_seat[target]]
            if sum(len(indices_by_seat[target]) for target in targets) < 2:
                return None
            return [
                player_field("firstSeat", "第一张底细的玩家", targets),
                dependent_card_field(
                    "firstCardIndex",
                    "第一张公开底细",
                    "firstSeat",
                    targets,
                    indices_by_seat,
                    show_identity=True,
                ),
                player_field("secondSeat", "第二张底细的玩家", targets),
                dependent_card_field(
                    "secondCardIndex",
                    "第二张公开底细",
                    "secondSeat",
                    targets,
                    indices_by_seat,
                    show_identity=True,
                    distinctLocationFrom={
                        "seatField": "firstSeat",
                        "cardField": "firstCardIndex",
                        "ownSeatField": "secondSeat",
                    },
                ),
            ]
        return None

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
        if card_id == "new_assignment":
            raise GameRuleError("卧底牌能力尚未启用，新任务暂时不能使用")
        if card_id not in self._playable_equipment_ids(room, state, seat):
            raise GameRuleError("当前不是这张装备的使用时机")

        original_state = copy.deepcopy(state)
        board.equipment.remove(card_id)
        keep_card = card_id == "fingerprint_kit" and bool(payload.get("returnToHand"))
        try:
            if card_id != "surveillance_camera":
                state.last_investigation = None
            self._resolve_equipment(room, state, seat, card_id, payload)
            if state.choice is not None and state.choice.source_card_id is None:
                state.choice.source_card_id = card_id
                state.choice.source_seat = seat
        except Exception:
            room.state = original_state
            raise
        definition = EQUIPMENT_BY_ID[card_id]
        if keep_card:
            board.equipment.append(card_id)
        elif not definition.persistent:
            state.equipment_deck.append(card_id)
        self._record_equipment_use(room, state, seat, card_id, payload)
        if room.phase == "finished":
            return

        pending = state.pending_action
        if pending is not None and state.choice is None:
            self._resume_pending_action(room, state, after=seat)
        elif pending is not None and state.choice is not None:
            state.choice.resume_pending_after_seat = seat

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
            self._queue_extra_turn(state, seat)
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
                state.choice = PendingChoice("equipment_limit", recipient)
            return
        if card_id == "flashbang":
            target = self._target_seat(room, state, payload)
            state.choice = PendingChoice("flashbang", target)
            return
        if card_id == "k9_unit":
            target = self._armed_target(room, state, payload)
            self._drop_gun(state, target)
            return
        if card_id == "metal_detector":
            targets = self._metal_detector_target_seats(state)
            if not targets:
                raise GameRuleError("当前没有可调查的持枪玩家")
            choices = payload.get("choices", {})
            selected_cards: list[IntegrityCard] = []
            for target in targets:
                target_board = state.boards[target]
                index = self._metal_detector_choice_index(
                    choices,
                    target,
                    target_board,
                )
                selected_cards.append(target_board.cards[index])
            state.knowledge[seat].update(card.id for card in selected_cards)
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
            state.choice = PendingChoice("report_audit", seats[0], queue=seats)
            return
        if card_id == "restraining_order":
            pending = self._pending_shoot(state)
            target = self._target_seat(room, state, payload, other_than=pending.actor_seat)
            old_target = self._pending_target_seat(state, pending)
            if target == old_target:
                raise GameRuleError("限制令必须改瞄另一名目标")
            self._retarget_pending_shot(
                state,
                pending,
                target,
                require_completion=True,
            )
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
            state.choice = PendingChoice("truth_serum", target)
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
            if not self._redirect_target_seats(state, pending.actor_seat):
                raise GameRuleError("当前没有新的合法射击目标")
            decider = self._target_seat(room, state, payload, key="deciderSeat", other_than=seat)
            state.choice = PendingChoice(
                "classified_redirect",
                decider,
                shooter_seat=pending.actor_seat,
            )
            pending.completion_required = True
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
            target = self._target_seat(room, state, payload)
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
            target_board = state.boards[target]
            target_board.grenade_stage = 1
            target_board.grenade_received_turn = state.turn_number
            self._add_effect(target_board, card_id)
            return
        if card_id == "holster":
            pending = self._pending_shoot(state)
            if pending.actor_seat != seat:
                raise GameRuleError("枪套只能用于自己的射击")
            target = self._target_seat(room, state, payload, other_than=seat)
            if target not in self._redirect_target_seats(state, seat):
                raise GameRuleError("枪套必须选择新的射击目标")
            self._retarget_pending_shot(state, pending, target)
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
            if self._pending_target_seat(state, pending) != seat:
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
            state.choice = PendingChoice("inspection_gloves", target)
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
        grenade_is_due = (
            board.grenade_stage > 0
            and board.grenade_received_turn != state.turn_number
        )
        if grenade_is_due and board.grenade_stage == 1:
            state.choice = PendingChoice("grenade_pass", seat)
            return
        if grenade_is_due and board.grenade_stage == 2:
            board.grenade_stage = 0
            board.grenade_received_turn = None
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
        next_seat = self._next_turn_seat(state)
        state.turn_seat = next_seat
        state.turn_number += 1
        state.action_done = False
        state.extra_investigation_done = False
        state.last_investigation = None
        self._log(state, "turn", f"轮到{room.players[next_seat].name}")

    @staticmethod
    def _queue_extra_turn(state: DepartedSuspicionState, seat: int) -> None:
        if seat not in state.extra_turns.pending_seats:
            state.extra_turns.pending_seats.append(seat)

    def _next_turn_seat(self, state: DepartedSuspicionState) -> int:
        schedule = state.extra_turns
        while schedule.pending_seats:
            extra_seat = schedule.pending_seats.pop(0)
            if not state.boards[extra_seat].alive:
                continue
            if schedule.resume_after_seat is None:
                schedule.resume_after_seat = state.turn_seat
            return extra_seat

        if schedule.resume_after_seat is not None:
            resume_after = schedule.resume_after_seat
            schedule.resume_after_seat = None
            return self._next_alive(state, resume_after)

        return self._next_alive(state, state.turn_seat)

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
        response_start = shooter_seat if shooter_seat is not None else target_seat
        scanner_seat = next(
            (
                seat
                for seat in self._seat_order(state, response_start)
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
        if scanner_seat is None:
            self._reveal_and_apply_shot(room, state)

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
        board = state.boards[seat]
        if not shot.scanner_activated:
            if action == "pass_scanner":
                shot.scanner_seat = None
                self._reveal_and_apply_shot(room, state)
                return
            if action != "use_scanner":
                raise GameRuleError("请使用或放弃指纹扫描器")
            self._activate_scanner(room, state, shot, seat, board)
            return

        if action != "resolve_scanner":
            raise GameRuleError("请交换底细或直接继续结算中枪")
        self._resolve_scanner(room, state, shot, board, payload)

    def _activate_scanner(
        self,
        room: ArcadeRoom,
        state: DepartedSuspicionState,
        shot: PendingShot,
        seat: int,
        board: PlayerBoard,
    ) -> None:
        if "thumbprint_scanner" not in board.equipment:
            raise GameRuleError("你没有指纹扫描器")
        board.equipment.remove("thumbprint_scanner")
        state.equipment_deck.append("thumbprint_scanner")
        self._learn_all_hidden(
            state,
            seat,
            shot.target_seat,
            include_revealed=True,
        )
        shot.scanner_activated = True
        self._record_equipment_use(
            room,
            state,
            seat,
            "thumbprint_scanner",
            {"targetSeat": shot.target_seat},
        )

    def _resolve_scanner(
        self,
        room: ArcadeRoom,
        state: DepartedSuspicionState,
        shot: PendingShot,
        board: PlayerBoard,
        payload: dict[str, Any],
    ) -> None:
        own_value = payload.get("ownCardIndex")
        target_value = payload.get("targetCardIndex")
        wants_exchange = own_value is not None or target_value is not None
        if wants_exchange:
            if own_value is None or target_value is None:
                raise GameRuleError("交换时必须各选择一张底细")
            own_index = self._card_index(own_value)
            target_index = self._card_index(target_value)
            target = state.boards[shot.target_seat]
            target_card = target.cards[target_index]
            if target_card.kind not in {"honest", "crooked"}:
                raise GameRuleError("不能拿走目标的领袖牌")
            board.cards[own_index], target.cards[target_index] = (
                target_card,
                board.cards[own_index],
            )
            self._check_victory(room, state)
            if room.phase == "finished":
                state.pending_shot = None
                return
        shot.scanner_seat = None
        self._reveal_and_apply_shot(room, state)

    def _reveal_and_apply_shot(
        self,
        room: ArcadeRoom,
        state: DepartedSuspicionState,
    ) -> None:
        shot = state.pending_shot
        if shot is None:
            return
        target = state.boards[shot.target_seat]
        for card in target.cards:
            card.revealed = True
        self._log(
            state,
            "shot_reveal",
            f"{room.players[shot.target_seat].name}中枪并公开全部底细",
        )
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
                if had_mobile:
                    self._discard_all_equipment(state, target)
                return
        if had_mobile:
            state.post_shot = PostShotResolution(
                kind="mobile_detonator",
                seat=target_seat,
                draw_after=draw_after,
                eliminated=eliminated,
                advance_after=advance_after,
            )
            return
        if draw_after:
            self._draw_equipment(
                state,
                target_seat,
                source="leader_wound",
                advance_after=advance_after,
            )
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
        if post is None or post.seat != seat:
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
            self._record_equipment_use(
                room,
                state,
                seat,
                "mobile_detonator",
                payload,
            )
        draw_after = post.draw_after
        eliminated = post.eliminated
        advance_after = post.advance_after
        state.post_shot = None
        if eliminated:
            self._discard_all_equipment(state, board)
        if draw_after:
            self._draw_equipment(
                state,
                seat,
                source="leader_wound",
                advance_after=advance_after and not use,
            )
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

    def _finish_choice(
        self,
        room: ArcadeRoom,
        state: DepartedSuspicionState,
        choice: PendingChoice,
    ) -> None:
        state.choice = None
        if choice.resume_pending_after_seat is not None:
            self._resume_pending_action(
                room,
                state,
                after=choice.resume_pending_after_seat,
            )
        elif choice.advance_after:
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
        if choice is None or choice.seat != seat:
            raise GameRuleError("正在等待其他玩家作出选择")
        kind = choice.kind
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
            self._log(
                state,
                "choice_resolved",
                f"{room.players[seat].name}选择保留{EQUIPMENT_BY_ID[keep].name}",
                playerId=room.players[seat].id,
                choiceKind=kind,
                cardId=keep,
            )
            self._finish_choice(room, state, choice)
            return
        if kind == "report_audit":
            if action != "choose_reveal":
                raise GameRuleError("请选择一张暗置底细公开")
            card_index = self._card_index(payload.get("cardIndex"))
            self._hidden_card(board, card_index).revealed = True
            self._log(
                state,
                "reveal",
                f"{room.players[seat].name}公开了自己的第{card_index + 1}张底细",
                playerId=room.players[seat].id,
                cardIndex=card_index,
                choiceKind=kind,
            )
            queue = [item for item in choice.queue if item != seat]
            if queue:
                choice.queue = queue
                choice.seat = queue[0]
            else:
                self._finish_choice(room, state, choice)
            return
        if kind == "truth_serum":
            if action != "choose_reveal":
                raise GameRuleError("请选择一张暗置底细公开")
            card_index = self._card_index(payload.get("cardIndex"))
            self._hidden_card(board, card_index).revealed = True
            self._log(
                state,
                "reveal",
                f"{room.players[seat].name}公开了自己的第{card_index + 1}张底细",
                playerId=room.players[seat].id,
                cardIndex=card_index,
                choiceKind=kind,
            )
            self._finish_choice(room, state, choice)
            return
        if kind == "flashbang":
            if action != "reorder_integrity":
                raise GameRuleError("请重新排列三张底细")
            order = self._integrity_card_order(payload.get("cardOrder"))
            cards = list(board.cards)
            hidden_ids = {card.id for card in cards if not card.revealed}
            board.cards = [cards[index] for index in order]
            if len(hidden_ids) > 1:
                for known in state.knowledge.values():
                    known.difference_update(hidden_ids)
            self._log(
                state,
                "choice_resolved",
                f"{room.players[seat].name}重新排列了自己的三张底细",
                playerId=room.players[seat].id,
                choiceKind=kind,
            )
            self._finish_choice(room, state, choice)
            return
        if kind == "inspection_gloves":
            if action != "inspection_choice":
                raise GameRuleError("请选择搜查手套的处理方式")
            decision = str(payload.get("choice", ""))
            if decision == "discard_equipment" and board.equipment:
                card_id = board.equipment.pop(0)
                state.equipment_deck.append(card_id)
                result_text = f"{room.players[seat].name}弃掉了装备"
            elif decision == "show_integrity" and any(not card.revealed for card in board.cards):
                for viewer in state.knowledge.values():
                    viewer.update(card.id for card in board.cards if not card.revealed)
                result_text = f"{room.players[seat].name}向所有人展示了全部暗牌"
            else:
                raise GameRuleError("这个搜查选项当前不能执行")
            self._log(
                state,
                "choice_resolved",
                result_text,
                playerId=room.players[seat].id,
                choiceKind=kind,
                decision=decision,
            )
            self._finish_choice(room, state, choice)
            return
        if kind == "classified_redirect":
            if action != "choose_redirect":
                raise GameRuleError("请选择新的射击目标")
            if choice.shooter_seat is None:
                raise GameRuleError("机密指令缺少射手信息")
            shooter = choice.shooter_seat
            target = self._target_seat(room, state, payload, other_than=shooter)
            if target not in self._redirect_target_seats(state, shooter):
                raise GameRuleError("机密指令必须选择新的射击目标")
            pending = state.pending_action
            if pending is None or pending.actor_seat != shooter:
                raise GameRuleError("机密指令对应的射击已经取消")
            self._retarget_pending_shot(state, pending, target)
            self._log(
                state,
                "choice_resolved",
                (
                    f"{room.players[seat].name}替{room.players[shooter].name}"
                    f"选择射击{room.players[target].name}"
                ),
                playerId=room.players[seat].id,
                targetPlayerId=room.players[target].id,
                choiceKind=kind,
            )
            self._finish_choice(room, state, choice)
            return
        if kind == "grenade_pass":
            if action != "pass_grenade":
                raise GameRuleError("请把手榴弹传给另一名玩家")
            target = self._target_seat(room, state, payload, other_than=seat)
            if state.boards[target].grenade_stage:
                raise GameRuleError("目标已经持有手榴弹")
            board.grenade_stage = 0
            board.grenade_received_turn = None
            if "grenade" in board.effects:
                board.effects.remove("grenade")
            target_board = state.boards[target]
            target_board.grenade_stage = 2
            target_board.grenade_received_turn = state.turn_number
            self._add_effect(target_board, "grenade")
            self._log(
                state,
                "grenade_pass",
                f"{room.players[seat].name}把手榴弹传给了{room.players[target].name}",
                playerId=room.players[seat].id,
                targetPlayerId=room.players[target].id,
            )
            state.choice = None
            self._advance_turn(room, state)
            return
        raise GameRuleError("未知的待处理选择")

    def _draw_equipment(
        self,
        state: DepartedSuspicionState,
        seat: int,
        *,
        source: str,
        advance_after: bool = False,
    ) -> None:
        if not state.equipment_deck:
            return
        board = state.boards[seat]
        card_id = state.equipment_deck.pop(0)
        board.equipment.append(card_id)
        state.equipment_draw_history.append(
            EquipmentDraw(
                sequence=len(state.equipment_draw_history) + 1,
                turn_number=state.turn_number,
                seat=seat,
                card_id=card_id,
                source=source,
            )
        )
        if len(board.equipment) > 1:
            state.choice = PendingChoice(
                "equipment_limit",
                seat,
                advance_after=advance_after,
            )

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
        was_turn = seat == state.turn_seat
        turn_number = state.turn_number
        if board.alive:
            for card in board.cards:
                card.revealed = True
            self._eliminate(state, seat)
            self._log(state, "resign", f"{room.players[seat].name}认输并出局")
            self._check_victory(room, state)
            if room.phase == "finished":
                return
        self._repair_waits_after_departure(room, state, seat)
        if (
            room.phase != "finished"
            and was_turn
            and state.turn_number == turn_number
        ):
            if not self._defer_turn_advance_until_wait_finishes(state):
                self._advance_turn(room, state)

    def _repair_waits_after_departure(
        self,
        room: ArcadeRoom,
        state: DepartedSuspicionState,
        seat: int,
    ) -> None:
        if self._repair_pending_shot_after_departure(room, state, seat):
            return
        if self._repair_post_shot_after_departure(room, state, seat):
            return
        self._cancel_departed_actor_action(state, seat)
        self._repair_choice_after_departure(room, state, seat)
        self._prune_pending_responders(room, state)

    @staticmethod
    def _defer_turn_advance_until_wait_finishes(
        state: DepartedSuspicionState,
    ) -> bool:
        wait = state.pending_shot or state.post_shot or state.choice
        if wait is None:
            return False
        wait.advance_after = True
        return True

    def _repair_pending_shot_after_departure(
        self,
        room: ArcadeRoom,
        state: DepartedSuspicionState,
        seat: int,
    ) -> bool:
        shot = state.pending_shot
        if shot is None:
            return False
        if shot.target_seat == seat:
            state.pending_shot = None
            if shot.advance_after:
                self._advance_turn(room, state)
            return True
        if shot.scanner_seat == seat:
            shot.scanner_seat = None
            self._reveal_and_apply_shot(room, state)
            return True
        return False

    def _repair_post_shot_after_departure(
        self,
        room: ArcadeRoom,
        state: DepartedSuspicionState,
        seat: int,
    ) -> bool:
        post_shot = state.post_shot
        if post_shot is None or post_shot.seat != seat:
            return False
        self._handle_post_shot(
            room,
            state,
            seat,
            "pass_mobile_detonator",
            {},
        )
        return True

    def _cancel_departed_actor_action(
        self,
        state: DepartedSuspicionState,
        seat: int,
    ) -> bool:
        pending = state.pending_action
        if pending is None or pending.actor_seat != seat:
            return False
        state.pending_action = None
        self._log(state, "action_cancelled", "行动玩家已经出局，原行动取消")
        if state.choice is not None:
            state.choice.resume_pending_after_seat = None
            if state.choice.kind == "classified_redirect":
                state.choice = None
        return True

    def _repair_choice_after_departure(
        self,
        room: ArcadeRoom,
        state: DepartedSuspicionState,
        seat: int,
    ) -> None:
        choice = state.choice
        if choice is None:
            return
        if choice.kind == "report_audit":
            queue = [
                queued_seat
                for queued_seat in choice.queue
                if queued_seat != seat
                and state.boards[queued_seat].alive
                and any(not card.revealed for card in state.boards[queued_seat].cards)
            ]
            if not queue:
                self._finish_choice(room, state, choice)
            else:
                choice.queue = queue
                if choice.seat not in queue:
                    choice.seat = queue[0]
        elif choice.kind == "classified_redirect":
            shooter = choice.shooter_seat
            if (
                choice.seat == seat
                or shooter is None
                or not self._redirect_target_seats(state, shooter)
            ):
                self._finish_choice(room, state, choice)
        elif choice.seat == seat:
            self._finish_choice(room, state, choice)

    def _check_victory(
        self, room: ArcadeRoom, state: DepartedSuspicionState
    ) -> None:
        for seat, board in state.boards.items():
            kinds = {card.kind for card in board.cards}
            if {"agent", "kingpin"} <= kinds:
                self._finish_game(
                    room,
                    state,
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
            self._finish_game(
                room,
                state,
                "honest",
                winners,
                "头目出局，正直阵营获胜",
            )
        elif agent_board is not None and not state.boards[agent_board].alive:
            winners = [
                room.players[seat].id
                for seat, board in state.boards.items()
                if self._team(board) == "crooked"
            ]
            self._finish_game(
                room,
                state,
                "crooked",
                winners,
                "探员出局，腐败阵营获胜",
            )

    @staticmethod
    def _finish_game(
        room: ArcadeRoom,
        state: DepartedSuspicionState,
        winner: str,
        winner_player_ids: list[str],
        reason: str,
    ) -> None:
        room.finish(winner, winner_player_ids, reason)
        state.pending_action = None
        state.pending_shot = None
        state.choice = None
        state.post_shot = None

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
            board.grenade_received_turn = None
            if "grenade" in board.effects:
                board.effects.remove("grenade")
            state.equipment_deck.append("grenade")
        if not keep_equipment:
            self._discard_all_equipment(state, board)

    @staticmethod
    def _revive(state: DepartedSuspicionState, seat: int, *, restricted: bool) -> None:
        board = state.boards[seat]
        board.alive = True
        board.restricted_to_equip = restricted or "crutches" in board.effects

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
            if is_own:
                knowledge = "own"
            elif card.revealed or finished:
                knowledge = "public"
            elif remembered:
                knowledge = "known"
            else:
                knowledge = "hidden"
            cards.append(
                {
                    "index": index,
                    "knowledgeKey": card.id if remembered and not visible else None,
                    "kind": card.kind if visible or remembered else None,
                    "label": INTEGRITY_NAMES[card.kind] if visible or remembered else "未知",
                    "revealed": card.revealed,
                    "knowledge": knowledge,
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
        choice: PendingChoice | None,
    ) -> dict[str, Any] | None:
        if choice is None:
            return None
        kind = choice.kind
        result: dict[str, Any] = {"kind": kind, "isMyDecision": True}
        if kind == "equipment_limit":
            result["cards"] = [
                EQUIPMENT_BY_ID[card_id].as_dict()
                for card_id in state.boards[choice.seat].equipment
            ]
        if kind == "flashbang":
            result["integrityCards"] = [
                {
                    "index": index,
                    "kind": card.kind,
                    "label": INTEGRITY_NAMES[card.kind],
                    "revealed": card.revealed,
                }
                for index, card in enumerate(state.boards[choice.seat].cards)
            ]
        if kind == "classified_redirect":
            result["shooterPlayerId"] = self._player_id(room, choice.shooter_seat)
            result["targetPlayerIds"] = [
                room.players[target].id
                for target in (
                    self._redirect_target_seats(state, choice.shooter_seat)
                    if choice.shooter_seat is not None
                    else []
                )
            ]
        if kind == "grenade_pass":
            result["targetPlayerIds"] = [
                room.players[target].id
                for target, board in state.boards.items()
                if board.alive
                and target != choice.seat
                and not board.grenade_stage
            ]
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
    def _pending_target_seat(
        state: DepartedSuspicionState,
        pending: PendingAction,
    ) -> int | None:
        value = pending.payload.get("targetSeat")
        return value if isinstance(value, int) and value in state.boards else None

    @staticmethod
    def _retarget_pending_shot(
        state: DepartedSuspicionState,
        pending: PendingAction,
        target_seat: int,
        *,
        require_completion: bool = False,
    ) -> None:
        if pending.action != "shoot":
            raise GameRuleError("当前待结算行动不是射击")
        state.boards[pending.actor_seat].aim_seat = target_seat
        pending.payload["targetSeat"] = target_seat
        pending.completion_required = (
            pending.completion_required or require_completion
        )

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

    @staticmethod
    def _integrity_card_order(value: Any) -> list[int]:
        if (
            not isinstance(value, list)
            or len(value) != 3
            or any(type(index) is not int for index in value)
            or set(value) != {0, 1, 2}
        ):
            raise GameRuleError("请按新顺序各选择一次三张底细")
        return value

    def _hidden_card(self, board: PlayerBoard, value: Any) -> IntegrityCard:
        card = board.cards[self._card_index(value)]
        if card.revealed:
            raise GameRuleError("请选择一张暗置底细")
        return card

    def _action_reveal_card(
        self,
        board: PlayerBoard,
        value: Any,
    ) -> IntegrityCard | None:
        if any(not card.revealed for card in board.cards):
            return self._hidden_card(board, value)
        return None

    def _metal_detector_choice_index(
        self, choices: Any, seat: int, board: PlayerBoard
    ) -> int:
        hidden = [index for index, card in enumerate(board.cards) if not card.revealed]
        if not hidden:
            raise GameRuleError("持枪玩家没有可调查的暗置底细")
        if isinstance(choices, dict):
            value = choices.get(str(seat), choices.get(seat))
            if isinstance(value, int) and value in hidden:
                return value
        raise GameRuleError("请为每名持枪玩家选择一张暗置底细")

    @staticmethod
    def _metal_detector_target_seats(
        state: DepartedSuspicionState,
    ) -> list[int]:
        return [
            target
            for target, board in state.boards.items()
            if (
                board.alive
                and board.gun
                and "disguise" not in board.effects
                and any(not card.revealed for card in board.cards)
            )
        ]

    @staticmethod
    def _redirect_target_seats(
        state: DepartedSuspicionState,
        shooter_seat: int,
    ) -> list[int]:
        pending = state.pending_action
        current_target = (
            pending.payload.get("targetSeat")
            if pending is not None
            and pending.action == "shoot"
            and pending.actor_seat == shooter_seat
            else state.boards[shooter_seat].aim_seat
        )
        return [
            target
            for target, board in state.boards.items()
            if board.alive
            and target != shooter_seat
            and target != current_target
        ]

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
        return [
            action
            for action in NORMAL_ACTIONS
            if self._normal_action_error(state, seat, action) is None
        ]

    def _require_normal_action_available(
        self,
        state: DepartedSuspicionState,
        seat: int,
        action: str,
    ) -> None:
        error = self._normal_action_error(state, seat, action)
        if error is not None:
            raise GameRuleError(error)

    def _normal_action_error(
        self,
        state: DepartedSuspicionState,
        seat: int,
        action: str,
    ) -> str | None:
        board = state.boards[seat]
        if board.restricted_to_equip and action != "equip":
            return "拐杖限制你只能执行获取装备"
        if action == "investigate":
            return (
                None
                if self._has_investigation_target(state, seat)
                else "当前没有可调查的暗置底细"
            )
        if action == "equip":
            return None
        if action == "arm":
            if board.gun:
                return "你已经持有一把枪"
            if self._central_guns(state) <= 0:
                return "中央已经没有可拿的枪"
            if not any(
                target != seat and target_board.alive
                for target, target_board in state.boards.items()
            ):
                return "当前没有可瞄准的其他玩家"
            return None
        if action == "shoot":
            if not board.gun or board.aim_seat is None:
                return "你必须持枪并已经瞄准目标"
            if state.acquired_gun_turn.get(seat) == state.turn_number:
                return "本回合刚取得的枪不能立刻射击"
            if not state.boards[board.aim_seat].alive:
                return "当前瞄准目标已经出局"
            return None
        return "不支持这个无间疑云操作"

    def _has_investigation_target(
        self,
        state: DepartedSuspicionState,
        seat: int,
    ) -> bool:
        return bool(self._investigation_target_seats(state, seat))

    @staticmethod
    def _investigation_target_seats(
        state: DepartedSuspicionState,
        seat: int,
    ) -> list[int]:
        return [
            target
            for target, target_board in state.boards.items()
            if (
                target != seat
                and target_board.alive
                and "disguise" not in target_board.effects
                and any(not card.revealed for card in target_board.cards)
            )
        ]

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

    def _action_declaration_text(
        self,
        room: ArcadeRoom,
        state: DepartedSuspicionState,
        pending: PendingAction,
    ) -> str:
        actor_name = room.players[pending.actor_seat].name
        target_seat = self._pending_target_seat(state, pending)
        target_name = room.players[target_seat].name if target_seat is not None else None
        card_index = self._pending_card_index(pending)
        if pending.action in {"investigate", "extra_investigate"} and target_name:
            return (
                f"{actor_name}宣布{ACTION_NAMES[pending.action]}"
                f"{target_name}的第{card_index + 1 if card_index is not None else '?'}张底细"
            )
        if pending.action == "arm" and target_name:
            return f"{actor_name}宣布武装并瞄准{target_name}"
        if pending.action == "shoot" and target_name:
            return f"{actor_name}宣布射击{target_name}"
        return f"{actor_name}宣布{ACTION_NAMES[pending.action]}"

    def _equipment_history_text(
        self,
        room: ArcadeRoom,
        state: DepartedSuspicionState,
        seat: int,
        card_id: str,
        payload: dict[str, Any],
    ) -> str:
        actor_name = room.players[seat].name
        card_name = EQUIPMENT_BY_ID[card_id].name

        def player_name(key: str) -> str | None:
            value = payload.get(key)
            if isinstance(value, int) and 0 <= value < len(room.players):
                return room.players[value].name
            return None

        def numbered_card(key: str) -> str:
            value = payload.get(key)
            return f"第{value + 1}张" if isinstance(value, int) else "所选底细"

        if card_id == "coffee":
            return (
                f"{actor_name}使用了咖啡，将在{room.players[state.turn_seat].name}"
                "回合结束后获得额外回合"
            )
        if card_id == "evidence_bag":
            owner = player_name("ownerSeat") or "所选玩家"
            recipient = player_name("recipientSeat") or "另一名玩家"
            return f"{actor_name}使用了证物袋，把{owner}的装备交给{recipient}"
        if card_id == "taser":
            target = player_name("targetSeat") or "持枪玩家"
            aim = player_name("aimSeat") or "新目标"
            return f"{actor_name}对{target}使用了电击枪并瞄准{aim}"
        if card_id == "classified_orders":
            decider = player_name("deciderSeat") or "所选玩家"
            return f"{actor_name}使用了机密指令，指定{decider}决定新的射击目标"
        if card_id in {"blackmail", "fake_id", "wiretap", "sunglasses"}:
            first = player_name("firstSeat") or "第一名玩家"
            second = player_name("secondSeat") or "第二名玩家"
            return (
                f"{actor_name}使用了{card_name}：{first}{numbered_card('firstCardIndex')}、"
                f"{second}{numbered_card('secondCardIndex')}"
            )
        target = player_name("targetSeat")
        if target and card_id in {"fingerprint_kit", "security_wand"}:
            return (
                f"{actor_name}对{target}的{numbered_card('cardIndex')}"
                f"使用了{card_name}"
            )
        if target:
            return f"{actor_name}对{target}使用了{card_name}"
        return f"{actor_name}使用了{card_name}"

    def _record_equipment_use(
        self,
        room: ArcadeRoom,
        state: DepartedSuspicionState,
        seat: int,
        card_id: str,
        payload: dict[str, Any],
    ) -> None:
        state.equipment_play_history.append(
            EquipmentPlay(
                sequence=len(state.equipment_play_history) + 1,
                turn_number=state.turn_number,
                seat=seat,
                card_id=card_id,
                target_seats=self._equipment_target_seats(payload),
            )
        )
        self._log(
            state,
            "equipment",
            self._equipment_history_text(room, state, seat, card_id, payload),
            playerId=room.players[seat].id,
            cardId=card_id,
            targetPlayerIds=self._equipment_target_player_ids(room, payload),
        )

    @staticmethod
    def _equipment_target_seats(
        payload: dict[str, Any],
    ) -> tuple[int, ...]:
        result: list[int] = []
        for key in (
            "targetSeat",
            "ownerSeat",
            "recipientSeat",
            "firstSeat",
            "secondSeat",
            "aimSeat",
            "deciderSeat",
        ):
            value = payload.get(key)
            if isinstance(value, int) and value not in result:
                result.append(value)
        choices = payload.get("choices")
        if isinstance(choices, dict):
            for raw_seat in choices:
                try:
                    target = int(raw_seat)
                except (TypeError, ValueError):
                    continue
                if target not in result:
                    result.append(target)
        return tuple(result)

    @staticmethod
    def _equipment_target_player_ids(
        room: ArcadeRoom,
        payload: dict[str, Any],
    ) -> list[str]:
        result: list[str] = []
        for key in (
            "targetSeat",
            "ownerSeat",
            "recipientSeat",
            "firstSeat",
            "secondSeat",
            "aimSeat",
            "deciderSeat",
        ):
            value = payload.get(key)
            if not isinstance(value, int) or not 0 <= value < len(room.players):
                continue
            player_id = room.players[value].id
            if player_id not in result:
                result.append(player_id)
        return result

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
                card.as_dict(available=card.id in BOMBERS_EQUIPMENT_IDS)
                for card in EQUIPMENT_CARDS
            ],
            "pendingAction": None,
            "pendingShot": None,
            "choice": None,
            "postShot": None,
            "waiting": None,
            "currentPrompt": None,
            "legal": {
                "canTakeNormalAction": False,
                "normalActionIds": [],
                "investigationTargetPlayerIds": [],
                "canTakeExtraInvestigation": False,
                "canEndTurn": False,
                "canRespond": False,
                "responseEquipmentIds": [],
                "playableEquipmentIds": [],
                "equipmentOptions": [],
            },
            "history": [],
            "rulesNotice": RULES_NOTICE,
        }

    @staticmethod
    def _waiting_view(
        room: ArcadeRoom,
        state: DepartedSuspicionState,
        response_seat: int | None,
    ) -> dict[str, str] | None:
        if state.choice is not None:
            seat = state.choice.seat
            return {
                "kind": state.choice.kind,
                "playerId": room.players[seat].id,
            }
        if state.pending_shot is not None and state.pending_shot.scanner_seat is not None:
            seat = state.pending_shot.scanner_seat
            return {"kind": "thumbprint_scanner", "playerId": room.players[seat].id}
        if state.post_shot is not None:
            seat = state.post_shot.seat
            return {"kind": "mobile_detonator", "playerId": room.players[seat].id}
        if response_seat is not None:
            return {"kind": "equipment_response", "playerId": room.players[response_seat].id}
        return None

    @staticmethod
    def _pending_card_index(pending: PendingAction | None) -> int | None:
        if pending is None or pending.action not in {"investigate", "extra_investigate"}:
            return None
        value = pending.payload.get("cardIndex")
        return value if isinstance(value, int) and 0 <= value <= 2 else None

    def _current_prompt_view(
        self,
        room: ArcadeRoom,
        state: DepartedSuspicionState,
        viewer_seat: int,
        response_seat: int | None,
    ) -> dict[str, Any] | None:
        if state.pending_shot is not None and state.pending_shot.scanner_seat is not None:
            decision_seat = state.pending_shot.scanner_seat
            target_name = room.players[state.pending_shot.target_seat].name
            decision_name = room.players[decision_seat].name
            activated = state.pending_shot.scanner_activated
            return self._prompt(
                "thumbprint_scanner",
                f"{target_name}中枪，底细与伤害尚未结算",
                (
                    f"{decision_name}已使用指纹扫描器，正在私看并决定是否交换。"
                    if activated
                    else f"等待{decision_name}决定是否使用指纹扫描器。"
                ),
                room,
                viewer_seat,
                decision_seat,
                source_card_id="thumbprint_scanner",
            )

        if state.post_shot is not None:
            decision_seat = state.post_shot.seat
            decision_name = room.players[decision_seat].name
            return self._prompt(
                "mobile_detonator",
                f"{decision_name}正在处理中枪后的装备效果",
                f"等待{decision_name}决定是否使用移动引爆器连锁射击。",
                room,
                viewer_seat,
                decision_seat,
                source_card_id="mobile_detonator",
            )

        if state.choice is not None:
            return self._choice_prompt_view(room, state.choice, viewer_seat)

        pending = state.pending_action
        if pending is None:
            return None
        actor_name = room.players[pending.actor_seat].name
        target_seat = self._pending_target_seat(state, pending)
        target_name = room.players[target_seat].name if target_seat is not None else None
        card_index = self._pending_card_index(pending)
        if pending.action in {"investigate", "extra_investigate"} and target_name is not None:
            title = (
                f"{actor_name}宣布{ACTION_NAMES[pending.action]}"
                f"{target_name}的第{card_index + 1 if card_index is not None else '?'}张底细"
            )
        elif pending.action == "arm" and target_name is not None:
            title = f"{actor_name}宣布武装并瞄准{target_name}"
        elif pending.action == "shoot" and target_name is not None:
            title = f"{actor_name}宣布射击{target_name}"
        else:
            title = f"{actor_name}宣布{ACTION_NAMES[pending.action]}"
        detail = (
            f"等待{room.players[response_seat].name}决定是否使用装备。"
            if response_seat is not None
            else "装备响应完成后立即结算。"
        )
        return self._prompt(
            "equipment_response",
            title,
            detail,
            room,
            viewer_seat,
            response_seat,
            actor_seat=pending.actor_seat,
            target_seat=target_seat,
            card_index=card_index,
        )

    def _choice_prompt_view(
        self,
        room: ArcadeRoom,
        choice: PendingChoice,
        viewer_seat: int,
    ) -> dict[str, Any]:
        decision_name = room.players[choice.seat].name
        source_name = (
            room.players[choice.source_seat].name
            if choice.source_seat is not None
            else None
        )
        card_name = (
            EQUIPMENT_BY_ID[choice.source_card_id].name
            if choice.source_card_id in EQUIPMENT_BY_ID
            else None
        )
        title = f"轮到{decision_name}作出选择"
        detail = "完成选择后，对局会自动继续。"
        if choice.kind == "equipment_limit":
            if source_name and card_name:
                title = f"{source_name}使用了{card_name}"
            detail = f"{decision_name}持有多张装备，必须选择一张保留。"
        elif choice.kind == "report_audit":
            title = f"{source_name or '一名玩家'}使用了报告审查"
            detail = f"轮到{decision_name}选择自己的一张暗置底细永久公开。"
        elif choice.kind == "truth_serum":
            title = f"{source_name or '一名玩家'}对{decision_name}使用了吐真剂"
            detail = f"{decision_name}必须选择自己的一张暗置底细永久公开。"
        elif choice.kind == "flashbang":
            title = f"{source_name or '一名玩家'}对{decision_name}使用了闪光弹"
            detail = f"由{decision_name}决定自己三张底细的新顺序。"
        elif choice.kind == "inspection_gloves":
            title = f"{source_name or '一名玩家'}对{decision_name}使用了搜查手套"
            detail = f"{decision_name}必须弃掉装备，或向所有人展示全部暗牌。"
        elif choice.kind == "classified_redirect":
            shooter_name = (
                room.players[choice.shooter_seat].name
                if choice.shooter_seat is not None
                else "射手"
            )
            title = f"{source_name or '一名玩家'}使用了机密指令"
            detail = f"由{decision_name}替{shooter_name}选择新的射击目标。"
        elif choice.kind == "grenade_pass":
            title = f"{decision_name}必须传递手榴弹"
            detail = "请选择另一名未持有手榴弹的存活玩家。"
        return self._prompt(
            choice.kind,
            title,
            detail,
            room,
            viewer_seat,
            choice.seat,
            actor_seat=choice.source_seat,
            source_card_id=choice.source_card_id,
        )

    @staticmethod
    def _prompt(
        kind: str,
        title: str,
        detail: str,
        room: ArcadeRoom,
        viewer_seat: int,
        decision_seat: int | None,
        *,
        actor_seat: int | None = None,
        target_seat: int | None = None,
        card_index: int | None = None,
        source_card_id: str | None = None,
    ) -> dict[str, Any]:
        return {
            "kind": kind,
            "title": title,
            "detail": detail,
            "decisionPlayerId": (
                room.players[decision_seat].id if decision_seat is not None else None
            ),
            "isMyDecision": decision_seat == viewer_seat,
            "actorPlayerId": (
                room.players[actor_seat].id if actor_seat is not None else None
            ),
            "targetPlayerId": (
                room.players[target_seat].id if target_seat is not None else None
            ),
            "targetCardIndex": card_index,
            "sourceCardId": source_card_id,
        }
