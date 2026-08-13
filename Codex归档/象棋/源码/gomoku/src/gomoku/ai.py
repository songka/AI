from __future__ import annotations

from .model import Board, Player


def choose_move(board: Board) -> tuple[int, int]:
    """Choose a deterministic legal move: win, block, center, then nearest open."""
    open_positions = [
        (row, column)
        for row in range(board.size)
        for column in range(board.size)
        if board.cells[row][column] is None
    ]
    if not open_positions:
        raise ValueError("No legal moves remain.")

    for player in (Player.AI, Player.HUMAN):
        for row, column in open_positions:
            if _would_win(board, row, column, player):
                return row, column

    center = board.size // 2
    return min(
        open_positions,
        key=lambda position: (
            abs(position[0] - center) + abs(position[1] - center),
            position[0],
            position[1],
        ),
    )


def _would_win(board: Board, row: int, column: int, player: Player) -> bool:
    board.cells[row][column] = player
    try:
        return board.has_five_from(row, column)
    finally:
        board.cells[row][column] = None

