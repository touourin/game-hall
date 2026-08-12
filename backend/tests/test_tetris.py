from __future__ import annotations

import pytest

from backend.app.arcade.models import ArcadePlayer, ArcadeRoom
from backend.app.games.base import GameRuleError
from backend.app.games.tetris import TetrisEngine


def make_room() -> tuple[TetrisEngine, ArcadeRoom, ArcadePlayer]:
    engine = TetrisEngine()
    player = ArcadePlayer(
        id="player-1",
        account_id="account-1",
        name="挑战者",
        token_hash="token",
        seat=0,
    )
    room = ArcadeRoom(
        code="DROP",
        game_key=engine.key,
        host_id=player.id,
        players=[player],
        state=engine.initial_state(),
        options={"challengeMode": "endless", "durationSeconds": 180},
    )
    engine.start(room)
    return engine, room, player


def test_tetris_accepts_a_plausible_finished_run() -> None:
    engine, room, player = make_room()

    engine.act(
        room,
        player,
        "finish",
        {
            "score": 12_480,
            "lines": 24,
            "level": 3,
            "pieces": 82,
            "elapsedMs": 184_000,
        },
    )

    assert room.phase == "finished"
    assert room.winner == "completed"
    assert engine.player_score(room, player) == 12_480
    assert engine.view(room, player) == {
        "challengeMode": "endless",
        "durationSeconds": 180,
        "score": 12_480,
        "lines": 24,
        "level": 3,
        "pieces": 82,
        "elapsedMs": 184_000,
    }
    assert engine.record_state(room)["lines"] == 24


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        ({"score": -1, "lines": 0, "level": 1, "pieces": 1, "elapsedMs": 1000}, "得分"),
        ({"score": 100, "lines": 10, "level": 1, "pieces": 10, "elapsedMs": 1000}, "等级"),
        ({"score": 100, "lines": 50, "level": 6, "pieces": 10, "elapsedMs": 1000}, "消行数"),
        ({"score": 50_000, "lines": 0, "level": 1, "pieces": 1, "elapsedMs": 1000}, "得分"),
    ],
)
def test_tetris_rejects_malformed_or_impossible_scores(payload, message) -> None:
    engine, room, player = make_room()

    with pytest.raises(GameRuleError, match=message):
        engine.act(room, player, "finish", payload)

    assert room.phase == "playing"


def test_tetris_is_a_private_single_player_room() -> None:
    engine = TetrisEngine()

    assert engine.min_players == 1
    assert engine.max_players == 1
    assert engine.public_rooms is False


def test_tetris_timed_mode_finishes_at_the_selected_duration() -> None:
    engine, room, player = make_room()
    room.options = engine.room_options(
        {"challengeMode": "timed", "durationSeconds": 60}
    )
    engine.start(room)

    engine.act(
        room,
        player,
        "finish",
        {
            "score": 4_200,
            "lines": 8,
            "level": 1,
            "pieces": 40,
            "elapsedMs": 60_000,
            "endReason": "timeout",
        },
    )

    assert room.phase == "finished"
    assert room.win_reason == "1 分钟限时结束 · 最终得分 4,200 · 消除 8 行"
    assert engine.record_state(room)["challenge_mode"] == "timed"


@pytest.mark.parametrize(
    "options",
    [
        {"challengeMode": "sprint", "durationSeconds": 180},
        {"challengeMode": "timed", "durationSeconds": 90},
    ],
)
def test_tetris_rejects_unknown_modes_and_durations(options) -> None:
    engine = TetrisEngine()

    with pytest.raises(GameRuleError):
        engine.room_options(options)


def test_tetris_rejects_an_invalid_timed_finish() -> None:
    engine, room, player = make_room()
    room.options = engine.room_options(
        {"challengeMode": "timed", "durationSeconds": 60}
    )
    engine.start(room)

    with pytest.raises(GameRuleError, match="用时"):
        engine.act(
            room,
            player,
            "finish",
            {
                "score": 4_200,
                "lines": 8,
                "level": 1,
                "pieces": 40,
                "elapsedMs": 59_000,
                "endReason": "timeout",
            },
        )
