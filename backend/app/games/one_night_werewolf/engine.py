from __future__ import annotations

import random
from collections import Counter
from dataclasses import dataclass, field
from typing import Any

from backend.app.arcade.models import ArcadePlayer, ArcadeRoom
from backend.app.games.base import GameRuleError


ROLE_LABELS = {
    "werewolf": "狼人",
    "minion": "爪牙",
    "mason": "守夜人",
    "seer": "预言家",
    "robber": "强盗",
    "troublemaker": "捣蛋鬼",
    "drunk": "酒鬼",
    "insomniac": "失眠者",
    "villager": "村民",
    "tanner": "皮匠",
    "hunter": "猎人",
}

ROLE_DESCRIPTIONS = {
    "werewolf": "查看开局的其他狼人；若你是唯一醒来的狼人，可以查看一张中央牌。",
    "minion": "查看开局的狼人。场上最终有狼人时跟随狼人胜负；没有狼人时，需要让一名爪牙以外的玩家被处决。",
    "mason": "查看开局的另一名守夜人；没有同伴醒来时，另一张守夜人牌在中央。",
    "seer": "选择查看一名其他玩家的牌，或者查看两张不同的中央牌。",
    "robber": "可以不行动；也可以与一名其他玩家交换牌，并查看自己交换后拿到的牌。",
    "troublemaker": "可以不行动；也可以交换两名其他玩家的牌，但不能查看任何被交换的牌。",
    "drunk": "必须与一张中央牌交换，且不能查看自己交换后拿到的牌。",
    "insomniac": "在夜间行动的最后查看自己的当前身份，确认是否被换牌。",
    "villager": "没有夜间技能，只能结合发言、已知信息和其他玩家的行动推理。",
    "tanner": "属于独立阵营；最终身份为皮匠、自己被处决且狼人阵营没有获胜时获胜。",
    "hunter": "如果最终身份为猎人并被处决，猎人投票选择的玩家也会一同死亡。",
}

ROLE_ALIGNMENTS = {
    "werewolf": "werewolf",
    "minion": "werewolf",
    "tanner": "tanner",
}

WAKE_ORDER = (
    "werewolf",
    "minion",
    "mason",
    "seer",
    "robber",
    "troublemaker",
    "drunk",
    "insomniac",
)

PRESET_LABELS = {
    "beginner": "初见月夜",
    "standard": "标准疑云",
    "chaos": "混沌之夜",
}

PRESET_ROLE_ORDERS = {
    "beginner": (
        "werewolf", "werewolf", "seer", "robber", "troublemaker",
        "villager", "insomniac", "drunk", "hunter", "villager",
        "villager", "minion", "tanner",
    ),
    "standard": (
        "werewolf", "werewolf", "seer", "robber", "troublemaker",
        "tanner", "minion", "insomniac", "drunk", "hunter",
        "villager", "villager", "villager",
    ),
    "chaos": (
        "werewolf", "werewolf", "minion", "seer", "tanner",
        "drunk", "robber", "troublemaker", "insomniac", "hunter",
        "mason", "mason", "villager",
    ),
}

@dataclass
class NightResult:
    kind: str
    text: str


@dataclass
class OneNightWerewolfState:
    initial_roles: list[str] = field(default_factory=list)
    current_roles: list[str] = field(default_factory=list)
    role_deck: list[str] = field(default_factory=list)
    confirmed_player_ids: set[str] = field(default_factory=set)
    wake_index: int = 0
    current_actor_ids: set[str] = field(default_factory=set)
    completed_actor_ids: set[str] = field(default_factory=set)
    night_results: dict[str, list[NightResult]] = field(default_factory=dict)
    votes: dict[str, str] = field(default_factory=dict)
    eliminated_player_ids: list[str] = field(default_factory=list)
    vote_counts: dict[str, int] = field(default_factory=dict)


class OneNightWerewolfEngine:
    key = "one_night_werewolf"
    name = "一夜狼人"
    min_players = 3
    max_players = 10
    uses_first_player = False
    public_rooms = True
    action_phases = {"role_reveal", "night", "discussion", "voting"}

    def __init__(self, rng: random.Random | random.SystemRandom | None = None):
        self.rng = rng or random.SystemRandom()

    def initial_state(self) -> OneNightWerewolfState:
        return OneNightWerewolfState()

    @staticmethod
    def is_active_phase(phase: str) -> bool:
        return phase not in {"lobby", "finished"}

    @staticmethod
    def room_options(options: dict[str, Any]) -> dict[str, Any]:
        preset = options.get("rolePreset", "standard")
        if preset not in PRESET_ROLE_ORDERS:
            raise GameRuleError("请选择有效的角色组合")
        listed = options.get("listed", True)
        if not isinstance(listed, bool):
            raise GameRuleError("公开房间设置格式不正确")
        return {
            "rolePreset": preset,
            "listed": listed,
            # First-person spectating would expose the target's private role.
            "allowSpectators": False,
        }

    def start(self, room: ArcadeRoom) -> None:
        role_deck = self._roles_for_room(room)
        dealt = list(role_deck)
        self.rng.shuffle(dealt)
        room.state = OneNightWerewolfState(
            initial_roles=list(dealt),
            current_roles=list(dealt),
            role_deck=list(role_deck),
            night_results={player.id: [] for player in room.players},
        )
        room.phase = "role_reveal"

    def act(
        self,
        room: ArcadeRoom,
        player: ArcadePlayer,
        action: str,
        payload: dict[str, Any],
    ) -> None:
        state = self._state(room)
        if action == "confirm_role":
            self._confirm_role(room, state, player)
        elif action == "night_action":
            self._night_action(room, state, player, payload)
        elif action == "start_vote":
            self._start_vote(room, state, player)
        elif action == "vote":
            self._vote(room, state, player, payload)
        else:
            raise GameRuleError("不支持这个一夜狼人操作")

    def view(self, room: ArcadeRoom, viewer: ArcadePlayer) -> dict[str, Any]:
        state = self._state(room)
        role_guide = [self._role_view(role) for role in ROLE_LABELS]
        if not state.initial_roles:
            return {
                "roleDeck": [],
                "roleGuide": role_guide,
                "presetLabel": PRESET_LABELS.get(
                    str(room.options.get("rolePreset", "standard")),
                    "标准疑云",
                ),
                "self": {"initialRole": None, "nightResults": []},
                "night": {"isMyTurn": False, "prompt": None},
                "votesSubmitted": 0,
                "hasVoted": False,
                "resolution": None,
                "legal": {},
            }

        player_count = len(room.players)
        initial_role = state.initial_roles[viewer.seat]
        finished = room.phase == "finished"
        is_my_turn = (
            room.phase == "night"
            and viewer.id in state.current_actor_ids
            and viewer.id not in state.completed_actor_ids
        )
        active_role = (
            state.initial_roles[viewer.seat] if is_my_turn else None
        )
        initial_wolf_count = sum(
            state.initial_roles[player.seat] == "werewolf"
            for player in room.players
        )
        return {
            "roleDeck": [self._role_view(role) for role in state.role_deck],
            "roleGuide": role_guide,
            "presetLabel": PRESET_LABELS[str(room.options["rolePreset"])],
            "self": {
                "initialRole": self._role_view(initial_role),
                "nightResults": [
                    {"kind": item.kind, "text": item.text}
                    for item in state.night_results.get(viewer.id, [])
                ],
                "finalRole": (
                    self._role_view(state.current_roles[viewer.seat])
                    if finished
                    else None
                ),
            },
            "roleConfirmedCount": len(state.confirmed_player_ids),
            "night": {
                "isMyTurn": is_my_turn,
                "prompt": self._night_prompt(active_role),
            },
            "votesSubmitted": len(state.votes),
            "hasVoted": viewer.id in state.votes,
            "resolution": (
                {
                    "players": [
                        {
                            "playerId": player.id,
                            "initialRole": self._role_view(
                                state.initial_roles[player.seat]
                            ),
                            "finalRole": self._role_view(
                                state.current_roles[player.seat]
                            ),
                            "votedForId": state.votes.get(player.id),
                            "voteCount": state.vote_counts.get(player.id, 0),
                            "eliminated": player.id
                            in state.eliminated_player_ids,
                            "won": player.id in room.winner_player_ids,
                        }
                        for player in room.players
                    ],
                    "centerRoles": [
                        self._role_view(role)
                        for role in state.current_roles[player_count:]
                    ],
                }
                if finished
                else None
            ),
            "legal": {
                "canConfirmRole": (
                    room.phase == "role_reveal"
                    and viewer.id not in state.confirmed_player_ids
                ),
                "canSubmitNightAction": is_my_turn,
                "nightRole": active_role,
                "targetPlayerIds": (
                    [
                        player.id
                        for player in room.players
                        if player.id != viewer.id
                    ]
                    if active_role in {"seer", "robber", "troublemaker"}
                    else []
                ),
                "centerSelectionCount": (
                    1
                    if active_role == "drunk"
                    or (active_role == "werewolf" and initial_wolf_count == 1)
                    else 2
                    if active_role == "seer"
                    else 0
                ),
                "canStartVote": (
                    room.phase == "discussion" and viewer.id == room.host_id
                ),
                "voteTargetPlayerIds": (
                    [
                        player.id
                        for player in room.players
                        if player.id != viewer.id
                    ]
                    if room.phase == "voting" and viewer.id not in state.votes
                    else []
                ),
            },
        }

    def player_result(
        self, room: ArcadeRoom, player: ArcadePlayer
    ) -> tuple[str, str, bool]:
        state = self._state(room)
        role = state.current_roles[player.seat]
        alignment = ROLE_ALIGNMENTS.get(role, "village")
        recorded_role = "one_night_minion" if role == "minion" else role
        return recorded_role, alignment, player.id in room.winner_player_ids

    def record_state(self, room: ArcadeRoom) -> dict[str, Any]:
        state = self._state(room)
        return {
            "rolePreset": room.options.get("rolePreset"),
            "initialRoles": list(state.initial_roles),
            "finalRoles": list(state.current_roles),
            "votes": dict(state.votes),
            "voteCounts": dict(state.vote_counts),
            "eliminatedPlayerIds": list(state.eliminated_player_ids),
        }

    def manual_forfeit(self, room: ArcadeRoom, player: ArcadePlayer) -> bool:
        winners = [member.id for member in room.players if member.id != player.id]
        room.finish(
            "abandoned",
            winners,
            f"{player.name}退出，本局由其余玩家获胜",
        )
        return True

    def disconnect_timeout(
        self, room: ArcadeRoom, player: ArcadePlayer
    ) -> bool:
        return self.manual_forfeit(room, player)

    def _confirm_role(
        self,
        room: ArcadeRoom,
        state: OneNightWerewolfState,
        player: ArcadePlayer,
    ) -> None:
        if room.phase != "role_reveal":
            raise GameRuleError("当前不是身份确认阶段")
        if player.id in state.confirmed_player_ids:
            raise GameRuleError("你已经确认过身份")
        state.confirmed_player_ids.add(player.id)
        if len(state.confirmed_player_ids) == len(room.players):
            room.phase = "night"
            state.wake_index = 0
            self._advance_wake(room, state)

    def _advance_wake(
        self,
        room: ArcadeRoom,
        state: OneNightWerewolfState,
    ) -> None:
        state.current_actor_ids.clear()
        state.completed_actor_ids.clear()
        while state.wake_index < len(WAKE_ORDER):
            role = WAKE_ORDER[state.wake_index]
            actor_ids = {
                player.id
                for player in room.players
                if state.initial_roles[player.seat] == role
            }
            state.wake_index += 1
            if actor_ids:
                state.current_actor_ids = actor_ids
                return
        room.phase = "discussion"

    def _night_action(
        self,
        room: ArcadeRoom,
        state: OneNightWerewolfState,
        player: ArcadePlayer,
        payload: dict[str, Any],
    ) -> None:
        if room.phase != "night" or player.id not in state.current_actor_ids:
            raise GameRuleError("现在还没有轮到你的夜间行动")
        if player.id in state.completed_actor_ids:
            raise GameRuleError("你已经完成夜间行动")
        role = state.initial_roles[player.seat]
        handler = getattr(self, f"_act_{role}", None)
        if handler is None:
            raise GameRuleError("这个身份没有夜间行动")
        handler(room, state, player, payload)
        state.completed_actor_ids.add(player.id)
        if state.completed_actor_ids >= state.current_actor_ids:
            self._advance_wake(room, state)

    def _act_werewolf(
        self,
        room: ArcadeRoom,
        state: OneNightWerewolfState,
        player: ArcadePlayer,
        payload: dict[str, Any],
    ) -> None:
        wolves = [
            member
            for member in room.players
            if state.initial_roles[member.seat] == "werewolf"
        ]
        others = [member for member in wolves if member.id != player.id]
        if others:
            names = "、".join(member.name for member in others)
            self._add_result(state, player.id, "werewolves", f"开局狼人同伴：{names}")
            return
        center_index = self._center_index(room, payload.get("centerIndex"))
        role = state.current_roles[center_index]
        self._add_result(
            state,
            player.id,
            "center",
            f"你是孤狼，中央第 {center_index - len(room.players) + 1} 张是{ROLE_LABELS[role]}",
        )

    def _act_minion(
        self,
        room: ArcadeRoom,
        state: OneNightWerewolfState,
        player: ArcadePlayer,
        _: dict[str, Any],
    ) -> None:
        wolves = [
            member.name
            for member in room.players
            if state.initial_roles[member.seat] == "werewolf"
        ]
        text = f"开局狼人：{'、'.join(wolves)}" if wolves else "场上开局没有狼人"
        self._add_result(state, player.id, "werewolves", text)

    def _act_mason(
        self,
        room: ArcadeRoom,
        state: OneNightWerewolfState,
        player: ArcadePlayer,
        _: dict[str, Any],
    ) -> None:
        partners = [
            member.name
            for member in room.players
            if member.id != player.id
            and state.initial_roles[member.seat] == "mason"
        ]
        text = (
            f"另一名守夜人：{'、'.join(partners)}"
            if partners
            else "没有其他守夜人醒来，另一张守夜人在中央"
        )
        self._add_result(state, player.id, "masons", text)

    def _act_seer(
        self,
        room: ArcadeRoom,
        state: OneNightWerewolfState,
        player: ArcadePlayer,
        payload: dict[str, Any],
    ) -> None:
        target_id = payload.get("targetPlayerId")
        center_indices = payload.get("centerIndices")
        if isinstance(target_id, str):
            target = self._other_player(room, player, target_id)
            role = state.current_roles[target.seat]
            self._add_result(
                state,
                player.id,
                "seer",
                f"{target.name}的牌是{ROLE_LABELS[role]}",
            )
            return
        indices = self._center_indices(room, center_indices, required=2)
        labels = [
            f"第 {index - len(room.players) + 1} 张{ROLE_LABELS[state.current_roles[index]]}"
            for index in indices
        ]
        self._add_result(state, player.id, "seer", f"中央牌：{'、'.join(labels)}")

    def _act_robber(
        self,
        room: ArcadeRoom,
        state: OneNightWerewolfState,
        player: ArcadePlayer,
        payload: dict[str, Any],
    ) -> None:
        if payload.get("skip") is True:
            self._add_result(state, player.id, "robber", "你选择不交换身份")
            return
        target = self._other_player(room, player, payload.get("targetPlayerId"))
        state.current_roles[player.seat], state.current_roles[target.seat] = (
            state.current_roles[target.seat],
            state.current_roles[player.seat],
        )
        role = state.current_roles[player.seat]
        self._add_result(
            state,
            player.id,
            "robber",
            f"你与{target.name}交换后拿到{ROLE_LABELS[role]}",
        )

    def _act_troublemaker(
        self,
        room: ArcadeRoom,
        state: OneNightWerewolfState,
        player: ArcadePlayer,
        payload: dict[str, Any],
    ) -> None:
        if payload.get("skip") is True:
            self._add_result(state, player.id, "troublemaker", "你选择不交换任何身份")
            return
        raw_ids = payload.get("targetPlayerIds")
        if (
            not isinstance(raw_ids, list)
            or len(raw_ids) != 2
            or len(set(raw_ids)) != 2
            or not all(isinstance(item, str) for item in raw_ids)
        ):
            raise GameRuleError("请选择两名不同的其他玩家")
        first = self._other_player(room, player, raw_ids[0])
        second = self._other_player(room, player, raw_ids[1])
        state.current_roles[first.seat], state.current_roles[second.seat] = (
            state.current_roles[second.seat],
            state.current_roles[first.seat],
        )
        self._add_result(
            state,
            player.id,
            "troublemaker",
            f"你交换了{first.name}与{second.name}的身份，没有查看牌面",
        )

    def _act_drunk(
        self,
        room: ArcadeRoom,
        state: OneNightWerewolfState,
        player: ArcadePlayer,
        payload: dict[str, Any],
    ) -> None:
        center_index = self._center_index(room, payload.get("centerIndex"))
        state.current_roles[player.seat], state.current_roles[center_index] = (
            state.current_roles[center_index],
            state.current_roles[player.seat],
        )
        self._add_result(
            state,
            player.id,
            "drunk",
            f"你与中央第 {center_index - len(room.players) + 1} 张交换，但不知道新身份",
        )

    def _act_insomniac(
        self,
        _: ArcadeRoom,
        state: OneNightWerewolfState,
        player: ArcadePlayer,
        __: dict[str, Any],
    ) -> None:
        role = state.current_roles[player.seat]
        self._add_result(
            state,
            player.id,
            "insomniac",
            f"夜晚结束时，你的身份是{ROLE_LABELS[role]}",
        )

    def _start_vote(
        self,
        room: ArcadeRoom,
        state: OneNightWerewolfState,
        player: ArcadePlayer,
    ) -> None:
        if room.phase != "discussion":
            raise GameRuleError("当前不是讨论阶段")
        if player.id != room.host_id:
            raise GameRuleError("只有房主可以开始投票")
        room.phase = "voting"

    def _vote(
        self,
        room: ArcadeRoom,
        state: OneNightWerewolfState,
        player: ArcadePlayer,
        payload: dict[str, Any],
    ) -> None:
        if room.phase != "voting":
            raise GameRuleError("当前不是投票阶段")
        if player.id in state.votes:
            raise GameRuleError("你已经投过票")
        target = self._other_player(room, player, payload.get("targetPlayerId"))
        state.votes[player.id] = target.id
        if len(state.votes) == len(room.players):
            self._resolve_vote(room, state)

    def _resolve_vote(
        self,
        room: ArcadeRoom,
        state: OneNightWerewolfState,
    ) -> None:
        counts = Counter(state.votes.values())
        state.vote_counts = dict(counts)
        highest = max(counts.values(), default=0)
        eliminated = (
            {player_id for player_id, count in counts.items() if count == highest}
            if highest > 1
            else set()
        )
        # A killed hunter also eliminates the player they voted for.
        hunter_targets = {
            state.votes[player.id]
            for player in room.players
            if player.id in eliminated
            and state.current_roles[player.seat] == "hunter"
        }
        eliminated.update(hunter_targets)
        state.eliminated_player_ids = [
            player.id for player in room.players if player.id in eliminated
        ]
        winner, winners, reason = self._winners(room, state, eliminated)
        room.finish(winner, winners, reason)

    def _winners(
        self,
        room: ArcadeRoom,
        state: OneNightWerewolfState,
        eliminated: set[str],
    ) -> tuple[str, list[str], str]:
        final_roles = {
            player.id: state.current_roles[player.seat]
            for player in room.players
        }
        killed_tanners = [
            player_id
            for player_id, role in final_roles.items()
            if role == "tanner" and player_id in eliminated
        ]
        wolf_ids = {
            player_id
            for player_id, role in final_roles.items()
            if role == "werewolf"
        }
        minion_ids = {
            player_id
            for player_id, role in final_roles.items()
            if role == "minion"
        }
        village_ids = [
            player_id
            for player_id, role in final_roles.items()
            if role not in {"werewolf", "minion", "tanner"}
        ]
        werewolf_team_ids = [
            player_id
            for player_id, role in final_roles.items()
            if role in {"werewolf", "minion"}
        ]

        if wolf_ids:
            killed_wolves = wolf_ids & eliminated
            if killed_wolves:
                winners = [*village_ids, *killed_tanners]
                reason = "村庄成功处决了狼人"
                if killed_tanners:
                    reason += "，皮匠也达成了自己的目标"
                return "village", winners, reason
            return "werewolf", werewolf_team_ids, "没有狼人被处决"

        if minion_ids:
            killed_others = eliminated - minion_ids
            if killed_others:
                return (
                    "werewolf",
                    list(minion_ids),
                    "场上没有狼人，爪牙诱导村庄处决了其他人",
                )
            if not eliminated:
                return "village", village_ids, "场上没有狼人，村庄正确地没有处决任何人"
            return "none", [], "场上没有狼人，但只有爪牙被处决，本局无人达成胜利条件"

        if killed_tanners:
            return "tanner", killed_tanners, "皮匠成功让村庄处决了自己"
        if not eliminated:
            return "village", village_ids, "场上没有狼人，村庄正确地没有处决任何人"
        return "none", [], "场上没有狼人，但村庄错误地处决了无辜者"

    def _roles_for_room(self, room: ArcadeRoom) -> list[str]:
        count = len(room.players) + 3
        preset = str(room.options.get("rolePreset", "standard"))
        roles = list(PRESET_ROLE_ORDERS[preset][:count])
        if roles.count("mason") == 1:
            roles[roles.index("mason")] = "villager"
        return roles

    @staticmethod
    def _state(room: ArcadeRoom) -> OneNightWerewolfState:
        if not isinstance(room.state, OneNightWerewolfState):
            raise GameRuleError("一夜狼人状态无效")
        return room.state

    @staticmethod
    def _role_view(role: str) -> dict[str, str]:
        return {
            "code": role,
            "label": ROLE_LABELS[role],
            "alignment": ROLE_ALIGNMENTS.get(role, "village"),
            "description": ROLE_DESCRIPTIONS[role],
        }

    @staticmethod
    def _night_prompt(role: str | None) -> str | None:
        return {
            "werewolf": "确认狼人同伴；若你是孤狼，选择一张中央牌查看。",
            "minion": "查看开局狼人后确认。",
            "mason": "查看另一名守夜人后确认。",
            "seer": "查看一名玩家，或查看两张中央牌。",
            "robber": "选择另一名玩家交换身份。",
            "troublemaker": "选择两名其他玩家交换身份。",
            "drunk": "选择一张中央牌交换。",
            "insomniac": "查看自己夜晚结束时的身份。",
        }.get(role)

    @staticmethod
    def _add_result(
        state: OneNightWerewolfState,
        player_id: str,
        kind: str,
        text: str,
    ) -> None:
        state.night_results.setdefault(player_id, []).append(
            NightResult(kind=kind, text=text)
        )

    @staticmethod
    def _other_player(
        room: ArcadeRoom,
        actor: ArcadePlayer,
        player_id: Any,
    ) -> ArcadePlayer:
        if not isinstance(player_id, str):
            raise GameRuleError("请选择一名玩家")
        try:
            target = room.player(player_id)
        except KeyError as error:
            raise GameRuleError("目标玩家不存在") from error
        if target.id == actor.id:
            raise GameRuleError("不能选择自己")
        return target

    @staticmethod
    def _center_index(room: ArcadeRoom, raw_index: Any) -> int:
        if isinstance(raw_index, bool) or not isinstance(raw_index, int):
            raise GameRuleError("请选择一张中央牌")
        if raw_index not in {0, 1, 2}:
            raise GameRuleError("中央牌位置无效")
        return len(room.players) + raw_index

    @classmethod
    def _center_indices(
        cls,
        room: ArcadeRoom,
        raw_indices: Any,
        *,
        required: int,
    ) -> list[int]:
        if (
            not isinstance(raw_indices, list)
            or len(raw_indices) != required
            or len(set(raw_indices)) != required
        ):
            raise GameRuleError(f"请选择 {required} 张不同的中央牌")
        return [cls._center_index(room, index) for index in raw_indices]
