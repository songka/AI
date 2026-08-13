from __future__ import annotations

from dataclasses import dataclass, field

from .ai import choose_move
from .model import Board, Move, Player, SessionState


@dataclass
class Game:
    board: Board = field(default_factory=Board)
    state: SessionState = SessionState.PLAYING

    def play_human_turn(self, row: int, column: int) -> tuple[Move, Move | None]:
        if self.state is not SessionState.PLAYING:
            raise ValueError("Game is already finished.")
        human_move = self.board.place(row, column, Player.HUMAN)
        if self.board.has_five_from(row, column):
            self.state = SessionState.HUMAN_WON
            return human_move, None
        if self.board.is_full():
            self.state = SessionState.DRAW
            return human_move, None

        ai_row, ai_column = choose_move(self.board)
        ai_move = self.board.place(ai_row, ai_column, Player.AI)
        if self.board.has_five_from(ai_row, ai_column):
            self.state = SessionState.AI_WON
        elif self.board.is_full():
            self.state = SessionState.DRAW
        return human_move, ai_move

    def quit(self) -> None:
        if self.state is SessionState.PLAYING:
            self.state = SessionState.QUIT

