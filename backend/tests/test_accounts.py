from backend.app.accounts import AccountStore
from backend.app.games.avalon.models import Alignment, Phase, Role

from .test_engine import start_room


def account_for_player(store: AccountStore, index: int, prefix: str):
    account, _ = store.register(
        f"{prefix}_{index}", "secret123", f"玩家{index}"
    )
    return account


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
    assert summary["games"] == 1
    assert summary["wins"] == int(first_player.alignment == Alignment.EVIL)
    assert detail["details"]["players"][0]["name"] == "玩家0"
    assert detail["assassinationHit"] is True


def test_ranked_leaderboard_excludes_matches_with_ai_players(tmp_path):
    store = AccountStore(tmp_path / "leaderboard.sqlite3")
    ranked_room = completed_room_with_accounts(store)
    store.record_match(ranked_room)

    leaderboard = store.leaderboard()
    assert leaderboard
    assert leaderboard[0]["wins"] == 1
    assert all(player["games"] == 1 for player in leaderboard)

    ai_room = completed_room_with_accounts(store, prefix="ai_player")
    ai_room.players[-1].is_bot = True
    ai_room.players[-1].account_id = None
    store.record_match(ai_room)

    assert all(player["games"] == 1 for player in store.leaderboard())
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
                    "displayName": account.display_name,
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
    assert store.leaderboard() == []
