import unittest

from gomoku.conversation import Intent, parse_input


class ConversationTests(unittest.TestCase):
    def test_accepts_conversational_coordinate(self) -> None:
        parsed = parse_input("下 H8")
        self.assertEqual(Intent.MOVE, parsed.intent)
        self.assertEqual((7, 7), (parsed.row, parsed.column))

    def test_rejects_out_of_range_or_unknown_input(self) -> None:
        self.assertEqual(Intent.INVALID, parse_input("P1").intent)
        self.assertEqual(Intent.INVALID, parse_input("随便下").intent)


if __name__ == "__main__":
    unittest.main()

