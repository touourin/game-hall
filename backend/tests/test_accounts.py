from datetime import datetime, timedelta

import pytest
from sqlalchemy import inspect, select, update

from backend.app.accounts import (
    AVATAR_PRESET_IDS,
    AccountError,
    AccountStore,
)
from backend.app.database import matches, users
from backend.app.email_delivery import EmailPolicy
from backend.app.games.avalon.models import Alignment, AvalonMode, Phase, Role
from backend.app.games.avalon.records import (
    ROLE_SKIN_FREE_WEEK_END,
    ROLE_SKIN_FREE_WEEK_START,
    ROLE_SKIN_PROGRESSION_START,
    avalon_role_skin_progress,
    persist_avalon_match,
)

from .test_engine import start_room


def account_for_player(store: AccountStore, index: int, prefix: str):
    account, _ = store.register(
        f"{prefix}_{index}", "secret123", f"{prefix}{index}"
    )
    return account


def email_policy(
    *,
    account_limit: int = 3,
    server_limit: int = 20,
    cooldown_seconds: int = 60,
) -> EmailPolicy:
    return EmailPolicy(
        account_daily_limit=account_limit,
        server_daily_limit=server_limit,
        cooldown_seconds=cooldown_seconds,
        code_ttl_minutes=10,
        max_code_attempts=5,
        timezone_name="Asia/Shanghai",
    )


def test_existing_local_sqlite_score_column_is_upgraded(tmp_path):
    database_path = tmp_path / "legacy-score.sqlite3"
    store = AccountStore(database_path)
    store.initialize()
    with store.engine.begin() as connection:
        connection.exec_driver_sql(
            "ALTER TABLE match_players "
            "RENAME COLUMN score_value TO score_ms"
        )
    store.dispose()

    upgraded_store = AccountStore(database_path)
    upgraded_store.initialize()

    columns = {
        column["name"]
        for column in inspect(upgraded_store.engine).get_columns(
            "match_players"
        )
    }
    assert "score_value" in columns
    assert "score_ms" not in columns


def test_username_stays_stable_when_game_nickname_changes(tmp_path):
    store = AccountStore(tmp_path / "rename.sqlite3")
    account, _ = store.register("zhangsan", "secret123", "张三玩家")

    renamed = store.rename_player(account.id, "王五玩家")
    logged_in, _ = store.login("zhangsan", "secret123")

    assert renamed.id == account.id
    assert renamed.username == "zhangsan"
    assert renamed.player_name == "王五玩家"
    assert logged_in.player_name == "王五玩家"


def test_email_style_username_can_be_registered_and_used_to_login(tmp_path):
    store = AccountStore(tmp_path / "email-username.sqlite3")
    username = "gantianyu+game.account@sinodata.example"

    account, _ = store.register(username, "secret123", "邮箱玩家")
    logged_in, _ = store.login(username.upper(), "secret123")

    assert account.username == username
    assert logged_in.id == account.id


def test_verified_email_can_reset_password_and_revoke_sessions(tmp_path):
    store = AccountStore(tmp_path / "email-security.sqlite3")
    account, old_token = store.register(
        "email_security", "secret123", "邮箱安全玩家"
    )
    started_at = datetime(2026, 8, 16, 1, 0, 0)
    binding = store.begin_email_binding(
        account.id,
        "Player@Example.com",
        email_policy(),
        now=started_at,
    )

    bound = store.verify_and_bind_email(
        account.id,
        "player@example.com",
        binding.code,
        email_policy(),
        now=started_at + timedelta(minutes=1),
    )
    reset = store.begin_password_reset(
        "PLAYER@EXAMPLE.COM",
        email_policy(),
        now=started_at + timedelta(minutes=2),
    )

    assert bound.email == "player@example.com"
    assert bound.email_verified_at is not None
    assert bound.as_dict()["emailVerified"] is True
    assert reset is not None
    account_id = store.reset_password_with_code(
        "email_security",
        reset.code,
        "new-secret-456",
        email_policy(),
        now=started_at + timedelta(minutes=3),
    )
    assert account_id == account.id
    assert store.account_for_token(old_token) is None
    with pytest.raises(AccountError, match="账号名或密码不正确"):
        store.login("email_security", "secret123")
    logged_in, _ = store.login("email_security", "new-secret-456")
    assert logged_in.id == account.id


def test_registration_email_is_verified_atomically_and_can_be_unbound(
    tmp_path,
):
    store = AccountStore(tmp_path / "registration-email.sqlite3")
    policy = email_policy(cooldown_seconds=1)
    started_at = datetime(2026, 8, 16, 1, 30, 0)
    challenge = store.begin_registration_email_verification(
        "New.Player@Example.com",
        policy,
        now=started_at,
    )

    with pytest.raises(AccountError, match="验证码不正确"):
        store.register(
            "registration_mail",
            "secret123",
            "注册邮箱",
            email="new.player@example.com",
            email_code=(
                "000000" if challenge.code != "000000" else "999999"
            ),
            policy=policy,
            now=started_at + timedelta(minutes=1),
        )
    with pytest.raises(AccountError, match="账号名或密码不正确"):
        store.login("registration_mail", "secret123")

    account, token = store.register(
        "registration_mail",
        "secret123",
        "注册邮箱",
        email="new.player@example.com",
        email_code=challenge.code,
        policy=policy,
        now=started_at + timedelta(minutes=2),
    )

    assert account.email == "new.player@example.com"
    assert account.email_verified_at is not None
    assert store.account_for_token(token) is not None

    unbinding = store.begin_email_unbinding(
        account.id,
        policy,
        now=started_at + timedelta(minutes=3),
    )
    unbound = store.verify_and_unbind_email(
        account.id,
        unbinding.code,
        policy,
        now=started_at + timedelta(minutes=4),
    )

    assert unbound.email is None
    assert unbound.email_verified_at is None
    assert store.account_for_token(token) is not None
    assert store.begin_password_reset(
        "new.player@example.com",
        policy,
        now=started_at + timedelta(minutes=5),
    ) is None


def test_registration_email_send_limit_is_applied_per_email(tmp_path):
    store = AccountStore(tmp_path / "registration-email-limit.sqlite3")
    policy = email_policy(cooldown_seconds=1)
    started_at = datetime(2026, 8, 16, 1, 45, 0)

    for index in range(3):
        store.begin_registration_email_verification(
            "limited@example.com",
            policy,
            now=started_at + timedelta(seconds=index * 2),
        )

    with pytest.raises(AccountError, match="每个邮箱每天最多发送 3 封"):
        store.begin_registration_email_verification(
            "LIMITED@example.com",
            policy,
            now=started_at + timedelta(seconds=8),
        )


def test_email_send_limits_apply_per_account_and_server(tmp_path):
    store = AccountStore(tmp_path / "email-limits.sqlite3")
    accounts = [
        store.register(f"mail_limit_{index}", "secret123", f"邮{index}")[0]
        for index in range(7)
    ]
    policy = email_policy(cooldown_seconds=1)
    started_at = datetime(2026, 8, 16, 2, 0, 0)

    for index in range(20):
        account = accounts[index % len(accounts)]
        store.begin_email_binding(
            account.id,
            f"mail-{index}@example.com",
            policy,
            now=started_at + timedelta(seconds=index * 2),
        )

    with pytest.raises(AccountError, match="邮件发送额度"):
        store.begin_email_binding(
            accounts[6].id,
            "server-limit@example.com",
            policy,
            now=started_at + timedelta(seconds=42),
        )

    isolated_store = AccountStore(tmp_path / "account-email-limit.sqlite3")
    isolated, _ = isolated_store.register(
        "isolated_mail", "secret123", "独立限额"
    )
    for index in range(3):
        isolated_store.begin_email_binding(
            isolated.id,
            f"isolated-{index}@example.com",
            policy,
            now=started_at + timedelta(seconds=index * 2),
        )
    with pytest.raises(AccountError, match="每个账号每天最多发送 3 封"):
        isolated_store.begin_email_binding(
            isolated.id,
            "fourth@example.com",
            policy,
            now=started_at + timedelta(seconds=8),
        )


def test_email_code_cooldown_and_attempt_limit_are_enforced(tmp_path):
    store = AccountStore(tmp_path / "email-code-guard.sqlite3")
    account, _ = store.register("guarded_mail", "secret123", "验证保护")
    policy = email_policy()
    started_at = datetime(2026, 8, 16, 3, 0, 0)
    challenge = store.begin_email_binding(
        account.id,
        "guarded@example.com",
        policy,
        now=started_at,
    )

    with pytest.raises(AccountError, match="等待"):
        store.begin_email_binding(
            account.id,
            "guarded@example.com",
            policy,
            now=started_at + timedelta(seconds=20),
        )

    for attempt in range(5):
        expected = "尝试次数过多" if attempt == 4 else "验证码不正确"
        with pytest.raises(AccountError, match=expected):
            store.verify_and_bind_email(
                account.id,
                "guarded@example.com",
                "000000" if challenge.code != "000000" else "999999",
                policy,
                now=started_at + timedelta(minutes=1, seconds=attempt),
            )

    with pytest.raises(AccountError, match="无效或已过期"):
        store.verify_and_bind_email(
            account.id,
            "guarded@example.com",
            challenge.code,
            policy,
            now=started_at + timedelta(minutes=2),
        )


def test_single_character_game_nickname_is_allowed(tmp_path):
    store = AccountStore(tmp_path / "single-character-nickname.sqlite3")

    account, _ = store.register("single_name", "secret123", "王")
    renamed = store.rename_player(account.id, "李")

    assert account.player_name == "王"
    assert renamed.player_name == "李"


def test_username_rejects_more_than_fifty_characters(tmp_path):
    store = AccountStore(tmp_path / "long-username.sqlite3")

    with pytest.raises(AccountError, match="2–50"):
        store.register("a" * 51, "secret123", "超长账号")


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


def test_ai_match_records_the_human_but_is_not_ranked(tmp_path) -> None:
    store = AccountStore(tmp_path / "ai-match.sqlite3")
    human, _ = store.register("human_player", "secret123", "真人棋手")

    assert store.record_game_match(
        game_key="xiangqi",
        match_id="xiangqi-ai-match",
        room_code="ROBO",
        winner="red",
        reason="将死",
        started_at="2026-08-09T00:00:00+00:00",
        ended_at="2026-08-09T00:10:00+00:00",
        details={"players": [{"isBot": False}, {"isBot": True}]},
        players=[
            {
                "accountId": human.id,
                "playerName": human.player_name,
                "seat": 0,
                "role": "red",
                "alignment": "red",
                "won": True,
                "isHost": True,
            }
        ],
        ranked=False,
        participant_count=2,
    )

    history = store.history_for_account(human.id, game_key="xiangqi")
    assert history[0]["playerCount"] == 2
    assert history[0]["ranked"] is False


def test_departed_suspicion_match_and_equipment_audit_are_persisted(tmp_path):
    store = AccountStore(tmp_path / "departed-suspicion.sqlite3")
    account = account_for_player(store, 0, "departed")
    audit = {
        "initial_equipment_order": ["coffee", "key"],
        "equipment_draw_history": [
            {
                "sequence": 1,
                "turn_number": 1,
                "seat": 0,
                "card_id": "coffee",
                "source": "normal_action",
            }
        ],
        "equipment_audit_complete": True,
    }

    assert store.record_game_match(
        game_key="departed_suspicion",
        game_name="无间疑云",
        match_id="departed-match",
        room_code="COPS",
        winner="honest",
        reason="头目出局，正直阵营获胜",
        started_at="2026-08-07T00:00:00+00:00",
        ended_at="2026-08-07T00:10:00+00:00",
        details={"options": {"equipmentSet": "base"}, "state": audit},
        players=[
            {
                "accountId": account.id,
                "playerName": account.player_name,
                "seat": 0,
                "role": "探员",
                "alignment": "honest",
                "won": True,
                "isHost": True,
            }
        ],
    )

    with store.engine.connect() as connection:
        recorded = connection.execute(
            select(matches.c.game_key, matches.c.details_json).where(
                matches.c.id == "departed-match"
            )
        ).mappings().one()

    assert recorded["game_key"] == "departed_suspicion"
    assert recorded["details_json"]["state"] == audit


def test_existing_accounts_keep_every_avalon_role_skin(tmp_path):
    store = AccountStore(tmp_path / "legacy-role-skins.sqlite3")
    account, _ = store.register("legacy_skin", "secret123", "旧皮肤玩家")
    with store.engine.begin() as connection:
        connection.execute(
            update(users)
            .where(users.c.id == account.id)
            .values(
                created_at=(
                    ROLE_SKIN_PROGRESSION_START
                    - timedelta(seconds=1)
                )
            )
        )

    progress = avalon_role_skin_progress(
        store.engine,
        account.id,
        now=ROLE_SKIN_FREE_WEEK_END,
    )

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
                    ROLE_SKIN_PROGRESSION_START
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

    progress = avalon_role_skin_progress(
        store.engine,
        account.id,
        now=ROLE_SKIN_FREE_WEEK_END,
    )
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

    completed = avalon_role_skin_progress(
        store.engine,
        account.id,
        now=ROLE_SKIN_FREE_WEEK_END,
    )["roles"]["loyal_servant"]
    assert completed["wins"] == 5
    assert completed["ultimateUnlocked"] is True


def test_everyone_can_use_every_avalon_role_skin_during_free_week(tmp_path):
    store = AccountStore(tmp_path / "role-skin-free-week.sqlite3")
    account, _ = store.register("free_week_skin", "secret123", "本周玩家")

    progress = avalon_role_skin_progress(
        store.engine,
        account.id,
        now=ROLE_SKIN_FREE_WEEK_START + timedelta(days=2),
    )

    assert progress["eventAllUnlocked"] is True
    assert progress["eventEndsAt"] == "2026-08-09T16:00:00+00:00"
    assert all(
        role["upgradeUnlocked"] and role["ultimateUnlocked"]
        for role in progress["roles"].values()
    )

    after_event = avalon_role_skin_progress(
        store.engine,
        account.id,
        now=ROLE_SKIN_FREE_WEEK_END,
    )
    assert after_event["eventAllUnlocked"] is False
    assert all(
        not role["upgradeUnlocked"] and not role["ultimateUnlocked"]
        for role in after_event["roles"].values()
    )


def test_completed_match_is_saved_once_with_personal_history(tmp_path):
    store = AccountStore(tmp_path / "stats.sqlite3")
    room = completed_room_with_accounts(store)
    first_player = room.players[0]

    assert persist_avalon_match(room, store) is True
    assert persist_avalon_match(room, store) is False

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

    assert persist_avalon_match(room, store) is True

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


def test_court_stats_separate_shadow_merlin_and_legacy_matches(tmp_path):
    store = AccountStore(tmp_path / "court-variants.sqlite3")
    account = account_for_player(store, 0, "variant")

    def record_variant(match_id: str, shadow_enabled: bool | None) -> None:
        details = {"mode": "court_undercurrent"}
        if shadow_enabled is not None:
            details["shadowMerlinEnabled"] = shadow_enabled
        assert store.record_game_match(
            game_key="avalon",
            match_id=match_id,
            room_code="DARK",
            winner="good",
            reason="王庭暗流统计分组测试",
            started_at="2026-08-01T00:00:00+00:00",
            ended_at="2026-08-01T00:10:00+00:00",
            details=details,
            ranked=True,
            players=[
                {
                    "accountId": account.id,
                    "playerName": account.player_name,
                    "seat": 0,
                    "role": "merlin",
                    "alignment": "good",
                    "won": True,
                    "isHost": True,
                }
            ],
        )

    record_variant("court-legacy", None)
    record_variant("court-classic", False)
    record_variant("court-shadow", True)
    with store.engine.begin() as connection:
        connection.execute(
            update(matches)
            .where(
                matches.c.id.in_(
                    {"court-legacy", "court-classic", "court-shadow"}
                )
            )
            .values(mode="court_undercurrent")
        )

    classic_history = store.history_for_account(
        account.id,
        game_key="avalon",
        game_mode="court_undercurrent",
        game_variant="classic",
    )
    shadow_history = store.history_for_account(
        account.id,
        game_key="avalon",
        game_mode="court_undercurrent",
        game_variant="shadow_merlin",
    )

    assert {match["id"] for match in classic_history} == {
        "court-legacy",
        "court-classic",
    }
    assert [match["id"] for match in shadow_history] == ["court-shadow"]
    assert store.summary_for_account(
        account.id,
        game_key="avalon",
        game_mode="court_undercurrent",
        game_variant="classic",
    )["games"] == 2
    assert store.summary_for_account(
        account.id,
        game_key="avalon",
        game_mode="court_undercurrent",
        game_variant="shadow_merlin",
    )["games"] == 1
    assert store.leaderboard(
        game_key="avalon",
        game_mode="court_undercurrent",
        game_variant="classic",
    )[0]["games"] == 2
    assert store.leaderboard(
        game_key="avalon",
        game_mode="court_undercurrent",
        game_variant="shadow_merlin",
    )[0]["games"] == 1


def test_ranked_leaderboard_excludes_matches_with_ai_players(tmp_path):
    store = AccountStore(tmp_path / "leaderboard.sqlite3")
    ranked_room = completed_room_with_accounts(store)
    persist_avalon_match(ranked_room, store)

    leaderboard = store.leaderboard(game_key="avalon")
    assert leaderboard
    assert leaderboard[0]["wins"] == 1
    assert all(player["games"] == 1 for player in leaderboard)

    ai_room = completed_room_with_accounts(store, prefix="ai_player")
    ai_room.players[-1].is_bot = True
    ai_room.players[-1].account_id = None
    persist_avalon_match(ai_room, store)

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


def test_tetris_scores_use_highest_first_leaderboard(tmp_path):
    store = AccountStore(tmp_path / "tetris.sqlite3")
    first = account_for_player(store, 1, "blocks")
    second = account_for_player(store, 2, "blocks")

    def record(
        match_id: str,
        account,
        score: int,
        options: dict | None = None,
    ) -> None:
        assert store.record_game_match(
            game_key="tetris",
            match_id=match_id,
            room_code="DROP",
            winner="completed",
            reason=f"最终得分 {score}",
            started_at="2026-08-12T00:00:00+00:00",
            ended_at="2026-08-12T00:03:00+00:00",
            details={
                "options": options or {"challengeMode": "endless"},
                "players": [],
                "state": {"score": score, "lines": 12, "level": 2},
            },
            players=[
                {
                    "accountId": account.id,
                    "playerName": account.player_name,
                    "seat": 0,
                    "role": "stacker",
                    "alignment": "solo",
                    "won": True,
                    "isHost": True,
                    "scoreValue": score,
                }
            ],
        )

    record("tetris-1", first, 8_000)
    record("tetris-2", first, 12_000)
    record("tetris-3", second, 10_000)
    record(
        "tetris-4",
        first,
        20_000,
        {"challengeMode": "timed", "durationSeconds": 180},
    )

    summary = store.summary_for_account(
        first.id, game_key="tetris", game_mode="standard"
    )
    timed_summary = store.summary_for_account(
        first.id, game_key="tetris", game_mode="timed_180"
    )
    history = store.history_for_account(
        first.id, game_key="tetris", game_mode="standard"
    )
    leaderboard = store.leaderboard(game_key="tetris", game_mode="standard")
    timed_leaderboard = store.leaderboard(
        game_key="tetris", game_mode="timed_180"
    )

    assert summary["games"] == 2
    assert summary["bestScore"] == 12_000
    assert summary["averageScore"] == 10_000
    assert timed_summary["games"] == 1
    assert timed_summary["bestScore"] == 20_000
    assert history[0]["scoreValue"] == 12_000
    assert history[0]["scoreMs"] is None
    assert history[0]["outcome"] == "completed"
    assert leaderboard[0]["accountId"] == first.id
    assert leaderboard[0]["bestScore"] == 12_000
    assert timed_leaderboard[0]["bestScore"] == 20_000


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
