from __future__ import annotations

from backend.app.arcade.models import ArcadePlayer, ArcadeRoom
from backend.app.games.plugins import discover_game_plugins, third_party_games_root


def engine():
    return next(
        plugin.engine
        for plugin in discover_game_plugins(third_party_games_root())
        if plugin.engine.key == "plugin-number-vault"
    )


def test_secret_stays_hidden_until_the_challenge_finishes() -> None:
    game = engine()
    player = ArcadePlayer("p1", "a1", "玩家一", "token", 0)
    room = ArcadeRoom("SOLO", game.key, player.id, [player], game.initial_state())

    game.start(room)
    secret = room.state.secret

    assert game.view(room, player)["answer"] is None
    game.act(room, player, "guess", {"value": secret})
    view = game.view(room, player)

    assert room.phase == "finished"
    assert view["answer"] == secret
    assert view["won"] is True
