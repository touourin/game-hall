from __future__ import annotations

import asyncio
import os
import random
import sys
from unittest.mock import AsyncMock

import pytest

from backend.app.ai.douzero import DouZeroClient
from backend.app.ai.douzero_models import (
    DouZeroModelError,
    require_model_paths,
    stage_model_bundle,
    write_checksum_manifest,
)
from backend.app.ai.douzero_worker import _configure_inference_environment
from backend.app.ai.katago import (
    DEFAULT_VISITS,
    KataGoAnalysisClient,
    KataGoBusyError,
)
from backend.app.ai.pikafish import PikafishClient
from backend.app.arcade.bots import ArcadeBotService, BotAction
from backend.app.arcade.rooms import ArcadeRoomError, ArcadeRoomManager
from backend.app.arcade.views import build_room_view
from backend.app.games.doudizhu import DoudizhuEngine
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


class FakeDouZero:
    configured = True

    def __init__(self, opening_value: float = 1.0) -> None:
        self.opening_value = opening_value
        self.action_calls: list[dict] = []
        self.opening_calls: list[list[dict]] = []

    async def best_action(self, infoset: dict) -> list[int]:
        self.action_calls.append(infoset)
        return next(
            (
                action
                for action in infoset["legalActions"]
                if action
            ),
            [],
        )

    async def opening_values(self, infosets: list[dict]) -> list[float]:
        self.opening_calls.append(infosets)
        return [self.opening_value] * len(infosets)

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


async def test_go_adapter_keeps_handicap_stones_with_move_history() -> None:
    engine = GoEngine()
    fake = FakeKataGo("pass")
    engine.bot_strategy.client = fake
    manager = ArcadeRoomManager({engine.key: engine})
    room, host, _ = manager.create_room(
        engine.key,
        "房主",
        "account-host",
        {
            "firstPlayer": "host",
            "handicap": 3,
            "handicapGiver": "host",
        },
    )
    manager.add_ai_player(room, host.id, difficulty="hard")
    manager.start(room, host.id)
    manager.act(room, host.id, "place", {"row": 9, "column": 9})

    await engine.choose_bot_action_async(room)

    query, _ = fake.calls[0]
    assert query["initialStones"] == [
        ["W", "D4"],
        ["W", "Q16"],
        ["W", "D16"],
    ]
    assert query["initialPlayer"] == "B"
    assert query["moves"] == [["B", "K10"]]


async def test_go_adapter_rebases_full_handicap_board_after_resuming() -> None:
    engine = GoEngine()
    fake = FakeKataGo("pass")
    engine.bot_strategy.client = fake
    manager = ArcadeRoomManager({engine.key: engine})
    room, host, _ = manager.create_room(
        engine.key,
        "房主",
        "account-host",
        {"handicap": 2, "handicapGiver": "host"},
    )
    manager.add_ai_player(room, host.id, difficulty="hard")
    manager.start(room, host.id)
    room.state.board[9][9] = 1
    room.state.move_history.clear()
    room.state.turn_seat = host.seat

    query = engine.bot_strategy._query(room)
    assert ["B", "K10"] in query["initialStones"]
    assert len(query["initialStones"]) == 3
    assert query["moves"] == []


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


async def test_doudizhu_adapter_builds_a_role_infoset_and_uses_model_move() -> None:
    engine = DoudizhuEngine()
    fake = FakeDouZero()
    engine.bot_strategy.client = fake
    manager = ArcadeRoomManager({engine.key: engine})
    room, host, _ = manager.create_room(
        engine.key,
        "房主",
        "account-host",
        {"firstPlayer": "host"},
    )
    first_bot = manager.add_ai_player(room, host.id, difficulty="douzero")
    manager.add_ai_player(room, host.id, difficulty="douzero")
    manager.start(room, host.id)
    manager.act(room, host.id, "bid", {"decision": "call"})
    manager.act(room, first_bot.id, "bid", {"decision": "pass"})
    second_bot = room.players[2]
    manager.act(room, second_bot.id, "bid", {"decision": "pass"})
    lead = min(room.state.hands[host.seat], key=lambda card: card.rank)
    manager.act(room, host.id, "play", {"cardIds": [lead.id]})

    action = await engine.choose_bot_action_async(room)

    assert action is not None
    assert action.player_id == first_bot.id
    assert action.action == "play"
    infoset = fake.action_calls[0]
    assert infoset["position"] == "landlord_down"
    assert infoset["cardPlayActionSeq"]
    assert infoset["lastPid"] == "landlord"
    assert infoset["numCardsLeftDict"]["landlord"] == 19
    manager.apply_bot_action(room, action)


@pytest.mark.parametrize("variant", ["classic", "no_shuffle"])
def test_doudizhu_douzero_seat_is_available_for_standard_rules(
    variant: str,
) -> None:
    engine = DoudizhuEngine()
    engine.bot_strategy.client = FakeDouZero()
    manager = ArcadeRoomManager({engine.key: engine})
    room, host, _ = manager.create_room(
        engine.key,
        "房主",
        "account-host",
        {"variant": variant},
    )

    view = build_room_view(room, host, engine)
    bot = manager.add_ai_player(room, host.id)

    assert view["actions"]["canAddAiPlayer"] is True
    assert view["ai"] == {
        "difficulties": [{"key": "douzero", "label": "DouZero"}],
        "defaultDifficulty": "douzero",
    }
    assert bot.bot_difficulty == "douzero"


@pytest.mark.parametrize(
    ("variant", "message"),
    [
        ("classic", "请先配置完整的 DouZero 模型"),
        ("laizi", "癞子玩法暂不支持 DouZero"),
    ],
)
def test_doudizhu_unavailable_ai_seat_is_hidden_and_rejected(
    variant: str,
    message: str,
) -> None:
    engine = DoudizhuEngine()
    if variant == "laizi":
        engine.bot_strategy.client = FakeDouZero()
    manager = ArcadeRoomManager({engine.key: engine})
    room, host, _ = manager.create_room(
        engine.key,
        "房主",
        "account-host",
        {"variant": variant},
    )

    view = build_room_view(room, host, engine)

    assert view["actions"]["canAddAiPlayer"] is False
    with pytest.raises(ArcadeRoomError, match=message):
        manager.add_ai_player(room, host.id)


def test_doudizhu_room_with_ai_cannot_switch_to_laizi() -> None:
    engine = DoudizhuEngine()
    engine.bot_strategy.client = FakeDouZero()
    manager = ArcadeRoomManager({engine.key: engine})
    room, host, _ = manager.create_room(
        engine.key,
        "房主",
        "account-host",
        {"variant": "classic"},
    )
    manager.add_ai_player(room, host.id)
    manager.update_options(room, host.id, {"variant": "no_shuffle"})

    assert room.options["variant"] == "no_shuffle"

    with pytest.raises(ArcadeRoomError, match="癞子玩法暂不支持 DouZero"):
        manager.update_options(room, host.id, {"variant": "laizi"})

    assert room.options["variant"] == "no_shuffle"


async def test_doudizhu_bidding_samples_hidden_bottoms_for_model_values() -> None:
    engine = DoudizhuEngine(random.Random(11))
    fake = FakeDouZero(opening_value=1.0)
    engine.bot_strategy.client = fake
    engine.bot_strategy.bid_samples = 8
    manager = ArcadeRoomManager({engine.key: engine})
    room, host, _ = manager.create_room(
        engine.key,
        "房主",
        "account-host",
        {"firstPlayer": "host"},
    )
    bot = manager.add_ai_player(room, host.id)
    manager.add_ai_player(room, host.id)
    manager.start(room, host.id)
    manager.act(room, host.id, "bid", {"decision": "pass"})

    action = await engine.choose_bot_action_async(room)

    assert action == BotAction(bot.id, "bid", {"decision": "call"})
    infosets = fake.opening_calls[0]
    assert len(infosets) == 8
    assert all(len(infoset["playerHandCards"]) == 20 for infoset in infosets)
    assert all(len(infoset["otherHandCards"]) == 34 for infoset in infosets)
    assert all(len(infoset["threeLandlordCards"]) == 3 for infoset in infosets)
    assert all(infoset["position"] == "landlord" for infoset in infosets)
    assert len(
        {tuple(infoset["threeLandlordCards"]) for infoset in infosets}
    ) > 1


@pytest.mark.parametrize("variant", ["classic", "no_shuffle"])
async def test_doudizhu_douzero_bots_finish_supported_variants(
    variant: str,
) -> None:
    engine = DoudizhuEngine()
    engine.bot_strategy.client = FakeDouZero()
    engine.bot_strategy.bid_samples = 2
    manager = ArcadeRoomManager({engine.key: engine})
    room, host, _ = manager.create_room(
        engine.key,
        "房主",
        "account-host",
        {"firstPlayer": "host", "variant": variant},
    )
    manager.add_ai_player(room, host.id)
    manager.add_ai_player(room, host.id)
    manager.start(room, host.id)
    host.is_bot = True
    host.bot_difficulty = "douzero"

    for _ in range(300):
        if room.phase == "finished":
            break
        action = await engine.choose_bot_action_async(room)
        assert action is not None
        manager.apply_bot_action(room, action)

    assert room.phase == "finished"
    assert room.winner in {"landlord", "farmers"}


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


async def test_douzero_json_process_is_reused(tmp_path) -> None:
    script = tmp_path / "fake_douzero.py"
    script.write_text(
        """import json
import sys
for line in sys.stdin:
    request = json.loads(line)
    if request['type'] == 'ping':
        response = {'ready': True}
    elif request['type'] == 'act':
        actions = request['infoset']['legalActions']
        response = {'action': actions[0]}
    else:
        response = {'values': [0.25] * len(request['infosets'])}
    print(json.dumps(response), flush=True)
""",
        encoding="utf-8",
    )
    client = DouZeroClient()
    client.process.command = (sys.executable, str(script))
    infoset = {"legalActions": [[3], []]}

    assert client.available is False
    await client.warm_up()
    first = await client.best_action(infoset)
    process = client.process._process
    values = await client.opening_values([infoset, infoset])
    second = await client.best_action(infoset)

    assert first == second == [3]
    assert values == [0.25, 0.25]
    assert client.available is True
    assert client.process._process is process
    await client.close()


def test_douzero_requires_all_three_role_models(tmp_path) -> None:
    for filename in ("landlord.ckpt", "landlord_up.ckpt"):
        (tmp_path / filename).write_bytes(b"model")
    incomplete = DouZeroClient(model_dir=str(tmp_path))
    assert incomplete.configured is False

    (tmp_path / "landlord_down.ckpt").write_bytes(b"model")
    complete = DouZeroClient(model_dir=str(tmp_path), threads=2)

    assert complete.configured is True
    assert complete.available is False
    assert complete.process.command is not None
    assert complete.process.command[-1] == "2"

    with pytest.raises(ValueError, match="必须大于零"):
        DouZeroClient(model_dir=str(tmp_path), threads=0)


def test_douzero_model_manifest_detects_changed_weights(tmp_path) -> None:
    filenames = ("landlord.ckpt", "landlord_up.ckpt", "landlord_down.ckpt")
    for index, filename in enumerate(filenames):
        (tmp_path / filename).write_bytes(f"model-{index}".encode())

    manifest = write_checksum_manifest(tmp_path)

    assert manifest.name == "SHA256SUMS"
    assert set(require_model_paths(tmp_path)) == {
        "landlord",
        "landlord_up",
        "landlord_down",
    }
    output = tmp_path / "bundle"
    stage_model_bundle(tmp_path, output)
    assert {path.name for path in output.iterdir()} == {
        "landlord.ckpt",
        "landlord_up.ckpt",
        "landlord_down.ckpt",
        "SHA256SUMS",
    }

    (tmp_path / "landlord.ckpt").write_bytes(b"changed")
    with pytest.raises(DouZeroModelError, match="landlord.ckpt"):
        require_model_paths(tmp_path)
    assert DouZeroClient(model_dir=str(tmp_path)).configured is False


def test_douzero_inference_does_not_require_a_git_executable(
    monkeypatch,
) -> None:
    monkeypatch.delenv("CUDA_VISIBLE_DEVICES", raising=False)
    monkeypatch.delenv("GIT_PYTHON_REFRESH", raising=False)

    _configure_inference_environment()

    assert os.environ["CUDA_VISIBLE_DEVICES"] == ""
    assert os.environ["GIT_PYTHON_REFRESH"] == "quiet"


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
