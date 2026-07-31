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


def test_host_can_rename_another_player_during_a_game():
    manager = RoomManager()
    room, host, _ = manager.create_room("亚瑟")
    _, guest, _ = manager.join_room(room.code, "旧名字")
    message = manager.send_chat(room, guest.id, "我赞成")
    room.phase = Phase.TEAM_VOTING
    previous_revision = room.revision

    manager.rename_player(room, host.id, guest.id, "  新   名字  ")

    assert guest.name == "新 名字"
    assert message.sender_name == "新 名字"
    assert room.revision == previous_revision + 1


def test_rename_player_rejects_unauthorized_self_and_duplicate_names():
    manager = RoomManager()
    room, host, _ = manager.create_room("亚瑟")
    _, guest, _ = manager.join_room(room.code, "兰斯洛特")

    with pytest.raises(RoomError, match="只有房主"):
        manager.rename_player(room, guest.id, host.id, "新名字")
    with pytest.raises(RoomError, match="其他玩家"):
        manager.rename_player(room, host.id, host.id, "新名字")
    with pytest.raises(RoomError, match="同名"):
        manager.rename_player(room, host.id, guest.id, "亚瑟")
