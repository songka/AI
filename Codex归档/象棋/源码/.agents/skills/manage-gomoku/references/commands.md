# Commands

Run commands from the `gomoku/` directory. The Windows play and validation scripts
set `PYTHONPATH=src` automatically.

The following block is contractual and must exactly match the `commands` object in
`gomoku/project-contract.json`.

<!-- CONTRACT:COMMANDS -->
```json
{
  "play": "powershell -ExecutionPolicy Bypass -File scripts/play.ps1",
  "validate": "powershell -ExecutionPolicy Bypass -File scripts/validate-project.ps1",
  "release": "powershell -ExecutionPolicy Bypass -File scripts/release.ps1",
  "release_with_skill": "powershell -ExecutionPolicy Bypass -File scripts/release.ps1 -IncludeSkill",
  "smoke_test": "python scripts/smoke-test.py"
}
```

`validate-project.ps1` executes, in order: compile/static check, unit tests,
regression tests, business/safety smoke test, Skill smoke test, local
`quick_validate.py`, code–Skill contract test, and sensitive-file check.

The release command always invokes validation first. `-IncludeSkill` is off by
default. `-OutputPath` may select a new destination but never an existing file.

