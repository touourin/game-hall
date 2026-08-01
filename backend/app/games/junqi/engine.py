from __future__ import annotations

import random
from collections import deque
from dataclasses import dataclass, field
from typing import Any

from backend.app.arcade.models import ArcadePlayer, ArcadeRoom
from backend.app.games.base import GameRuleError


ROWS = 12
COLUMNS = 5
SIDES = ("red", "blue")
MODE_LABELS = {"dark": "暗军旗", "flip": "翻棋军旗"}

CAMPS = {
    (1, 1), (1, 3), (2, 2), (3, 1), (3, 3),
    (8, 1), (8, 3), (9, 2), (10, 1), (10, 3),
}
HEADQUARTERS = {(0, 1), (0, 3), (11, 1), (11, 3)}
RAIL_ROWS = {1, 5, 6, 10}

PIECE_COUNTS = {
    "commander": 1,
    "general": 1,
    "division": 2,
    "brigade": 2,
    "regiment": 2,
    "battalion": 2,
    "company": 3,
    "platoon": 3,
    "engineer": 3,
    "bomb": 2,
    "mine": 3,
    "flag": 1,
}
PIECE_LABELS = {
    "commander": "司令",
    "general": "军长",
    "division": "师长",
    "brigade": "旅长",
    "regiment": "团长",
    "battalion": "营长",
    "company": "连长",
    "platoon": "排长",
    "engineer": "工兵",
    "bomb": "炸弹",
    "mine": "地雷",
    "flag": "军旗",
}
RANKS = {
    "commander": 9,
    "general": 8,
    "division": 7,
    "brigade": 6,
    "regiment": 5,
    "battalion": 4,
    "company": 3,
    "platoon": 2,
    "engineer": 1,
}


@dataclass
class JunqiPiece:
    id: str
    side: int
    kind: str
    revealed: bool = False


@dataclass
class JunqiState:
    mode: str = "dark"
    board: list[list[JunqiPiece | None]] = field(
        default_factory=lambda: [[None] * COLUMNS for _ in range(ROWS)]
    )
    turn_seat: int = 0
    seat_sides: list[int | None] = field(default_factory=lambda: [0, 1])
    setup_ready: list[bool] = field(default_factory=lambda: [False, False])
    commander_captured: list[bool] = field(default_factory=lambda: [False, False])
    move_count: int = 0
    last_action: dict[str, Any] | None = None
    history: list[dict[str, Any]] = field(default_factory=list)


class JunqiEngine:
    key = "junqi"
    name = "军旗"
    min_players = 2
    max_players = 2

    def room_options(self, options: dict[str, Any]) -> dict[str, Any]:
        mode = options.get("mode", "dark")
        if mode not in MODE_LABELS:
            raise GameRuleError("请选择暗军旗或翻棋军旗")
        return {"mode": mode}

    def initial_state(self) -> JunqiState:
        return JunqiState()

    def start(self, room: ArcadeRoom) -> None:
        mode = room.options.get("mode", "dark")
        state = JunqiState(mode=mode)
        if mode == "dark":
            state.seat_sides = [0, 1]
            self._deploy_dark_side(state, 0)
            self._deploy_dark_side(state, 1)
            room.phase = "setup"
        else:
            state.seat_sides = [None, None]
            self._deploy_flip(state)
            room.phase = "playing"
        room.state = state

    def act(
        self,
        room: ArcadeRoom,
        player: ArcadePlayer,
        action: str,
        payload: dict[str, Any],
    ) -> None:
        state: JunqiState = room.state
        if action == "resign":
            opponent = room.players[1 - player.seat]
            winner_side = self._side_for_seat(state, opponent.seat)
            room.finish(
                SIDES[winner_side],
                [opponent.id],
                f"{player.name} 认输，{opponent.name} 获胜",
            )
            return
        if room.phase == "setup":
            self._setup_action(room, player, action, payload)
            return
        if room.phase != "playing":
            raise GameRuleError("当前不能进行军旗操作")
        if player.seat != state.turn_seat:
            raise GameRuleError("还没有轮到你")
        if action == "flip":
            self._flip(room, player, payload)
            return
        if action == "move":
            self._move(room, player, payload)
            return
        raise GameRuleError("不支持这个军旗操作")

    def view(self, room: ArcadeRoom, viewer: ArcadePlayer) -> dict[str, Any]:
        state: JunqiState = room.state
        viewer_side = state.seat_sides[viewer.seat]
        board: list[list[dict[str, Any] | None]] = []
        for row in state.board:
            public_row: list[dict[str, Any] | None] = []
            for piece in row:
                if piece is None:
                    public_row.append(None)
                    continue
                if state.mode == "flip":
                    visible = piece.revealed
                else:
                    visible = (
                        piece.side == viewer_side
                        or (
                            piece.kind == "flag"
                            and state.commander_captured[piece.side]
                        )
                    )
                public_row.append(
                    {
                        "id": piece.id if visible else None,
                        "side": SIDES[piece.side] if visible or state.mode == "dark" else None,
                        "kind": piece.kind if visible else None,
                        "label": PIECE_LABELS[piece.kind] if visible else None,
                        "revealed": visible,
                    }
                )
            board.append(public_row)
        colors = {
            room.players[seat].id: SIDES[side]
            for seat, side in enumerate(state.seat_sides)
            if side is not None and seat < len(room.players)
        }
        return {
            "mode": state.mode,
            "modeLabel": MODE_LABELS[state.mode],
            "board": board,
            "rows": ROWS,
            "columns": COLUMNS,
            "turnPlayerId": (
                room.players[state.turn_seat].id
                if room.phase == "playing" and len(room.players) == 2
                else None
            ),
            "colors": colors,
            "viewerSide": SIDES[viewer_side] if viewer_side is not None else None,
            "setupReady": {
                room.players[seat].id: ready
                for seat, ready in enumerate(state.setup_ready)
                if seat < len(room.players)
            },
            "lastAction": state.last_action,
            "moveCount": state.move_count,
            "terrain": {
                "camps": [list(position) for position in sorted(CAMPS)],
                "headquarters": [list(position) for position in sorted(HEADQUARTERS)],
            },
        }

    def player_result(
        self, room: ArcadeRoom, player: ArcadePlayer
    ) -> tuple[str, str, bool]:
        state: JunqiState = room.state
        side = SIDES[self._side_for_seat(state, player.seat)]
        return (
            f"{state.mode}-{side}",
            side,
            player.id in room.winner_player_ids,
        )

    def _setup_action(
        self,
        room: ArcadeRoom,
        player: ArcadePlayer,
        action: str,
        payload: dict[str, Any],
    ) -> None:
        state: JunqiState = room.state
        if state.mode != "dark":
            raise GameRuleError("翻棋军旗不需要布阵")
        if state.setup_ready[player.seat]:
            raise GameRuleError("你已经确认布阵")
        side = self._side_for_seat(state, player.seat)
        if action == "randomize":
            self._clear_side(state, side)
            self._deploy_dark_side(state, side)
            return
        if action == "swap":
            source = self._position(payload, "fromRow", "fromColumn")
            target = self._position(payload, "toRow", "toColumn")
            source_piece = state.board[source[0]][source[1]]
            target_piece = state.board[target[0]][target[1]]
            if (
                source_piece is None
                or target_piece is None
                or source_piece.side != side
                or target_piece.side != side
            ):
                raise GameRuleError("只能交换自己的两枚棋子")
            state.board[source[0]][source[1]], state.board[target[0]][target[1]] = (
                target_piece,
                source_piece,
            )
            if not self._valid_deployment(state, side):
                state.board[source[0]][source[1]], state.board[target[0]][target[1]] = (
                    source_piece,
                    target_piece,
                )
                raise GameRuleError("军旗必须在大本营，地雷在后两排，炸弹不能在第一排")
            return
        if action == "ready":
            if not self._valid_deployment(state, side):
                raise GameRuleError("当前布阵不符合规则")
            state.setup_ready[player.seat] = True
            if all(state.setup_ready):
                room.phase = "playing"
                state.turn_seat = 0
                state.last_action = {"type": "ready", "message": "双方布阵完成，红方先行"}
            return
        raise GameRuleError("布阵阶段只能交换、随机或确认棋子")

    def _flip(
        self,
        room: ArcadeRoom,
        player: ArcadePlayer,
        payload: dict[str, Any],
    ) -> None:
        state: JunqiState = room.state
        if state.mode != "flip":
            raise GameRuleError("暗军旗不能翻棋")
        row, column = self._position(payload, "row", "column")
        piece = state.board[row][column]
        if piece is None or piece.revealed:
            raise GameRuleError("请选择一枚未翻开的棋子")
        piece.revealed = True
        if state.seat_sides[player.seat] is None:
            state.seat_sides[player.seat] = piece.side
            state.seat_sides[1 - player.seat] = 1 - piece.side
        state.last_action = {
            "type": "flip",
            "row": row,
            "column": column,
            "side": SIDES[piece.side],
            "label": PIECE_LABELS[piece.kind],
            "actorSeat": player.seat,
            "message": f"翻开{self._side_label(piece.side)}{PIECE_LABELS[piece.kind]}",
        }
        state.history.append(dict(state.last_action))
        state.move_count += 1
        state.turn_seat = 1 - player.seat

    def _move(
        self,
        room: ArcadeRoom,
        player: ArcadePlayer,
        payload: dict[str, Any],
    ) -> None:
        state: JunqiState = room.state
        source = self._position(payload, "fromRow", "fromColumn")
        target = self._position(payload, "toRow", "toColumn")
        piece = state.board[source[0]][source[1]]
        defender = state.board[target[0]][target[1]]
        player_side = state.seat_sides[player.seat]
        if player_side is None:
            raise GameRuleError("请先翻开一枚棋子确定阵营")
        if piece is None or piece.side != player_side:
            raise GameRuleError("请选择自己的棋子")
        if state.mode == "flip" and not piece.revealed:
            raise GameRuleError("未翻开的棋子不能移动")
        if defender is not None:
            if state.mode == "flip" and not defender.revealed:
                raise GameRuleError("必须先翻开目标棋子")
            if defender.side == piece.side:
                raise GameRuleError("不能移动到自己的棋子上")
            if target in CAMPS:
                raise GameRuleError("行营中的棋子不能被攻击")
        if not self._can_move(state.board, piece, source, target):
            raise GameRuleError("这枚棋子不能这样移动")

        action_result = "move"
        if defender is None:
            state.board[target[0]][target[1]] = piece
            state.board[source[0]][source[1]] = None
        else:
            action_result = self._combat(piece, defender)
            if action_result in {"attacker", "flag"}:
                self._mark_removed(state, defender)
                state.board[target[0]][target[1]] = piece
                state.board[source[0]][source[1]] = None
            elif action_result == "defender":
                self._mark_removed(state, piece)
                state.board[source[0]][source[1]] = None
            else:
                self._mark_removed(state, piece)
                self._mark_removed(state, defender)
                state.board[source[0]][source[1]] = None
                state.board[target[0]][target[1]] = None

        messages = {
            "move": "完成移动",
            "attacker": "进攻方获胜",
            "defender": "防守方获胜",
            "both": "双方同归于尽",
            "flag": "夺取军旗",
        }
        state.last_action = {
            "type": "move",
            "fromRow": source[0],
            "fromColumn": source[1],
            "toRow": target[0],
            "toColumn": target[1],
            "actorSeat": player.seat,
            "result": action_result,
            "message": messages[action_result],
        }
        state.history.append(dict(state.last_action))
        state.move_count += 1

        if action_result == "flag":
            room.finish(
                SIDES[player_side],
                [player.id],
                f"{player.name} 夺取对方军旗",
            )
            return
        opponent_seat = 1 - player.seat
        opponent_side = state.seat_sides[opponent_seat]
        if opponent_side is not None and not self._has_movable_piece(state, opponent_side):
            room.finish(
                SIDES[player_side],
                [player.id],
                f"{room.players[opponent_seat].name} 已无可移动棋子",
            )
            return
        state.turn_seat = opponent_seat

    def _deploy_dark_side(self, state: JunqiState, side: int) -> None:
        positions = self._side_positions(side)
        headquarters = list(self._side_headquarters(side))
        rear_rows = {10, 11} if side == 0 else {0, 1}
        front_row = 6 if side == 0 else 5
        available = set(positions)

        flag_position = random.choice(headquarters)
        self._place_piece(state, flag_position, side, "flag", 0)
        available.remove(flag_position)

        mine_positions = random.sample(
            [position for position in available if position[0] in rear_rows], 3
        )
        for index, position in enumerate(mine_positions):
            self._place_piece(state, position, side, "mine", index)
            available.remove(position)

        bomb_positions = random.sample(
            [position for position in available if position[0] != front_row], 2
        )
        for index, position in enumerate(bomb_positions):
            self._place_piece(state, position, side, "bomb", index)
            available.remove(position)

        remaining_kinds = [
            kind
            for kind, count in PIECE_COUNTS.items()
            if kind not in {"flag", "mine", "bomb"}
            for _ in range(count)
        ]
        remaining_positions = list(available)
        random.shuffle(remaining_kinds)
        random.shuffle(remaining_positions)
        seen: dict[str, int] = {}
        for position, kind in zip(remaining_positions, remaining_kinds):
            index = seen.get(kind, 0)
            seen[kind] = index + 1
            self._place_piece(state, position, side, kind, index)

    def _deploy_flip(self, state: JunqiState) -> None:
        pieces = [
            JunqiPiece(f"{side}-{kind}-{index}", side, kind)
            for side in range(2)
            for kind, count in PIECE_COUNTS.items()
            for index in range(count)
        ]
        positions = [
            (row, column)
            for row in range(ROWS)
            for column in range(COLUMNS)
            if (row, column) not in CAMPS
        ]
        random.shuffle(pieces)
        random.shuffle(positions)
        for position, piece in zip(positions, pieces):
            state.board[position[0]][position[1]] = piece

    @staticmethod
    def _place_piece(
        state: JunqiState,
        position: tuple[int, int],
        side: int,
        kind: str,
        index: int,
    ) -> None:
        state.board[position[0]][position[1]] = JunqiPiece(
            id=f"{side}-{kind}-{index}",
            side=side,
            kind=kind,
        )

    @staticmethod
    def _clear_side(state: JunqiState, side: int) -> None:
        for row in range(ROWS):
            for column in range(COLUMNS):
                piece = state.board[row][column]
                if piece is not None and piece.side == side:
                    state.board[row][column] = None

    def _valid_deployment(self, state: JunqiState, side: int) -> bool:
        placements = [
            ((row, column), piece)
            for row in range(ROWS)
            for column in range(COLUMNS)
            if (piece := state.board[row][column]) is not None and piece.side == side
        ]
        if len(placements) != 25:
            return False
        allowed = set(self._side_positions(side))
        if any(position not in allowed for position, _ in placements):
            return False
        rear_rows = {10, 11} if side == 0 else {0, 1}
        front_row = 6 if side == 0 else 5
        for position, piece in placements:
            if piece.kind == "flag" and position not in self._side_headquarters(side):
                return False
            if piece.kind == "mine" and position[0] not in rear_rows:
                return False
            if piece.kind == "bomb" and position[0] == front_row:
                return False
        return True

    @staticmethod
    def _side_positions(side: int) -> list[tuple[int, int]]:
        rows = range(6, 12) if side == 0 else range(0, 6)
        return [
            (row, column)
            for row in rows
            for column in range(COLUMNS)
            if (row, column) not in CAMPS
        ]

    @staticmethod
    def _side_headquarters(side: int) -> set[tuple[int, int]]:
        row = 11 if side == 0 else 0
        return {(row, 1), (row, 3)}

    def _can_move(
        self,
        board: list[list[JunqiPiece | None]],
        piece: JunqiPiece,
        source: tuple[int, int],
        target: tuple[int, int],
    ) -> bool:
        if source == target or piece.kind in {"mine", "flag"} or source in HEADQUARTERS:
            return False
        if target in self._road_neighbors(source):
            return True
        if piece.kind == "engineer":
            return self._engineer_rail_reachable(board, source, target)
        return self._straight_rail_reachable(board, source, target)

    def _straight_rail_reachable(
        self,
        board: list[list[JunqiPiece | None]],
        source: tuple[int, int],
        target: tuple[int, int],
    ) -> bool:
        if source[0] != target[0] and source[1] != target[1]:
            return False
        row_step = 0 if source[0] == target[0] else (1 if target[0] > source[0] else -1)
        column_step = 0 if source[1] == target[1] else (1 if target[1] > source[1] else -1)
        current = source
        while current != target:
            following = (current[0] + row_step, current[1] + column_step)
            if not self._is_rail_edge(current, following):
                return False
            if following != target and board[following[0]][following[1]] is not None:
                return False
            current = following
        return True

    def _engineer_rail_reachable(
        self,
        board: list[list[JunqiPiece | None]],
        source: tuple[int, int],
        target: tuple[int, int],
    ) -> bool:
        queue = deque([source])
        visited = {source}
        while queue:
            current = queue.popleft()
            for neighbor in self._rail_neighbors(current):
                if neighbor in visited:
                    continue
                if neighbor == target:
                    return True
                if board[neighbor[0]][neighbor[1]] is not None:
                    continue
                visited.add(neighbor)
                queue.append(neighbor)
        return False

    @staticmethod
    def _road_neighbors(position: tuple[int, int]) -> set[tuple[int, int]]:
        row, column = position
        neighbors: set[tuple[int, int]] = set()
        for row_step, column_step in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            target = (row + row_step, column + column_step)
            if not (0 <= target[0] < ROWS and 0 <= target[1] < COLUMNS):
                continue
            if {row, target[0]} == {5, 6} and column not in {0, 2, 4}:
                continue
            neighbors.add(target)
        for row_step in (-1, 1):
            for column_step in (-1, 1):
                target = (row + row_step, column + column_step)
                if not (0 <= target[0] < ROWS and 0 <= target[1] < COLUMNS):
                    continue
                if position in CAMPS or target in CAMPS:
                    neighbors.add(target)
        return neighbors

    @staticmethod
    def _is_rail_edge(
        source: tuple[int, int], target: tuple[int, int]
    ) -> bool:
        if abs(source[0] - target[0]) + abs(source[1] - target[1]) != 1:
            return False
        if source[0] == target[0]:
            return source[0] in RAIL_ROWS
        if source[1] == target[1] and source[1] in {0, 4}:
            return 1 <= min(source[0], target[0]) and max(source[0], target[0]) <= 10
        return {source, target} == {(5, 2), (6, 2)}

    def _rail_neighbors(self, position: tuple[int, int]) -> set[tuple[int, int]]:
        neighbors = set()
        for row_step, column_step in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            target = (position[0] + row_step, position[1] + column_step)
            if 0 <= target[0] < ROWS and 0 <= target[1] < COLUMNS:
                if self._is_rail_edge(position, target):
                    neighbors.add(target)
        return neighbors

    @staticmethod
    def _combat(attacker: JunqiPiece, defender: JunqiPiece) -> str:
        if defender.kind == "flag":
            return "flag"
        if attacker.kind == "bomb" or defender.kind == "bomb":
            return "both"
        if defender.kind == "mine":
            return "attacker" if attacker.kind == "engineer" else "defender"
        attacker_rank = RANKS[attacker.kind]
        defender_rank = RANKS[defender.kind]
        if attacker_rank > defender_rank:
            return "attacker"
        if attacker_rank < defender_rank:
            return "defender"
        return "both"

    def _mark_removed(self, state: JunqiState, piece: JunqiPiece) -> None:
        if piece.kind != "commander":
            return
        state.commander_captured[piece.side] = True
        for row in state.board:
            for candidate in row:
                if candidate is not None and candidate.side == piece.side and candidate.kind == "flag":
                    candidate.revealed = True

    @staticmethod
    def _has_movable_piece(state: JunqiState, side: int) -> bool:
        for row_index, row in enumerate(state.board):
            for column_index, piece in enumerate(row):
                if piece is None or piece.side != side:
                    continue
                if piece.kind not in {"mine", "flag"} and (row_index, column_index) not in HEADQUARTERS:
                    return True
        return False

    @staticmethod
    def _position(
        payload: dict[str, Any], row_key: str, column_key: str
    ) -> tuple[int, int]:
        row = payload.get(row_key)
        column = payload.get(column_key)
        if (
            not isinstance(row, int)
            or isinstance(row, bool)
            or not isinstance(column, int)
            or isinstance(column, bool)
        ):
            raise GameRuleError("棋盘坐标格式不正确")
        if not 0 <= row < ROWS or not 0 <= column < COLUMNS:
            raise GameRuleError("棋盘坐标超出范围")
        return row, column

    @staticmethod
    def _side_for_seat(state: JunqiState, seat: int) -> int:
        side = state.seat_sides[seat]
        return seat if side is None else side

    @staticmethod
    def _side_label(side: int) -> str:
        return "红方" if side == 0 else "蓝方"
