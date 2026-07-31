from __future__ import annotations

from typing import Any, Protocol, TYPE_CHECKING

if TYPE_CHECKING:
    from backend.app.arcade.models import ArcadePlayer, ArcadeRoom


class GameRuleError(ValueError):
    """Raised when a player submits an action that violates game rules."""


class GameEngine(Protocol):
    key: str
    name: str
    min_players: int
    max_players: int

    def initial_state(self) -> Any: ...

    def start(self, room: ArcadeRoom) -> None: ...

    def act(
        self,
        room: ArcadeRoom,
        player: ArcadePlayer,
        action: str,
        payload: dict[str, Any],
    ) -> None: ...

    def view(self, room: ArcadeRoom, viewer: ArcadePlayer) -> dict[str, Any]: ...

    def player_result(
        self, room: ArcadeRoom, player: ArcadePlayer
    ) -> tuple[str, str, bool]: ...
