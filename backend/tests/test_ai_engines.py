from __future__ import annotations

import asyncio
import sys
from unittest.mock import AsyncMock

import pytest

from backend.app.ai.katago import (
    DEFAULT_VISITS,
    KataGoAnalysisClient,
    KataGoBusyError,
)
from backend.app.ai.pikafish import PikafishClient
from backend.app.arcade.bots import ArcadeBotService, BotAction
from backend.app.arcade.rooms import ArcadeRoomManager
from backend.app.games.go import GoEngine
from backend.app.games.xiangqi import XiangqiEngine


class FakePikafish:
    def __init__(self, move: str = "a6a5") -> None:
        self.move = move
        self.calls: list[tuple[str, str]] = []

    async def best_move(self, fen: str, difficulty: str) -> str:
        self.calls.append((fen, difficulty))
        return self.move

    async def close(self) -> None:
        pass


class FakeKataGo:
    def __init__(self, move: str = "Q16") -> None:
        self.move = move
        self.calls: list[tuple[dict, str]] = []

    async def analyze(self, query: dict, difficulty: str) -> dict:
        self.calls.append((query, difficulty))
        return {"moveInfos": [{"move": self.move}]}

    async def close(self) -> None:
        pass


def _human_vs_bot(engine):
    manager = ArcadeRoomManager({engine.key: engine})
    room, host, _ = manager.create_room(
        engine.key,
        "房主",
        "account-host",
        {"firstPlayer": "host"},
    )
    manager.add_ai_player(room, host.id, difficulty="hard")
    manager.start(room, host.id)
    return manager, room, host, room.players[1]


async def test_xiangqi_adapter_translates_fen_and_uci_move() -> None:
    engine = XiangqiEngine()
    fake = FakePikafish()
    engine.bot_strategy.client = fake
    manager, room, host, bot = _human_vs_bot(engine)
    manager.act(
        room,
        host.id,
        "move",
        {"fromRow": 6, "fromColumn": 0, "toRow": 5, "toColumn": 0},
    )

    action = await engine.choose_bot_action_async(room)

    assert action == BotAction(
        bot.id,
        "move",
        {"fromRow": 3, "fromColumn": 0, "toRow": 4, "toColumn": 0},
    )
    fen, difficulty = fake.calls[0]
    assert fen.split()[1] == "b"
    assert difficulty == "hard"


async def test_go_adapter_sends_history_and_translates_gtp_move() -> None:
    engine = GoEngine()
    fake = FakeKataGo()
    engine.bot_strategy.client = fake
    manager, room, host, bot = _human_vs_bot(engine)
    manager.act(room, host.id, "place", {"row": 3, "column": 3})

    action = await engine.choose_bot_action_async(room)

    assert action == BotAction(bot.id, "place", {"row": 3, "column": 15})
    query, difficulty = fake.calls[0]
    assert query["moves"] == [["B", "D16"]]
    assert query["boardXSize"] == query["boardYSize"] == 19
    assert difficulty == "hard"


async def test_go_bot_passes_and_confirms_the_scoring_phase() -> None:
    engine = GoEngine()
    engine.bot_strategy.client = FakeKataGo("pass")
    manager, room, host, bot = _human_vs_bot(engine)
    manager.act(room, host.id, "pass", {})

    passed = await engine.choose_bot_action_async(room)
    assert passed == BotAction(bot.id, "pass")
    manager.apply_bot_action(room, passed)
    assert room.phase == "scoring"

    confirmation = await engine.choose_bot_action_async(room)
    assert confirmation == BotAction(bot.id, "confirm_score")
    manager.apply_bot_action(room, confirmation)
    assert room.state.score_confirmed_player_ids == [bot.id]


async def test_missing_external_engine_falls_back_to_legal_move() -> None:
    engine = XiangqiEngine()
    manager, room, host, bot = _human_vs_bot(engine)
    manager.act(
        room,
        host.id,
        "move",
        {"fromRow": 6, "fromColumn": 0, "toRow": 5, "toColumn": 0},
    )

    action = await ArcadeBotService().select_action(room, engine)

    assert action is not None
    assert action.player_id == bot.id
    manager.apply_bot_action(room, action)
    assert room.state.turn_color == "red"


async def test_pikafish_uci_process_is_reused(tmp_path) -> None:
    script = tmp_path / "fake_pikafish.py"
    script.write_text(
        """import sys
for line in sys.stdin:
    line = line.strip()
    if line == 'uci':
        print('id name FakePikafish', flush=True)
        print('uciok', flush=True)
    elif line == 'isready':
        print('readyok', flush=True)
    elif line.startswith('go '):
        print('bestmove a6a5', flush=True)
""",
        encoding="utf-8",
    )
    client = PikafishClient()
    client.process.command = (sys.executable, str(script))

    first = await client.best_move("9/9/9/9/9/9/9/9/9/9 w - - 0 1", "easy")
    process = client.process._process
    second = await client.best_move("9/9/9/9/9/9/9/9/9/9 b - - 0 1", "hard")

    assert first == second == "a6a5"
    assert client.process._process is process
    await client.close()


async def test_katago_json_process_is_reused(tmp_path) -> None:
    script = tmp_path / "fake_katago.py"
    script.write_text(
        """import json
import sys
for line in sys.stdin:
    request = json.loads(line)
    print(json.dumps({
        'id': request['id'],
        'moveInfos': [{'move': 'pass'}],
    }), flush=True)
""",
        encoding="utf-8",
    )
    client = KataGoAnalysisClient()
    client.process.command = (sys.executable, str(script))

    result = await client.analyze(
        {
            "rules": "chinese",
            "komi": 7.5,
            "boardXSize": 9,
            "boardYSize": 9,
            "moves": [],
        },
        "normal",
    )
    process = client.process._process
    again = await client.analyze(
        {
            "rules": "chinese",
            "komi": 7.5,
            "boardXSize": 9,
            "boardYSize": 9,
            "moves": [],
        },
        "normal",
    )

    assert result["moveInfos"][0]["move"] == "pass"
    assert again["moveInfos"][0]["move"] == "pass"
    assert client.process._process is process
    await client.close()


async def test_katago_routes_two_out_of_order_responses(tmp_path) -> None:
    script = tmp_path / "fake_parallel_katago.py"
    script.write_text(
        """import json
import sys

requests = []
for line in sys.stdin:
    request = json.loads(line)
    if request.get('action') == 'terminate':
        print(json.dumps(request), flush=True)
        continue
    requests.append(request)
    if len(requests) == 2:
        for pending in reversed(requests):
            print(json.dumps({
                'id': pending['id'],
                'maxVisits': pending['maxVisits'],
                'moveInfos': [{'move': 'pass'}],
            }), flush=True)
        requests.clear()
""",
        encoding="utf-8",
    )
    client = KataGoAnalysisClient(max_concurrent=2, max_queued=0)
    client.process.command = (sys.executable, str(script))
    query = {
        "rules": "chinese",
        "komi": 7.5,
        "boardXSize": 19,
        "boardYSize": 19,
        "moves": [],
    }

    easy, hard = await asyncio.gather(
        client.analyze(query, "easy"),
        client.analyze(query, "hard"),
    )

    assert easy["maxVisits"] == DEFAULT_VISITS["easy"] == 4
    assert hard["maxVisits"] == DEFAULT_VISITS["hard"] == 48
    await client.close()


async def test_katago_rejects_requests_beyond_bounded_queue(tmp_path) -> None:
    script = tmp_path / "fake_slow_katago.py"
    script.write_text(
        """import json
import sys
import time

for line in sys.stdin:
    request = json.loads(line)
    time.sleep(0.1)
    print(json.dumps({
        'id': request['id'],
        'moveInfos': [{'move': 'pass'}],
    }), flush=True)
""",
        encoding="utf-8",
    )
    client = KataGoAnalysisClient(max_concurrent=1, max_queued=0)
    client.process.command = (sys.executable, str(script))
    query = {
        "rules": "chinese",
        "komi": 7.5,
        "boardXSize": 9,
        "boardYSize": 9,
        "moves": [],
    }
    active = asyncio.create_task(client.analyze(query, "normal"))
    while client._outstanding == 0:
        await asyncio.sleep(0)

    with pytest.raises(KataGoBusyError, match="队列已满"):
        await client.analyze(query, "normal")

    await active
    await client.close()


async def test_katago_cancels_one_query_without_restarting_process(tmp_path) -> None:
    script = tmp_path / "fake_cancellable_katago.py"
    script.write_text(
        """import json
import sys

terminated = False
for line in sys.stdin:
    request = json.loads(line)
    if request.get('action') == 'terminate':
        terminated = True
        print(json.dumps(request), flush=True)
    elif terminated:
        print(json.dumps({
            'id': request['id'],
            'moveInfos': [{'move': 'pass'}],
        }), flush=True)
""",
        encoding="utf-8",
    )
    client = KataGoAnalysisClient(max_concurrent=1, max_queued=0)
    client.process.command = (sys.executable, str(script))
    query = {
        "rules": "chinese",
        "komi": 7.5,
        "boardXSize": 9,
        "boardYSize": 9,
        "moves": [],
    }
    cancelled = asyncio.create_task(client.analyze(query, "hard"))
    while not client._pending:
        await asyncio.sleep(0)
    await asyncio.sleep(0.01)
    process = client.process._process

    cancelled.cancel()
    with pytest.raises(asyncio.CancelledError):
        await cancelled
    result = await client.analyze(query, "easy")

    assert result["moveInfos"][0]["move"] == "pass"
    assert client.process._process is process
    await client.close()


async def test_katago_warm_up_uses_one_visit() -> None:
    client = KataGoAnalysisClient(
        executable="/fake/katago",
        model="/fake/model.bin.gz",
        config="/fake/analysis.cfg",
    )
    client.analyze = AsyncMock(return_value={"moveInfos": [{"move": "pass"}]})

    await client.warm_up()

    query, difficulty = client.analyze.await_args.args
    assert query["boardXSize"] == query["boardYSize"] == 9
    assert difficulty == "easy"
    assert client.analyze.await_args.kwargs == {"max_visits": 1}
    await client.close()
