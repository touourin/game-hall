from __future__ import annotations

import hashlib
import secrets
import string
from datetime import datetime, timezone

from .game.models import ChatMessage, GameSettings, Phase, Player, Room


class RoomError(ValueError):
    pass


ROOM_ALPHABET = "".join(
    character
    for character in string.ascii_uppercase + string.digits
    if character not in "0O1I"
)
MAX_CHAT_MESSAGES = 100
MAX_CHAT_LENGTH = 300


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


class RoomManager:
    def __init__(self) -> None:
        self.rooms: dict[str, Room] = {}

    def create_room(self, player_name: str) -> tuple[Room, Player, str]:
        name = self._normalize_name(player_name)
        code = self._new_code()
        token = secrets.token_urlsafe(32)
        player = Player(
            id=secrets.token_urlsafe(10),
            name=name,
            token_hash=hash_token(token),
            seat=0,
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
        self, code: str, player_name: str
    ) -> tuple[Room, Player, str]:
        room = self.get_room(code)
        if room.phase != Phase.LOBBY:
            raise RoomError("游戏已经开始，不能加入新玩家")
        if len(room.players) >= 10:
            raise RoomError("房间已经满员")

        name = self._normalize_name(player_name)
        if any(player.name.casefold() == name.casefold() for player in room.players):
            raise RoomError("房间里已经有同名玩家")

        token = secrets.token_urlsafe(32)
        player = Player(
            id=secrets.token_urlsafe(10),
            name=name,
            token_hash=hash_token(token),
            seat=len(room.players),
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

    def resume(self, code: str, token: str) -> tuple[Room, Player]:
        room = self.get_room(code)
        token_digest = hash_token(token)
        for player in room.players:
            if secrets.compare_digest(player.token_hash, token_digest):
                player.connected = True
                room.revision += 1
                return room, player
        raise RoomError("恢复凭证无效，请重新加入房间")

    def leave_lobby(self, room: Room, player_id: str) -> None:
        if room.phase != Phase.LOBBY:
            raise RoomError("游戏开始后不能退出座位，请等待本局结束")
        self._remove_player(room, player_id)
        if not room.players:
            self.rooms.pop(room.code, None)
            return
        if room.host_id == player_id:
            room.host_id = room.players[0].id
        room.revision += 1

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

    def rename_player(
        self, room: Room, actor_id: str, target_id: str, player_name: str
    ) -> None:
        if room.host_id != actor_id:
            raise RoomError("只有房主可以修改玩家名字")
        if target_id == actor_id:
            raise RoomError("房主只能修改其他玩家的名字")
        try:
            target = room.player(target_id)
        except KeyError as exc:
            raise RoomError("玩家不存在") from exc

        name = self._normalize_name(player_name)
        if any(
            player.id != target_id
            and player.name.casefold() == name.casefold()
            for player in room.players
        ):
            raise RoomError("房间里已经有同名玩家")

        target.name = name
        for message in room.chat_messages:
            if message.sender_id == target_id:
                message.sender_name = name
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
