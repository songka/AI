from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


BOARD_SIZE = 15


class Player(str, Enum):
    HUMAN = "human"
    AI = "ai"


class SessionState(str, Enum):
    PLAYING = "playing"
    HUMAN_WON = "human_won"
    AI_WON = "ai_won"
    DRAW = "draw"
    QUIT = "quit"


@dataclass(frozen=True)
class Move:
    turn: int
    row: int
    column: int
    player: Player


@dataclass
class Board:
    size: int = BOARD_SIZE
    cells: list[list[Player | None]] = field(init=False)
    moves: list[Move] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.size < 5:
            raise ValueError("Board size must be at least 5.")
        self.cells = [[None for _ in range(self.size)] for _ in range(self.size)]

    def place(self, row: int, column: int, player: Player) -> Move:
        if not self.in_bounds(row, column):
            raise ValueError("Move is outside the board.")
        if self.cells[row][column] is not None:
            raise ValueError("Position is already occupied.")
        move = Move(len(self.moves) + 1, row, column, player)
        self.cells[row][column] = player
        self.moves.append(move)
        return move

    def in_bounds(self, row: int, column: int) -> bool:
        return 0 <= row < self.size and 0 <= column < self.size

    def is_full(self) -> bool:
        return len(self.moves) == self.size * self.size

    def has_five_from(self, row: int, column: int) -> bool:
        player = self.cells[row][column]
        if player is None:
            return False
        for row_step, column_step in ((1, 0), (0, 1), (1, 1), (1, -1)):
            total = 1
            total += self._count(row, column, row_step, column_step, player)
            total += self._count(row, column, -row_step, -column_step, player)
            if total >= 5:
                return True
        return False

    def _count(
        self,
        row: int,
        column: int,
        row_step: int,
        column_step: int,
        player: Player,
    ) -> int:
        count = 0
        row += row_step
        column += column_step
        while self.in_bounds(row, column) and self.cells[row][column] is player:
            count += 1
            row += row_step
            column += column_step
        return count

