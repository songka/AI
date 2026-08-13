---
name: manage-gomoku
description: Safely modify, diagnose, test, validate, or release the local Python conversational Gomoku project. Use for gameplay rules, board or move data, human/AI dialogue, AI move strategy, CLI commands, regression fixes, safety controls, packaging, version changes, or any change under gomoku/ that may require synchronized updates to the project contract, tests, AGENTS.md, or this Skill.
---

# Manage Gomoku

Manage the Windows-local, in-memory human-versus-AI Gomoku application while
keeping code, tests, safety policy, commands, schema, and release behavior in sync.

Project version: `0.1.0`

## Start every task

1. Read `../../../AGENTS.md` and `../../../gomoku/project-contract.json`.
2. Read the references relevant to the task:
   - Read [references/architecture.md](references/architecture.md) for module or
     behavior changes.
   - Read [references/data-schema.md](references/data-schema.md) for board, move,
     session, coordinate, or version changes.
   - Read [references/safety-policy.md](references/safety-policy.md) for input,
     persistence, filesystem, network, packaging, or other risky changes.
   - Read [references/commands.md](references/commands.md) for test, validation,
     execution, or release work.
3. Classify the request as modify, diagnose, test, or release.
4. Decide whether architecture, commands, schema, safety rules, tests, release
   behavior, or version changes. Update the matching reference and
   `project-contract.json` in the same patch when it does.

## Follow the fixed workflow

### Modify

1. Inspect the affected module and its tests.
2. Make the smallest compatible change within the module boundaries below.
3. Update the contract, Skill reference, and mapped safety test together when
   their shared subject changes.
4. Add or update unit and regression coverage.
5. Run the unified validation command from `references/commands.md`.

### Diagnose

1. Reproduce the failure with the narrowest test or command.
2. Trace the behavior through conversation, game, model, and AI layers as needed.
3. Report the cause with evidence. Do not change code unless the user requests a
   fix.
4. If fixing, follow the Modify workflow and add a regression test.

### Test

1. Run the narrowest relevant test during iteration.
2. Finish with `scripts/validate-project.ps1`; do not skip or reorder its gates.
3. Treat a failed contract, safety, sensitive-file, or Skill check as a project
   failure, not a documentation-only warning.

### Release

1. Review `references/safety-policy.md` and `references/commands.md`.
2. Run `scripts/release.ps1`; never bypass its validation call.
3. Include this Skill only when the user explicitly requests it, using
   `-IncludeSkill`.
4. Never overwrite an existing package. Report any partial package left by a
   packaging failure; do not delete it automatically.

## Respect module boundaries

- `model.py`: board, players, moves, session states, placement, and win detection.
- `ai.py`: deterministic legal AI move selection only.
- `conversation.py`: safe text-to-intent and coordinate parsing.
- `game.py`: turn orchestration and terminal state transitions.
- `cli.py`: terminal input/output and board rendering.
- `scripts/`: deterministic validation, contract, safety, smoke, and release gates.
- `tests/`: unit, regression, and safety behavior.

Read `references/architecture.md` before moving responsibilities across modules.

## Never execute automatically

- Delete, clear, reset, overwrite, or migrate user/project data or existing packages.
- Add or use persistence, telemetry, networking, subprocess/shell execution, or
  credential handling without explicit user authorization.
- Publish, upload, push, tag, install, or deploy externally.
- Weaken, skip, or reorder validation gates to make a change pass.
- Package passwords, tokens, keys, user data, logs, caches, or generated packages.
- Include the project Skill in the runtime package without `-IncludeSkill`.

