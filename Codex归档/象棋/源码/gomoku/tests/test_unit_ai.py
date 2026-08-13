import unittest

from gomoku.ai import choose_move
from gomoku.model import Board, Player


class AiTests(unittest.TestCase):
    def test_ai_takes_winning_move(self) -> None:
        board = Board()
        for column in range(4):
            board.place(0, column, Player.AI)
        self.assertEqual((0, 4), choose_move(board))

    def test_ai_blocks_human_win(self) -> None:
        board = Board()
        for column in range(4):
            board.place(0, column, Player.HUMAN)
        self.assertEqual((0, 4), choose_move(board))

    def test_ai_opens_in_center(self) -> None:
        self.assertEqual((7, 7), choose_move(Board()))


if __name__ == "__main__":
    unittest.main()

