from __future__ import annotations

import hashlib
import logging
import secrets
import string
from datetime import datetime, timedelta, timezone

from .models import Alignment, ChatMessage, GameSettings, Phase, Player, Room


logger = logging.getLogger(__name__)


class RoomError(ValueError):
    pass


ROOM_ALPHABET = "".join(
    character
    for character in string.ascii_uppercase + string.digits
    if character not in "0O1I"
)
MAX_CHAT_MESSAGES = 100
MAX_CHAT_LENGTH = 300
ROOM_CLEANUP_GRACE = timedelta(minutes=10)
DISCONNECT_FORFEIT_GRACE = timedelta(minutes=10)
HOST_TRANSFER_GRACE = timedelta(seconds=20)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


class RoomManager:
    def __init__(self) -> None:
        self.rooms: dict[str, Room] = {}

    def create_room(
        self, player_name: str, account_id: str | None = None
    ) -> tuple[Room, Player, str]:
        name = self._normalize_name(player_name)
        code = self._new_code()
        token = secrets.token_urlsafe(32)
        player = Player(
            id=secrets.token_urlsafe(10),
            name=name,
            token_hash=hash_token(token),
            seat=0,
            account_id=account_id,
        )
        room = Room(
            code=code,
            host_id=player.id,
            players=[player],
            settings=GameSettings(lady_enabled=True),
        )
        self.rooms[code] = room
        return room, player, token

    def join_room(
        self,
        code: str,
        player_name: str,
        account_id: str | None = None,
    ) -> tuple[Room, Player, str]:
        room = self.get_room(code)
        if room.phase != Phase.LOBBY:
            raise RoomError("游戏已经开始，不能加入新玩家")
        if not any(
            not player.is_bot and player.connected
            for player in room.players
        ):
            raise RoomError("房间成员暂时都不在线，请等待原成员恢复房间")
        if len(room.players) >= 10:
            raise RoomError("房间已经满员")

        if account_id is not None and any(
            player.account_id == account_id for player in room.players
        ):
            raise RoomError("你的账号已经在这个房间中")

        name = self._normalize_name(player_name)
        if any(player.name.casefold() == name.casefold() for player in room.players):
            raise RoomError("房间里已经有同名玩家")

        token = secrets.token_urlsafe(32)
        player = Player(
            id=secrets.token_urlsafe(10),
            name=name,
            token_hash=hash_token(token),
            seat=len(room.players),
            account_id=account_id,
        )
        room.players.append(player)
        room.revision += 1
        return room, player, token

    def add_ai_player(self, room: Room, actor_id: str) -> Player:
        if room.phase != Phase.LOBBY:
            raise RoomError("只能在等待房间添加 AI 玩家")
        if room.host_id != actor_id:
            raise RoomError("只有房主可以添加 AI 玩家")
        if len(room.players) >= 10:
            raise RoomError("房间已经满员")

        existing_names = {player.name.casefold() for player in room.players}
        ai_number = 1
        while f"AI玩家 {ai_number}".casefold() in existing_names:
            ai_number += 1
        token = secrets.token_urlsafe(32)
        player = Player(
            id=f"bot-{secrets.token_urlsafe(8)}",
            name=f"AI玩家 {ai_number}",
            token_hash=hash_token(token),
            seat=len(room.players),
            is_bot=True,
        )
        room.players.append(player)
        room.revision += 1
        return player

    def resume(
        self, code: str, token: str, account_id: str | None = None
    ) -> tuple[Room, Player]:
        room = self.get_room(code)
        token_digest = hash_token(token)
        for player in room.players:
            if secrets.compare_digest(player.token_hash, token_digest):
                if account_id is not None and player.account_id != account_id:
                    raise RoomError("这个座位属于其他账号")
                player.connected = True
                self.update_human_presence(room)
                room.revision += 1
                return room, player
        raise RoomError("恢复凭证无效，请重新加入房间")

    def leave_lobby(self, room: Room, player_id: str) -> None:
        if room.phase != Phase.LOBBY:
            raise RoomError("游戏开始后不能退出座位，请等待本局结束")
        self._remove_player(room, player_id)
        if not any(not player.is_bot for player in room.players):
            self.rooms.pop(room.code, None)
            return
        if room.host_id == player_id:
            room.host_id = room.players[0].id
        room.revision += 1

    def update_human_presence(
        self, room: Room, *, now: datetime | None = None
    ) -> None:
        current = now or datetime.now(timezone.utc)
        was_all_offline = room.all_humans_offline_since is not None
        for player in room.players:
            if not hasattr(player, "disconnected_at"):
                player.disconnected_at = None
            if not hasattr(player, "disconnect_forfeited"):
                player.disconnect_forfeited = False
        connected_humans = [
            player
            for player in room.players
            if not player.is_bot and player.connected
        ]
        if connected_humans:
            room.all_humans_offline_since = None
            room.cleanup_ready = False
            for player in room.players:
                if player.is_bot:
                    continue
                if player.connected:
                    player.disconnected_at = None
                elif not player.disconnect_forfeited and (
                    was_all_offline or player.disconnected_at is None
                ):
                    player.disconnected_at = current
            host = room.player(room.host_id)
            transferable_phase = room.phase in {Phase.LOBBY, Phase.GAME_OVER}
            if (
                transferable_phase
                and not host.is_bot
                and not host.connected
                and any(player.id != host.id for player in connected_humans)
            ):
                if room.host_offline_since is None:
                    room.host_offline_since = current
            else:
                room.host_offline_since = None
            return
        room.host_offline_since = None
        for player in room.players:
            if not player.is_bot and not player.disconnect_forfeited:
                player.disconnected_at = None
        if room.all_humans_offline_since is None:
            room.all_humans_offline_since = current

    def maintain(
        self,
        *,
        now: datetime | None = None,
        cleanup_grace: timedelta = ROOM_CLEANUP_GRACE,
        disconnect_grace: timedelta = DISCONNECT_FORFEIT_GRACE,
        host_grace: timedelta = HOST_TRANSFER_GRACE,
    ) -> list[Room]:
        current = now or datetime.now(timezone.utc)
        changed: list[Room] = []
        for room in list(self.rooms.values()):
            self.update_human_presence(room, now=current)
            offline_since = room.all_humans_offline_since
            if (
                offline_since is not None
                and current - offline_since >= cleanup_grace
                and not room.cleanup_ready
            ):
                room.cleanup_ready = True
                room.revision += 1
                changed.append(room)
                logger.info(
                    "Avalon room became eligible for offline cleanup",
                    extra={
                        "event": "room.cleanup_ready",
                        "game_key": "avalon",
                        "room_code": room.code,
                    },
                )

            if (
                offline_since is None
                and room.phase not in {Phase.LOBBY, Phase.GAME_OVER}
            ):
                expired_players = sorted(
                    (
                        player
                        for player in room.players
                        if not player.is_bot
                        and not player.connected
                        and not player.disconnect_forfeited
                        and player.disconnected_at is not None
                        and current - player.disconnected_at >= disconnect_grace
                    ),
                    key=lambda player: (player.disconnected_at, player.seat),
                )
                if expired_players:
                    self._forfeit_disconnected_player(
                        room, expired_players[0]
                    )
                    if room not in changed:
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
                        if not player.is_bot
                        and player.connected
                        and player.id != room.host_id
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
    ) -> Room:
        current = now or datetime.now(timezone.utc)
        room = self.get_room(code)
        self.update_human_presence(room, now=current)
        if any(
            not player.is_bot and player.connected
            for player in room.players
        ):
            raise RoomError("已有玩家重新连接，不能清理这个房间")
        offline_since = room.all_humans_offline_since
        if offline_since is None or current - offline_since < grace:
            raise RoomError("房间全员离线满 10 分钟后才可以清理")
        self.rooms.pop(room.code, None)
        return room

    def kick_player(
        self, room: Room, actor_id: str, target_id: str
    ) -> None:
        if room.phase != Phase.LOBBY:
            raise RoomError("只能在等待房间移除玩家")
        if room.host_id != actor_id:
            raise RoomError("只有房主可以移除玩家")
        if target_id == actor_id:
            raise RoomError("房主不能移除自己")
        try:
            room.player(target_id)
        except KeyError as exc:
            raise RoomError("玩家不存在") from exc
        self._remove_player(room, target_id)
        room.revision += 1

    def dissolve_room(self, room: Room, actor_id: str) -> None:
        if room.phase != Phase.LOBBY:
            raise RoomError("游戏开始后不能直接解散房间")
        if room.host_id != actor_id:
            raise RoomError("只有房主可以解散房间")
        self.rooms.pop(room.code, None)

    def set_lady_enabled(
        self, room: Room, actor_id: str, enabled: bool
    ) -> None:
        if room.phase != Phase.LOBBY:
            raise RoomError("只能在等待房间修改规则")
        if room.host_id != actor_id:
            raise RoomError("只有房主可以修改规则")
        room.settings.lady_enabled = enabled
        room.revision += 1

    def set_listed(
        self, room: Room, actor_id: str, listed: bool
    ) -> None:
        if room.phase != Phase.LOBBY:
            raise RoomError("只能在等待房间修改展示状态")
        if room.host_id != actor_id:
            raise RoomError("只有房主可以修改展示状态")
        room.settings.listed = listed
        room.revision += 1

    def set_early_assassination_enabled(
        self, room: Room, actor_id: str, enabled: bool
    ) -> None:
        if room.phase != Phase.LOBBY:
            raise RoomError("只能在等待房间修改提前刺杀规则")
        if room.host_id != actor_id:
            raise RoomError("只有房主可以修改提前刺杀规则")
        room.settings.early_assassination_enabled = enabled
        room.revision += 1

    def send_chat(
        self, room: Room, player_id: str, content: str
    ) -> ChatMessage:
        player = room.player(player_id)
        normalized_content = " ".join(
            content.replace("\x00", "").strip().split()
        )
        if not normalized_content:
            raise RoomError("消息不能为空")
        if len(normalized_content) > MAX_CHAT_LENGTH:
            raise RoomError(f"消息最多 {MAX_CHAT_LENGTH} 个字符")

        message = ChatMessage(
            id=secrets.token_urlsafe(8),
            sender_id=player.id,
            sender_name=player.name,
            content=normalized_content,
            created_at=datetime.now(timezone.utc).isoformat(
                timespec="seconds"
            ),
        )
        room.chat_messages.append(message)
        if len(room.chat_messages) > MAX_CHAT_MESSAGES:
            room.chat_messages = room.chat_messages[-MAX_CHAT_MESSAGES:]
        room.revision += 1
        return message

    def get_room(self, code: str) -> Room:
        normalized_code = code.strip().upper()
        room = self.rooms.get(normalized_code)
        if room is None:
            raise RoomError("没有找到这个房间")
        return room

    @staticmethod
    def _forfeit_disconnected_player(room: Room, player: Player) -> None:
        if player.alignment is None:
            return
        winner = (
            Alignment.EVIL
            if player.alignment == Alignment.GOOD
            else Alignment.GOOD
        )
        player.disconnect_forfeited = True
        player.disconnected_at = None
        room.winner = winner
        room.win_reason = (
            f"{player.name} 掉线超过 10 分钟，所属阵营视为弃权"
        )
        room.phase = Phase.GAME_OVER
        room.revision += 1
        logger.info(
            "Avalon player forfeited after disconnect grace expired",
            extra={
                "action": "disconnect_timeout",
                "event": "room.disconnect_forfeit",
                "game_key": "avalon",
                "player_id": player.id,
                "room_code": room.code,
            },
        )

    def _new_code(self) -> str:
        for _ in range(100):
            code = "".join(secrets.choice(ROOM_ALPHABET) for _ in range(4))
            if code not in self.rooms:
                return code
        raise RoomError("暂时无法创建房间，请重试")

    @staticmethod
    def _remove_player(room: Room, player_id: str) -> None:
        room.players = [
            player for player in room.players if player.id != player_id
        ]
        for seat, player in enumerate(room.players):
            player.seat = seat

    @staticmethod
    def _normalize_name(player_name: str) -> str:
        name = " ".join(player_name.strip().split())
        if not name:
            raise RoomError("请输入昵称")
        if len(name) > 12:
            raise RoomError("昵称最多 12 个字符")
        return name
