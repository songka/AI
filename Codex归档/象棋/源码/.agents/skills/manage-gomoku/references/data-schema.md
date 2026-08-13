# Data schema

The application keeps one session in memory. It writes no game or user data.
Coordinates are presented as `A1` through `O15` and stored as zero-based row and
column integers.

The following block is contractual and must exactly match the `data_schema` object
in `gomoku/project-contract.json`.

<!-- CONTRACT:DATA_SCHEMA -->
```json
{
  "board": {
    "size": 15,
    "columns": "A-O",
    "rows": "1-15",
    "cell_values": [
      "empty",
      "human",
      "ai"
    ]
  },
  "move": {
    "fields": {
      "turn": "positive integer",
      "row": "integer 0-14",
      "column": "integer 0-14",
      "player": "human|ai"
    }
  },
  "session": {
    "persistence": "none",
    "states": [
      "playing",
      "human_won",
      "ai_won",
      "draw",
      "quit"
    ]
  }
}
```

`Board.cells` uses `None`, `Player.HUMAN`, and `Player.AI` internally. `Move` is
immutable. `Board.moves` is append-only during a session. A session state may leave
`playing` only once.

