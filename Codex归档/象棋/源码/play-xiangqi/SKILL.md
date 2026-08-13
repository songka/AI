---
name: play-xiangqi
description: Conduct interactive Chinese chess (Xiangqi) games in conversation, including starting or resuming games, rendering boards, accepting Chinese notation or coordinate moves, checking move legality, maintaining turn-by-turn state, giving tiered hints, explaining positions, and reviewing completed games. Use when the user wants to play 象棋/中国象棋, submit a move such as 炮二平五, inspect a Xiangqi FEN position, ask for a hint, undo a move, or analyze/replay a game.
---

# Play Xiangqi

Act as a reliable, conversational Xiangqi board and opponent. Keep the game easy to operate from ordinary chat.

## Interaction contract

Read [references/interaction.md](references/interaction.md) before starting or resuming an interactive game.

- Treat the conversation as the session. Maintain the initial position, move list, current FEN, side to move, user side, difficulty, and pending confirmation.
- Accept natural commands, Chinese descriptive notation, UCCI coordinates, and FEN. Prefer Chinese notation in user-facing replies.
- Never invent a move when input is ambiguous. Show the matching candidates and ask for a choice.
- Validate every committed move. Use `scripts/xiangqi.py` for FEN display and UCCI move validation when exactness matters.
- Render the complete current board in every reply while a game is active, including routine turns, hints, analysis, rejected moves, and confirmation prompts. Then state whose turn it is.
- Do not reveal evaluation or best moves unless the user asks for analysis or a hint.

## Start or resume

When the user says only “下棋”, “开始” or similar, start from the standard position, let the user play Red, choose normal difficulty, and briefly state that Red moves first. Do not force a setup questionnaire.

Honor preferences given in the same request: user side, difficulty, handicap, starting FEN, board orientation, and whether Codex should play the opponent. If the user chooses Black, make Red's first move and then present the board.

On resume, reconstruct state from the latest trusted board/FEN and move list. If the history and board disagree, pause and identify the discrepancy instead of guessing.

## Process a turn

1. Parse the command without changing state.
2. Resolve notation against the current legal moves. If zero moves match, explain the precise conflict and suggest likely legal alternatives. If multiple moves match, request confirmation.
3. Commit exactly one move only after it is unambiguous and legal.
4. Detect check, checkmate, stalemate, repetition, or user resignation. Announce check immediately.
5. If acting as opponent, select a move appropriate to the chosen difficulty and commit it with the same checks.
6. Reply using the turn format in the interaction reference and always include the complete board.

For a user correction such as “不是炮二平五，是马二进三”, roll back only the most recent affected turn, confirm the replacement is legal, and restate the corrected position.

## Commands

- `棋盘` / `局面`: show the current board and status.
- `提示`: give one progressive hint; do not move a piece.
- `分析`: explain threats, candidate moves, and tactical/strategic considerations.
- `悔棋`: undo the last full turn by default; if only one ply exists, undo that ply.
- `重来`: request confirmation if a game is active, then reset.
- `认输` / `和棋`: handle the game result explicitly.
- `导出`: return FEN plus numbered Chinese move history; include UCCI history if requested.
- `复盘`: summarize turning points first, then inspect requested moves in depth.

## Hint ladder

Track the hint level for the current position:

1. Point out the relevant area or danger.
2. Name the tactical motif or strategic goal.
3. Offer two candidate pieces or moves.
4. Give the recommended move with a short principal variation.

Advance one level per repeated “提示”. Reset after the position changes.

## Rule reliability

Enforce palace limits, river restrictions, horse-leg blocks, elephant-eye blocks, cannon screens, flying generals, self-check, and turn order. Distinguish “将军” from “将死”. Do not claim a draw from repetition without enough recorded history.

Use the utility as follows:

```powershell
python scripts/xiangqi.py show --fen "<fen>"
python scripts/xiangqi.py move --fen "<fen>" --move h2e2
```

The `move` command prints the resulting FEN and board or exits nonzero with the legality error. UCCI files are `a` through `i` from Black's left to right; ranks are `0` through `9` from Black's home rank to Red's home rank.

## Analysis style

Separate facts from judgment. Name immediate checks, captures, and threats before positional advice. At beginner difficulty, prefer instructive natural moves and explain errors kindly. At advanced difficulty, be concise and include concrete variations. Never pretend to have searched deeper than actually performed.
