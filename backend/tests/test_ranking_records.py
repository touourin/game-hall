from __future__ import annotations

from types import SimpleNamespace

import pytest

import backend.app.accounts as accounts_module
import backend.app.arcade.realtime as realtime_module
from backend.app.accounts import AccountStore
from backend.app.arcade.models import ArcadePlayer, ArcadeRoom
from backend.app.arcade.realtime import ArcadeRealtime
from backend.app.games.definition import GameRecords


GAME_KEY = "plugin-ranking-test"


@pytest.fixture
def ranking_store(tmp_path, monkeypatch):
    original_registration = accounts_module.game_registration
    definition = SimpleNamespace(records=GameRecords(score_kind="ranking"))
    monkeypatch.setattr(accounts_module, "game_registration", lambda key: definition if key == GAME_KEY else original_registration(key))
    monkeypatch.setattr(accounts_module, "GAME_NAMES", {**accounts_module.GAME_NAMES, GAME_KEY: "名次积分测试"})
    monkeypatch.setattr(accounts_module, "SCORED_GAME_KEYS", accounts_module.SCORED_GAME_KEYS | {GAME_KEY})
    store = AccountStore(tmp_path / "ranking.sqlite3")
    accounts = [store.register(f"ranking_{i}", "test-pass-123", f"玩家{i + 1}")[0] for i in range(4)]
    yield store, accounts
    store.dispose()


def record(store, accounts, match_id, points, *, ranked=True):
    return store.record_game_match(
        game_key=GAME_KEY, match_id=match_id, room_code="RANK", winner="player", reason="四人名次结算",
        started_at="2026-08-31T01:00:00+00:00", ended_at="2026-08-31T01:30:00+00:00",
        details={"players": []}, ranked=ranked,
        players=[{
            "accountId": account.id, "playerName": account.player_name, "seat": seat,
            "role": f"第 {3 - score} 名", "alignment": "ranking", "won": score == 2,
            "isHost": seat == 0, "scoreValue": score,
        } for seat, (account, score) in enumerate(zip(accounts, points, strict=True))],
    )


def test_ranking_preserves_zero_negative_points_and_win_outcomes(ranking_store):
    store, accounts = ranking_store
    assert record(store, accounts, "one", [2, 1, 0, -1]) is True
    for index, score in enumerate((2, 1, 0, -1)):
        summary = store.summary_for_account(accounts[index].id, game_key=GAME_KEY)
        history = store.history_for_account(accounts[index].id, game_key=GAME_KEY)
        assert summary["totalPoints"] == score
        assert summary["games"] == 1
        assert summary["wins"] == (index == 0)
        assert history[0]["scoreValue"] == score
        assert history[0]["scoreMs"] is None
        assert history[0]["role"] == f"第 {index + 1} 名"
        assert history[0]["outcome"] == ("win" if index == 0 else "loss")


def test_leaderboard_accumulates_points_before_wins_and_ignores_duplicate_and_unranked_matches(ranking_store):
    store, accounts = ranking_store
    assert record(store, accounts, "one", [2, 1, 0, -1])
    assert record(store, accounts, "two", [-1, 1, 2, 0])
    assert record(store, accounts, "two", [-1, 1, 2, 0]) is False
    assert record(store, accounts, "practice", [2, 1, 0, -1], ranked=False)
    leaderboard = store.leaderboard(game_key=GAME_KEY)
    assert [row["accountId"] for row in leaderboard] == [accounts[i].id for i in (2, 1, 0, 3)]
    assert [row["totalPoints"] for row in leaderboard] == [2, 2, 1, -1]
    assert [row["games"] for row in leaderboard] == [2, 2, 2, 2]
    assert [row["wins"] for row in leaderboard] == [1, 0, 1, 0]
    assert len(store.leaderboard(game_key=GAME_KEY, limit=1)) == 1
    assert store.leaderboard(game_key="gomoku") == []
    assert store.summary_for_account(accounts[3].id, game_key=GAME_KEY)["totalPoints"] == -2


def test_empty_ranking_summary_has_zero_total(ranking_store):
    store, accounts = ranking_store
    summary = store.summary_for_account(accounts[0].id, game_key=GAME_KEY)
    assert summary["totalPoints"] == 0
    assert summary["games"] == 0
    assert store.leaderboard(game_key=GAME_KEY) == []


def test_overall_competitive_summary_counts_ranking_games_without_mixing_points(ranking_store):
    store, accounts = ranking_store
    record(store, accounts, "one", [2, 1, 0, -1])
    record(store, accounts, "two", [-1, 1, 2, 0])
    summary = store.summary_for_account(accounts[0].id)
    assert summary["games"] == 2
    assert summary["wins"] == summary["losses"] == 1
    assert "totalPoints" not in summary


def test_realtime_persists_engine_scores_and_public_detail_without_double_counting(ranking_store, monkeypatch):
    store, accounts = ranking_store
    points = (2, 1, 0, -1)

    class RankingEngine:
        name = "名次积分测试"

        def player_result(self, room, player):
            return f"第 {player.seat + 1} 名", "ranking", player.seat == 0

        def player_score(self, room, player):
            return points[player.seat]

    runtime = ArcadeRealtime()
    runtime.engines[GAME_KEY] = RankingEngine()
    monkeypatch.setattr(realtime_module, "account_store", lambda: store)
    players = [ArcadePlayer(f"p{i}", account.id, account.player_name, "t", i) for i, account in enumerate(accounts)]
    room = ArcadeRoom(
        "RANK", GAME_KEY, players[0].id, players, {}, game_id="from-runtime",
        started_at="2026-08-31T01:00:00+00:00",
    )
    room.finish("player", [players[0].id], "名次结算")
    runtime._record_room(room)
    runtime._record_room(room)
    assert room.recorded is True
    assert [row["totalPoints"] for row in store.leaderboard(game_key=GAME_KEY)] == [2, 1, 0, -1]
    detail = store.match_for_account("from-runtime", accounts[3].id)
    assert [player["scoreValue"] for player in detail["details"]["players"]] == [2, 1, 0, -1]
    assert store.summary_for_account(accounts[3].id, game_key=GAME_KEY)["games"] == 1


def test_guest_round_does_not_persist_ranking_points(ranking_store, monkeypatch):
    store, accounts = ranking_store
    runtime = ArcadeRealtime()
    monkeypatch.setattr(realtime_module, "account_store", lambda: store)
    players = [ArcadePlayer("p0", accounts[0].id, "游客对局", "t", 0)]
    room = ArcadeRoom(
        "RANK", GAME_KEY, players[0].id, players, {}, game_id="guest-round",
        started_at="2026-08-31T01:00:00+00:00", stats_eligible=False,
    )
    room.finish("player", [players[0].id], "游客局结束")
    runtime._record_room(room)
    assert room.recorded is True
    assert store.leaderboard(game_key=GAME_KEY) == []
