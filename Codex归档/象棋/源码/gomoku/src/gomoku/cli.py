from __future__ import annotations

from .conversation import Intent, parse_input
from .game import Game
from .model import Board, Player, SessionState


def coordinate(row: int, column: int) -> str:
    return f"{chr(ord('A') + column)}{row + 1}"


def render_board(board: Board) -> str:
    header = "    " + " ".join(chr(ord("A") + column) for column in range(board.size))
    lines = [header]
    symbols = {None: "·", Player.HUMAN: "●", Player.AI: "○"}
    for row in range(board.size):
        cells = " ".join(symbols[board.cells[row][column]] for column in range(board.size))
        lines.append(f"{row + 1:>2}  {cells}")
    return "\n".join(lines)


def main() -> int:
    game = Game()
    print("五子棋：你是 ●，AI 是 ○。输入 H8 或“下 H8”；输入 help 查看帮助。")
    print(render_board(game.board))
    while game.state is SessionState.PLAYING:
        try:
            raw = input("你> ")
        except (EOFError, KeyboardInterrupt):
            game.quit()
            print("\n对局已退出；本程序不保存对局数据。")
            break
        parsed = parse_input(raw)
        if parsed.intent is Intent.HELP:
            print("输入 A1 到 O15 的空位坐标落子；输入 quit 退出。")
            continue
        if parsed.intent is Intent.QUIT:
            game.quit()
            print("对局已退出；本程序不保存对局数据。")
            break
        if parsed.intent is Intent.INVALID:
            print(parsed.message)
            continue
        assert parsed.row is not None and parsed.column is not None
        try:
            _, ai_move = game.play_human_turn(parsed.row, parsed.column)
        except ValueError as error:
            print(f"不能落子：{error}")
            continue
        if ai_move is not None:
            print(f"AI> 下 {coordinate(ai_move.row, ai_move.column)}")
        print(render_board(game.board))

    endings = {
        SessionState.HUMAN_WON: "你赢了！",
        SessionState.AI_WON: "AI 赢了。",
        SessionState.DRAW: "和棋。",
    }
    if game.state in endings:
        print(endings[game.state])
    return 0

