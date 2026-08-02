from datetime import timedelta

import pytest
from sqlalchemy import update

from backend.app.accounts import (
    AVALON_ROLE_SKIN_PROGRESSION_START,
    AVATAR_PRESET_IDS,
    AccountError,
    AccountStore,
)
from backend.app.database import users
from backend.app.games.avalon.models import Alignment, AvalonMode, Phase, Role

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


def test_new_login_replaces_the_previous_account_session(tmp_path):
    store = AccountStore(tmp_path / "single-session.sqlite3")
    account, first_token = store.register(
        "single_login", "secret123", "单点玩家"
    )

    logged_in, second_token = store.login("single_login", "secret123")
    restored = store.account_for_token(second_token)

    assert logged_in.id == account.id
    assert first_token != second_token
    assert store.account_for_token(first_token) is None
    assert restored is not None
    assert restored.id == account.id
    assert store.session_is_active(
        account.id,
        store.session_fingerprint(first_token),
    ) is False
    assert store.session_is_active(
        account.id,
        store.session_fingerprint(second_token),
    ) is True


def test_account_avatar_can_switch_between_preset_and_custom(tmp_path):
    store = AccountStore(tmp_path / "avatars.sqlite3")
    account, _ = store.register("avatar_user", "secret123", "头像玩家")

    assert account.avatar_preset in AVATAR_PRESET_IDS
    assert account.avatar_type == "preset"
    assert account.avatar_url == f"/avatars/{account.avatar_preset}.webp"

    custom = store.set_custom_avatar(account.id, b"webp-avatar", "image/webp")
    assert custom.avatar_type == "custom"
    assert custom.avatar_url.startswith("/api/avatars/")
    assert store.custom_avatar(custom.avatar_token or "") == (
        b"webp-avatar",
        "image/webp",
    )

    preset = store.set_avatar_preset(account.id, "jade-owl")
    assert preset.avatar_type == "preset"
    assert preset.avatar_url == "/avatars/jade-owl.webp"
    assert store.custom_avatar(custom.avatar_token or "") is None


def test_account_rejects_unknown_avatar_preset(tmp_path):
    store = AccountStore(tmp_path / "invalid-avatar.sqlite3")
    account, _ = store.register("avatar_user", "secret123", "头像玩家")

    with pytest.raises(AccountError, match="有效的内置头像"):
        store.set_avatar_preset(account.id, "not-a-real-avatar")


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


def record_avalon_role_result(
    store: AccountStore,
    account_id: str,
    *,
    match_id: str,
    role: str,
    won: bool = True,
    ranked: bool = True,
) -> None:
    assert store.record_game_match(
        game_key="avalon",
        match_id=match_id,
        room_code="SKIN",
        winner="good" if won else "evil",
        reason="皮肤进度测试",
        started_at="2026-08-03T00:00:00+00:00",
        ended_at="2026-08-03T00:10:00+00:00",
        details={},
        ranked=ranked,
        players=[
            {
                "accountId": account_id,
                "playerName": "皮肤玩家",
                "seat": 0,
                "role": role,
                "alignment": "good",
                "won": won,
                "isHost": True,
            }
        ],
    )


def test_existing_accounts_keep_every_avalon_role_skin(tmp_path):
    store = AccountStore(tmp_path / "legacy-role-skins.sqlite3")
    account, _ = store.register("legacy_skin", "secret123", "旧皮肤玩家")
    with store.engine.begin() as connection:
        connection.execute(
            update(users)
            .where(users.c.id == account.id)
            .values(
                created_at=(
                    AVALON_ROLE_SKIN_PROGRESSION_START
                    - timedelta(seconds=1)
                )
            )
        )

    progress = store.avalon_role_skin_progress(account.id)

    assert progress["legacyAllUnlocked"] is True
    assert all(
        role["upgradeUnlocked"] and role["ultimateUnlocked"]
        for role in progress["roles"].values()
    )


def test_new_accounts_unlock_role_skins_from_ranked_family_wins(tmp_path):
    store = AccountStore(tmp_path / "role-skin-progress.sqlite3")
    account, _ = store.register("new_skin", "secret123", "新皮肤玩家")
    with store.engine.begin() as connection:
        connection.execute(
            update(users)
            .where(users.c.id == account.id)
            .values(
                created_at=(
                    AVALON_ROLE_SKIN_PROGRESSION_START
                    + timedelta(seconds=1)
                )
            )
        )

    record_avalon_role_result(
        store,
        account.id,
        match_id="skin-loyal-1",
        role="loyal_servant",
    )
    record_avalon_role_result(
        store,
        account.id,
        match_id="skin-dissenting-2",
        role="dissenting_courtier",
    )
    record_avalon_role_result(
        store,
        account.id,
        match_id="skin-ai-unranked",
        role="loyal_servant",
        ranked=False,
    )

    progress = store.avalon_role_skin_progress(account.id)
    loyal = progress["roles"]["loyal_servant"]
    assert progress["legacyAllUnlocked"] is False
    assert progress["rankedOnly"] is True
    assert loyal == {
        "wins": 2,
        "upgradeUnlocked": True,
        "ultimateUnlocked": False,
    }
    assert progress["roles"]["merlin"]["wins"] == 0

    for index in range(3, 6):
        record_avalon_role_result(
            store,
            account.id,
            match_id=f"skin-loyal-{index}",
            role="loyal_servant",
        )

    completed = store.avalon_role_skin_progress(account.id)["roles"][
        "loyal_servant"
    ]
    assert completed["wins"] == 5
    assert completed["ultimateUnlocked"] is True


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


def test_court_undercurrent_match_records_final_alignment_and_mode(tmp_path):
    store = AccountStore(tmp_path / "court-undercurrent.sqlite3")
    engine, room = start_room(7, mode=AvalonMode.COURT_UNDERCURRENT)
    for index, player in enumerate(room.players):
        player.account_id = account_for_player(store, index, "court").id
    assassin = next(
        player for player in room.players if player.role == Role.ASSASSIN
    )
    dissenting = next(
        player
        for player in room.players
        if player.role == Role.DISSENTING_COURTIER
    )
    merlin = next(player for player in room.players if player.role == Role.MERLIN)
    room.phase = Phase.DAGGER_GRANT
    room.dagger_candidate_ids = [dissenting.id, merlin.id]
    engine.grant_dagger(room, assassin.id, dissenting.id)
    engine.dissenting_assassinate(room, dissenting.id, merlin.id)

    assert store.record_match(room) is True

    court_history = store.history_for_account(
        dissenting.account_id,
        game_key="avalon",
        game_mode="court_undercurrent",
    )
    standard_history = store.history_for_account(
        dissenting.account_id,
        game_key="avalon",
        game_mode="standard",
    )
    detail = store.match_for_account(room.game_id, dissenting.account_id)
    summary = store.summary_for_account(
        dissenting.account_id,
        game_key="avalon",
        game_mode="court_undercurrent",
    )

    assert len(court_history) == 1
    assert standard_history == []
    assert court_history[0]["alignment"] == "evil"
    assert court_history[0]["won"] is True
    assert detail["gameMode"] == "court_undercurrent"
    assert detail["recruitmentHit"] is True
    assert detail["assassinationHit"] is True
    assert summary["recruitmentAttempts"] == 1
    assert summary["recruitmentHits"] == 1
    assert summary["dissentingAssassinationAttempts"] == 1
    assert summary["dissentingAssassinationHits"] == 1
    assert detail["details"]["courtUndercurrent"] == {
        "daggerCandidateIds": [dissenting.id, merlin.id],
        "daggerTargetId": dissenting.id,
        "daggerHit": True,
        "transformedPlayerId": dissenting.id,
        "eligibleTargetIds": [
            player.id
            for player in room.players
            if player.id != dissenting.id
            and player.role
            not in {
                Role.ASSASSIN,
                Role.MORGANA,
                Role.MORDRED,
                Role.MINION,
            }
        ],
        "assassinationTargetId": merlin.id,
    }
    recorded_dissenting = next(
        player
        for player in detail["details"]["players"]
        if player["id"] == dissenting.id
    )
    assert recorded_dissenting["initialAlignment"] == "good"
    assert recorded_dissenting["finalAlignment"] == "evil"
    assert recorded_dissenting["transformed"] is True


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


def test_schulte_scores_use_server_time_trial_ranking(tmp_path):
    store = AccountStore(tmp_path / "schulte.sqlite3")
    first = account_for_player(store, 1, "schulte")
    second = account_for_player(store, 2, "schulte")

    def record(match_id: str, account, score_ms: int) -> None:
        assert store.record_game_match(
            game_key="schulte",
            match_id=match_id,
            room_code="GRID",
            winner="completed",
            reason=f"5×5 舒尔特方格完成，用时 {score_ms} 毫秒",
            started_at="2026-08-01T00:00:00+00:00",
            ended_at="2026-08-01T00:01:00+00:00",
            details={
                "players": [],
                "state": {"elapsed_ms": score_ms, "mistakes": 0},
            },
            players=[
                {
                    "accountId": account.id,
                    "playerName": account.player_name,
                    "seat": 0,
                    "role": "challenger",
                    "alignment": "solo",
                    "won": True,
                    "isHost": True,
                    "scoreMs": score_ms,
                }
            ],
        )

    record("schulte-1", first, 13_400)
    record("schulte-2", first, 12_800)
    record("schulte-3", second, 13_100)

    summary = store.summary_for_account(first.id, game_key="schulte")
    leaderboard = store.leaderboard(game_key="schulte")

    assert summary["games"] == 2
    assert summary["bestMs"] == 12_800
    assert summary["averageMs"] == 13_100
    assert leaderboard[0]["accountId"] == first.id
    assert leaderboard[0]["bestMs"] == 12_800


def test_minesweeper_scores_are_ranked_separately_by_difficulty(tmp_path):
    store = AccountStore(tmp_path / "minesweeper.sqlite3")
    first = account_for_player(store, 1, "mines")
    second = account_for_player(store, 2, "mines")

    def record(
        match_id: str,
        account,
        difficulty: str,
        score_ms: int | None,
    ) -> None:
        assert store.record_game_match(
            game_key="minesweeper",
            match_id=match_id,
            room_code="MINE",
            winner="completed" if score_ms is not None else "mine",
            reason="扫雷挑战结束",
            started_at="2026-08-01T00:00:00+00:00",
            ended_at="2026-08-01T00:01:00+00:00",
            details={
                "players": [],
                "state": {
                    "difficulty": difficulty,
                    "elapsed_ms": score_ms or 4_000,
                },
            },
            players=[
                {
                    "accountId": account.id,
                    "playerName": account.player_name,
                    "seat": 0,
                    "role": "sweeper",
                    "alignment": "solo",
                    "won": score_ms is not None,
                    "isHost": True,
                    "scoreMs": score_ms,
                }
            ],
        )

    record("mine-beginner-1", first, "beginner", 12_000)
    record("mine-expert-1", first, "expert", 68_000)
    record("mine-beginner-2", second, "beginner", 13_000)
    record("mine-beginner-loss", first, "beginner", None)

    beginner = store.summary_for_account(
        first.id,
        game_key="minesweeper",
        game_mode="beginner",
    )
    expert = store.summary_for_account(
        first.id,
        game_key="minesweeper",
        game_mode="expert",
    )
    history = store.history_for_account(
        first.id,
        game_key="minesweeper",
        game_mode="beginner",
    )
    leaderboard = store.leaderboard(
        game_key="minesweeper",
        game_mode="beginner",
    )

    assert beginner["games"] == 1
    assert beginner["bestMs"] == 12_000
    assert expert["games"] == 1
    assert expert["bestMs"] == 68_000
    assert len(history) == 2
    assert {item["gameMode"] for item in history} == {"beginner"}
    assert {item["outcome"] for item in history} == {"completed", "loss"}
    assert leaderboard[0]["accountId"] == first.id


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
