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
    connected: bool = True


@dataclass
class ArcadeRoom:
    code: str
    game_key: str
    host_id: str
    players: list[ArcadePlayer]
    state: Any
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
    all_humans_offline_since: datetime | None = None
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
