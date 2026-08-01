import pytest

from backend.app.accounts import AccountError, AccountStore
from backend.app.games.avalon.models import Alignment, Phase, Role

from .test_engine import start_room


def account_for_player(store: AccountStore, index: int, prefix: str):
    account, _ = store.register(
        f"{prefix}_{index}", "secret123", f"{prefix}{index}"
    )
    return account


def test_username_stays_stable_when_game_nickname_changes(tmp_path):
    store = AccountStore(tmp_path / "rename.sqlite3")
    account, _ = store.register("zhangsan", "secret123", "张三玩家")

    renamed = store.rename_player(account.id, "王五玩家")
    logged_in, _ = store.login("zhangsan", "secret123")

    assert renamed.id == account.id
    assert renamed.username == "zhangsan"
    assert renamed.player_name == "王五玩家"
    assert logged_in.player_name == "王五玩家"


def test_old_game_nickname_remains_reserved_for_its_account(tmp_path):
    store = AccountStore(tmp_path / "reserved-name.sqlite3")
    first, _ = store.register("account_one", "secret123", "张三玩家")
    second, _ = store.register("account_two", "secret123", "李四玩家")

    store.rename_player(first.id, "王五玩家")

    with pytest.raises(AccountError, match="归其他账号所有"):
        store.rename_player(second.id, "张三玩家")


def test_game_nickname_can_only_change_once_every_thirty_days(tmp_path):
    store = AccountStore(tmp_path / "rename-limit.sqlite3")
    account, _ = store.register("rename_user", "secret123", "初始昵称")

    store.rename_player(account.id, "第一次改名")

    with pytest.raises(AccountError, match="每 30 天只能改名一次"):
        store.rename_player(account.id, "第二次改名")


def completed_room_with_accounts(
    store: AccountStore, player_count: int = 5, prefix: str = "player"
):
    engine, room = start_room(player_count)
    for index, player in enumerate(room.players):
        player.account_id = account_for_player(store, index, prefix).id
    assassin = next(
        player for player in room.players if player.role == Role.ASSASSIN
    )
    merlin = next(player for player in room.players if player.role == Role.MERLIN)
    room.phase = Phase.ASSASSINATION
    engine.assassinate(room, assassin.id, merlin.id)
    return room


def test_completed_match_is_saved_once_with_personal_history(tmp_path):
    store = AccountStore(tmp_path / "stats.sqlite3")
    room = completed_room_with_accounts(store)
    first_player = room.players[0]

    assert store.record_match(room) is True
    assert store.record_match(room) is False

    history = store.history_for_account(first_player.account_id)
    summary = store.summary_for_account(first_player.account_id)
    detail = store.match_for_account(room.game_id, first_player.account_id)

    assert len(history) == 1
    assert history[0]["role"] == first_player.role.value
    assert history[0]["won"] is (
        first_player.alignment == Alignment.EVIL
    )
    assert history[0]["outcome"] == (
        "win" if first_player.alignment == Alignment.EVIL else "loss"
    )
    assert summary["games"] == 1
    assert summary["wins"] == int(first_player.alignment == Alignment.EVIL)
    assert detail["details"]["players"][0]["name"] == "玩家0"
    assert detail["assassinationHit"] is True


def test_ranked_leaderboard_excludes_matches_with_ai_players(tmp_path):
    store = AccountStore(tmp_path / "leaderboard.sqlite3")
    ranked_room = completed_room_with_accounts(store)
    store.record_match(ranked_room)

    leaderboard = store.leaderboard(game_key="avalon")
    assert leaderboard
    assert leaderboard[0]["wins"] == 1
    assert all(player["games"] == 1 for player in leaderboard)

    ai_room = completed_room_with_accounts(store, prefix="ai_player")
    ai_room.players[-1].is_bot = True
    ai_room.players[-1].account_id = None
    store.record_match(ai_room)

    assert all(
        player["games"] == 1
        for player in store.leaderboard(game_key="avalon")
    )
    human = ai_room.players[0]
    assert len(store.history_for_account(human.account_id)) == 1
    assert store.history_for_account(human.account_id)[0]["ranked"] is False


def test_reaction_scores_have_lowest_time_leaderboard(tmp_path):
    store = AccountStore(tmp_path / "reaction.sqlite3")
    first = account_for_player(store, 1, "reaction")
    second = account_for_player(store, 2, "reaction")

    def record(match_id: str, account, score_ms: int) -> None:
        assert store.record_game_match(
            game_key="reaction",
            match_id=match_id,
            room_code="SOLO",
            winner="completed",
            reason=f"三轮平均反应时间 {score_ms} 毫秒",
            started_at="2026-08-01T00:00:00+00:00",
            ended_at="2026-08-01T00:01:00+00:00",
            details={"players": [], "state": {"results_ms": [score_ms] * 3}},
            players=[
                {
                    "accountId": account.id,
                    "playerName": account.player_name,
                    "seat": 0,
                    "role": "tester",
                    "alignment": "solo",
                    "won": True,
                    "isHost": True,
                    "scoreMs": score_ms,
                }
            ],
        )

    record("reaction-1", first, 240)
    record("reaction-2", first, 220)
    record("reaction-3", second, 230)

    summary = store.summary_for_account(first.id, game_key="reaction")
    history = store.history_for_account(first.id, game_key="reaction")
    leaderboard = store.leaderboard(game_key="reaction")

    assert summary["games"] == 2
    assert summary["bestMs"] == 220
    assert summary["averageMs"] == 230
    assert history[0]["scoreMs"] == 220
    assert leaderboard[0]["accountId"] == first.id
    assert leaderboard[0]["bestMs"] == 220
    assert store.leaderboard(game_key="avalon") == []


def test_gomoku_draw_is_not_recorded_as_two_losses(tmp_path):
    store = AccountStore(tmp_path / "gomoku-draw.sqlite3")
    first = account_for_player(store, 1, "draw")
    second = account_for_player(store, 2, "draw")

    assert store.record_game_match(
        game_key="gomoku",
        match_id="gomoku-draw",
        room_code="DRAW",
        winner="draw",
        reason="棋盘已满，双方和棋",
        started_at="2026-08-01T00:00:00+00:00",
        ended_at="2026-08-01T00:10:00+00:00",
        details={"players": [], "state": {}},
        players=[
            {
                "accountId": account.id,
                "playerName": account.player_name,
                "seat": seat,
                "role": role,
                "alignment": role,
                "won": False,
                "isHost": seat == 0,
            }
            for seat, (account, role) in enumerate(
                ((first, "black"), (second, "white"))
            )
        ],
    )

    for account in (first, second):
        summary = store.summary_for_account(account.id, game_key="gomoku")
        history = store.history_for_account(account.id, game_key="gomoku")

        assert summary["games"] == 1
        assert summary["wins"] == 0
        assert summary["draws"] == 1
        assert summary["losses"] == 0
        assert history[0]["won"] is False
        assert history[0]["outcome"] == "draw"

    leaderboard = store.leaderboard(game_key="gomoku")
    assert all(entry["draws"] == 1 for entry in leaderboard)
