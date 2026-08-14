from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import Any, Literal

from backend.app.games.base import GameEngine


@dataclass(frozen=True)
class GameCapabilities:
    """Platform features used by a built-in game.

    Game-specific rules stay on the engine.  This object only describes the
    services supplied by the shared room platform.
    """

    undo_actions: frozenset[str] = field(default_factory=frozenset)
    draw_requests: bool = False
    guests: bool = True
    spectators: bool = True
    first_player: bool = True
    replay: bool = False
    ai: bool = False

    @property
    def undo_requests(self) -> bool:
        return bool(self.undo_actions)


def social_table_capabilities(
    *,
    guests: bool = True,
    spectators: bool = True,
    first_player: bool = True,
    replay: bool = False,
    ai: bool = False,
) -> GameCapabilities:
    """Shared platform defaults for social, card, and party tables."""

    return GameCapabilities(
        guests=guests,
        spectators=spectators,
        first_player=first_player,
        replay=replay,
        ai=ai,
    )


@dataclass(frozen=True)
class GameCatalogMetadata:
    order: int
    name: str
    min_players: int
    max_players: int
    description: str
    players_label: str | None = None

    @property
    def players(self) -> str:
        if self.players_label:
            return self.players_label
        if self.min_players == self.max_players:
            return f"{self.min_players} 人"
        return f"{self.min_players}–{self.max_players} 人"

    def as_dict(self, key: str) -> dict[str, str]:
        return {
            "key": key,
            "name": self.name,
            "players": self.players,
            "description": self.description,
        }


GameScoreKind = Literal["outcome", "time_trial", "high_score"]


class GameRecordQueryError(ValueError):
    """Raised when shared stats endpoints receive unsupported filters."""


def standard_match_mode(_: Mapping[str, Any]) -> str:
    return "standard"


@dataclass(frozen=True)
class GameRecords:
    """How the shared account service stores and aggregates game records."""

    score_kind: GameScoreKind = "outcome"
    match_mode: Callable[[Mapping[str, Any]], str] = standard_match_mode
    query_modes: frozenset[str] = field(default_factory=frozenset)
    query_variants: Mapping[str, frozenset[str]] = field(default_factory=dict)
    invalid_mode_message: str = "游戏模式或难度不正确"
    invalid_variant_message: str = "战绩统计分组不正确"

    def validate_query(
        self,
        mode: str | None,
        variant: str | None,
    ) -> None:
        if mode is not None and mode not in self.query_modes:
            raise GameRecordQueryError(self.invalid_mode_message)
        if variant is None:
            return
        allowed_variants = self.query_variants.get(mode or "", frozenset())
        if variant not in allowed_variants:
            raise GameRecordQueryError(self.invalid_variant_message)


@dataclass(frozen=True)
class GameDefinition:
    key: str
    engine_factory: Callable[[], GameEngine]
    catalog: GameCatalogMetadata
    capabilities: GameCapabilities = field(default_factory=GameCapabilities)
    records: GameRecords = field(default_factory=GameRecords)

    def create_engine(self) -> GameEngine:
        engine = self.engine_factory()
        if engine.key != self.key:
            raise ValueError(
                f"官方游戏 {self.key} 的引擎 key 不一致：{engine.key}"
            )
        if engine.name != self.catalog.name:
            raise ValueError(
                f"官方游戏 {self.key} 的目录名称与引擎名称不一致"
            )
        if (
            engine.min_players != self.catalog.min_players
            or engine.max_players != self.catalog.max_players
        ):
            raise ValueError(
                f"官方游戏 {self.key} 的目录人数与引擎人数不一致"
            )
        supports_ai = any(
            callable(getattr(engine, attribute, None))
            for attribute in ("choose_bot_action_async", "choose_bot_action")
        )
        if supports_ai != self.capabilities.ai:
            raise ValueError(
                f"官方游戏 {self.key} 的 AI 能力声明与引擎不一致"
            )
        return engine

    @property
    def catalog_entry(self) -> dict[str, str]:
        return self.catalog.as_dict(self.key)
