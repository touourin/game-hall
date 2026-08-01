from backend.app.arcade.rooms import ArcadeRoomManager
from backend.app.games.avalon.rooms import RoomManager
from backend.app.games.registry import build_engine_registry
from backend.app.room_state import RedisRoomStateStore


class FakeRedis:
    def __init__(self) -> None:
        self.value: bytes | None = None

    async def get(self, _: str) -> bytes | None:
        return self.value

    async def set(self, _: str, value: bytes) -> None:
        self.value = value


async def test_room_state_round_trip_preserves_both_room_systems() -> None:
    avalon = RoomManager()
    avalon_room, _, _ = avalon.create_room("亚瑟", "account-a")
    arcade = ArcadeRoomManager(build_engine_registry())
    arcade_room, _, _ = arcade.create_room(
        "hanoi", "梅林", "account-b", {"discCount": 5}
    )
    fake_redis = FakeRedis()
    writer = RedisRoomStateStore(None)
    writer.client = fake_redis  # type: ignore[assignment]

    await writer.save(
        {"avalon": avalon.rooms, "arcade": arcade.rooms}
    )
    reader = RedisRoomStateStore(None)
    reader.client = fake_redis  # type: ignore[assignment]
    restored = await reader.load()

    assert restored is not None
    assert restored["avalon"][avalon_room.code].players[0].account_id == "account-a"
    assert restored["arcade"][arcade_room.code].options["discCount"] == 5
