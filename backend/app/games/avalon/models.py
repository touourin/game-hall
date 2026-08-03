from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class Alignment(str, Enum):
    GOOD = "good"
    EVIL = "evil"


class AvalonMode(str, Enum):
    STANDARD = "standard"
    COURT_UNDERCURRENT = "court_undercurrent"


class Role(str, Enum):
    MERLIN = "merlin"
    PERCIVAL = "percival"
    LOYAL_SERVANT = "loyal_servant"
    DISSENTING_COURTIER = "dissenting_courtier"
    ASSASSIN = "assassin"
    MORGANA = "morgana"
    MORDRED = "mordred"
    OBERON = "oberon"
    MINION = "minion"


class Phase(str, Enum):
    LOBBY = "lobby"
    ROLE_REVEAL = "role_reveal"
    TEAM_BUILDING = "team_building"
    TEAM_VOTING = "team_voting"
    MISSION_VOTING = "mission_voting"
    ROUND_RESULT = "round_result"
    LADY_SELECT = "lady_select"
    LADY_REVEAL = "lady_reveal"
    ASSASSINATION = "assassination"
    DAGGER_GRANT = "dagger_grant"
    FINAL_COUNCIL = "final_council"
    GAME_OVER = "game_over"


ROLE_ALIGNMENT: dict[Role, Alignment] = {
    Role.MERLIN: Alignment.GOOD,
    Role.PERCIVAL: Alignment.GOOD,
    Role.LOYAL_SERVANT: Alignment.GOOD,
    Role.DISSENTING_COURTIER: Alignment.GOOD,
    Role.ASSASSIN: Alignment.EVIL,
    Role.MORGANA: Alignment.EVIL,
    Role.MORDRED: Alignment.EVIL,
    Role.OBERON: Alignment.EVIL,
    Role.MINION: Alignment.EVIL,
}


@dataclass
class Player:
    id: str
    name: str
    token_hash: str
    seat: int
    account_id: str | None = None
    avatar_url: str | None = None
    connected: bool = True
    disconnected_at: datetime | None = None
    disconnect_forfeited: bool = False
    is_bot: bool = False
    role: Role | None = None
    alignment_override: Alignment | None = None

    @property
    def alignment(self) -> Alignment | None:
        if self.alignment_override is not None:
            return self.alignment_override
        return ROLE_ALIGNMENT[self.role] if self.role is not None else None


@dataclass
class MissionRecord:
    number: int
    team_ids: list[str]
    success: bool
    fail_count: int
    failed_by_rejections: bool = False


@dataclass
class ProposalRecord:
    mission_number: int
    attempt: int
    leader_id: str
    team_ids: list[str]
    votes: dict[str, bool]
    accepted: bool


@dataclass
class LadyCheck:
    inspector_id: str
    target_id: str
    alignment: Alignment
    mission_number: int


@dataclass
class ChatMessage:
    id: str
    sender_id: str
    sender_name: str
    content: str
    created_at: str


@dataclass
class GameSettings:
    mode: AvalonMode = AvalonMode.STANDARD
    lady_enabled: bool = True
    listed: bool = True
    early_assassination_enabled: bool = False


@dataclass
class Room:
    code: str
    host_id: str
    players: list[Player]
    settings: GameSettings = field(default_factory=GameSettings)
    phase: Phase = Phase.LOBBY
    game_id: str | None = None
    game_started_at: str | None = None
    revision: int = 0
    leader_index: int = 0
    mission_index: int = 0
    proposal_attempt: int = 1
    selected_team_ids: list[str] = field(default_factory=list)
    team_votes: dict[str, bool] = field(default_factory=dict)
    last_team_votes: dict[str, bool] = field(default_factory=dict)
    mission_votes: dict[str, bool] = field(default_factory=dict)
    mission_history: list[MissionRecord] = field(default_factory=list)
    proposal_history: list[ProposalRecord] = field(default_factory=list)
    role_confirmed_ids: set[str] = field(default_factory=set)
    winner: Alignment | None = None
    win_reason: str | None = None
    assassin_target_id: str | None = None
    assassination_was_early: bool = False
    ending_route: str | None = None
    dagger_candidate_ids: list[str] = field(default_factory=list)
    dagger_target_id: str | None = None
    dagger_hit: bool | None = None
    transformed_player_id: str | None = None
    dissenting_assassination_target_id: str | None = None
    lady_holder_id: str | None = None
    lady_used_by_ids: set[str] = field(default_factory=set)
    lady_checks: list[LadyCheck] = field(default_factory=list)
    lady_pending_inspector_id: str | None = None
    lady_pending_target_id: str | None = None
    chat_messages: list[ChatMessage] = field(default_factory=list)
    all_humans_offline_since: datetime | None = None
    cleanup_ready: bool = False
    host_offline_since: datetime | None = None
    lock: asyncio.Lock = field(default_factory=asyncio.Lock, repr=False)

    def player(self, player_id: str) -> Player:
        for player in self.players:
            if player.id == player_id:
                return player
        raise KeyError(player_id)

    @property
    def leader(self) -> Player:
        return self.players[self.leader_index]

    @property
    def success_count(self) -> int:
        return sum(record.success for record in self.mission_history)

    @property
    def fail_count(self) -> int:
        return len(self.mission_history) - self.success_count
