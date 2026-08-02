from datetime import datetime, timedelta, timezone

import pytest

from backend.app.games.avalon.engine import GameEngine
from backend.app.games.avalon.models import Alignment, AvalonMode, Phase
from backend.app.games.avalon.rooms import RoomError, RoomManager


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


def test_only_host_can_dissolve_a_waiting_room():
    manager = RoomManager()
    room, host, _ = manager.create_room("亚瑟")
    _, guest, _ = manager.join_room(room.code, "兰斯洛特")

    with pytest.raises(RoomError, match="只有房主"):
        manager.dissolve_room(room, guest.id)

    room.phase = Phase.ROLE_REVEAL
    with pytest.raises(RoomError, match="游戏开始后"):
        manager.dissolve_room(room, host.id)

    room.phase = Phase.LOBBY
    manager.dissolve_room(room, host.id)

    assert room.code not in manager.rooms


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


def test_all_offline_humans_become_manually_cleanable_after_ten_minutes():
    manager = RoomManager()
    room, host, _ = manager.create_room("亚瑟")
    manager.add_ai_player(room, host.id)
    disconnected_at = datetime(2026, 8, 1, tzinfo=timezone.utc)
    host.connected = False

    manager.update_human_presence(room, now=disconnected_at)

    assert manager.maintain(
        now=disconnected_at + timedelta(minutes=9, seconds=59)
    ) == []
    assert manager.maintain(
        now=disconnected_at + timedelta(minutes=10)
    ) == [room]
    assert room.cleanup_ready is True
    assert room.code in manager.rooms

    removed = manager.cleanup_room(
        room.code,
        now=disconnected_at + timedelta(minutes=10),
    )

    assert removed is room
    assert room.code not in manager.rooms


def test_avalon_partial_disconnect_forfeits_players_alignment_after_ten_minutes():
    manager = RoomManager()
    engine = GameEngine()
    room, host, _ = manager.create_room("玩家1")
    for index in range(2, 6):
        manager.join_room(room.code, f"玩家{index}")
    engine.start_game(room, host.id)
    disconnected = room.players[1]
    disconnected_alignment = disconnected.alignment
    disconnected_at = datetime(2026, 8, 1, tzinfo=timezone.utc)
    disconnected.connected = False
    manager.update_human_presence(room, now=disconnected_at)

    assert manager.maintain(
        now=disconnected_at + timedelta(minutes=9, seconds=59)
    ) == []
    assert manager.maintain(
        now=disconnected_at + timedelta(minutes=10)
    ) == [room]

    assert room.phase == Phase.GAME_OVER
    assert room.winner == (
        Alignment.EVIL
        if disconnected_alignment == Alignment.GOOD
        else Alignment.GOOD
    )
    assert disconnected.disconnect_forfeited is True
    assert "掉线超过 10 分钟" in (room.win_reason or "")


def test_avalon_all_offline_never_creates_a_winner_before_cleanup():
    manager = RoomManager()
    engine = GameEngine()
    room, host, _ = manager.create_room("玩家1")
    for index in range(2, 6):
        manager.join_room(room.code, f"玩家{index}")
    engine.start_game(room, host.id)
    disconnected_at = datetime(2026, 8, 1, tzinfo=timezone.utc)
    for player in room.players:
        player.connected = False
    manager.update_human_presence(room, now=disconnected_at)

    assert manager.maintain(
        now=disconnected_at + timedelta(minutes=10)
    ) == [room]
    assert room.phase == Phase.ROLE_REVEAL
    assert room.winner is None
    assert room.cleanup_ready is True


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
    assert manager.maintain(
        now=disconnected_at + timedelta(minutes=10)
    ) == []


def test_room_cleanup_is_rejected_before_grace_or_after_reconnect():
    manager = RoomManager()
    room, host, _ = manager.create_room("亚瑟")
    disconnected_at = datetime(2026, 8, 1, tzinfo=timezone.utc)
    host.connected = False
    manager.update_human_presence(room, now=disconnected_at)

    with pytest.raises(RoomError, match="10 分钟"):
        manager.cleanup_room(
            room.code,
            now=disconnected_at + timedelta(minutes=9),
        )

    host.connected = True
    with pytest.raises(RoomError, match="重新连接"):
        manager.cleanup_room(
            room.code,
            now=disconnected_at + timedelta(minutes=11),
        )


def test_offline_lobby_does_not_accept_new_players():
    manager = RoomManager()
    room, host, _ = manager.create_room("亚瑟")
    host.connected = False

    with pytest.raises(RoomError, match="原成员恢复"):
        manager.join_room(room.code, "兰斯洛特")


def test_offline_host_transfers_after_twenty_seconds():
    manager = RoomManager()
    room, host, _ = manager.create_room("亚瑟")
    _, first_guest, _ = manager.join_room(room.code, "兰斯洛特")
    _, second_guest, _ = manager.join_room(room.code, "梅林")
    disconnected_at = datetime(2026, 8, 1, tzinfo=timezone.utc)
    host.connected = False
    manager.update_human_presence(room, now=disconnected_at)

    assert manager.maintain(
        now=disconnected_at + timedelta(seconds=19)
    ) == []
    assert room.host_id == host.id
    assert manager.maintain(
        now=disconnected_at + timedelta(seconds=20)
    ) == [room]
    assert room.host_id == first_guest.id
    assert room.host_id != second_guest.id


def test_host_is_not_transferred_during_an_active_game_or_when_all_offline():
    manager = RoomManager()
    room, host, _ = manager.create_room("亚瑟")
    _, guest, _ = manager.join_room(room.code, "兰斯洛特")
    disconnected_at = datetime(2026, 8, 1, tzinfo=timezone.utc)
    room.phase = Phase.ROLE_REVEAL
    host.connected = False
    manager.update_human_presence(room, now=disconnected_at)

    assert manager.maintain(
        now=disconnected_at + timedelta(minutes=1)
    ) == []
    assert room.host_id == host.id

    room.phase = Phase.LOBBY
    guest.connected = False
    manager.update_human_presence(room, now=disconnected_at)
    assert manager.maintain(
        now=disconnected_at + timedelta(minutes=1)
    ) == []
    assert room.host_id == host.id


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


def test_court_undercurrent_mode_disables_incompatible_house_rules():
    manager = RoomManager()
    room, host, _ = manager.create_room("亚瑟")
    _, guest, _ = manager.join_room(room.code, "兰斯洛特")
    manager.set_early_assassination_enabled(room, host.id, True)

    manager.set_mode(room, host.id, AvalonMode.COURT_UNDERCURRENT)

    assert room.settings.mode == AvalonMode.COURT_UNDERCURRENT
    assert room.settings.lady_enabled is False
    assert room.settings.early_assassination_enabled is False
    with pytest.raises(RoomError, match="湖中仙女"):
        manager.set_lady_enabled(room, host.id, True)
    with pytest.raises(RoomError, match="提前刺杀"):
        manager.set_early_assassination_enabled(room, host.id, True)
    with pytest.raises(RoomError, match="只有房主"):
        manager.set_mode(room, guest.id, AvalonMode.STANDARD)
