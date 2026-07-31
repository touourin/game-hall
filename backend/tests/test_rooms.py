from datetime import datetime, timedelta, timezone

import pytest

from backend.app.game.models import Phase
from backend.app.rooms import RoomError, RoomManager


def test_create_join_and_resume_room():
    manager = RoomManager()
    room, host, host_token = manager.create_room("亚瑟")
    _, player, player_token = manager.join_room(room.code, "桂妮维亚")

    resumed_room, resumed_player = manager.resume(room.code, player_token)

    assert resumed_room is room
    assert resumed_player.id == player.id
    assert host_token != player_token
    assert room.host_id == host.id


def test_resume_token_cannot_be_used_by_another_account():
    manager = RoomManager()
    room, _, token = manager.create_room("亚瑟", account_id="account-a")

    with pytest.raises(RoomError, match="其他账号"):
        manager.resume(room.code, token, account_id="account-b")

    _, player = manager.resume(room.code, token, account_id="account-a")
    assert player.account_id == "account-a"


def test_duplicate_name_is_rejected():
    manager = RoomManager()
    room, _, _ = manager.create_room("梅林")

    with pytest.raises(RoomError, match="同名"):
        manager.join_room(room.code, "梅林")


def test_host_can_remove_player_from_lobby():
    manager = RoomManager()
    room, host, _ = manager.create_room("亚瑟")
    _, player, _ = manager.join_room(room.code, "兰斯洛特")

    manager.kick_player(room, host.id, player.id)

    assert [current.id for current in room.players] == [host.id]


def test_host_can_add_and_remove_ai_players_from_lobby():
    manager = RoomManager()
    room, host, _ = manager.create_room("亚瑟")

    first_ai = manager.add_ai_player(room, host.id)
    second_ai = manager.add_ai_player(room, host.id)

    assert first_ai.is_bot is True
    assert first_ai.connected is True
    assert first_ai.seat == 1
    assert first_ai.name == "AI玩家 1"
    assert second_ai.seat == 2
    assert second_ai.name == "AI玩家 2"

    manager.kick_player(room, host.id, first_ai.id)
    assert [player.seat for player in room.players] == [0, 1]
    assert second_ai in room.players


def test_room_with_only_ai_players_is_removed_when_last_human_leaves():
    manager = RoomManager()
    room, host, _ = manager.create_room("亚瑟")
    manager.add_ai_player(room, host.id)

    manager.leave_lobby(room, host.id)

    assert room.code not in manager.rooms


def test_all_offline_humans_start_grace_period_before_room_cleanup():
    manager = RoomManager()
    room, host, _ = manager.create_room("亚瑟")
    manager.add_ai_player(room, host.id)
    disconnected_at = datetime(2026, 8, 1, tzinfo=timezone.utc)
    host.connected = False

    manager.update_human_presence(room, now=disconnected_at)

    assert manager.cleanup_abandoned(
        now=disconnected_at + timedelta(minutes=4, seconds=59)
    ) == []
    assert manager.cleanup_abandoned(
        now=disconnected_at + timedelta(minutes=5)
    ) == [room.code]
    assert room.code not in manager.rooms


def test_human_reconnect_cancels_abandoned_room_cleanup():
    manager = RoomManager()
    room, host, _ = manager.create_room("亚瑟")
    disconnected_at = datetime(2026, 8, 1, tzinfo=timezone.utc)
    host.connected = False
    manager.update_human_presence(room, now=disconnected_at)
    host.connected = True

    manager.update_human_presence(
        room, now=disconnected_at + timedelta(minutes=3)
    )

    assert room.all_humans_offline_since is None
    assert manager.cleanup_abandoned(
        now=disconnected_at + timedelta(minutes=10)
    ) == []


def test_only_host_can_add_ai_players_and_only_in_lobby():
    manager = RoomManager()
    room, host, _ = manager.create_room("亚瑟")
    _, guest, _ = manager.join_room(room.code, "兰斯洛特")

    with pytest.raises(RoomError, match="只有房主"):
        manager.add_ai_player(room, guest.id)

    room.phase = Phase.ROLE_REVEAL
    with pytest.raises(RoomError, match="等待房间"):
        manager.add_ai_player(room, host.id)


def test_chat_message_is_normalized_and_history_is_bounded():
    manager = RoomManager()
    room, host, _ = manager.create_room("亚瑟")

    message = manager.send_chat(room, host.id, "  第一轮   我赞成  ")

    assert message.sender_id == host.id
    assert message.sender_name == "亚瑟"
    assert message.content == "第一轮 我赞成"
    assert message.created_at.endswith("+00:00")

    for index in range(105):
        manager.send_chat(room, host.id, f"消息 {index}")

    assert len(room.chat_messages) == 100
    assert room.chat_messages[0].content == "消息 5"


def test_chat_rejects_empty_and_oversized_messages():
    manager = RoomManager()
    room, host, _ = manager.create_room("亚瑟")

    with pytest.raises(RoomError, match="不能为空"):
        manager.send_chat(room, host.id, "   ")

    with pytest.raises(RoomError, match="最多"):
        manager.send_chat(room, host.id, "密" * 301)


def test_host_controls_lobby_listing():
    manager = RoomManager()
    room, host, _ = manager.create_room("亚瑟")
    _, guest, _ = manager.join_room(room.code, "兰斯洛特")

    manager.set_listed(room, host.id, False)
    assert room.settings.listed is False

    with pytest.raises(RoomError, match="只有房主"):
        manager.set_listed(room, guest.id, True)


def test_host_controls_early_assassination_house_rule():
    manager = RoomManager()
    room, host, _ = manager.create_room("亚瑟")
    _, guest, _ = manager.join_room(room.code, "兰斯洛特")

    manager.set_early_assassination_enabled(room, host.id, True)
    assert room.settings.early_assassination_enabled is True

    with pytest.raises(RoomError, match="只有房主"):
        manager.set_early_assassination_enabled(room, guest.id, False)
