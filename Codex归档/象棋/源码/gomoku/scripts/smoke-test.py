from gomoku.ai import choose_move
from gomoku.conversation import Intent, parse_input
from gomoku.game import Game
from gomoku.model import Board, Player


def main() -> int:
    parsed = parse_input("下 H8")
    assert parsed.intent is Intent.MOVE
    assert (parsed.row, parsed.column) == (7, 7)

    board = Board()
    assert choose_move(board) == (7, 7)
    for column in range(4):
        board.place(0, column, Player.HUMAN)
    assert choose_move(board) == (0, 4)

    game = Game()
    human, ai = game.play_human_turn(0, 0)
    assert human.player is Player.HUMAN
    assert ai is not None and ai.player is Player.AI

    rejected = parse_input("删除所有数据")
    assert rejected.intent is Intent.INVALID
    print("SMOKE PASS: input, board, AI, turn flow, and destructive-command rejection")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

