from __future__ import annotations

import copy
import hashlib
import random
import secrets
import string
from datetime import datetime, timedelta, timezone
from typing import Any

from backend.app.games.base import GameEngine, GameRuleError

from .models import (
    ArcadeChatMessage,
    ArcadeGameRequest,
    ArcadePlayer,
    ArcadeRoom,
    utc_now_iso,
)


ROOM_ALPHABET = "".join(
    character
    for character in string.ascii_uppercase + string.digits
    if character not in "0O1I"
)
ROOM_CLEANUP_GRACE = timedelta(minutes=10)
HOST_TRANSFER_GRACE = timedelta(seconds=20)
MAX_CHAT_LENGTH = 300
MAX_CHAT_MESSAGES = 100
UNDO_GAMES = {"gomoku", "xiangqi", "go"}
DRAW_GAMES = {"gomoku", "xiangqi", "go"}
FIRST_PLAYER_MODES = {"random", "host"}
UNDOABLE_ACTIONS = {
    "gomoku": {"place", "pass"},
    "xiangqi": {"move"},
    "go": {"place", "pass"},
}
MAX_UNDO_HISTORY = 100


class ArcadeRoomError(ValueError):
    pass


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


class ArcadeRoomManager:
    def __init__(
        self,
        engines: dict[str, GameEngine],
        rng: random.Random | random.SystemRandom | None = None,
    ) -> None:
        self.engines = engines
        self.rooms: dict[str, ArcadeRoom] = {}
        self.rng = rng or random.SystemRandom()

    def create_room(
        self,
        game_key: str,
        player_name: str,
        account_id: str,
        options: dict[str, Any] | None = None,
    ) -> tuple[ArcadeRoom, ArcadePlayer, str]:
        engine = self.engine(game_key)
        normalized_options = self._room_options(engine, options or {})
        name = self._normalize_name(player_name)
        code = self._new_code()
        token = secrets.token_urlsafe(32)
        player = ArcadePlayer(
            id=secrets.token_urlsafe(10),
            account_id=account_id,
            name=name,
            token_hash=hash_token(token),
            seat=0,
        )
        room = ArcadeRoom(
            code=code,
            game_key=game_key,
            host_id=player.id,
            players=[player],
            state=engine.initial_state(),
            options=normalized_options,
            listed=getattr(engine, "public_rooms", True),
        )
        self.rooms[code] = room
        return room, player, token

    def join_room(
        self,
        code: str,
        game_key: str,
        player_name: str,
        account_id: str,
    ) -> tuple[ArcadeRoom, ArcadePlayer, str]:
        room = self.get_room(code)
        engine = self.engine(room.game_key)
        if room.game_key != game_key:
            raise ArcadeRoomError("房间所属游戏不正确")
        if room.phase != "lobby":
            raise ArcadeRoomError("游戏已经开始，不能加入新玩家")
        if not any(player.connected for player in room.players):
            raise ArcadeRoomError("房间成员暂时都不在线，请等待原成员恢复房间")
        if len(room.players) >= engine.max_players:
            raise ArcadeRoomError("房间已经满员")
        if any(player.account_id == account_id for player in room.players):
            raise ArcadeRoomError("你的账号已经在这个房间中")
        name = self._normalize_name(player_name)
        if any(player.name.casefold() == name.casefold() for player in room.players):
            raise ArcadeRoomError("房间里已经有同名玩家")
        token = secrets.token_urlsafe(32)
        player = ArcadePlayer(
            id=secrets.token_urlsafe(10),
            account_id=account_id,
            name=name,
            token_hash=hash_token(token),
            seat=len(room.players),
        )
        room.players.append(player)
        room.revision += 1
        return room, player, token

    def resume(
        self,
        code: str,
        token: str,
        account_id: str,
    ) -> tuple[ArcadeRoom, ArcadePlayer]:
        room = self.get_room(code)
        digest = hash_token(token)
        for player in room.players:
            if secrets.compare_digest(player.token_hash, digest):
                if player.account_id != account_id:
                    raise ArcadeRoomError("这个座位属于其他账号")
                player.connected = True
                self.update_presence(room)
                room.revision += 1
                return room, player
        raise ArcadeRoomError("恢复凭证无效，请重新加入房间")

    def leave(self, room: ArcadeRoom, player_id: str) -> bool:
        if room.phase in {"setup", "playing", "bidding", "scoring"}:
            room.player(player_id).connected = False
            room.revision += 1
            self.update_presence(room)
            return True
        if room.phase == "finished":
            self._remove_player(room, player_id)
            if room.players:
                self._prepare_lobby(room)
            else:
                self.rooms.pop(room.code, None)
            return False
        self._remove_player(room, player_id)
        if not room.players:
            self.rooms.pop(room.code, None)
            return False
        room.revision += 1
        return False

    def kick(self, room: ArcadeRoom, actor_id: str, target_id: str) -> None:
        if room.phase != "lobby":
            raise ArcadeRoomError("只能移除等待中的玩家")
        if room.host_id != actor_id:
            raise ArcadeRoomError("只有房主可以移除玩家")
        if actor_id == target_id:
            raise ArcadeRoomError("房主不能移除自己，请使用解散房间")
        room.player(target_id)
        self._remove_player(room, target_id)
        room.revision += 1

    def dissolve(self, room: ArcadeRoom, actor_id: str) -> None:
        if room.phase != "lobby":
            raise ArcadeRoomError("游戏开始后不能直接解散，请使用认输")
        if room.host_id != actor_id:
            raise ArcadeRoomError("只有房主可以解散房间")
        self.rooms.pop(room.code, None)

    def update_options(
        self,
        room: ArcadeRoom,
        actor_id: str,
        options: dict[str, Any],
    ) -> None:
        if room.phase not in {"lobby", "finished"}:
            raise ArcadeRoomError("对局进行中不能修改规则")
        if room.host_id != actor_id:
            raise ArcadeRoomError("只有房主可以修改规则")
        normalized = self._room_options(self.engine(room.game_key), options)
        if room.phase == "finished":
            self._prepare_lobby(room)
        room.options = normalized
        room.revision += 1

    def start(self, room: ArcadeRoom, actor_id: str) -> None:
        engine = self.engine(room.game_key)
        if room.host_id != actor_id:
            raise ArcadeRoomError("只有房主可以开始游戏")
        if room.phase != "lobby":
            raise ArcadeRoomError("当前不能开始游戏")
        if not engine.min_players <= len(room.players) <= engine.max_players:
            if engine.min_players == engine.max_players:
                raise ArcadeRoomError(f"该游戏需要 {engine.min_players} 名玩家")
            raise ArcadeRoomError(
                f"该游戏需要 {engine.min_players}–{engine.max_players} 名玩家"
            )
        self._start_round(room, engine, first_round=room.round_number == 0)
        room.revision += 1

    def act(
        self,
        room: ArcadeRoom,
        player_id: str,
        action: str,
        payload: dict[str, Any],
    ) -> None:
        if room.phase not in {"setup", "playing", "bidding", "scoring"}:
            raise ArcadeRoomError("当前不能进行这个操作")
        if room.pending_request is not None and action != "resign":
            raise ArcadeRoomError("请先处理当前申请")
        player = room.player(player_id)
        engine = self.engine(room.game_key)
        should_track_undo = (
            room.game_key in UNDO_GAMES
            and action in UNDOABLE_ACTIONS[room.game_key]
            and room.phase == "playing"
        )
        undo_guard = getattr(engine, "should_track_undo", None)
        if should_track_undo and undo_guard is not None:
            should_track_undo = undo_guard(room, action)
        previous_state = copy.deepcopy(room.state) if should_track_undo else None
        engine.act(room, player, action, payload)
        if previous_state is not None:
            room.undo_history.append(previous_state)
            room.undo_history = room.undo_history[-MAX_UNDO_HISTORY:]
        room.pending_request = None
        room.revision += 1

    def restart(self, room: ArcadeRoom, actor_id: str) -> None:
        if room.phase != "finished":
            raise ArcadeRoomError("本局尚未结束")
        room.player(actor_id)
        room.rematch_ready_ids.add(actor_id)
        if room.rematch_ready_ids == {player.id for player in room.players}:
            self._start_round(
                room,
                self.engine(room.game_key),
                first_round=False,
            )
        room.revision += 1

    def send_chat(
        self, room: ArcadeRoom, player_id: str, content: str
    ) -> ArcadeChatMessage:
        player = room.player(player_id)
        normalized = " ".join(content.strip().split())
        if not normalized:
            raise ArcadeRoomError("消息不能为空")
        if len(normalized) > MAX_CHAT_LENGTH:
            raise ArcadeRoomError(f"消息最多 {MAX_CHAT_LENGTH} 个字符")
        message = ArcadeChatMessage(
            id=secrets.token_urlsafe(10),
            sender_id=player.id,
            sender_name=player.name,
            content=normalized,
        )
        room.chat_messages.append(message)
        room.chat_messages = room.chat_messages[-MAX_CHAT_MESSAGES:]
        room.revision += 1
        return message

    def request_game_action(
        self, room: ArcadeRoom, player_id: str, kind: str
    ) -> None:
        room.player(player_id)
        if room.phase != "playing":
            raise ArcadeRoomError("当前不能发起这个申请")
        if room.pending_request is not None:
            raise ArcadeRoomError("已经有一项申请等待处理")
        if kind == "undo":
            if room.game_key not in UNDO_GAMES:
                raise ArcadeRoomError("这个游戏不支持悔棋")
            if not room.options.get("allowUndo", True):
                raise ArcadeRoomError("本房间没有开启悔棋")
            if not room.undo_history:
                raise ArcadeRoomError("当前还没有可以撤回的操作")
        elif kind == "draw":
            if room.game_key not in DRAW_GAMES:
                raise ArcadeRoomError("这个游戏不支持和棋申请")
            if not room.options.get("allowDraw", True):
                raise ArcadeRoomError("本房间没有开启和棋申请")
        else:
            raise ArcadeRoomError("不支持这个申请")
        room.pending_request = ArcadeGameRequest(
            kind=kind,
            requester_id=player_id,
        )
        room.revision += 1

    def resolve_game_request(
        self, room: ArcadeRoom, player_id: str, accept: bool
    ) -> None:
        request = room.pending_request
        if request is None:
            raise ArcadeRoomError("当前没有等待处理的申请")
        room.player(player_id)
        if request.requester_id == player_id:
            if accept:
                raise ArcadeRoomError("申请需要由其他玩家确认")
            room.pending_request = None
            room.revision += 1
            return
        room.pending_request = None
        if accept and request.kind == "draw":
            room.finish("draw", [], "双方同意和棋")
        elif accept and request.kind == "undo":
            if not room.undo_history:
                raise ArcadeRoomError("当前没有可以撤回的操作")
            room.state = room.undo_history.pop()
            resume_clock = getattr(
                self.engine(room.game_key),
                "resume_clock",
                None,
            )
            if resume_clock is not None:
                resume_clock(room)
        room.revision += 1

    def get_room(self, code: str) -> ArcadeRoom:
        normalized = code.strip().upper()
        room = self.rooms.get(normalized)
        if room is None:
            raise ArcadeRoomError("没有找到这个房间")
        return room

    def engine(self, game_key: str) -> GameEngine:
        try:
            return self.engines[game_key]
        except KeyError as exc:
            raise ArcadeRoomError("暂不支持这个游戏") from exc

    def update_presence(
        self, room: ArcadeRoom, *, now: datetime | None = None
    ) -> None:
        current = now or datetime.now(timezone.utc)
        connected_players = [player for player in room.players if player.connected]
        if connected_players:
            room.all_humans_offline_since = None
            room.cleanup_ready = False
            host = room.player(room.host_id)
            if (
                room.phase in {"lobby", "finished"}
                and not host.connected
                and any(player.id != host.id for player in connected_players)
            ):
                if room.host_offline_since is None:
                    room.host_offline_since = current
            else:
                room.host_offline_since = None
            return
        room.host_offline_since = None
        if room.all_humans_offline_since is None:
            room.all_humans_offline_since = current

    def maintain(
        self,
        *,
        now: datetime | None = None,
        cleanup_grace: timedelta = ROOM_CLEANUP_GRACE,
        host_grace: timedelta = HOST_TRANSFER_GRACE,
    ) -> list[ArcadeRoom]:
        current = now or datetime.now(timezone.utc)
        changed: list[ArcadeRoom] = []
        for room in list(self.rooms.values()):
            self.update_presence(room, now=current)
            offline_since = room.all_humans_offline_since
            if (
                offline_since is not None
                and current - offline_since >= cleanup_grace
                and not room.cleanup_ready
            ):
                room.cleanup_ready = True
                room.revision += 1
                changed.append(room)

            host_offline_since = room.host_offline_since
            if (
                host_offline_since is not None
                and current - host_offline_since >= host_grace
            ):
                candidates = sorted(
                    (
                        player
                        for player in room.players
                        if player.connected and player.id != room.host_id
                    ),
                    key=lambda player: player.seat,
                )
                if candidates:
                    room.host_id = candidates[0].id
                    room.host_offline_since = None
                    room.revision += 1
                    if room not in changed:
                        changed.append(room)
        return changed

    def cleanup_room(
        self,
        code: str,
        *,
        now: datetime | None = None,
        grace: timedelta = ROOM_CLEANUP_GRACE,
    ) -> ArcadeRoom:
        current = now or datetime.now(timezone.utc)
        room = self.get_room(code)
        self.update_presence(room, now=current)
        if any(player.connected for player in room.players):
            raise ArcadeRoomError("已有玩家重新连接，不能清理这个房间")
        offline_since = room.all_humans_offline_since
        if offline_since is None or current - offline_since < grace:
            raise ArcadeRoomError("房间全员离线满 10 分钟后才可以清理")
        self.rooms.pop(room.code, None)
        return room

    def _start_round(
        self,
        room: ArcadeRoom,
        engine: GameEngine,
        *,
        first_round: bool,
    ) -> None:
        if len(room.players) > 1:
            if first_round:
                if room.options.get("firstPlayer", "random") == "host":
                    room.players.sort(
                        key=lambda player: player.id != room.host_id
                    )
                else:
                    self.rng.shuffle(room.players)
            else:
                room.players = room.players[1:] + room.players[:1]
            for seat, player in enumerate(room.players):
                player.seat = seat
        room.game_id = secrets.token_urlsafe(16)
        room.started_at = utc_now_iso()
        room.ended_at = None
        room.winner = None
        room.winner_player_ids = []
        room.win_reason = None
        room.recorded = False
        room.round_number += 1
        room.rematch_ready_ids.clear()
        room.pending_request = None
        room.undo_history.clear()
        engine.start(room)

    def _prepare_lobby(self, room: ArcadeRoom) -> None:
        room.state = self.engine(room.game_key).initial_state()
        room.phase = "lobby"
        room.game_id = None
        room.started_at = None
        room.ended_at = None
        room.winner = None
        room.winner_player_ids = []
        room.win_reason = None
        room.recorded = False
        room.round_number = 0
        room.rematch_ready_ids.clear()
        room.pending_request = None
        room.undo_history.clear()
        room.revision += 1

    @staticmethod
    def _remove_player(room: ArcadeRoom, player_id: str) -> None:
        leaving = room.player(player_id)
        room.players.remove(leaving)
        room.rematch_ready_ids.discard(player_id)
        if (
            room.pending_request is not None
            and room.pending_request.requester_id == player_id
        ):
            room.pending_request = None
        for index, player in enumerate(room.players):
            player.seat = index
        if room.players and room.host_id == player_id:
            room.host_id = room.players[0].id

    def _new_code(self) -> str:
        for _ in range(100):
            code = "".join(secrets.choice(ROOM_ALPHABET) for _ in range(4))
            if code not in self.rooms:
                return code
        raise ArcadeRoomError("暂时无法创建房间，请稍后重试")

    @staticmethod
    def _normalize_name(name: str) -> str:
        normalized = " ".join(name.strip().split())
        if not normalized:
            raise ArcadeRoomError("请输入玩家名称")
        if len(normalized) > 12:
            raise ArcadeRoomError("玩家名称最多 12 个字符")
        return normalized

    @staticmethod
    def _room_options(
        engine: GameEngine, options: dict[str, Any]
    ) -> dict[str, Any]:
        normalized: dict[str, Any] = {}
        if engine.max_players > 1:
            first_player = options.get("firstPlayer", "random")
            if first_player not in FIRST_PLAYER_MODES:
                raise ArcadeRoomError("请选择随机先手或房主先手")
            normalized["firstPlayer"] = first_player
        if engine.key in UNDO_GAMES:
            allow_undo = options.get("allowUndo", True)
            allow_draw = options.get("allowDraw", True)
            if not isinstance(allow_undo, bool) or not isinstance(
                allow_draw, bool
            ):
                raise ArcadeRoomError("协商规则格式不正确")
            normalized["allowUndo"] = allow_undo
            normalized["allowDraw"] = allow_draw
        normalizer = getattr(engine, "room_options", None)
        if normalizer is not None:
            normalized.update(normalizer(options))
        return normalized


ACTION_ERRORS = (ArcadeRoomError, GameRuleError, KeyError)
