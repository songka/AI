# Architecture

## Scope and scenarios

The product is a Windows-local terminal conversation in which one human plays
standard freestyle Gomoku against a deterministic rule-based AI. Typical scenarios
are starting a game, entering a coordinate in natural shorthand, receiving an AI
reply, rejecting invalid or occupied moves, detecting a win/draw, asking for help,
and quitting without saving data.

Out of scope for version 0.1.0: accounts, saved games, deletion, online play,
telemetry, model APIs, GUI automation, and external deployment.

## Boundaries and flow

`cli` → `conversation` → `game` → (`model`, `ai`)

- `src/gomoku/model.py` owns domain values and pure board rules. It must not parse
  text, print, access files, or access the network.
- `src/gomoku/ai.py` reads a board and returns a legal move. It may simulate a cell
  only with guaranteed restoration and must not append fake move history.
- `src/gomoku/conversation.py` recognizes moves, help, quit, and invalid input. It
  rejects destructive wording and has no side effects.
- `src/gomoku/game.py` owns human/AI turn ordering and session transitions.
- `src/gomoku/cli.py` is the only interactive I/O layer.
- `scripts/` contains development and release gates; runtime modules do not import it.

Dependencies point inward toward the domain. No runtime third-party dependency is
required.

## AI strategy

Choose in this order: immediate AI win, immediate human-win block, center-nearest
open cell with deterministic row/column tie-breaking. This is intentionally simple
and testable, not a claim of strong play.

## Testing and release

Unit tests isolate parsing, board rules, AI decisions, and safety. Regression tests
cover full turn flows. Smoke testing covers the critical playable path. The
contract test binds machine-readable code and Skill facts. PowerShell performs all
gates before the release script constructs a ZIP.

No GitHub remote is configured at initialization, so no GitHub Actions workflow is
created. If the project later uses GitHub, add CI that runs the same
`scripts/validate-project.ps1` command on push and pull request.

