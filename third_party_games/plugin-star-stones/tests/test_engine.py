from __future__ import annotations

from backend.app.arcade.models import ArcadePlayer, ArcadeRoom
from backend.app.games.plugins import discover_game_plugins, third_party_games_root


def engine():
    return next(
        plugin.engine
        for plugin in discover_game_plugins(third_party_games_root())
        if plugin.engine.key == "plugin-star-stones"
    )


def test_players_take_turns_and_last_stone_wins() -> None:
    game = engine()
    first = ArcadePlayer("p1", "a1", "玩家一", "token-1", 0)
    second = ArcadePlayer("p2", "a2", "玩家二", "token-2", 1)
    room = ArcadeRoom(
        "DUEL",
        game.key,
        first.id,
        [first, second],
        game.initial_state(),
        options={"firstPlayer": "host"},
    )

    game.start(room)
    assert room.state.current_player_id == first.id

    game.act(room, first, "take", {"count": 3})
    assert room.state.remaining == 12
    assert room.state.current_player_id == second.id

    room.state.remaining = 1
    room.state.current_player_id = second.id
    game.act(room, second, "take", {"count": 1})

    assert room.phase == "finished"
    assert room.winner_player_ids == [second.id]
