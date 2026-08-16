from __future__ import annotations

import asyncio
import hashlib
import inspect
import logging
import secrets
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any, Protocol

from backend.app.games.base import GameEngine

from .models import ArcadePlayer, ArcadeRoom


MAX_AUTOMATIC_ACTIONS = 100
DEFAULT_BOT_DIFFICULTY = "normal"
DEFAULT_BOT_TIMEOUT_SECONDS = 12.0


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class BotAction:
    """A normal game action selected for one bot player."""

    player_id: str
    action: str
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class BotAvailability:
    """Whether the shared AI-seat flow is available for one room."""

    available: bool
    reason: str | None = None


class BotActionProvider(Protocol):
    """Optional game-engine capability consumed by ``ArcadeBotService``."""

    def choose_bot_action(self, room: ArcadeRoom) -> BotAction | None: ...


class AsyncBotActionProvider(Protocol):
    """Optional asynchronous provider used by external engine processes."""

    def choose_bot_action_async(
        self, room: ArcadeRoom
    ) -> Awaitable[BotAction | None]: ...


class BotAvailabilityProvider(Protocol):
    """Optional room-aware guard for engines with conditional AI support."""

    def bot_availability(self, room: ArcadeRoom) -> BotAvailability: ...


BotActionApplier = Callable[[BotAction], None]


class ArcadeBotService:
    """Shared bot seats and automatic-action orchestration for Arcade games.

    A game opts in with a synchronous or asynchronous action provider. The
    provider only chooses an action; the room manager applies it through the
    same authoritative ``engine.act`` path used for human actions.
    """

    def __init__(
        self,
        max_automatic_actions: int = MAX_AUTOMATIC_ACTIONS,
    ) -> None:
        self.max_automatic_actions = max_automatic_actions

    @staticmethod
    def supports(engine: GameEngine) -> bool:
        return any(
            callable(getattr(engine, attribute, None))
            for attribute in ("choose_bot_action_async", "choose_bot_action")
        )

    @classmethod
    def availability(
        cls,
        room: ArcadeRoom,
        engine: GameEngine,
    ) -> BotAvailability:
        if not cls.supports(engine):
            return BotAvailability(False, "这个游戏暂时没有接入 AI")
        checker = getattr(engine, "bot_availability", None)
        if not callable(checker):
            return BotAvailability(True)
        result = checker(room)
        if not isinstance(result, BotAvailability):
            raise RuntimeError("AI 可用性配置格式不正确")
        return result

    @staticmethod
    def difficulties(engine: GameEngine) -> tuple[str, ...]:
        configured = getattr(
            engine,
            "bot_difficulties",
            (DEFAULT_BOT_DIFFICULTY,),
        )
        if not isinstance(configured, (tuple, list)) or not configured:
            raise RuntimeError("AI 难度配置不能为空")
        difficulties = tuple(configured)
        if not all(
            isinstance(difficulty, str) and difficulty
            for difficulty in difficulties
        ):
            raise RuntimeError("AI 难度配置格式不正确")
        return difficulties

    def add_player(
        self,
        room: ArcadeRoom,
        engine: GameEngine,
        *,
        difficulty: str | None = None,
    ) -> ArcadePlayer:
        selected_difficulty = difficulty or getattr(
            engine,
            "default_bot_difficulty",
            self.difficulties(engine)[0],
        )
        if selected_difficulty not in self.difficulties(engine):
            raise ValueError("不支持这个 AI 难度")

        existing_names = {player.name.casefold() for player in room.players}
        number = 1
        while f"AI玩家 {number}".casefold() in existing_names:
            number += 1
        player_id = f"bot-{secrets.token_urlsafe(8)}"
        player = ArcadePlayer(
            id=player_id,
            account_id=f"bot:{player_id}",
            name=f"AI玩家 {number}",
            token_hash=hashlib.sha256(secrets.token_bytes(32)).hexdigest(),
            seat=len(room.players),
            is_bot=True,
            bot_difficulty=selected_difficulty,
        )
        room.players.append(player)
        return player

    def advance(
        self,
        room: ArcadeRoom,
        engine: GameEngine,
        apply_action: BotActionApplier,
    ) -> int:
        """Apply consecutive bot actions until a human decision is required."""
        provider = getattr(engine, "choose_bot_action", None)
        if not callable(provider):
            return 0

        applied = 0
        for _ in range(self.max_automatic_actions):
            selected = self._validate_action(room, provider(room))
            if selected is None:
                return applied
            apply_action(selected)
            applied += 1

        raise RuntimeError("AI 自动行动超过安全上限")

    async def select_action(
        self,
        room: ArcadeRoom,
        engine: GameEngine,
    ) -> BotAction | None:
        """Select one action without blocking the Socket.IO event loop.

        The caller supplies an isolated room snapshot and later applies the
        result under the live room lock. External engines may therefore think
        for several seconds without delaying unrelated rooms.
        """
        provider = getattr(engine, "choose_bot_action_async", None)
        asynchronous = callable(provider)
        if not asynchronous:
            provider = getattr(engine, "choose_bot_action", None)
        if not callable(provider):
            return None

        timeout = getattr(
            engine,
            "bot_timeout_seconds",
            DEFAULT_BOT_TIMEOUT_SECONDS,
        )
        try:
            if asynchronous:
                result = await asyncio.wait_for(provider(room), timeout=timeout)
            else:
                result = await asyncio.wait_for(
                    asyncio.to_thread(provider, room),
                    timeout=timeout,
                )
        except Exception:
            logger.warning(
                "AI engine unavailable; using the built-in fallback",
                exc_info=True,
                extra={
                    "event": "bot.engine_fallback",
                    "game_key": room.game_key,
                    "room_code": room.code,
                },
            )
            result = await self._fallback_action(room, engine)

        return self._validate_action(room, result)

    async def _fallback_action(
        self,
        room: ArcadeRoom,
        engine: GameEngine,
    ) -> BotAction | None:
        fallback = getattr(engine, "fallback_bot_action", None)
        if not callable(fallback):
            return None
        if inspect.iscoroutinefunction(fallback):
            return await fallback(room)
        return await asyncio.to_thread(fallback, room)

    @staticmethod
    def _validate_action(
        room: ArcadeRoom,
        selected: BotAction | None,
    ) -> BotAction | None:
        if selected is None:
            return None
        if not isinstance(selected, BotAction):
            raise RuntimeError("AI 策略必须返回 BotAction")
        if not selected.action:
            raise RuntimeError("AI 策略返回了空动作")
        try:
            player = room.player(selected.player_id)
        except KeyError as error:
            raise RuntimeError("AI 策略返回了不存在的玩家") from error
        if not player.is_bot:
            raise RuntimeError("AI 策略不能替真人玩家操作")
        return selected
