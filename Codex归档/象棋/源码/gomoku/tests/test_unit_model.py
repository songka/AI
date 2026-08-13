import unittest

from gomoku.model import Board, Player


class BoardTests(unittest.TestCase):
    def test_place_rejects_occupied_position(self) -> None:
        board = Board()
        board.place(0, 0, Player.HUMAN)
        with self.assertRaisesRegex(ValueError, "occupied"):
            board.place(0, 0, Player.AI)

    def test_detects_five_in_each_direction(self) -> None:
        for row_step, column_step in ((1, 0), (0, 1), (1, 1), (1, -1)):
            board = Board()
            start_row = 2
            start_column = 6
            for offset in range(5):
                row = start_row + offset * row_step
                column = start_column + offset * column_step
                board.place(row, column, Player.HUMAN)
            self.assertTrue(board.has_five_from(row, column))


if __name__ == "__main__":
    unittest.main()

