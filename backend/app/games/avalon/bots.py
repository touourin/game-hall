from __future__ import annotations

from backend.app.arcade.bots import BotAction

from .engine import GameEngine
from .models import Alignment, Phase, Role, Room
from .rules import mission_team_size


TEAM_APPROVAL_PROBABILITY = 0.7
EVIL_MISSION_SUCCESS_PROBABILITY = 0.5


def choose_ai_action(room: Room, engine: GameEngine) -> BotAction | None:
    """Choose one Avalon AI action without applying it to the room."""
    if room.phase == Phase.ROLE_REVEAL:
        player = next(
            (
                candidate
                for candidate in room.players
                if candidate.is_bot
                and candidate.id not in room.role_confirmed_ids
            ),
            None,
        )
        return (
            BotAction(player.id, "confirm_role")
            if player is not None
            else None
        )

    if room.phase == Phase.TEAM_BUILDING:
        leader = room.leader
        if not leader.is_bot:
            return None
        required_size = mission_team_size(
            len(room.players), room.mission_index
        )
        team = engine.rng.sample(room.players, required_size)
        return BotAction(
            leader.id,
            "propose_team",
            {"team_ids": [player.id for player in team]},
        )

    if room.phase == Phase.TEAM_VOTING:
        player = next(
            (
                candidate
                for candidate in room.players
                if candidate.is_bot and candidate.id not in room.team_votes
            ),
            None,
        )
        if player is None:
            return None
        return BotAction(
            player.id,
            "vote_team",
            {"approve": engine.rng.random() < TEAM_APPROVAL_PROBABILITY},
        )

    if room.phase == Phase.MISSION_VOTING:
        player = next(
            (
                room.player(player_id)
                for player_id in room.selected_team_ids
                if room.player(player_id).is_bot
                and player_id not in room.mission_votes
            ),
            None,
        )
        if player is None:
            return None
        success = (
            True
            if player.alignment == Alignment.GOOD
            or player.role == Role.SHADOW_MERLIN
            else engine.rng.random() < EVIL_MISSION_SUCCESS_PROBABILITY
        )
        return BotAction(player.id, "vote_mission", {"success": success})

    if room.phase == Phase.EXILE_COUNCIL_BALLOT:
        player = next(
            (
                candidate
                for candidate in room.players
                if candidate.is_bot
                and candidate.id not in room.exile_council_open_votes
            ),
            None,
        )
        if player is None:
            return None
        return BotAction(
            player.id,
            "exile_council_ballot",
            {
                "open_council": True,
                "target_id": engine.rng.choice(room.players).id,
            },
        )

    if room.phase == Phase.EXILE_COUNCIL_ASSASSINATION_DECISION:
        player = next(
            (
                candidate
                for candidate in room.players
                if candidate.is_bot
                and candidate.id
                not in room.exile_council_assassination_decisions
            ),
            None,
        )
        if player is None:
            return None
        return BotAction(
            player.id,
            "exile_council_assassination_decision",
            {"assassinate": bool(engine.rng.randrange(2))},
        )

    if room.phase == Phase.EXILE_COUNCIL_ASSASSINATION_TARGET:
        assassin = next(
            (
                candidate
                for candidate in room.players
                if candidate.role == Role.ASSASSIN
            ),
            None,
        )
        if (
            assassin is None
            or not assassin.is_bot
            or assassin.id in room.exile_council_assassination_targets
        ):
            return None
        return BotAction(
            assassin.id,
            "exile_council_assassination_target",
            {
                "target_id": engine.rng.choice(
                    engine.eligible_assassination_targets(room)
                )
            },
        )

    if room.phase == Phase.LADY_SELECT:
        if room.lady_holder_id is None:
            return None
        inspector = room.player(room.lady_holder_id)
        if not inspector.is_bot:
            return None
        target_ids = engine.eligible_lady_targets(room)
        if not target_ids:
            return None
        return BotAction(
            inspector.id,
            "lady_inspect",
            {"target_id": engine.rng.choice(target_ids)},
        )

    if room.phase == Phase.LADY_REVEAL:
        if room.lady_pending_inspector_id is None:
            return None
        inspector = room.player(room.lady_pending_inspector_id)
        return (
            BotAction(inspector.id, "lady_acknowledge")
            if inspector.is_bot
            else None
        )

    if room.phase == Phase.ASSASSINATION:
        assassin = next(
            (
                player
                for player in room.players
                if player.role == Role.ASSASSIN
            ),
            None,
        )
        if assassin is None or not assassin.is_bot:
            return None
        return BotAction(
            assassin.id,
            "assassinate",
            {
                "target_id": engine.rng.choice(
                    engine.eligible_assassination_targets(room)
                )
            },
        )

    if room.phase == Phase.DAGGER_GRANT:
        assassin = next(
            (
                player
                for player in room.players
                if player.role == Role.ASSASSIN
            ),
            None,
        )
        if assassin is None or not assassin.is_bot:
            return None
        return BotAction(
            assassin.id,
            "grant_dagger",
            {"target_id": engine.rng.choice(room.dagger_candidate_ids)},
        )

    if room.phase == Phase.FINAL_COUNCIL:
        if room.transformed_player_id is None:
            return None
        dissenting = room.player(room.transformed_player_id)
        if not dissenting.is_bot:
            return None
        return BotAction(
            dissenting.id,
            "dissenting_assassinate",
            {
                "target_id": engine.rng.choice(
                    engine.eligible_dissenting_targets(room)
                )
            },
        )

    return None
