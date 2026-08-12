from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass
class ArcadePlayer:
    id: str
    account_id: str
    name: str
    token_hash: str
    seat: int
    avatar_url: str | None = None
    is_bot: bool = False
    bot_difficulty: str | None = None
    is_guest: bool = False
    connected: bool = True
    disconnected_at: datetime | None = None
    disconnect_timeout_handled: bool = False
    disconnect_forfeited: bool = False
    left_room: bool = False


@dataclass(frozen=True)
class ArcadeSpectator:
    id: str
    account_id: str
    name: str
    target_player_id: str
    avatar_url: str | None = None
    is_guest: bool = False


@dataclass
class ArcadeChatMessage:
    id: str
    sender_id: str
    sender_name: str
    content: str
    created_at: str = field(default_factory=utc_now_iso)


@dataclass
class ArcadeGameRequest:
    kind: str
    requester_id: str
    approved_player_ids: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class ArcadeUndoEntry:
    player_id: str
    state: Any


def undo_entry_state(entry: Any) -> Any:
    """Unwrap a tracked undo entry while accepting legacy raw snapshots."""
    return entry.state if isinstance(entry, ArcadeUndoEntry) else entry


@dataclass
class ArcadeRoom:
    code: str
    game_key: str
    host_id: str
    players: list[ArcadePlayer]
    state: Any
    name: str = ""
    options: dict[str, Any] = field(default_factory=dict)
    listed: bool = True
    phase: str = "lobby"
    revision: int = 0
    game_id: str | None = None
    started_at: str | None = None
    ended_at: str | None = None
    winner: str | None = None
    winner_player_ids: list[str] = field(default_factory=list)
    win_reason: str | None = None
    recorded: bool = False
    stats_eligible: bool = True
    round_number: int = 0
    rematch_ready_ids: set[str] = field(default_factory=set)
    pending_request: ArcadeGameRequest | None = None
    chat_messages: list[ArcadeChatMessage] = field(default_factory=list)
    undo_history: list[Any] = field(default_factory=list, repr=False)
    all_humans_offline_since: datetime | None = None
    cleanup_ready: bool = False
    host_offline_since: datetime | None = None
    lock: asyncio.Lock = field(default_factory=asyncio.Lock, repr=False)

    def player(self, player_id: str) -> ArcadePlayer:
        for player in self.players:
            if player.id == player_id:
                return player
        raise KeyError(player_id)

    @property
    def host(self) -> ArcadePlayer:
        return self.player(self.host_id)

    def finish(
        self,
        winner: str,
        winner_player_ids: list[str],
        reason: str,
    ) -> None:
        if self.phase == "finished":
            return
        self.phase = "finished"
        self.winner = winner
        self.winner_player_ids = winner_player_ids
        self.win_reason = reason
        self.ended_at = utc_now_iso()
        self.revision += 1
