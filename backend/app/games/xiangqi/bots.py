from __future__ import annotations

import asyncio
import copy
import random
import string
from typing import TYPE_CHECKING

from backend.app.ai import PikafishClient
from backend.app.arcade.bots import BotAction
from backend.app.arcade.models import ArcadePlayer, ArcadeRoom
from backend.app.games.base import GameRuleError

if TYPE_CHECKING:
    from .engine import XiangqiEngine, XiangqiState


PIECE_TO_FEN = {
    "R": "r",
    "H": "n",
    "E": "b",
    "A": "a",
    "K": "k",
    "C": "c",
    "P": "p",
}
PIECE_VALUES = {
    "K": 10_000,
    "R": 900,
    "C": 450,
    "H": 400,
    "E": 200,
    "A": 200,
    "P": 100,
}


class XiangqiBotStrategy:
    def __init__(
        self,
        engine: XiangqiEngine,
        client: PikafishClient | None = None,
        rng: random.Random | random.SystemRandom | None = None,
    ) -> None:
        self.engine = engine
        self.client = client or PikafishClient()
        self.rng = rng or random.SystemRandom()

    async def choose_action(self, room: ArcadeRoom) -> BotAction | None:
        bot = self._active_bot(room)
        if bot is None:
            return None
        if not getattr(self.client, "configured", True):
            return await asyncio.to_thread(self.fallback_action, room)
        state: XiangqiState = room.state
        uci_move = await self.client.best_move(
            self._fen(state),
            bot.bot_difficulty or "normal",
        )
        move = self._parse_move(uci_move) if uci_move else None
        legal_moves = self.engine._legal_moves(state.board, state.turn_color)
        if move is None or not any(
            all(candidate.get(key) == value for key, value in move.items())
            for candidate in legal_moves
        ):
            return await asyncio.to_thread(self.fallback_action, room)
        selected = BotAction(bot.id, "move", move)
        if await asyncio.to_thread(self._is_legal, room, selected):
            return selected
        return await asyncio.to_thread(self.fallback_action, room)

    def fallback_action(self, room: ArcadeRoom) -> BotAction | None:
        bot = self._active_bot(room)
        if bot is None:
            return None
        state: XiangqiState = room.state
        moves = self.engine._legal_moves(state.board, state.turn_color)
        if not moves:
            return None
        difficulty = bot.bot_difficulty or "normal"
        if difficulty == "easy":
            self.rng.shuffle(moves)
        else:
            moves.sort(
                key=lambda move: self._move_score(state, move, difficulty),
                reverse=True,
            )
        for move in moves:
            selected = BotAction(bot.id, "move", dict(move))
            if self._is_legal(room, selected):
                return selected
        return None

    async def close(self) -> None:
        await self.client.close()

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

    def _active_bot(self, room: ArcadeRoom) -> ArcadePlayer | None:
        if room.phase != "playing" or len(room.players) != 2:
            return None
        state: XiangqiState = room.state
        seat = state.seat_colors.index(state.turn_color)
        player = room.players[seat]
        return player if player.is_bot else None

    def _move_score(
        self,
        state: XiangqiState,
        move: dict[str, int | bool],
        difficulty: str,
    ) -> float:
        target = state.board[int(move["toRow"])][int(move["toColumn"])]
        capture_value = PIECE_VALUES.get(target[1], 0) if target else 0
        center = 4 - abs(4 - int(move["toColumn"]))
        noise = self.rng.random() * (80 if difficulty == "normal" else 8)
        return capture_value + center + noise

    @staticmethod
    def _fen(state: XiangqiState) -> str:
        rows: list[str] = []
        for board_row in state.board:
            empty = 0
            encoded: list[str] = []
            for piece in board_row:
                if piece is None:
                    empty += 1
                    continue
                if empty:
                    encoded.append(str(empty))
                    empty = 0
                letter = PIECE_TO_FEN[piece[1]]
                encoded.append(letter.upper() if piece[0] == "r" else letter)
            if empty:
                encoded.append(str(empty))
            rows.append("".join(encoded))
        side = "w" if state.turn_color == "red" else "b"
        fullmove = max(1, state.move_count // 2 + 1)
        return f"{'/'.join(rows)} {side} - - 0 {fullmove}"

    @staticmethod
    def _parse_move(move: str) -> dict[str, int] | None:
        if len(move) < 4:
            return None
        source_file, source_rank, target_file, target_rank = move[:4]
        if (
            source_file not in string.ascii_lowercase[:9]
            or target_file not in string.ascii_lowercase[:9]
            or source_rank not in string.digits[:10]
            or target_rank not in string.digits[:10]
        ):
            return None
        return {
            "fromRow": 9 - int(source_rank),
            "fromColumn": ord(source_file) - ord("a"),
            "toRow": 9 - int(target_rank),
            "toColumn": ord(target_file) - ord("a"),
        }
