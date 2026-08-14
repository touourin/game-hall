from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Protocol

from sqlalchemy import func, insert, select
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError

from backend.app.database import match_players, matches, users

from .models import ROLE_ALIGNMENT, Room, Role


GAME_KEY = "avalon"

# Accounts present when role progression shipped retain the complete skin library.
ROLE_SKIN_PROGRESSION_START = datetime(2026, 8, 2, 17, 18, 0)
ROLE_SKIN_ROLES = (
    "merlin",
    "percival",
    "loyal_servant",
    "assassin",
    "morgana",
    "mordred",
    "oberon",
    "minion",
)
ROLE_SKIN_UPGRADE_WINS = 2
ROLE_SKIN_ULTIMATE_WINS = 5
# 2026-08-03 00:00 through 2026-08-10 00:00 in Asia/Shanghai (UTC+8).
ROLE_SKIN_FREE_WEEK_START = datetime(2026, 8, 2, 16, 0, 0)
ROLE_SKIN_FREE_WEEK_END = datetime(2026, 8, 9, 16, 0, 0)


class AvalonRecordStore(Protocol):
    engine: Engine

    def initialize(self) -> None: ...


class AvalonProgressionError(ValueError):
    pass


def persist_avalon_match(room: Room, store: AvalonRecordStore) -> bool:
    """Persist Avalon-specific match audit data through its owning module."""
    if (
        room.game_id is None
        or room.game_started_at is None
        or room.winner is None
        or room.win_reason is None
    ):
        return False
    human_players = [player for player in room.players if not player.is_bot]
    account_ids = [
        player.account_id
        for player in human_players
        if player.account_id is not None
    ]
    if not account_ids:
        return False
    ranked = (
        len(human_players) == len(room.players)
        and len(account_ids) == len(human_players)
        and len(set(account_ids)) == len(account_ids)
    )
    assassination_target_id = (
        room.dissenting_assassination_target_id or room.assassin_target_id
    )
    assassination_target = (
        room.player(assassination_target_id)
        if assassination_target_id is not None
        else None
    )
    assassination_hit = (
        assassination_target.role == Role.MERLIN
        if assassination_target is not None
        else None
    )
    store.initialize()
    try:
        with store.engine.begin() as connection:
            existing = connection.execute(
                select(matches.c.id).where(matches.c.id == room.game_id)
            ).scalar_one_or_none()
            if existing is not None:
                return False
            connection.execute(
                insert(matches).values(
                    id=room.game_id,
                    game_key=GAME_KEY,
                    room_code=room.code,
                    mode=room.settings.mode.value,
                    player_count=len(room.players),
                    winner=room.winner.value,
                    reason=room.win_reason,
                    ranked=ranked,
                    assassination_hit=assassination_hit,
                    ending_route=room.ending_route,
                    recruitment_hit=room.dagger_hit,
                    started_at=_parse_datetime(room.game_started_at),
                    ended_at=_utc_now(),
                    details_json=avalon_match_details(room),
                )
            )
            player_rows = [
                {
                    "match_id": room.game_id,
                    "account_id": player.account_id,
                    "player_name": player.name,
                    "seat": player.seat,
                    "role": player.role.value,
                    "alignment": player.alignment.value,
                    "won": player.alignment == room.winner,
                    "outcome": (
                        "win" if player.alignment == room.winner else "loss"
                    ),
                    "is_host": player.id == room.host_id,
                }
                for player in human_players
                if player.account_id is not None
            ]
            if player_rows:
                connection.execute(insert(match_players), player_rows)
    except IntegrityError:
        return False
    return True


def avalon_match_details(room: Room) -> dict[str, Any]:
    return {
        "mode": room.settings.mode.value,
        "shadowMerlinEnabled": room.settings.shadow_merlin_enabled,
        "players": [
            {
                "id": player.id,
                "name": player.name,
                "seat": player.seat,
                "isBot": player.is_bot,
                "role": player.role.value,
                "alignment": player.alignment.value,
                "initialAlignment": ROLE_ALIGNMENT[player.role].value,
                "finalAlignment": player.alignment.value,
                "transformed": player.id == room.transformed_player_id,
                "shadowMerlinTransformed": (
                    player.role == Role.SHADOW_MERLIN
                    and room.shadow_merlin_transformed
                ),
            }
            for player in room.players
        ],
        "missions": [
            {
                "number": mission.number,
                "teamIds": mission.team_ids,
                "success": mission.success,
                "failCount": mission.fail_count,
                "failedByRejections": getattr(
                    mission, "failed_by_rejections", False
                ),
            }
            for mission in room.mission_history
        ],
        "proposals": [
            {
                "missionNumber": proposal.mission_number,
                "attempt": proposal.attempt,
                "leaderId": proposal.leader_id,
                "teamIds": proposal.team_ids,
                "votes": proposal.votes,
                "accepted": proposal.accepted,
            }
            for proposal in room.proposal_history
        ],
        "ladyChecks": [
            {
                "inspectorId": check.inspector_id,
                "targetId": check.target_id,
                "alignment": check.alignment.value,
                "missionNumber": check.mission_number,
            }
            for check in room.lady_checks
        ],
        "assassinTargetId": room.assassin_target_id,
        "assassinationWasEarly": room.assassination_was_early,
        "courtUndercurrent": {
            "daggerCandidateIds": list(room.dagger_candidate_ids),
            "daggerTargetId": room.dagger_target_id,
            "daggerHit": room.dagger_hit,
            "transformedPlayerId": room.transformed_player_id,
            "eligibleTargetIds": (
                [
                    player.id
                    for player in room.players
                    if player.id != room.transformed_player_id
                    and player.role
                    not in {
                        Role.ASSASSIN,
                        Role.MORGANA,
                        Role.MORDRED,
                        Role.MINION,
                    }
                ]
                if room.transformed_player_id is not None
                else []
            ),
            "assassinationTargetId": room.dissenting_assassination_target_id,
        },
        "shadowMerlin": {
            "enabled": room.settings.shadow_merlin_enabled,
            "transformed": room.shadow_merlin_transformed,
            "councilTriggered": room.exile_council_triggered,
            "councilOpened": room.exile_council_opened,
            "openVotes": dict(room.exile_council_open_votes),
            "targetVotes": dict(room.exile_council_target_votes),
            "assassinationDecisions": dict(
                room.exile_council_assassination_decisions
            ),
            "assassinationChosen": (
                room.exile_council_assassination_chosen
            ),
            "assassinationTargets": dict(
                room.exile_council_assassination_targets
            ),
            "assassinationTargetId": (
                room.exile_council_assassination_target_id
            ),
            "exileTargetId": room.exile_council_exile_target_id,
            "exileSuccess": room.exile_council_exile_success,
        },
        "endingRoute": room.ending_route,
    }


def avalon_role_skin_progress(
    engine: Engine,
    account_id: str,
    *,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Return ranked Avalon wins by role family for skin progression."""
    current_time = now or _utc_now()
    event_all_unlocked = (
        ROLE_SKIN_FREE_WEEK_START
        <= current_time
        < ROLE_SKIN_FREE_WEEK_END
    )
    with engine.connect() as connection:
        created_at = connection.execute(
            select(users.c.created_at).where(users.c.id == account_id)
        ).scalar_one_or_none()
        if created_at is None:
            raise AvalonProgressionError("账号不存在")
        rows = connection.execute(
            select(
                match_players.c.role,
                func.count().label("wins"),
            )
            .select_from(
                match_players.join(
                    matches, matches.c.id == match_players.c.match_id
                )
            )
            .where(
                match_players.c.account_id == account_id,
                matches.c.game_key == GAME_KEY,
                matches.c.ranked.is_(True),
                match_players.c.won.is_(True),
            )
            .group_by(match_players.c.role)
        ).mappings().all()

    legacy_all_unlocked = created_at <= ROLE_SKIN_PROGRESSION_START
    wins = {role: 0 for role in ROLE_SKIN_ROLES}
    for row in rows:
        role = str(row["role"])
        if role == "dissenting_courtier":
            role_family = "loyal_servant"
        elif role == "shadow_merlin":
            role_family = "merlin"
        else:
            role_family = role
        if role_family in wins:
            wins[role_family] += int(row["wins"])

    return {
        "legacyAllUnlocked": legacy_all_unlocked,
        "eventAllUnlocked": event_all_unlocked,
        "eventEndsAt": _iso_datetime(ROLE_SKIN_FREE_WEEK_END),
        "rankedOnly": True,
        "upgradeWinsRequired": ROLE_SKIN_UPGRADE_WINS,
        "ultimateWinsRequired": ROLE_SKIN_ULTIMATE_WINS,
        "roles": {
            role: {
                "wins": role_wins,
                "upgradeUnlocked": event_all_unlocked
                or legacy_all_unlocked
                or role_wins >= ROLE_SKIN_UPGRADE_WINS,
                "ultimateUnlocked": event_all_unlocked
                or legacy_all_unlocked
                or role_wins >= ROLE_SKIN_ULTIMATE_WINS,
            }
            for role, role_wins in wins.items()
        },
    }


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _parse_datetime(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is not None:
        parsed = parsed.astimezone(timezone.utc).replace(tzinfo=None)
    return parsed


def _iso_datetime(value: datetime) -> str:
    return value.replace(tzinfo=timezone.utc).isoformat(timespec="seconds")
