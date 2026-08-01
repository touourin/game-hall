from __future__ import annotations

import hashlib
import secrets
import string
from datetime import datetime, timedelta, timezone
from typing import Any

from backend.app.games.base import GameEngine, GameRuleError

from .models import ArcadePlayer, ArcadeRoom, utc_now_iso


ROOM_ALPHABET = "".join(
    character
    for character in string.ascii_uppercase + string.digits
    if character not in "0O1I"
)
ABANDONED_ROOM_GRACE = timedelta(minutes=5)


class ArcadeRoomError(ValueError):
    pass


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


class ArcadeRoomManager:
    def __init__(self, engines: dict[str, GameEngine]) -> None:
        self.engines = engines
        self.rooms: dict[str, ArcadeRoom] = {}

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
                room.all_humans_offline_since = None
                room.revision += 1
                return room, player
        raise ArcadeRoomError("恢复凭证无效，请重新加入房间")

    def leave(self, room: ArcadeRoom, player_id: str) -> bool:
        if room.phase in {"setup", "playing", "bidding"}:
            room.player(player_id).connected = False
            room.revision += 1
            self.update_presence(room)
            return True
        if room.phase == "finished":
            room.player(player_id).connected = False
            room.revision += 1
            self.update_presence(room)
            return False
        leaving = room.player(player_id)
        room.players.remove(leaving)
        for index, player in enumerate(room.players):
            player.seat = index
        if not room.players:
            self.rooms.pop(room.code, None)
            return False
        if room.host_id == player_id:
            room.host_id = room.players[0].id
        room.revision += 1
        return False

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
        room.game_id = secrets.token_urlsafe(16)
        room.started_at = utc_now_iso()
        room.ended_at = None
        room.winner = None
        room.winner_player_ids = []
        room.win_reason = None
        room.recorded = False
        engine.start(room)
        room.revision += 1

    def act(
        self,
        room: ArcadeRoom,
        player_id: str,
        action: str,
        payload: dict[str, Any],
    ) -> None:
        if room.phase not in {"setup", "playing", "bidding"}:
            raise ArcadeRoomError("当前不能进行这个操作")
        player = room.player(player_id)
        self.engine(room.game_key).act(room, player, action, payload)
        room.revision += 1

    def restart(self, room: ArcadeRoom, actor_id: str) -> None:
        if room.host_id != actor_id:
            raise ArcadeRoomError("只有房主可以再来一局")
        if room.phase != "finished":
            raise ArcadeRoomError("本局尚未结束")
        room.state = self.engine(room.game_key).initial_state()
        room.phase = "lobby"
        room.game_id = None
        room.started_at = None
        room.ended_at = None
        room.winner = None
        room.winner_player_ids = []
        room.win_reason = None
        room.recorded = False
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
        if any(player.connected for player in room.players):
            room.all_humans_offline_since = None
        elif room.all_humans_offline_since is None:
            room.all_humans_offline_since = now or datetime.now(timezone.utc)

    def cleanup_abandoned(
        self,
        *,
        now: datetime | None = None,
        grace: timedelta = ABANDONED_ROOM_GRACE,
    ) -> list[str]:
        current = now or datetime.now(timezone.utc)
        removed: list[str] = []
        for code, room in list(self.rooms.items()):
            self.update_presence(room, now=current)
            offline_since = room.all_humans_offline_since
            if offline_since is not None and current - offline_since >= grace:
                self.rooms.pop(code, None)
                removed.append(code)
        return removed

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
        normalizer = getattr(engine, "room_options", None)
        if normalizer is None:
            return {}
        return normalizer(options)


ACTION_ERRORS = (ArcadeRoomError, GameRuleError, KeyError)
