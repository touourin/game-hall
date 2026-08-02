from backend.app.arcade.rooms import ArcadeRoomManager
from backend.app.games.registry import build_engine_registry
from backend.app.room_state import RedisRoomStateStore


class FakeRedis:
    def __init__(self) -> None:
        self.value: bytes | None = None

    async def get(self, _: str) -> bytes | None:
        return self.value

    async def set(self, _: str, value: bytes) -> None:
        self.value = value


async def test_room_state_round_trip_preserves_unified_game_rooms() -> None:
    arcade = ArcadeRoomManager(build_engine_registry())
    avalon_room, _, _ = arcade.create_room(
        "avalon", "亚瑟", "account-a"
    )
    arcade_room, _, _ = arcade.create_room(
        "hanoi", "梅林", "account-b", {"discCount": 5}
    )
    fake_redis = FakeRedis()
    writer = RedisRoomStateStore(None)
    writer.client = fake_redis  # type: ignore[assignment]

    await writer.save({"arcade": arcade.rooms})
    reader = RedisRoomStateStore(None)
    reader.client = fake_redis  # type: ignore[assignment]
    restored = await reader.load()

    assert restored is not None
    assert restored["arcade"][avalon_room.code].game_key == "avalon"
    assert restored["arcade"][avalon_room.code].players[0].account_id == "account-a"
    assert restored["arcade"][arcade_room.code].options["discCount"] == 5
