from __future__ import annotations

from .engine import GameEngine
from .models import Alignment, Phase, Role, Room
from .rules import mission_team_size


MAX_AUTOMATIC_ACTIONS = 100
TEAM_APPROVAL_PROBABILITY = 0.7
EVIL_MISSION_SUCCESS_PROBABILITY = 0.5


def advance_ai_players(room: Room, engine: GameEngine) -> None:
    """Run mandatory AI actions until the game needs a human decision."""
    for _ in range(MAX_AUTOMATIC_ACTIONS):
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
            if player is None:
                return
            engine.confirm_role(room, player.id)
            continue

        if room.phase == Phase.TEAM_BUILDING:
            leader = room.leader
            if not leader.is_bot:
                return
            required_size = mission_team_size(
                len(room.players), room.mission_index
            )
            team = engine.rng.sample(room.players, required_size)
            engine.propose_team(
                room, leader.id, [player.id for player in team]
            )
            continue

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
                return
            approve = engine.rng.random() < TEAM_APPROVAL_PROBABILITY
            engine.vote_team(room, player.id, approve)
            continue

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
                return
            success = (
                True
                if player.alignment == Alignment.GOOD
                or player.role == Role.SHADOW_MERLIN
                else engine.rng.random() < EVIL_MISSION_SUCCESS_PROBABILITY
            )
            engine.vote_mission(room, player.id, success)
            continue

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
                return
            engine.submit_exile_council_ballot(
                room,
                player.id,
                open_council=bool(engine.rng.randrange(2)),
                target_id=engine.rng.choice(room.players).id,
            )
            continue

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
                return
            engine.submit_exile_council_assassination_decision(
                room,
                player.id,
                bool(engine.rng.randrange(2)),
            )
            continue

        if room.phase == Phase.EXILE_COUNCIL_ASSASSINATION_TARGET:
            player = next(
                (
                    candidate
                    for candidate in room.players
                    if candidate.is_bot
                    and candidate.id
                    not in room.exile_council_assassination_targets
                ),
                None,
            )
            if player is None:
                return
            if player.role == Role.ASSASSIN:
                target_ids = engine.eligible_assassination_targets(room)
            else:
                target_ids = [
                    candidate.id
                    for candidate in room.players
                    if candidate.id != player.id
                ]
            engine.submit_exile_council_assassination_target(
                room,
                player.id,
                engine.rng.choice(target_ids),
            )
            continue

        if room.phase == Phase.LADY_SELECT:
            if room.lady_holder_id is None:
                return
            inspector = room.player(room.lady_holder_id)
            if not inspector.is_bot:
                return
            target_ids = engine.eligible_lady_targets(room)
            if not target_ids:
                return
            engine.inspect_with_lady(
                room, inspector.id, engine.rng.choice(target_ids)
            )
            continue

        if room.phase == Phase.LADY_REVEAL:
            if room.lady_pending_inspector_id is None:
                return
            inspector = room.player(room.lady_pending_inspector_id)
            if not inspector.is_bot:
                return
            engine.acknowledge_lady(room, inspector.id)
            continue

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
                return
            target_ids = engine.eligible_assassination_targets(room)
            engine.assassinate(
                room, assassin.id, engine.rng.choice(target_ids)
            )
            continue

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
                return
            engine.grant_dagger(
                room,
                assassin.id,
                engine.rng.choice(room.dagger_candidate_ids),
            )
            continue

        if room.phase == Phase.FINAL_COUNCIL:
            if room.transformed_player_id is None:
                return
            dissenting = room.player(room.transformed_player_id)
            if not dissenting.is_bot:
                return
            engine.dissenting_assassinate(
                room,
                dissenting.id,
                engine.rng.choice(
                    engine.eligible_dissenting_targets(room)
                ),
            )
            continue

        return

    raise RuntimeError("AI 自动行动超过安全上限")
