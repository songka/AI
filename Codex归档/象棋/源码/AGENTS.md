# Gomoku project instructions

These instructions apply to the `gomoku/` project and its project skill at
`.agents/skills/manage-gomoku/`.

## Mandatory code–Skill synchronization gate

Before every project change:

1. Read `.agents/skills/manage-gomoku/SKILL.md` and the reference files relevant
   to the requested work.
2. Decide whether the change affects architecture, commands, data structures,
   safety rules, tests, release behavior, or the project version.
3. If it does, update the corresponding Skill reference and
   `gomoku/project-contract.json` in the same change.
4. If it does not, state why no Skill update is needed in the handoff.
5. Run `powershell -ExecutionPolicy Bypass -File gomoku/scripts/validate-project.ps1`.
   Do not describe the change as complete, publish it, or package it if validation
   fails.

The contract file is the machine-readable synchronization source. Never weaken a
contract check merely to make validation pass.

## Safety

- Never automatically delete or overwrite project data, user data, releases, or
  saved games.
- Never add persistence, telemetry, network access, shell execution, or destructive
  commands without explicit user authorization and corresponding safety tests and
  Skill updates.
- Treat passwords, tokens, keys, user data, logs, caches, and generated packages as
  forbidden release contents.
- Preserve unrelated user changes.

