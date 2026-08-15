from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping

from backend.app.games.base import GameEngine
from backend.app.games.builtin import BUILTIN_GAME_REGISTRATIONS
from backend.app.games.definition import GameRegistration
from backend.app.games.plugins import validate_game_plugins


@dataclass(frozen=True)
class GameRegistry:
    registrations: tuple[GameRegistration, ...]
    _by_key: Mapping[str, GameRegistration] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        by_key = {
            registration.key: registration
            for registration in self.registrations
        }
        if len(by_key) != len(self.registrations):
            raise ValueError("游戏注册表存在重复 key")
        object.__setattr__(self, "_by_key", MappingProxyType(by_key))

    def get(self, game_key: str | None) -> GameRegistration | None:
        if game_key is None:
            return None
        return self._by_key.get(game_key)

    @property
    def catalog(self) -> tuple[dict[str, str], ...]:
        published = (
            registration
            for registration in self.registrations
            if registration.availability == "enabled"
        )
        return tuple(
            registration.catalog_entry
            for registration in sorted(
                published,
                key=lambda item: (
                    item.source != "official",
                    item.catalog.order,
                ),
            )
        )

    @property
    def names(self) -> Mapping[str, str]:
        return MappingProxyType(
            {
                registration.key: registration.catalog.name
                for registration in self.registrations
            }
        )

    @property
    def scored_game_keys(self) -> frozenset[str]:
        return frozenset(
            registration.key
            for registration in self.registrations
            if registration.records.score_kind != "outcome"
        )

    def create_engines(self) -> dict[str, GameEngine]:
        return {
            registration.key: registration.create_engine()
            for registration in self.registrations
        }


PLUGIN_GAME_REGISTRATIONS = tuple(
    plugin.registration for plugin in validate_game_plugins()
)
GAME_REGISTRY = GameRegistry(
    (*BUILTIN_GAME_REGISTRATIONS, *PLUGIN_GAME_REGISTRATIONS)
)
GAME_REGISTRATIONS = GAME_REGISTRY.registrations
GAME_CATALOG = list(GAME_REGISTRY.catalog)
GAME_NAMES = GAME_REGISTRY.names


def game_registration(game_key: str | None) -> GameRegistration | None:
    return GAME_REGISTRY.get(game_key)


def build_engine_registry() -> dict[str, GameEngine]:
    return GAME_REGISTRY.create_engines()
