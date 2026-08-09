from __future__ import annotations

import asyncio
import copy
import random
from typing import TYPE_CHECKING

from backend.app.ai import KataGoAnalysisClient
from backend.app.arcade.bots import BotAction
from backend.app.arcade.models import ArcadePlayer, ArcadeRoom
from backend.app.games.base import GameRuleError

if TYPE_CHECKING:
    from .engine import GoEngine, GoState


GTP_COLUMNS = "ABCDEFGHJKLMNOPQRST"


class GoBotStrategy:
    def __init__(
        self,
        engine: GoEngine,
        client: KataGoAnalysisClient | None = None,
        rng: random.Random | random.SystemRandom | None = None,
    ) -> None:
        self.engine = engine
        self.client = client or KataGoAnalysisClient()
        self.rng = rng or random.SystemRandom()

    async def choose_action(self, room: ArcadeRoom) -> BotAction | None:
        bot = self._active_bot(room)
        if bot is None:
            return None
        if room.phase == "scoring":
            return BotAction(bot.id, "confirm_score")
        if not getattr(self.client, "configured", True):
            return await asyncio.to_thread(self.fallback_action, room)

        result = await self.client.analyze(
            self._query(room),
            bot.bot_difficulty or "normal",
        )
        move_infos = result.get("moveInfos")
        move = (
            move_infos[0].get("move")
            if isinstance(move_infos, list) and move_infos
            else None
        )
        selected = self._action_from_gtp(bot, move, len(room.state.board))
        if selected is None or not await asyncio.to_thread(
            self._is_legal, room, selected
        ):
            return await asyncio.to_thread(self.fallback_action, room)
        return selected

    def fallback_action(self, room: ArcadeRoom) -> BotAction | None:
        bot = self._active_bot(room)
        if bot is None:
            return None
        if room.phase == "scoring":
            return BotAction(bot.id, "confirm_score")
        state: GoState = room.state
        board_size = len(state.board)
        candidates = [
            (row, column)
            for row in range(board_size)
            for column in range(board_size)
            if state.board[row][column] == 0
        ]
        self.rng.shuffle(candidates)
        difficulty = bot.bot_difficulty or "normal"
        if difficulty != "easy":
            center = (board_size - 1) / 2
            candidates.sort(
                key=lambda point: (
                    abs(point[0] - center) + abs(point[1] - center)
                    + self.rng.random() * (6 if difficulty == "normal" else 1)
                )
            )
        for row, column in candidates:
            action = BotAction(bot.id, "place", {"row": row, "column": column})
            if self._is_legal(room, action):
                return action
        return BotAction(bot.id, "pass")

    async def close(self) -> None:
        await self.client.close()

    def _active_bot(self, room: ArcadeRoom) -> ArcadePlayer | None:
        if len(room.players) != 2:
            return None
        state: GoState = room.state
        if room.phase == "playing":
            player = room.players[state.turn_seat]
            return player if player.is_bot else None
        if room.phase == "scoring":
            return next(
                (
                    player
                    for player in room.players
                    if player.is_bot
                    and player.id not in state.score_confirmed_player_ids
                ),
                None,
            )
        return None

    @staticmethod
    def _query(room: ArcadeRoom) -> dict:
        state: GoState = room.state
        board_size = len(state.board)
        history = getattr(state, "move_history", [])
        query = {
            "rules": "chinese",
            "komi": float(room.options.get("komi", 7.5)),
            "boardXSize": board_size,
            "boardYSize": board_size,
            "moves": [
                [
                    "B" if int(move["seat"]) == 0 else "W",
                    "pass"
                    if move.get("pass")
                    else GoBotStrategy._to_gtp(
                        int(move["row"]), int(move["column"]), board_size
                    ),
                ]
                for move in history
            ],
        }
        if not history and any(cell for row in state.board for cell in row):
            query["initialStones"] = [
                [
                    "B" if stone == 1 else "W",
                    GoBotStrategy._to_gtp(row, column, board_size),
                ]
                for row, line in enumerate(state.board)
                for column, stone in enumerate(line)
                if stone
            ]
            query["initialPlayer"] = "B" if state.turn_seat == 0 else "W"
        return query

    def _is_legal(self, room: ArcadeRoom, action: BotAction) -> bool:
        clone = copy.deepcopy(room)
        try:
            self.engine.act(
                clone,
                clone.player(action.player_id),
                action.action,
                dict(action.payload),
            )
        except (GameRuleError, IndexError, KeyError, TypeError, ValueError):
            return False
        return True

    @staticmethod
    def _action_from_gtp(
        bot: ArcadePlayer,
        move: object,
        board_size: int,
    ) -> BotAction | None:
        if not isinstance(move, str):
            return None
        if move.casefold() == "pass":
            return BotAction(bot.id, "pass")
        column_letter = move[:1].upper()
        if column_letter not in GTP_COLUMNS[:board_size]:
            return None
        try:
            row_number = int(move[1:])
        except ValueError:
            return None
        row = board_size - row_number
        if not 0 <= row < board_size:
            return None
        return BotAction(
            bot.id,
            "place",
            {"row": row, "column": GTP_COLUMNS.index(column_letter)},
        )

    @staticmethod
    def _to_gtp(row: int, column: int, board_size: int) -> str:
        return f"{GTP_COLUMNS[column]}{board_size - row}"
