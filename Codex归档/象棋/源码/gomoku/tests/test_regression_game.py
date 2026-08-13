import unittest

from gomoku.game import Game
from gomoku.model import Player, SessionState


class GameRegressionTests(unittest.TestCase):
    def test_human_win_stops_ai_reply(self) -> None:
        game = Game()
        for column in range(4):
            game.board.place(0, column, Player.HUMAN)
        _, ai_move = game.play_human_turn(0, 4)
        self.assertIsNone(ai_move)
        self.assertEqual(SessionState.HUMAN_WON, game.state)

    def test_normal_turn_records_human_then_ai(self) -> None:
        game = Game()
        human, ai = game.play_human_turn(0, 0)
        self.assertEqual(Player.HUMAN, human.player)
        self.assertIsNotNone(ai)
        self.assertEqual(Player.AI, ai.player)
        self.assertEqual(2, len(game.board.moves))


if __name__ == "__main__":
    unittest.main()

