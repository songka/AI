from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum

from .model import BOARD_SIZE


class Intent(str, Enum):
    MOVE = "move"
    HELP = "help"
    QUIT = "quit"
    INVALID = "invalid"


@dataclass(frozen=True)
class ParsedInput:
    intent: Intent
    row: int | None = None
    column: int | None = None
    message: str = ""


_MOVE_PATTERN = re.compile(
    r"^\s*(?:(?:下|落子|move|play)\s*)?([A-Oa-o])\s*(1[0-5]|[1-9])\s*$",
    re.IGNORECASE,
)
_HELP_WORDS = {"help", "?", "帮助", "说明"}
_QUIT_WORDS = {"quit", "exit", "q", "退出", "结束"}
_DESTRUCTIVE_WORDS = {"delete", "remove", "clear", "reset", "删除", "清空", "重置"}


def parse_input(text: str) -> ParsedInput:
    normalized = text.strip().lower()
    if normalized in _HELP_WORDS:
        return ParsedInput(Intent.HELP)
    if normalized in _QUIT_WORDS:
        return ParsedInput(Intent.QUIT)
    if any(word in normalized for word in _DESTRUCTIVE_WORDS):
        return ParsedInput(Intent.INVALID, message="不支持删除、清空或重置数据的命令。")
    match = _MOVE_PATTERN.fullmatch(text)
    if not match:
        return ParsedInput(Intent.INVALID, message="请输入坐标，例如 H8 或“下 H8”。")
    column = ord(match.group(1).upper()) - ord("A")
    row = int(match.group(2)) - 1
    if row >= BOARD_SIZE or column >= BOARD_SIZE:
        return ParsedInput(Intent.INVALID, message="坐标必须在 A1 到 O15 之间。")
    return ParsedInput(Intent.MOVE, row=row, column=column)

